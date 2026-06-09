from __future__ import annotations

import argparse
import asyncio
import json
import statistics
from datetime import datetime
from pathlib import Path
from time import perf_counter

import httpx


SCENARIOS = [
    ["帮我查一下订单 10001 到哪里了"],
    ["路由器无法连接 WiFi 怎么办？"],
    ["7 天无理由退货规则是什么？"],
    ["我要找人工客服"],
    ["我要退货", "10001", "买错了", "确认"],
]


async def run_single(client: httpx.AsyncClient, scenario: list[str], index: int) -> dict:
    conversation_id = None
    started = perf_counter()
    try:
        for message in scenario:
            response = await client.post(
                "/api/chat",
                json={"message": message, "user_id": f"LOAD_{index}", "conversation_id": conversation_id},
            )
            response.raise_for_status()
            body = response.json()
            conversation_id = body.get("conversation_id")
        return {"success": True, "latency_ms": (perf_counter() - started) * 1000, "error": None}
    except Exception as exc:
        return {"success": False, "latency_ms": (perf_counter() - started) * 1000, "error": str(exc)}


async def run_load_test(base_url: str, users: int, requests: int) -> dict:
    semaphore = asyncio.Semaphore(users)
    started = perf_counter()

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        async def bounded(index: int):
            async with semaphore:
                # 轮询不同场景，覆盖订单、RAG、转人工和多轮退货。
                return await run_single(client, SCENARIOS[index % len(SCENARIOS)], index)

        results = await asyncio.gather(*(bounded(index) for index in range(requests)))

    total_seconds = perf_counter() - started
    latencies = [item["latency_ms"] for item in results]
    success = sum(1 for item in results if item["success"])
    failed = requests - success
    return {
        "total_requests": requests,
        "success": success,
        "failed": failed,
        "avg_latency_ms": round(statistics.mean(latencies), 3) if latencies else 0,
        "p95_latency_ms": percentile(latencies, 0.95),
        "qps": round(requests / total_seconds, 3) if total_seconds else 0,
        "errors": [item["error"] for item in results if item["error"]][:10],
    }


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((len(ordered) - 1) * ratio)))
    return round(ordered[index], 3)


def write_report(result: dict) -> Path:
    reports_dir = Path(__file__).resolve().parents[1] / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(
        "# ServiceFlow Load Test Report\n\n"
        f"- Total Requests: {result['total_requests']}\n"
        f"- Success: {result['success']}\n"
        f"- Failed: {result['failed']}\n"
        f"- Average Latency: {result['avg_latency_ms']} ms\n"
        f"- P95 Latency: {result['p95_latency_ms']} ms\n"
        f"- QPS: {result['qps']}\n\n"
        "## Errors\n\n"
        + ("\n".join(f"- {error}" for error in result["errors"]) if result["errors"] else "None")
        + "\n",
        encoding="utf-8",
    )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="ServiceFlow Agent async load test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--users", type=int, default=20)
    parser.add_argument("--requests", type=int, default=200)
    args = parser.parse_args()

    result = asyncio.run(run_load_test(args.base_url, args.users, args.requests))
    report = write_report(result)
    print(json.dumps({**result, "report": str(report)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
