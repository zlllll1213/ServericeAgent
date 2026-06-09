from __future__ import annotations

from app.agent.nodes_helpers import pending_action as _pending_action
from app.agent.nodes_helpers import tool_call as _tool_call
from app.agent.nodes_helpers import trace_step as _trace
from app.agent.nodes_support import create_human_ticket as _create_human_ticket
from app.agent.state import AgentState
from app.tools.customer_tools import create_return_request, get_order_status, get_refund_status


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
