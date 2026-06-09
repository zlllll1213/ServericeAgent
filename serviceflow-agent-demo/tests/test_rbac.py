import pytest


def test_customer_without_admin_credentials_cannot_access_admin(client):
    response = client.get("/api/admin/conversations")

    assert response.status_code == 401


def test_demo_admin_role_can_manage_knowledge(client, admin_headers):
    response = client.post(
        "/api/admin/knowledge-documents",
        json={"title": "测试文档", "knowledge_base": "policy", "content": "测试内容"},
        headers=admin_headers,
    )

    assert response.status_code == 200


@pytest.mark.skip(reason="当前本地 Demo 尚未接入完整 tenant_admin/super_admin RBAC 策略。")
def test_full_rbac_matrix_for_tenant_admin_and_super_admin():
    pass
