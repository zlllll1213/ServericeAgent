# 测试说明

## 单元与集成测试

```bash
make test
python -m pytest tests/test_tools.py -q
python -m pytest tests/test_chat_return.py -q
```

测试会使用 `app.seed.seed_database(reset=True)` 初始化独立演示数据，避免污染人工调试产生的数据。

## 覆盖率

```bash
make coverage
```

覆盖率配置位于 `pyproject.toml`。当前阶段优先覆盖工具函数、Agent 工作流、RAG fallback、后台 Trace/Metrics API。

## CI 测试

GitHub Actions 配置位于 `.github/workflows/ci.yml`，会执行：

1. 安装依赖；
2. 初始化演示数据库；
3. `make lint`；
4. `make test`；
5. `make eval`；
6. 上传 `reports/`。

## 新增测试用例

新增测试时优先复用 `tests/conftest.py` 的 `client`、`chat`、`admin_headers` fixture。对于当前 Demo 尚未接入的外部系统能力，可以先写契约测试或标注 skip 原因，避免伪造外部依赖通过。
