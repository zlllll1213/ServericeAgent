# Agent 评测说明

## 数据集

评测数据位于 `evals/datasets/`：

- `intent_eval.jsonl`：意图识别样本。
- `rag_eval.jsonl`：RAG 检索与引用样本。
- `tool_eval.jsonl`：工具选择与工具成功率样本。
- `end_to_end_eval.jsonl`：多轮闭环任务样本。

每行一个 JSON 对象，新增样本时请保持字段稳定并加入 `id`。

## 运行方式

```bash
make eval
python evals/run_eval.py --dataset intent
python evals/run_eval.py --dataset rag
python evals/run_eval.py --dataset tool
python evals/run_eval.py --dataset e2e
python evals/run_eval.py --all
```

运行后会在 `reports/eval_report_日期.md` 生成 Markdown 报告。

## 指标解释

- Intent Accuracy：预测意图与期望意图一致的比例。
- RAG Hit Rate：检索知识库类型命中的比例。
- Citation Hit Rate：引用来源命中的比例。
- Tool Selection Accuracy：期望工具被调用的比例。
- End-to-End Task Success Rate：多轮任务最终状态满足预期的比例。

## 失败样本分析

报告中的 Failed Cases 会列出样本 ID、输入、期望、实际和原因。处理失败样本时建议先判断：

- 是规则意图词缺失；
- 是知识库内容或标题不够可检索；
- 是工具槽位抽取不足；
- 是测试期望过窄。
