from dataclasses import asdict, dataclass, field
from typing import Any

from app.agent.intents import Intent
from app.config import settings
from app.llm.client import get_llm_client
from app.llm.prompts import INTENT_RECOGNITION_PROMPT


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float
    reason: str
    slots: dict[str, Any] = field(default_factory=dict)


INTENT_KEYWORDS = {
    "ORDER_QUERY": ["订单", "快递", "发货", "物流", "到哪了", "到哪里", "签收"],
    "RETURN_REQUEST": ["退货", "退款", "不想要", "退掉", "申请售后"],
    "REFUND_STATUS": ["退款状态", "退货单", "退货进度", "return_id"],
    "TECH_SUPPORT": ["无法连接", "连接 wifi", "连接WiFi", "wifi", "搜不到设备", "报错", "安装", "配置", "联网"],
    "POLICY_QA": ["保修", "延保", "7天", "七天", "7 天", "售后政策", "退货政策", "无理由"],
    "PRODUCT_QA": ["支持 macos", "macos", "参数", "规格", "5g wifi", "5G WiFi", "产品", "SmartRouter", "SmartCamera"],
    "COMPLAINT": ["投诉", "生气", "差评", "太差"],
    "HUMAN_TRANSFER": ["人工", "客服"],
}


def classify_intent(message: str) -> IntentResult:
    normalized = message.lower().replace("５", "5").replace("ｇ", "g")

    complaint_score = sum(1 for kw in INTENT_KEYWORDS["COMPLAINT"] if kw.lower() in normalized)
    human_score = sum(1 for kw in INTENT_KEYWORDS["HUMAN_TRANSFER"] if kw.lower() in normalized)
    if complaint_score:
        return IntentResult(Intent.COMPLAINT.value, min(0.96, 0.82 + complaint_score * 0.06), "用户表达了投诉或强烈不满，需要升级处理")
    if human_score:
        return IntentResult(Intent.HUMAN_TRANSFER.value, min(0.94, 0.8 + human_score * 0.07), "用户明确要求人工客服")

    policy_score = sum(1 for kw in INTENT_KEYWORDS["POLICY_QA"] if kw.lower() in normalized)
    if policy_score:
        return IntentResult(Intent.POLICY_QA.value, min(0.95, 0.76 + policy_score * 0.08), "用户在询问售后或退货政策规则")

    product_score = sum(1 for kw in INTENT_KEYWORDS["PRODUCT_QA"] if kw.lower() in normalized)
    if product_score:
        return IntentResult(Intent.PRODUCT_QA.value, min(0.95, 0.76 + product_score * 0.08), "用户在询问产品兼容性、参数或规格")

    refund_score = sum(1 for kw in INTENT_KEYWORDS["REFUND_STATUS"] if kw.lower() in normalized)
    if refund_score:
        return IntentResult(Intent.REFUND_STATUS.value, min(0.95, 0.76 + refund_score * 0.08), "用户在查询退款或退货进度")

    return_score = sum(1 for kw in INTENT_KEYWORDS["RETURN_REQUEST"] if kw.lower() in normalized)
    if return_score:
        return IntentResult(Intent.RETURN_REQUEST.value, min(0.95, 0.78 + return_score * 0.08), "用户提到了退货、退款或申请售后")

    best_intent = Intent.UNKNOWN.value
    best_score = 0
    for intent, keywords in INTENT_KEYWORDS.items():
        if intent in {"COMPLAINT", "HUMAN_TRANSFER"}:
            continue
        score = sum(1 for kw in keywords if kw.lower() in normalized)
        if score > best_score:
            best_intent = intent
            best_score = score

    if best_score == 0:
        return IntentResult(Intent.UNKNOWN.value, 0.2, "没有匹配到订单、退货、技术、政策、产品或投诉关键词")

    confidence = min(0.95, 0.72 + best_score * 0.08)
    return IntentResult(best_intent, confidence, f"命中 {best_intent} 相关关键词 {best_score} 个")


def classify_intent_hybrid(message: str) -> tuple[IntentResult, dict[str, Any]]:
    rule_result = classify_intent(message)
    llm_result = classify_intent_with_llm(message)
    route_debug: dict[str, Any] = {
        "rule_result": asdict(rule_result),
        "llm_result": asdict(llm_result) if llm_result else None,
        "final_intent": rule_result.intent,
        "conflict": False,
        "decision_reason": "LLM 不可用或未配置 API Key，使用规则路由。",
    }

    if llm_result is None:
        return rule_result, route_debug

    conflict = rule_result.intent != llm_result.intent
    route_debug["conflict"] = conflict

    if not conflict:
        confidence = min(0.99, max(rule_result.confidence, llm_result.confidence) + 0.05)
        final = IntentResult(
            intent=rule_result.intent,
            confidence=confidence,
            reason=f"规则和 LLM 结果一致：{rule_result.reason}",
            slots={**rule_result.slots, **llm_result.slots},
        )
        route_debug["final_intent"] = final.intent
        route_debug["decision_reason"] = "规则路由和 LLM 路由一致，提高置信度。"
        return final, route_debug

    # 冲突时优先选择高置信度结果；两个高置信度且差距不大时交给 clarify_node。
    high_confidence = settings.intent_conflict_high_confidence_threshold
    max_gap = settings.intent_conflict_confidence_gap
    if min(rule_result.confidence, llm_result.confidence) >= high_confidence and abs(rule_result.confidence - llm_result.confidence) < max_gap:
        final = IntentResult(Intent.UNKNOWN.value, 0.42, "规则和 LLM 对用户意图判断冲突，需要追问确认")
        route_debug["final_intent"] = final.intent
        route_debug["decision_reason"] = "规则与 LLM 高置信度冲突，进入澄清。"
        return final, route_debug

    final = llm_result if llm_result.confidence > rule_result.confidence else rule_result
    route_debug["final_intent"] = final.intent
    route_debug["decision_reason"] = "规则和 LLM 不一致，选择置信度更高的结果。"
    return final, route_debug


def classify_intent_with_llm(message: str) -> IntentResult | None:
    client = get_llm_client()
    if not client.available:
        return None

    result = client.json_completion(INTENT_RECOGNITION_PROMPT.format(message=message))
    if not result:
        return None

    intent = str(result.get("intent") or Intent.UNKNOWN.value).upper()
    if intent not in {item.value for item in Intent}:
        return None
    try:
        confidence = max(0.0, min(1.0, float(result.get("confidence", 0.0))))
    except (TypeError, ValueError):
        confidence = 0.0
    slots = result.get("slots") if isinstance(result.get("slots"), dict) else {}
    return IntentResult(intent=intent, confidence=confidence, reason=str(result.get("reason") or "LLM 路由结果"), slots=slots)
