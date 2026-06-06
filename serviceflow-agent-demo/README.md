# ServiceFlow Agent Demo

ServiceFlow Agent Demo 是一个本地可运行的企业级知识库智能客服 Agent。它面向电商和数码产品售后场景，支持订单查询、退货申请、技术咨询、售后政策问答、产品咨询和投诉转人工。

## 为什么这不是普通 RAG

普通 RAG 通常把用户问题直接送去知识库检索，再生成回答。这个 Demo 会先识别意图，再通过 LangGraph 路由到不同流程：有些问题查 SQLite 订单库，有些调用模拟 ERP 工具，有些检索指定知识库，有些直接创建人工客服工单。每次响应都会返回 `route_trace`、`tool_calls`、`retrieved_docs` 和 `ticket_id`，方便演示 Agent 的决策过程。

## V0.3 更新内容

- OpenAI-compatible LLM 配置：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`。
- 混合意图路由：规则路由 + LLM 路由 + 置信度融合，并返回 `route_debug`。
- 多轮会话状态：新增 `conversation_id`、`slots`、`missing_slots`、`pending_action` 和会话日志。
- 工具调用前确认：`create_return_request`、`create_ticket` 等状态变更工具必须经过确认或高风险升级分支。
- RAG 回答增强：基于检索文档生成回答，并返回 `citations`。
- 回答质量评估：每轮回复写入 `evaluation_result`，并落库到 `chat_logs`。
- 前端调试面板增强：展示 slots、route_debug、citations、evaluation_result 和多轮测试按钮。

## 系统架构图

```text
Web Chat
   |
   v
FastAPI /api/chat
   |
   v
LangGraph Agent State + conversation_id
   |
   +--> load_conversation_node --> SQLite conversations
   +--> parse_input_node
   +--> intent_router_node --> rule router + LLM router + confidence fusion
   +--> route_decision
          |
          +--> order_query_node --> SQLite orders
          +--> slot_filling_node --> missing slot question / pending_action
          +--> confirm_node --> tool_execute_node --> SQLite return_requests
          +--> rag_node --> QdrantRetriever / SimpleRetriever --> citations
          +--> human_ticket_node --> LLM/template summary --> SQLite tickets
          +--> clarify_node
   |
   v
final_response_node
   |
   v
evaluation_node --> save_conversation_node --> SQLite chat_logs
   |
   v
Answer + Intent + Trace + Tools + Retrieved Docs + Citations + Evaluation
```

## 功能列表

- 规则意图识别：订单、退货、退款状态、技术、政策、产品、投诉、人工、未知。
- LangGraph 工作流：每个节点写入 `route_trace`。
- SQLite 业务数据库：订单、退货申请、人工工单。
- 模拟 ERP 工具：订单查询、退货创建、退款状态、工单创建。
- Qdrant 知识库检索：按 `tech`、`policy`、`product` 写入向量库，并带 metadata filter 检索。
- SimpleRetriever 兜底：Qdrant 未启动或不可用时，自动回退到本地 Markdown 检索。
- 调试证据：展示命中的知识库、来源文件、相似度分数、检索器类型和原始 retrieved docs。
- 无 LLM 降级模式：未配置 API Key 时仍可通过规则和模板跑通。
- 多轮槽位补全：退货流程会跨轮保存订单号和退货原因。
- 状态变更确认：退货单只会在用户回复“确认”后创建，取消不会写入退货记录。
- 审计日志：`chat_logs` 记录每轮 route_trace、tool_calls、retrieved_docs、citations 和 evaluation_result。
- Web Chat 页面：左侧对话，右侧展示 Agent 调试证据。

## 技术栈

- Python 3.11+
- FastAPI
- LangGraph
- Pydantic
- SQLite
- SQLAlchemy
- Qdrant
- Uvicorn
- 原生 HTML / CSS / JavaScript

## 启动方式（无 Qdrant 兜底模式）

```bash
cd serviceflow-agent-demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/seed.py
uvicorn main:app --reload
```

访问：

```text
http://127.0.0.1:8000
```

这个模式不要求 Qdrant 已启动。后端会优先尝试 Qdrant，如果连接失败，会自动使用 `SimpleRetriever`，方便快速演示。

## Qdrant Docker Compose 启动方式

启动 Qdrant：

```bash
cd serviceflow-agent-demo
docker compose up -d qdrant
```

Qdrant 默认 REST 地址：

```text
http://127.0.0.1:6333
```

安装依赖并写入知识库向量：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.rag.index_qdrant
```

启动 Demo：

```bash
python app/seed.py
uvicorn main:app --reload
```

### Qdrant 环境变量

```bash
QDRANT_URL=http://127.0.0.1:6333
QDRANT_COLLECTION=serviceflow_knowledge
QDRANT_VECTOR_SIZE=384
QDRANT_ENABLED=true
```

### LLM 环境变量

```bash
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

如果 `OPENAI_API_KEY` 为空，系统会自动进入 fallback 模式：

- 意图识别使用规则路由；
- RAG 回答使用检索文档模板生成；
- 人工工单摘要使用模板摘要；
- 回复质量评估使用轻量规则评估。

每个 chunk 写入 Qdrant 时会携带这些 metadata：

```json
{
  "knowledge_base": "tech",
  "source_file": "knowledge_base/tech/smart_router_wifi.md",
  "product_name": "SmartRouter X1",
  "category": "smart_router_wifi"
}
```

检索时会根据 intent 自动添加 filter：

```text
TECH_SUPPORT -> knowledge_base = tech
POLICY_QA    -> knowledge_base = policy
PRODUCT_QA   -> knowledge_base = product
```

如果问题中识别出 `SmartRouter X1` 或 `SmartCamera C2`，还会追加 `product_name` filter。

## 测试问题示例

- 帮我查一下订单 10001 到哪里了
- 我要退货
- 10001
- 买错了
- 确认
- 取消
- 我要退货，订单号 10003，原因是买错了
- 路由器怎么连接 WiFi
- 7 天无理由退货规则是什么
- SmartRouter X1 支持 macOS 吗
- 我要投诉，转人工客服

## 多轮对话与确认机制

退货申请的必填槽位是 `order_id` 和 `return_reason`。如果用户第一轮只说“我要退货”，Agent 会追问订单号；第二轮用户回复“10001”，Agent 会继续追问退货原因；第三轮用户回复“买错了”，Agent 只设置 `pending_action=CREATE_RETURN_REQUEST` 并提示确认。只有用户再回复“确认”时，`tool_execute_node` 才会调用 `create_return_request`。

取消词包括：`取消`、`算了`、`不用了`、`先不退了`。确认词包括：`确认`、`是的`、`可以`、`提交`、`帮我创建`。

## API 示例

### POST /api/chat

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"我要退货","user_id":"U1001","conversation_id":null}'
```

响应会包含：

```json
{
  "conversation_id": "C202606060001",
  "answer": "请提供需要退货的订单号。",
  "intent": "RETURN_REQUEST",
  "confidence": 0.86,
  "slots": {"order_id": null, "return_reason": null},
  "missing_slots": ["order_id"],
  "pending_action": null,
  "awaiting_user_input": true,
  "route_trace": ["load_conversation_node", "parse_input_node", "intent_router_node", "slot_filling_node", "final_response_node"],
  "route_debug": {},
  "tool_calls": [],
  "retrieved_docs": [],
  "citations": [],
  "evaluation_result": {},
  "need_human": false,
  "ticket_id": null
}
```

### GET /api/conversations/{conversation_id}

返回当前会话状态，包括 `current_intent`、`pending_action`、`slots` 和 `history`。

### GET /api/conversations/{conversation_id}/logs

返回当前会话完整日志，每轮包含 `route_trace`、`tool_calls`、`retrieved_docs`、`citations` 和 `evaluation_result`。

### POST /api/conversations/{conversation_id}/reset

重置当前会话状态，清空 slots、history 和 pending_action。

### GET /api/orders/{order_id}

```bash
curl http://127.0.0.1:8000/api/orders/10001
```

### GET /api/tickets

```bash
curl http://127.0.0.1:8000/api/tickets
```

### GET /api/returns

```bash
curl http://127.0.0.1:8000/api/returns
```

## 后续扩展方向

- 替换当前 HashEmbedding 为 OpenAI-compatible embedding 或本地 embedding 模型。
- 为 Qdrant 增加 collection schema 版本、批量重建和增量索引。
- 接入真实 ERP，把工具函数从 SQLite 模拟替换成真实 API。
- 接入客服后台，处理工单分配、状态流转和 SLA。
- 加入人工审核，允许客服确认退货或投诉处理结果。
- V0.4 规划：接入真实客服权限、人工审核队列、Agent 指标看板、跨渠道会话合并、embedding 服务配置化和更严格的 LLM Judge 评测集。
