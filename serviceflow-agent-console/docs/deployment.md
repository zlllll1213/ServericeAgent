# 部署说明

## 本地开发

```bash
make dev
```

默认会初始化 SQLite 演示数据，并启动 `uvicorn main:app --reload --port 8001`。

## Docker Compose

```bash
make docker-up
make docker-down
```

当前 Compose 主要用于启动 Qdrant。Qdrant 不可用时，系统会自动 fallback 到 `SimpleRetriever`。

## 环境变量

```bash
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
QDRANT_URL=http://127.0.0.1:6333
QDRANT_COLLECTION=serviceflow_knowledge
QDRANT_ENABLED=true
QDRANT_TIMEOUT_SECONDS=3.0
AUTH_SECRET=please-change-this-secret-in-real-environments
DEMO_AUTH_ENABLED=false
ADMIN_PASSWORD_HASH=
AGENT_PASSWORD_HASH=
REDIS_URL=
RATE_LIMIT_BACKEND=memory
CHAT_RATE_LIMIT_ENABLED=true
CHAT_RATE_LIMIT_REQUESTS=60
CHAT_RATE_LIMIT_WINDOW_SECONDS=60
```

CI 和测试不依赖真实 OpenAI API Key。`AUTH_SECRET` 在生产或公网环境必须替换为强随机值；`DEMO_AUTH_ENABLED` 只用于本地演示，不能在生产开启。生产环境需要从环境变量或密钥管理系统提供 `ADMIN_PASSWORD_HASH` 和 `AGENT_PASSWORD_HASH`。

当前内存限流只适合单进程 Demo。多 worker 或多实例部署时应设置 `RATE_LIMIT_BACKEND=redis` 并配置 `REDIS_URL`，系统会使用 Redis `INCR` + `EXPIRE` 做跨进程统一计数。

## 压测

启动服务后执行：

```bash
python scripts/load_test.py --users 20 --requests 200
```

结果会输出 JSON，并写入 `reports/load_test_report_日期.md`。
