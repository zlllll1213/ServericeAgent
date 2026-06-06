from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.agent.persistence import get_or_create_conversation, save_conversation_state, write_chat_log
from app.agent.router import classify_intent_hybrid
from app.agent.state import AgentState
from app.evaluation import evaluate_response
from app.llm.client import get_llm_client
from app.llm.prompts import HUMAN_SUMMARY_PROMPT, RAG_ANSWER_PROMPT
from app.rag.service import retrieve_documents
from app.tools.customer_tools import create_return_request, create_ticket, get_order_status, get_refund_status

ORDER_PATTERN = re.compile(r"(?:订单号?|order)\s*[:：]?\s*(\d{5,})|(\b\d{5,}\b)", re.IGNORECASE)
RETURN_PATTERN = re.compile(r"(?:退货单|return_id)\s*[:：]?\s*([A-Z]?\d{8,})", re.IGNORECASE)
REASON_PATTERN = re.compile(r"(?:原因是|原因[:：]|因为)([^，。,.!！?？]+)")
CONFIRM_WORDS = {"确认", "是的", "可以", "提交", "帮我创建"}
CANCEL_WORDS = {"取消", "算了", "不用了", "先不退了"}
RETURN_REASONS = ["不想要了", "质量问题", "买错了", "其他"]


def _trace(state: AgentState, node_name: str) -> list[str]:
    return [*state.get("route_trace", []), node_name]


def _tool_call(name: str, input_data: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "input": input_data, "output": output}


def _pending_action(value: str | None) -> str:
    return value if value and value != "NONE" else "NONE"


def load_conversation_node(state: AgentState) -> AgentState:
    conversation = get_or_create_conversation(state.get("conversation_id"), state.get("user_id", "U1001"))
    return {
        **state,
        "conversation_id": conversation["conversation_id"],
        "current_intent": conversation.get("current_intent"),
        "pending_action": conversation.get("pending_action") or "NONE",
        "slots": conversation.get("slots", {}),
        "history": conversation.get("history", []),
        "route_trace": _trace(state, "load_conversation_node"),
    }


def parse_input_node(state: AgentState) -> AgentState:
    message = state["user_message"].strip()
    slots = {**state.get("slots", {})}
    extracted_slots: dict[str, Any] = {}
    order_match = ORDER_PATTERN.search(message)
    return_match = RETURN_PATTERN.search(message)
    reason_match = REASON_PATTERN.search(message)

    if order_match:
        extracted_slots["order_id"] = next(group for group in order_match.groups() if group)
    if return_match:
        extracted_slots["return_id"] = return_match.group(1)
    if reason_match:
        extracted_slots["return_reason"] = reason_match.group(1).strip()
    else:
        for reason in RETURN_REASONS:
            if reason in message:
                extracted_slots["return_reason"] = reason
                break

    confirm_decision = _parse_confirm_decision(message)
    if (
        state.get("current_intent") == "RETURN_REQUEST"
        and not confirm_decision
        and "return_reason" not in extracted_slots
        and not order_match
        and not any(keyword in message for keyword in ["退货", "退款", "订单"])
    ):
        # 用户在退货流程里只回复“买错了”这类短句时，应视为上一轮缺失的退货原因。
        extracted_slots["return_reason"] = message

    slots.update({key: value for key, value in extracted_slots.items() if value})
    return {
        **state,
        "slots": slots,
        "extracted_slots": extracted_slots,
        "confirm_decision": confirm_decision,
        "route_trace": _trace(state, "parse_input_node"),
        "tool_calls": [],
        "retrieved_docs": [],
        "citations": [],
        "evaluation_result": {},
        "missing_slots": [],
        "awaiting_user_input": False,
        "need_human": False,
        "ticket_id": None,
        "order_info": None,
        "return_result": None,
        "final_answer": "",
    }


def intent_router_node(state: AgentState) -> AgentState:
    pending = _pending_action(state.get("pending_action"))
    if pending != "NONE":
        intent = state.get("current_intent") or "UNKNOWN"
        return {
            **state,
            "intent": intent,
            "confidence": 0.9,
            "reason": f"会话中存在待确认动作 {pending}，优先进入确认节点。",
            "route_debug": {
                "rule_result": None,
                "llm_result": None,
                "final_intent": intent,
                "conflict": False,
                "decision_reason": "pending_action 优先级高于新一轮意图识别。",
            },
            "route_trace": _trace(state, "intent_router_node"),
        }

    if _should_continue_return_flow(state):
        return {
            **state,
            "intent": "RETURN_REQUEST",
            "current_intent": "RETURN_REQUEST",
            "confidence": 0.88,
            "reason": "根据会话状态继续退货槽位补全流程。",
            "route_debug": {
                "rule_result": None,
                "llm_result": None,
                "final_intent": "RETURN_REQUEST",
                "conflict": False,
                "decision_reason": "用户正在补充退货流程必填槽位，沿用 current_intent。",
            },
            "route_trace": _trace(state, "intent_router_node"),
        }

    result, route_debug = classify_intent_hybrid(state["user_message"])
    slots = {**state.get("slots", {}), **{key: value for key, value in result.slots.items() if value}}
    return {
        **state,
        "intent": result.intent,
        "current_intent": result.intent if result.intent != "UNKNOWN" else state.get("current_intent"),
        "confidence": result.confidence,
        "reason": result.reason,
        "slots": slots,
        "route_debug": route_debug,
        "route_trace": _trace(state, "intent_router_node"),
    }


def route_decision(state: AgentState) -> str:
    if _pending_action(state.get("pending_action")) != "NONE":
        return "confirm_node"
    if state.get("confidence", 0) < 0.45:
        return "clarify_node"
    return {
        "ORDER_QUERY": "order_query_node",
        "RETURN_REQUEST": "slot_filling_node",
        "REFUND_STATUS": "refund_status_node",
        "TECH_SUPPORT": "rag_node",
        "POLICY_QA": "rag_node",
        "PRODUCT_QA": "rag_node",
        "COMPLAINT": "human_ticket_node",
        "HUMAN_TRANSFER": "human_ticket_node",
        "UNKNOWN": "clarify_node",
    }.get(state.get("intent", "UNKNOWN"), "clarify_node")


def order_query_node(state: AgentState) -> AgentState:
    order_id = state.get("slots", {}).get("order_id") or state.get("extracted_slots", {}).get("order_id")
    if not order_id:
        return {
            **state,
            "missing_slots": ["order_id"],
            "awaiting_user_input": True,
            "final_answer": "请补充订单号，我就能帮你查询物流和订单状态。",
            "route_trace": _trace(state, "order_query_node"),
        }

    output = get_order_status(order_id)
    answer = (
        f"订单 {order_id} 当前状态为 {output['status']}，商品是 {output['product_name']}。物流信息：{output['logistics_info']}。"
        if output.get("success")
        else f"没有查到订单 {order_id}，请确认订单号是否正确。"
    )
    return {
        **state,
        "order_info": output if output.get("success") else None,
        "final_answer": answer,
        "tool_calls": [*state.get("tool_calls", []), _tool_call("get_order_status", {"order_id": order_id}, output)],
        "route_trace": _trace(state, "order_query_node"),
    }


def slot_filling_node(state: AgentState) -> AgentState:
    slots = {**state.get("slots", {})}
    missing = [slot for slot in ["order_id", "return_reason"] if not slots.get(slot)]
    if missing:
        answer = (
            "请提供需要退货的订单号。"
            if missing[0] == "order_id"
            else "请问退货原因是什么？例如：不想要了、质量问题、买错了、其他。"
        )
        return {
            **state,
            "missing_slots": [missing[0]],
            "awaiting_user_input": True,
            "pending_action": "NONE",
            "final_answer": answer,
            "route_trace": _trace(state, "slot_filling_node"),
        }

    order_id = slots["order_id"]
    order_output = get_order_status(order_id)
    calls = [*state.get("tool_calls", []), _tool_call("get_order_status", {"order_id": order_id}, order_output)]
    if not order_output.get("success"):
        return {
            **state,
            "pending_action": "NONE",
            "return_result": {"success": False, "error": "订单不存在", "order_id": order_id},
            "final_answer": f"没有查到订单 {order_id}，请确认订单号后再申请退货。",
            "tool_calls": calls,
            "route_trace": _trace(state, "slot_filling_node"),
        }
    if not order_output.get("can_return"):
        error = f"订单 {order_id} 当前不符合无理由退货条件：{order_output.get('logistics_info', '不符合退货条件')}"
        return {
            **state,
            "order_info": order_output,
            "pending_action": "NONE",
            "return_result": {"success": False, "error": error, "order_id": order_id},
            "final_answer": error,
            "tool_calls": calls,
            "route_trace": _trace(state, "slot_filling_node"),
        }

    # 这里是状态变更工具的安全门：只设置 pending_action，真正创建退货单必须等 confirm_node 放行。
    return {
        **state,
        "order_info": order_output,
        "pending_action": "CREATE_RETURN_REQUEST",
        "awaiting_user_input": True,
        "missing_slots": [],
        "final_answer": f"查到订单 {order_id} 符合退货条件，是否确认创建退货申请？",
        "tool_calls": calls,
        "route_trace": _trace(state, "slot_filling_node"),
    }


def confirm_node(state: AgentState) -> AgentState:
    decision = state.get("confirm_decision")
    pending = _pending_action(state.get("pending_action"))
    if decision == "CONFIRMED":
        return {**state, "route_trace": _trace(state, "confirm_node")}
    if decision == "CANCELLED":
        return {
            **state,
            "pending_action": "NONE",
            "awaiting_user_input": False,
            "final_answer": "已取消本次退货申请。",
            "route_trace": _trace(state, "confirm_node"),
        }
    return {
        **state,
        "awaiting_user_input": True,
        "final_answer": f"请回复“确认”或“取消”，我再继续处理 {pending}。",
        "route_trace": _trace(state, "confirm_node"),
    }


def confirm_decision(state: AgentState) -> str:
    return "tool_execute_node" if state.get("confirm_decision") == "CONFIRMED" else "final_response_node"


def tool_execute_node(state: AgentState) -> AgentState:
    pending = _pending_action(state.get("pending_action"))
    if pending == "CREATE_RETURN_REQUEST":
        slots = state.get("slots", {})
        output = create_return_request(slots.get("order_id", ""), slots.get("return_reason", "用户未说明"))
        answer = (
            f"已成功创建退货申请，退货单号为 {output['return_id']}。"
            if output.get("success")
            else f"订单 {slots.get('order_id')} 暂时不能创建退货申请：{output.get('error', '不符合退货条件')}。"
        )
        return {
            **state,
            "pending_action": "NONE",
            "awaiting_user_input": False,
            "return_result": output,
            "final_answer": answer,
            "tool_calls": [
                *state.get("tool_calls", []),
                _tool_call("create_return_request", {"order_id": slots.get("order_id"), "reason": slots.get("return_reason")}, output),
            ],
            "route_trace": _trace(state, "tool_execute_node"),
        }

    if pending == "CREATE_TICKET":
        output = _create_human_ticket(state)
        return {
            **state,
            "pending_action": "NONE",
            "need_human": True,
            "ticket_id": output.get("ticket_id"),
            "final_answer": f"已为你创建人工客服工单，工单号为 {output.get('ticket_id')}。",
            "tool_calls": [*state.get("tool_calls", []), _tool_call("create_ticket", {"user_id": state.get("user_id")}, output)],
            "route_trace": _trace(state, "tool_execute_node"),
        }

    return {**state, "pending_action": "NONE", "route_trace": _trace(state, "tool_execute_node")}


def refund_status_node(state: AgentState) -> AgentState:
    return_id = state.get("slots", {}).get("return_id") or state.get("extracted_slots", {}).get("return_id")
    if not return_id:
        return {
            **state,
            "missing_slots": ["return_id"],
            "awaiting_user_input": True,
            "final_answer": "请补充退货单号，我可以继续查询退款或退货进度。",
            "route_trace": _trace(state, "refund_status_node"),
        }
    output = get_refund_status(return_id)
    answer = f"退货单 {return_id} 当前状态为 {output['status']}。" if output.get("success") else output["error"]
    return {
        **state,
        "final_answer": answer,
        "tool_calls": [*state.get("tool_calls", []), _tool_call("get_refund_status", {"return_id": return_id}, output)],
        "route_trace": _trace(state, "refund_status_node"),
    }


def rag_node(state: AgentState) -> AgentState:
    docs = retrieve_documents(state["user_message"], intent=state.get("intent", "UNKNOWN"), top_k=3)
    answer_payload = _generate_rag_answer(state["user_message"], docs)
    return {
        **state,
        "retrieved_docs": docs,
        "citations": answer_payload["citations"],
        "final_answer": answer_payload["answer"],
        "route_trace": _trace(state, "rag_node"),
    }


def human_ticket_node(state: AgentState) -> AgentState:
    output = _create_human_ticket(state)
    return {
        **state,
        "need_human": True,
        "ticket_id": output.get("ticket_id"),
        "final_answer": f"已为你创建人工客服工单，工单号为 {output.get('ticket_id')}。我们会优先处理这次反馈。",
        "tool_calls": [
            *state.get("tool_calls", []),
            _tool_call("create_ticket", {"user_id": state.get("user_id", "U1001"), "issue_type": state.get("intent")}, output),
        ],
        "route_trace": _trace(state, "human_ticket_node"),
    }


def clarify_node(state: AgentState) -> AgentState:
    return {
        **state,
        "awaiting_user_input": True,
        "final_answer": "我还没能明确识别你的需求，请补充你要查询订单、申请退货、咨询技术问题、了解政策，还是需要人工客服。",
        "route_trace": _trace(state, "clarify_node"),
    }


def final_response_node(state: AgentState) -> AgentState:
    return {
        **state,
        "final_answer": state.get("final_answer") or "我已经收到你的问题，但还需要更多信息才能继续处理。",
        "route_trace": _trace(state, "final_response_node"),
    }


def evaluation_node(state: AgentState) -> AgentState:
    evaluation = evaluate_response(dict(state))
    return {**state, "evaluation_result": evaluation, "route_trace": _trace(state, "evaluation_node")}


def save_conversation_node(state: AgentState) -> AgentState:
    saved = save_conversation_state(dict(state))
    logged = write_chat_log({**state, "route_trace": _trace(state, "save_conversation_node")})
    return {
        **state,
        "history": saved.get("history", state.get("history", [])),
        "chat_log_id": logged.get("id"),
        "route_trace": _trace(state, "save_conversation_node"),
    }


def _should_continue_return_flow(state: AgentState) -> bool:
    if state.get("current_intent") != "RETURN_REQUEST":
        return False
    slots = state.get("slots", {})
    missing = [slot for slot in ["order_id", "return_reason"] if not slots.get(slot)]
    extracted = state.get("extracted_slots", {})
    return bool(missing or {"order_id", "return_reason"} & set(extracted))


def _parse_confirm_decision(message: str) -> str | None:
    compact = message.strip().lower()
    if any(word.lower() in compact for word in CANCEL_WORDS):
        return "CANCELLED"
    if any(word.lower() in compact for word in CONFIRM_WORDS):
        return "CONFIRMED"
    return None


def _generate_rag_answer(question: str, docs: list[dict[str, Any]]) -> dict[str, Any]:
    if not docs:
        return {"answer": "暂未找到相关资料，建议转人工客服进一步确认。", "citations": []}

    client = get_llm_client()
    if client.available:
        result = client.json_completion(RAG_ANSWER_PROMPT.format(question=question, docs=json.dumps(docs, ensure_ascii=False)))
        if result and isinstance(result.get("answer"), str):
            return {
                "answer": result["answer"],
                "citations": _normalize_citations(result.get("citations") or docs),
            }

    bullets = [f"- 参考《{doc.get('title', '知识库文档')}》：{doc.get('snippet', '')}" for doc in docs[:2]]
    return {
        "answer": "根据知识库，我找到这些信息：\n"
        + "\n".join(bullets)
        + f"\n\n针对你的问题“{question}”，建议先按上述资料核对；如果仍无法解决，我可以继续帮你转人工。",
        "citations": _normalize_citations(docs),
    }


def _normalize_citations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations = []
    for index, item in enumerate(items[:3], start=1):
        source = item.get("source_file") or item.get("source") or "unknown.md"
        source_name = Path(source).name
        citations.append(
            {
                "source_file": source_name,
                "chunk_id": item.get("chunk_id") or f"{item.get('category', 'doc')}_{index:03d}",
                "score": float(item.get("score", 0.0) or 0.0),
            }
        )
    return citations


def _create_human_ticket(state: AgentState) -> dict[str, Any]:
    summary_payload = _build_human_summary(state)
    return create_ticket(
        user_id=state.get("user_id", "U1001"),
        issue_type=summary_payload["issue_type"],
        priority=summary_payload["priority"],
        summary=summary_payload["summary"],
        chat_history=[*state.get("history", []), {"role": "user", "content": state.get("user_message", "")}],
    )


def _build_human_summary(state: AgentState) -> dict[str, str]:
    client = get_llm_client()
    if client.available:
        result = client.json_completion(
            HUMAN_SUMMARY_PROMPT.format(
                user_id=state.get("user_id", "U1001"),
                intent=state.get("intent", "HUMAN_TRANSFER"),
                history=json.dumps([*state.get("history", []), {"role": "user", "content": state.get("user_message", "")}], ensure_ascii=False),
            )
        )
        if result and result.get("summary"):
            return {
                "summary": str(result.get("summary")),
                "priority": str(result.get("priority") or "HIGH").upper(),
                "issue_type": str(result.get("issue_type") or state.get("intent") or "HUMAN_TRANSFER"),
                "suggested_action": str(result.get("suggested_action") or "建议客服尽快跟进。"),
            }

    message = state.get("user_message", "")
    priority = "HIGH" if any(keyword in message for keyword in ["投诉", "差评", "举报", "人工"]) else "MEDIUM"
    if len(message.strip()) < 8:
        priority = "LOW"
    return {
        "summary": f"用户反馈：{message}。当前意图为 {state.get('intent', 'HUMAN_TRANSFER')}，需要人工客服介入处理。",
        "priority": priority,
        "issue_type": state.get("intent", "HUMAN_TRANSFER"),
        "suggested_action": "建议客服查看完整会话并主动联系用户。",
    }
