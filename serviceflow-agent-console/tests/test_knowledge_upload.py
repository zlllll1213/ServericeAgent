def test_knowledge_document_publish_refreshes_simple_retrieval(chat, client, admin_headers):
    created = client.post(
        "/api/admin/knowledge-documents",
        json={"title": "延保服务政策", "knowledge_base": "policy", "content": "SmartRouter X1 支持 1 年延保服务。"},
        headers=admin_headers,
    )
    doc_id = created.json()["doc_id"]

    published = client.post(f"/api/admin/knowledge-documents/{doc_id}/publish", headers=admin_headers)
    answer = chat("SmartRouter X1 有延保服务吗？")

    assert published.status_code == 200
    assert any(citation["source_file"] == f"{doc_id}.md" for citation in answer["citations"])
