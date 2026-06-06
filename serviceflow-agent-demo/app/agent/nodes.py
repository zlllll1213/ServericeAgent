import re
from typing import Any

from app.agent.router import classify_intent
from app.agent.state import AgentState
from app.rag.prompts import render_rag_answer
from app.rag.retriever import SimpleRetriever
from app.tools.customer_tools import create_return_request, create_ticket, get_order_status, get_refund_status

ORDER_PATTERN = re.compile(r"(?:订单号?|order)\s*[:：]?\s*(\d{5,})|(\b\d{5,}\b)", re.IGNORECASE)
RETURN_PATTERN = re.compile(r"(?:退货单|return_id)\s*[:：]?\s*([A-Z]?\d{8,})", re.IGNORECASE)


def _trace(state: AgentState, node_name: str) -> list[str]:
    return [*state.get("route_trace", []), node_name]


def _tool_call(name: str, input_data: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "input": input_data, "output": output}


def parse_input_node(state: AgentState) -> AgentState:
    message = state["user_message"]
    order_match = ORDER_PATTERN.search(message)
    return_match = RETURN_PATTERN.search(message)
    slots: dict[str, Any] = {}
    if order_match:
        slots["order_id"] = next(group for group in order_match.groups() if group)
    if return_match:
        slots["return_id"] = return_match.group(1)
    return {
        **state,
        "extracted_slots": slots,
        "route_trace": _trace(state, "parse_input_node"),
        "tool_calls": [],
        "retrieved_docs": [],
        "need_human": False,
        "ticket_id": None,
        "order_info": None,
        "return_result": None,
    }


def intent_router_node(state: AgentState) -> AgentState:
    result = classify_intent(state["user_message"])
    return {
        **state,
        "intent": result.intent,
        "confidence": result.confidence,
        "reason": result.reason,
        "route_trace": _trace(state, "intent_router_node"),
    }


def route_decision(state: AgentState) -> str:
    intent = state.get("intent", "UNKNOWN")
    if state.get("confidence", 0) < 0.45:
        return "clarify_node"
    return {
        "ORDER_QUERY": "order_query_node",
        "RETURN_REQUEST": "return_request_node",
        "REFUND_STATUS": "refund_status_node",
        "TECH_SUPPORT": "rag_tech_node",
        "POLICY_QA": "rag_policy_node",
        "PRODUCT_QA": "rag_product_node",
        "COMPLAINT": "human_ticket_node",
        "HUMAN_TRANSFER": "human_ticket_node",
        "UNKNOWN": "clarify_node",
    }.get(intent, "clarify_node")


def order_query_node(state: AgentState) -> AgentState:
    order_id = state.get("extracted_slots", {}).get("order_id")
    if not order_id:
        return {
            **state,
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


def return_request_node(state: AgentState) -> AgentState:
    order_id = state.get("extracted_slots", {}).get("order_id")
    if not order_id:
        return {
            **state,
            "final_answer": "请补充需要退货的订单号，例如：我要退货，订单号 10001。",
            "route_trace": _trace(state, "return_request_node"),
        }

    order_output = get_order_status(order_id)
    calls = [*state.get("tool_calls", []), _tool_call("get_order_status", {"order_id": order_id}, order_output)]
    if not order_output.get("success"):
        return {
            **state,
            "final_answer": f"没有查到订单 {order_id}，请确认订单号后再申请退货。",
            "tool_calls": calls,
            "route_trace": _trace(state, "return_request_node"),
        }

    return_output = create_return_request(order_id, reason=state["user_message"])
    calls.append(_tool_call("create_return_request", {"order_id": order_id, "reason": state["user_message"]}, return_output))
    if return_output.get("success"):
        answer = f"已为你创建退货申请，退货单号为 {return_output['return_id']}。请保持商品包装完整，后续客服会同步寄回方式。"
    else:
        answer = f"订单 {order_id} 暂时不能创建退货申请：{return_output.get('error', '不符合退货条件')}。"

    return {
        **state,
        "order_info": order_output,
        "return_result": return_output,
        "final_answer": answer,
        "tool_calls": calls,
        "route_trace": _trace(state, "return_request_node"),
    }


def refund_status_node(state: AgentState) -> AgentState:
    return_id = state.get("extracted_slots", {}).get("return_id")
    if not return_id:
        return {
            **state,
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


def _rag_node(state: AgentState, knowledge_base: str, node_name: str, fallback: str) -> AgentState:
    retriever = SimpleRetriever()
    docs = retriever.retrieve(state["user_message"], knowledge_base=knowledge_base, top_k=3)
    answer = render_rag_answer(state["user_message"], docs, fallback=fallback)
    return {
        **state,
        "retrieved_docs": docs,
        "final_answer": answer,
        "route_trace": _trace(state, node_name),
    }


def rag_tech_node(state: AgentState) -> AgentState:
    return _rag_node(state, "tech", "rag_tech_node", "我暂时没有检索到对应技术文档。可以补充设备型号、App 版本或报错信息。")


def rag_policy_node(state: AgentState) -> AgentState:
    return _rag_node(state, "policy", "rag_policy_node", "我暂时没有检索到对应售后政策。可以补充订单状态或签收时间。")


def rag_product_node(state: AgentState) -> AgentState:
    return _rag_node(state, "product", "rag_product_node", "我暂时没有检索到对应产品资料。可以补充产品型号或规格问题。")


def human_ticket_node(state: AgentState) -> AgentState:
    output = create_ticket(
        user_id=state.get("user_id", "U1001"),
        issue_type=state.get("intent", "HUMAN_TRANSFER"),
        summary=state["user_message"],
        chat_history=[{"role": "user", "content": state["user_message"]}],
    )
    return {
        **state,
        "need_human": True,
        "ticket_id": output.get("ticket_id"),
        "final_answer": f"已为你创建人工客服工单，工单号为 {output.get('ticket_id')}。我们会优先处理这次反馈。",
        "tool_calls": [
            *state.get("tool_calls", []),
            _tool_call(
                "create_ticket",
                {"user_id": state.get("user_id", "U1001"), "issue_type": state.get("intent"), "summary": state["user_message"]},
                output,
            ),
        ],
        "route_trace": _trace(state, "human_ticket_node"),
    }


def clarify_node(state: AgentState) -> AgentState:
    return {
        **state,
        "final_answer": "我还没能明确识别你的需求，请补充你要查询订单、申请退货、咨询技术问题、了解政策，还是需要人工客服。",
        "route_trace": _trace(state, "clarify_node"),
    }


def final_response_node(state: AgentState) -> AgentState:
    return {
        **state,
        "final_answer": state.get("final_answer") or "我已经收到你的问题，但还需要更多信息才能继续处理。",
        "route_trace": _trace(state, "final_response_node"),
    }
