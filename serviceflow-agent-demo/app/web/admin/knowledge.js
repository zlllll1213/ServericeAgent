// 知识库管理视图 —— 文档 CRUD、发布、归档、重建索引
// 从 admin.js loadKnowledge 完整迁移

import { apiAuthGet, apiAuthPost } from "../shared/api-client.js";
import { table, toast } from "../shared/ui-kit.js";

/** 加载知识库文档列表 + 创建表单 */
export async function loadKnowledge(token) {
  const data = await apiAuthGet("/api/admin/knowledge-documents", token);

  const rows = data.map(
    (item) => `<tr>
      <td>${item.title}</td>
      <td>${item.knowledge_base}</td>
      <td>${item.status}</td>
      <td>${item.version}</td>
      <td>${item.updated_at}</td>
      <td class="admin-actions">
        <button data-publish="${item.doc_id}">发布</button>
        <button data-archive="${item.doc_id}">归档</button>
      </td>
    </tr>`,
  );

  const viewEl = document.querySelector("#view-knowledge");
  viewEl.innerHTML = `
    <section class="admin-form">
      <input id="knowledge-title" placeholder="标题" />
      <select id="knowledge-base">
        <option value="tech">tech</option>
        <option value="policy">policy</option>
        <option value="product">product</option>
      </select>
      <textarea id="knowledge-content" placeholder="这里是文档正文"></textarea>
      <button id="knowledge-create">新建文档</button>
      <button id="knowledge-reindex">重建索引</button>
    </section>
    ${table(["Title", "KB", "Status", "Version", "Updated", "操作"], rows)}`;

  // 新建文档
  document.querySelector("#knowledge-create").addEventListener("click", async () => {
    try {
      await apiAuthPost("/api/admin/knowledge-documents", token, {
        title: document.querySelector("#knowledge-title").value,
        knowledge_base: document.querySelector("#knowledge-base").value,
        content: document.querySelector("#knowledge-content").value,
      });
      loadKnowledge(token);
    } catch (error) {
      toast(error.message, "error");
    }
  });

  // 重建索引
  document.querySelector("#knowledge-reindex").addEventListener("click", async () => {
    try {
      await apiAuthPost("/api/admin/knowledge-documents/reindex", token);
      toast("索引重建请求已提交", "success");
    } catch (error) {
      toast(error.message, "error");
    }
  });

  // 发布
  viewEl.querySelectorAll("[data-publish]").forEach((button) =>
    button.addEventListener("click", async () => {
      try {
        await apiAuthPost(`/api/admin/knowledge-documents/${button.dataset.publish}/publish`, token);
        loadKnowledge(token);
      } catch (error) {
        toast(error.message, "error");
      }
    }),
  );

  // 归档
  viewEl.querySelectorAll("[data-archive]").forEach((button) =>
    button.addEventListener("click", async () => {
      try {
        await apiAuthPost(`/api/admin/knowledge-documents/${button.dataset.archive}/archive`, token);
        loadKnowledge(token);
      } catch (error) {
        toast(error.message, "error");
      }
    }),
  );
}
