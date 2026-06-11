from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# 评测会大量写入会话、日志和 trace；默认使用临时库，避免 make eval 污染已跟踪的演示 SQLite。
EVAL_DB_PATH = Path(tempfile.gettempdir()) / "serviceflow-agent-console-eval.db"
os.environ.setdefault("SERVICEFLOW_DB_PATH", str(EVAL_DB_PATH))

from fastapi.testclient import TestClient  # noqa: E402

from app.rate_limit import reset_rate_limit_buckets  # noqa: E402
from app.seed import seed_database  # noqa: E402
from evals.metrics import accuracy, confusion_matrix, rate  # noqa: E402
from main import app  # noqa: E402

DATASET_DIR = ROOT / "evals" / "datasets"
REPORT_DIR = ROOT / "reports"
ADMIN_HEADERS = {"X-User-Role": "admin"}


def load_jsonl(name: str) -> list[dict]:
    path = DATASET_DIR / f"{name}_eval.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def post_chat(client: TestClient, message: str, conversation_id: str | None = None) -> dict:
    # 离线评测关注业务链路质量，避免 TestClient 固定 IP 触发 Demo 防刷限流。
    reset_rate_limit_buckets()
    response = client.post("/api/chat", json={"message": message, "user_id": "U1001", "conversation_id": conversation_id})
    response.raise_for_status()
    return response.json()


def eval_intent(client: TestClient) -> dict:
    pairs = []
    failed = []
    for item in load_jsonl("intent"):
        actual = post_chat(client, item["input"])["intent"]
        pairs.append((item["expected_intent"], actual))
        if actual != item["expected_intent"]:
            failed.append((item["id"], item["input"], item["expected_intent"], actual, "intent mismatch"))
    return {"accuracy": accuracy(pairs), "confusion_matrix": confusion_matrix(pairs), "failed": failed}


def eval_rag(client: TestClient) -> dict:
    hit, citation_hit, contains, empty, failed = [], [], [], [], []
    for item in load_jsonl("rag"):
        result = post_chat(client, item["input"])
        docs = result.get("retrieved_docs", [])
        citations = result.get("citations", [])
        hit_ok = any(doc.get("knowledge_base") == item["expected_knowledge_base"] for doc in docs)
        citation_ok = any(item["expected_source_contains"] in citation.get("source_file", "") for citation in citations)
        contains_ok = all(word in result.get("answer", "") for word in item.get("must_contain", []))
        hit.append(hit_ok)
        citation_hit.append(citation_ok)
        contains.append(contains_ok)
        empty.append(not docs)
        if not (hit_ok and citation_ok and contains_ok):
            failed.append((item["id"], item["input"], item["expected_source_contains"], str(citations), "rag expectation failed"))
    return {
        "hit_rate": rate(hit),
        "citation_hit_rate": rate(citation_hit),
        "answer_contains_rate": rate(contains),
        "empty_result_rate": rate(empty),
        "failed": failed,
    }


def eval_tool(client: TestClient) -> dict:
    selected, success, wrong, failed = [], [], 0, []
    for item in load_jsonl("tool"):
        result = post_chat(client, item["input"])
        calls = result.get("tool_calls", [])
        names = [call.get("name") for call in calls]
        selected_ok = item["expected_tool"] in names
        selected.append(selected_ok)
        call_success = any(call.get("name") == item["expected_tool"] and bool((call.get("output") or {}).get("success", True)) == item["expected_success"] for call in calls)
        success.append(call_success)
        if calls and not selected_ok:
            wrong += 1
        if not (selected_ok and call_success):
            failed.append((item["id"], item["input"], item["expected_tool"], ",".join(names), "tool expectation failed"))
    return {"tool_selection_accuracy": rate(selected), "tool_success_rate": rate(success), "wrong_tool_call_count": wrong, "failed": failed}


def eval_e2e(client: TestClient) -> dict:
    task_ok, state_ok, turns, failed = [], [], [], []
    for item in load_jsonl("end_to_end"):
        conversation_id = None
        final = {}
        seen_tools = set()
        for message in item["messages"]:
            final = post_chat(client, message, conversation_id)
            conversation_id = final["conversation_id"]
            seen_tools.update(call.get("name") for call in final.get("tool_calls", []))
        expected_tools = set(item.get("expected_tools", []))
        tools_ok = expected_tools.issubset(seen_tools)
        intent_ok = final.get("intent") == item.get("expected_final_intent")
        return_created = not item.get("expected_state", {}).get("return_created") or bool(final.get("return_result", {}).get("success"))
        ok = intent_ok and tools_ok and return_created
        task_ok.append(ok)
        state_ok.append(return_created)
        turns.append(len(item["messages"]))
        if not ok:
            failed.append((item["id"], " / ".join(item["messages"]), str(expected_tools), str(seen_tools), "e2e failed"))
    return {"task_success_rate": rate(task_ok), "avg_turns": round(sum(turns) / len(turns), 2), "state_success_rate": rate(state_ok), "regression_failed_cases": len(failed), "failed": failed}


def run(selected: list[str]) -> dict:
    seed_database(reset=True)
    client = TestClient(app)
    results = {}
    if "intent" in selected:
        results["intent"] = eval_intent(client)
    if "rag" in selected:
        results["rag"] = eval_rag(client)
    if "tool" in selected:
        results["tool"] = eval_tool(client)
    if "e2e" in selected:
        results["e2e"] = eval_e2e(client)
    return results


def write_report(results: dict) -> Path:
    REPORT_DIR.mkdir(exist_ok=True)
    failed = []
    for result in results.values():
        failed.extend(result.get("failed", []))
    failed_rows = "\n".join(f"| {case[0]} | {case[1]} | {case[2]} | {case[3]} | {case[4]} |" for case in failed) or "| - | - | - | - | - |"
    content = (ROOT / "evals" / "report_template.md").read_text(encoding="utf-8").format(
        intent_accuracy=results.get("intent", {}).get("accuracy", "-"),
        rag_hit_rate=results.get("rag", {}).get("hit_rate", "-"),
        tool_selection_accuracy=results.get("tool", {}).get("tool_selection_accuracy", "-"),
        e2e_success_rate=results.get("e2e", {}).get("task_success_rate", "-"),
        failed_rows=failed_rows,
    )
    path = REPORT_DIR / f"eval_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(content, encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["intent", "rag", "tool", "e2e"])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    selected = ["intent", "rag", "tool", "e2e"] if args.all or not args.dataset else [args.dataset]
    results = run(selected)
    report_path = write_report(results)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
