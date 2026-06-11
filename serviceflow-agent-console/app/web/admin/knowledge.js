import { apiClient } from "../shared/api-client.js";
import { actionButton, confirmAction, escapeHtml, renderTable, toast } from "../shared/ui-kit.js";
import { adminContext } from "./context.js";

function knowledgeRows(items) {
  return items.map((item) => [
    escapeHtml(item.title),
    escapeHtml(item.knowledge_base),
    escapeHtml(item.status),
    escapeHtml(item.version),
    escapeHtml(item.source_file || "-"),
    escapeHtml(item.updated_at),
    `<div class="admin-actions">
      ${actionButton("发布", "publish", item.doc_id)}
      ${actionButton("归档", "archive", item.doc_id)}
    </div>`,
  ]);
}

async function createDocument(container) {
  const title = container.querySelector("#knowledge-title").value.trim();
  const content = container.querySelector("#knowledge-content").value.trim();
  const knowledgeBase = container.querySelector("#knowledge-base").value;
  const error = container.querySelector("#knowledge-error");
  error.textContent = "";
  if (!title || !content) {
    error.textContent = "请输入标题和正文。";
    return false;
  }
  await apiClient.post("/api/admin/knowledge-documents", {
    title,
    knowledge_base: knowledgeBase,
    content,
    created_by: adminContext().username,
  });
  toast("知识库文档已创建为草稿。", "success");
  return true;
}

async function reindexDocuments() {
  const confirmed = await confirmAction("将重新构建知识库检索索引，过程可能需要几秒。", {
    title: "重建索引",
    confirmLabel: "重建",
  });
  if (!confirmed) return false;
  const result = await apiClient.post("/api/admin/knowledge-documents/reindex", {});
  toast(`索引已重建：${result.indexed_chunks ?? 0} 个 chunk。`, "success");
  return false;
}

async function updateStatus(action, docId) {
  const copy = action === "publish"
    ? ["发布文档", "发布后会写入知识库文件并重建索引。", "发布"]
    : ["归档文档", "归档后该文档不会作为当前知识库来源展示。", "归档"];
  const confirmed = await confirmAction(copy[1], { title: copy[0], confirmLabel: copy[2], destructive: action === "archive" });
  if (!confirmed) return false;
  await apiClient.post(`/api/admin/knowledge-documents/${docId}/${action}`, {});
  toast(action === "publish" ? "文档已发布。" : "文档已归档。", "success");
  return true;
}

export async function loadKnowledge(container) {
  const data = await apiClient.get("/api/admin/knowledge-documents");
  container.innerHTML = `
    <section class="admin-form">
      <label for="knowledge-title">标题</label>
      <input id="knowledge-title" placeholder="例如：SmartRouter X1 兼容性说明" />
      <label for="knowledge-base">知识库</label>
      <select id="knowledge-base">
        <option value="tech">tech</option>
        <option value="policy">policy</option>
        <option value="product">product</option>
      </select>
      <label for="knowledge-content">正文</label>
      <textarea id="knowledge-content" placeholder="这里是文档正文"></textarea>
      <div class="admin-form-actions">
        <button type="button" data-action="create">新建文档</button>
        <button type="button" data-action="reindex">重建索引</button>
      </div>
      <p id="knowledge-error" class="error-text" role="status"></p>
    </section>
    ${renderTable(
      ["Title", "KB", "Status", "Version", "Source", "Updated", "操作"],
      knowledgeRows(data),
      { emptyMessage: "暂无知识库文档。", emptyAction: `<button type="button" data-action="focus-create">新建第一篇文档</button>` },
    )}`;

  container.onclick = async (event) => {
    const button = event.target.closest("[data-action]");
    if (!button || !container.contains(button)) return;
    try {
      if (button.dataset.action === "focus-create") {
        container.querySelector("#knowledge-title").focus();
        return;
      }
      if (button.dataset.action === "create" && !await createDocument(container)) return;
      if (button.dataset.action === "reindex" && !await reindexDocuments()) return;
      if ((button.dataset.action === "publish" || button.dataset.action === "archive")
        && !await updateStatus(button.dataset.action, button.dataset.value)) return;
      await loadKnowledge(container);
    } catch (error) {
      toast(`操作失败：${error.message}`, "error");
    }
  };
}
