# ServiceFlow Agent Demo

ServiceFlow Agent Demo 是一个本地可运行的企业级知识库智能客服 Agent。它面向电商和数码产品售后场景，支持订单查询、退货申请、技术咨询、售后政策问答、产品咨询和投诉转人工。

## 为什么这不是普通 RAG

普通 RAG 通常把用户问题直接送去知识库检索，再生成回答。这个 Demo 会先识别意图，再通过 LangGraph 路由到不同流程：有些问题查 SQLite 订单库，有些调用模拟 ERP 工具，有些检索指定知识库，有些直接创建人工客服工单。每次响应都会返回 `route_trace`、`tool_calls`、`retrieved_docs` 和 `ticket_id`，方便演示 Agent 的决策过程。

## 系统架构图

```text
Web Chat
   |
   v
FastAPI /api/chat
   |
   v
LangGraph Agent State
   |
   +--> parse_input_node
   +--> intent_router_node
   +--> route_decision
          |
          +--> order_query_node --> SQLite orders
          +--> return_request_node --> customer tools --> SQLite return_requests
          +--> rag_tech_node --> SimpleRetriever --> knowledge_base/tech
          +--> rag_policy_node --> SimpleRetriever --> knowledge_base/policy
          +--> rag_product_node --> SimpleRetriever --> knowledge_base/product
          +--> human_ticket_node --> SQLite tickets
          +--> clarify_node
   |
   v
final_response_node
   |
   v
Answer + Intent + Trace + Tools + Retrieved Docs
```

## 功能列表

- 规则意图识别：订单、退货、退款状态、技术、政策、产品、投诉、人工、未知。
- LangGraph 工作流：每个节点写入 `route_trace`。
- SQLite 业务数据库：订单、退货申请、人工工单。
- 模拟 ERP 工具：订单查询、退货创建、退款状态、工单创建。
- 本地知识库检索：按 `tech`、`policy`、`product` 分类检索 Markdown。
- 无 LLM 降级模式：未配置 API Key 时仍可通过规则和模板跑通。
- Web Chat 页面：左侧对话，右侧展示 Agent 调试证据。

## 技术栈

- Python 3.11+
- FastAPI
- LangGraph
- Pydantic
- SQLite
- SQLAlchemy
- Uvicorn
- 原生 HTML / CSS / JavaScript

## 启动方式

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

## 测试问题示例

- 帮我查一下订单 10001 到哪里了
- 我要退货，订单号 10001
- 我要退货，订单号 10003
- 路由器怎么连接 WiFi
- 7 天无理由退货规则是什么
- SmartRouter X1 支持 macOS 吗
- 我要投诉，转人工客服

## API 示例

### POST /api/chat

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"我要退货，订单号 10001","user_id":"U1001"}'
```

响应会包含：

```json
{
  "answer": "已为你创建退货申请...",
  "intent": "RETURN_REQUEST",
  "confidence": 0.8,
  "route_trace": ["parse_input_node", "intent_router_node", "return_request_node", "final_response_node"],
  "tool_calls": [],
  "retrieved_docs": [],
  "need_human": false,
  "ticket_id": null
}
```

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

- 接入 Qdrant 或 pgvector，替换 `VectorRetriever` 预留接口。
- 接入真实 ERP，把工具函数从 SQLite 模拟替换成真实 API。
- 接入客服后台，处理工单分配、状态流转和 SLA。
- 接入大模型意图识别，在低置信度时用 LLM 复核分类。
- 支持多轮槽位补全，例如缺少订单号时继续追问并保留上下文。
- 加入人工审核，允许客服确认退货或投诉处理结果。
- 加入对话评估，统计意图准确率、转人工率和检索命中率。
