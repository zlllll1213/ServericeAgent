from dataclasses import dataclass


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float
    reason: str


INTENT_KEYWORDS = {
    "ORDER_QUERY": ["订单", "快递", "发货", "物流", "到哪了", "到哪里", "签收"],
    "RETURN_REQUEST": ["退货", "退款", "不想要", "退掉", "申请售后"],
    "REFUND_STATUS": ["退款状态", "退货单", "退货进度", "return_id"],
    "TECH_SUPPORT": ["无法连接", "连接 wifi", "连接WiFi", "wifi", "搜不到设备", "报错", "安装", "配置", "联网"],
    "POLICY_QA": ["保修", "7天", "七天", "7 天", "售后政策", "退货政策", "无理由"],
    "PRODUCT_QA": ["支持 macos", "macos", "参数", "规格", "5g wifi", "5G WiFi", "产品", "SmartRouter", "SmartCamera"],
    "COMPLAINT": ["投诉", "生气", "差评", "太差"],
    "HUMAN_TRANSFER": ["人工", "客服"],
}


def classify_intent(message: str) -> IntentResult:
    normalized = message.lower().replace("５", "5").replace("ｇ", "g")

    complaint_score = sum(1 for kw in INTENT_KEYWORDS["COMPLAINT"] if kw.lower() in normalized)
    human_score = sum(1 for kw in INTENT_KEYWORDS["HUMAN_TRANSFER"] if kw.lower() in normalized)
    if complaint_score:
        return IntentResult("COMPLAINT", min(0.96, 0.82 + complaint_score * 0.06), "用户表达了投诉或强烈不满，需要升级处理")
    if human_score:
        return IntentResult("HUMAN_TRANSFER", min(0.94, 0.8 + human_score * 0.07), "用户明确要求人工客服")

    policy_score = sum(1 for kw in INTENT_KEYWORDS["POLICY_QA"] if kw.lower() in normalized)
    if policy_score:
        return IntentResult("POLICY_QA", min(0.95, 0.76 + policy_score * 0.08), "用户在询问售后或退货政策规则")

    product_score = sum(1 for kw in INTENT_KEYWORDS["PRODUCT_QA"] if kw.lower() in normalized)
    if product_score:
        return IntentResult("PRODUCT_QA", min(0.95, 0.76 + product_score * 0.08), "用户在询问产品兼容性、参数或规格")

    refund_score = sum(1 for kw in INTENT_KEYWORDS["REFUND_STATUS"] if kw.lower() in normalized)
    if refund_score:
        return IntentResult("REFUND_STATUS", min(0.95, 0.76 + refund_score * 0.08), "用户在查询退款或退货进度")

    return_score = sum(1 for kw in INTENT_KEYWORDS["RETURN_REQUEST"] if kw.lower() in normalized)
    if return_score:
        return IntentResult("RETURN_REQUEST", min(0.95, 0.78 + return_score * 0.08), "用户提到了退货、退款或申请售后")

    best_intent = "UNKNOWN"
    best_score = 0
    for intent, keywords in INTENT_KEYWORDS.items():
        if intent in {"COMPLAINT", "HUMAN_TRANSFER"}:
            continue
        score = sum(1 for kw in keywords if kw.lower() in normalized)
        if score > best_score:
            best_intent = intent
            best_score = score

    if best_score == 0:
        return IntentResult("UNKNOWN", 0.2, "没有匹配到订单、退货、技术、政策、产品或投诉关键词")

    confidence = min(0.95, 0.72 + best_score * 0.08)
    return IntentResult(best_intent, confidence, f"命中 {best_intent} 相关关键词 {best_score} 个")
