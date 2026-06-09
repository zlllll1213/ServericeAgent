# ServiceFlow API 文档

## Auth API

- `POST /api/auth/login`：后台登录，密码以 PBKDF2 hash 形式配置；本地演示可显式开启 `DEMO_AUTH_ENABLED=true` 使用演示账号。
- `GET /api/auth/me`：读取当前 token 对应用户。

## Chat API

- `POST /api/chat`：进入 Agent 工作流，返回 `conversation_id`、`trace_id`、`intent`、`route_trace`、`tool_calls`、`citations`。
- `GET /api/conversations/{conversation_id}`：读取会话状态。
- `GET /api/conversations/{conversation_id}/logs`：读取会话日志。
- `POST /api/conversations/{conversation_id}/reset`：重置会话。

## Admin API

后台接口默认使用 `Authorization: Bearer <token>` 访问。`X-User-Role` 只有在 `DEMO_AUTH_ENABLED=true` 时才允许作为本地演示 fallback。

- `GET /api/admin/conversations`
- `GET /api/admin/conversations/{conversation_id}`
- `POST /api/admin/conversations/{conversation_id}/assign`
- `POST /api/admin/conversations/{conversation_id}/reply`
- `POST /api/admin/conversations/{conversation_id}/resolve`
- `GET /api/admin/chat-logs`

## Knowledge API

- `GET /api/admin/knowledge-documents`
- `POST /api/admin/knowledge-documents`
- `PUT /api/admin/knowledge-documents/{doc_id}`
- `POST /api/admin/knowledge-documents/{doc_id}/publish`
- `POST /api/admin/knowledge-documents/{doc_id}/archive`
- `POST /api/admin/knowledge-documents/reindex`

## Ticket API

- `GET /api/admin/tickets`
- `GET /api/admin/tickets/{ticket_id}`
- `POST /api/admin/tickets/{ticket_id}/assign`
- `POST /api/admin/tickets/{ticket_id}/resolve`
- `POST /api/admin/tickets/{ticket_id}/close`

## Trace API

- `GET /api/admin/traces`：支持 `conversation_id`、`trace_id`、`node_name`、`success`、`page`、`page_size`。
- `GET /api/admin/traces/{trace_id}`：返回完整节点链路、输入输出、耗时和错误信息。

## Metrics API

- `GET /api/admin/metrics/overview`：返回今日对话数、平均耗时、P95、意图分布、工具成功率、转人工率、差评率和错误率。
- `GET /api/admin/metrics/daily`：返回最近 7 天对话数和错误数。

## Evaluation API

- `GET /api/admin/evaluation-reports`
- `GET /api/admin/evaluation-reports/latest`
- `GET /api/admin/evaluation-reports/{filename}/download`
