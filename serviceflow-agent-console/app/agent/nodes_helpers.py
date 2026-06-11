from __future__ import annotations

import re
from typing import Any

from app.agent.state import AgentState

ORDER_PATTERN = re.compile(r"(?:订单号?|order)\s*[:：]?\s*(\d{5,})|(\b\d{5,}\b)", re.IGNORECASE)
RETURN_PATTERN = re.compile(r"(?:退货单|return_id)\s*[:：]?\s*([A-Z]?\d{8,})", re.IGNORECASE)
REASON_PATTERN = re.compile(r"(?:原因是|原因[:：]|因为)([^，。,.!！?？]+)")
CONFIRM_WORDS = {"确认", "是的", "可以", "提交", "帮我创建"}
CANCEL_WORDS = {"取消", "算了", "不用了", "先不退了"}
RETURN_REASONS = ["不想要了", "质量问题", "买错了", "其他"]


def trace_step(state: AgentState, node_name: str) -> list[str]:
    return [*state.get("route_trace", []), node_name]


def tool_call(name: str, input_data: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "input": input_data, "output": output}


def pending_action(value: str | None) -> str:
    return value if value and value != "NONE" else "NONE"
