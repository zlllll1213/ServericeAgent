def render_rag_answer(question: str, docs: list[dict], fallback: str) -> str:
    if not docs:
        return fallback

    bullets = []
    for doc in docs[:2]:
        bullets.append(f"- 参考《{doc['title']}》：{doc['snippet']}")
    return "根据知识库，我找到这些信息：\n" + "\n".join(bullets) + f"\n\n针对你的问题“{question}”，建议先按上述步骤核对；如果仍无法解决，我可以继续帮你转人工。"
