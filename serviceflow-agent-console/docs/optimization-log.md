# 优化过程记录

## 2026-06-09 安全与稳定性优化

- 将后台认证从默认信任 `X-User-Role` 改为默认使用 Bearer token。
- 将 `X-User-Role` 限定为 `DEMO_AUTH_ENABLED=true` 时的本地演示 fallback。
- 将后台密码校验改为 PBKDF2 hash 校验。
- 将 token 改为 HS256 JWT 结构，补充 `iss`、`aud`、`iat`、`exp`、`jti` 字段。
- 将 `AUTH_SECRET` 改为环境变量稳定强随机值，缺失或过短时拒绝签发 token，避免进程随机 secret 导致重启后 token 全部失效。
- 后台前端改为先登录获取 token，再用 `Authorization: Bearer` 调用后台接口。
- 为 `/api/chat` 增加单进程滑动窗口限流。
- 限流 identity 支持 `X-Forwarded-For`、`X-Real-IP` 和直连 IP。
- 限流桶增加空 key 清理，避免长期运行时 `_BUCKETS` 无限增长。
- 健康检查增加 `rate_limit` 状态。
- LLM Client 不再裸 `except Exception` 静默吞错，改为区分 HTTP 状态、超时、HTTP 异常、响应结构异常和 JSON 解析异常。
- 增加 LLM 调用失败日志。
- 将意图冲突阈值和澄清阈值迁移到配置项。
- 退货流程短句原因推断增加新意图保护，避免用户中途切换话题时被误判为退货原因。
- Qdrant REST timeout 改为 `QDRANT_TIMEOUT_SECONDS` 配置项。
- `traced_node` 增加节点级错误策略：IO 节点短重试，质检节点失败时降级，不阻断用户回复。
- Trace 写入失败不再反向拖垮主请求。
- 人工接管节点不再绕过统一链路，改为进入 `final_response_node`、`evaluation_node`、`save_conversation_node`。
- 人工接管轮次现在会写入 `evaluation_result`。
- 测试改为使用临时 SQLite 文件，避免污染 `data/serviceflow.db`。
- `test_agent_demo.py` 改为复用 `conftest.py` 的 `client`、`chat`、`admin_headers` fixture。
- 新增限流真实拦截测试。
- 新增代理 IP 限流 identity 测试。
- 新增限流桶清理测试。
- 更新 README、API 文档、部署文档和开发阶段记录中的认证说明。

## 2026-06-09 第二轮性能与限流优化

- 将 `/api/chat` 限流 identity 从 `user_id + IP` 改为纯 IP。
- 新增伪造不同 `user_id` 不能绕过限流的测试。
- 保留 `X-Forwarded-For`、`X-Real-IP` 支持，但不信任客户端提交的 `user_id` 参与限流。
- 新增 `RATE_LIMIT_BACKEND` 和 `REDIS_URL` 配置项。
- 健康检查明确返回 `in_memory_single_process`，避免把内存限流误认为多进程生产方案。
- 当 `RATE_LIMIT_BACKEND=redis` 但未配置 Redis 时，明确返回限流配置错误。
- 移除 `config.py` 中默认密码哈希。
- 非 Demo 模式下要求通过环境变量提供 `ADMIN_PASSWORD_HASH` 和 `AGENT_PASSWORD_HASH`。
- 更新 `.env.example`，不再内置默认密码哈希。
- 优化 `evaluation-summary`，增加时间窗口参数并使用 SQL 计数和分组聚合。
- 优化 `metrics/overview`，增加时间窗口参数并避免全表加载日志、反馈、会话。
- 优化 `metrics/daily`，使用 SQL 日期聚合统计最近 7 天聊天和错误数。
- 保留对 JSON 字段中 `tool_calls` 和 `evaluation_result` 的窗口内解析，后续可通过结构化表进一步优化。

## 2026-06-09 第三轮 Redis 与认证落地

- 为 `AdminUser` 表新增 `password_hash` 字段。
- 为已有 SQLite 演示库补充 `admin_users.password_hash` 追加列迁移。
- seed 阶段将后台用户密码 hash 写入 `admin_users` 表。
- 登录认证优先读取 `admin_users.password_hash`，配置项只作为无数据库用户时的 fallback。
- 新增测试，确认 seed 后 `AdminUser.password_hash` 已写入数据库。
- 使用标准库 socket 实现最小 Redis RESP 客户端。
- `RATE_LIMIT_BACKEND=redis` 时通过 Redis `INCR` + `EXPIRE` 做统一限流计数。
- Redis 后端支持 `redis://[:password]@host:port/db` 形式的 `REDIS_URL`。
- 新增 Redis 限流后端计数测试。
- 健康检查中 `rate_limit` 会根据配置返回 `redis`、`redis_unconfigured` 或 `in_memory_single_process`。

## 2026-06-09 第四轮后台路由拆分

- 将原 `app/admin.py` 从 500+ 行后台大文件改为聚合 router。
- 新增 `app/admin_routes/common.py`，集中后台共享 helper。
- 新增 `app/admin_routes/conversations.py`，承载会话列表、详情、认领、人工回复和关闭接口。
- 新增 `app/admin_routes/tickets.py`，承载工单列表、详情、认领、处理和关闭接口。
- 新增 `app/admin_routes/knowledge.py`，承载知识库文档增删改发布、归档和重建索引接口。
- 新增 `app/admin_routes/feedback_metrics.py`，承载用户反馈、质量统计、聊天日志和 Metrics 接口。
- 新增 `app/admin_routes/traces_reports.py`，承载 Agent Trace 和 Evaluation 报告接口。
- 保持原有 API 路径不变，前端和测试无需改调用地址。

## 2026-06-09 第五轮 Agent 与检索维护性优化

- 修复 `seed.py` 中订单已存在时调用 `seed_admin_users` 后未提交的遗漏。
- 后台鉴权中间件改为只捕获 `AuthException` 和 `PermissionDeniedException`，其他异常交给统一异常处理器记录。
- 新增 `app/agent/intents.py`，用 `Intent` StrEnum 集中管理意图常量。
- `agent/router.py` 和 `rag/service.py` 开始使用 `Intent` 枚举，降低字符串拼写错误风险。
- 将 Qdrant REST 客户端从 `urllib` 迁移到 `httpx.Client`。
- Qdrant 客户端保留同步接口，同时支持连接复用、统一超时和更清晰的 HTTP 错误处理。
- 新增 `app/agent/nodes_helpers.py`，抽出节点通用正则、确认词、trace 和 tool call helper。
- 新增 `app/agent/nodes_support.py`，抽出 RAG 回答生成、citation 归一化、人工工单摘要和退货流程辅助判断。
- `nodes.py` 保留 LangGraph 节点主体，减少辅助逻辑堆积。

## 2026-06-09 第六轮 Agent 节点按业务域拆分

- 新增 `app/agent/session_nodes.py`，承载会话加载和接管分流节点。
- 新增 `app/agent/input_routing_nodes.py`，承载输入解析、意图路由和路由决策。
- 新增 `app/agent/order_return_nodes.py`，承载订单查询、退货槽位补全、确认、工具执行和退款状态查询。
- 新增 `app/agent/rag_nodes.py`，承载知识库检索节点。
- 新增 `app/agent/handoff_nodes.py`，承载人工接管等待和人工工单创建节点。
- 新增 `app/agent/final_nodes.py`，承载澄清、最终响应、质量评估和会话保存节点。
- 将 `app/agent/nodes.py` 改为兼容导出层，保持 `graph.py` 的导入路径不变。
- 保留 `CREATE_TICKET` pending action 分支，避免拆分时丢失历史行为。

## 仍待后续优化

- 将后台子路由、工具函数和 Agent persistence 继续收敛到 request-level dependency 或 service-level unit of work。
- 将意图字符串抽象为 `StrEnum`。
- 为 Agent nodes、persistence、tools 扩展结构化日志。
- 增加应用 Dockerfile。
- 将前端 JS/CSS 逐步模块化。

## 2026-06-11 安全复核优化

- `/api/orders/{order_id}` 保持 ORM 参数绑定查询，并新增“疑似注入字符串只按普通订单号处理”的回归测试。
- `main.py` 中健康检查、订单、工单和退货列表接口改为使用 `Depends(get_db)` 注入数据库会话。
- `auth.py` 登录查询改为使用 `Depends(get_db)` 注入数据库会话，不再直接实例化 `SessionLocal()`。
- 后台管理子路由统一使用 `Depends(get_db)`，request 路由层不再直接创建数据库 session。
- 移除认证模块内置 demo 密码哈希；seed 阶段按演示密码运行时加盐生成 PBKDF2 hash。
- `traced_node` 重试等待时间改为 `AGENT_NODE_RETRY_DELAY_SECONDS` 配置项。
- `parse_input_node` 不再清空上一轮 tool calls、retrieved docs、citations、evaluation 和关键业务结果，避免多轮证据丢失。
- LLM Client 增加 `LLM_RETRY_ATTEMPTS` 和 `LLM_RETRY_DELAY_SECONDS`，对超时、网络错误、429 和 5xx 做短重试。
- 补充安全与韧性回归测试，覆盖认证密钥、demo hash fallback、输入解析证据保留、节点重试延迟和 LLM transient retry。
