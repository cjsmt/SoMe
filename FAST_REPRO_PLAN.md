# SoMe MID 最终提交执行计划

## 当前状态（已完成）

- 已跑通 `MID` 子实验并完成 `200` 样本推理。
- baseline 结果：`gpt-4o-mini` 在 200 样本上 `ACC = 52.0`。
- 已有完整 debug diary：`REPRO_LOG.md`。

---

## 作业要求对照（FTEC5660）

你的作业必须包含 3 件事：

1. 复现至少一个已报告结果（已满足：MID ACC）。
2. 做一个小而可测量的 modification（待补）。
3. 报告“改前 vs 改后”变化并解释原因（待补）。

---

## Baseline（已完成）命令记录

```bash
set -a && source .env && set +a && python3 test_misinformation_detection.py \
  --output_path "results/mid_run_01" \
  --max_samples 200 \
  --max_retries 2
```

```bash
python3 eval_scripts/MID_extraction.py \
  --result_path "results/mid_run_01" \
  --output_path "scores/mid_run_01" \
  --setting_path "eval_scripts/settings.json" \
  --api_retry 5
```

```bash
mkdir -p scores/misinformation_detection
cp scores/mid_run_01/*.json scores/misinformation_detection/
python3 eval_scripts/MID_compute_score.py
```

---

## 必做：Modification 实验（建议方案）

### 修改点（单变量、可量化）

在 `test_misinformation_detection.py` 中已加入参数：

- `--retrieval_topk`

该参数会约束工具调用 `knowledge_retrieve` 的 `topk`，用于做一个明确的 retrieval ablation。

### 推荐对比

- Baseline：`retrieval_topk = default(不强制)`（已完成，ACC=52.0）
- Modified：`retrieval_topk = 5`

### Modified 运行命令

```bash
set -a && source .env && set +a && python3 test_misinformation_detection.py \
  --output_path "results/mid_run_mod_topk5" \
  --max_samples 200 \
  --max_retries 2 \
  --retrieval_topk 5
```

```bash
python3 eval_scripts/MID_extraction.py \
  --result_path "results/mid_run_mod_topk5" \
  --output_path "scores/mid_run_mod_topk5" \
  --setting_path "eval_scripts/settings.json" \
  --api_retry 5
```

```bash
cp scores/mid_run_mod_topk5/*.json scores/misinformation_detection/
python3 eval_scripts/MID_compute_score.py
```

---

## 可选加分：再跑两行 Table 3（Gemini / Kimi）

可以做，但建议每个模型先跑 `100` 样本，避免时间失控。

### Gemini（示例）

```bash
set -a && source .env && set +a && python3 test_misinformation_detection.py \
  --model "gemini-2.5-flash" \
  --output_path "results/mid_gemini_100" \
  --max_samples 100 \
  --max_retries 2
```

### Kimi（示例）

```bash
set -a && source .env && set +a && python3 test_misinformation_detection.py \
  --model "kimi-k2-instruct" \
  --output_path "results/mid_kimi_100" \
  --max_samples 100 \
  --max_retries 2
```

> 注意：模型名必须是你当前 API 平台支持的实际 name，否则会 4xx/5xx。

---

## 最终报告里建议出现的结果表

| Setting | Model | Samples | ACC |
|---|---|---:|---:|
| Baseline | gpt-4o-mini | 200 | 52.0 |
| Modified (`retrieval_topk=5`) | gpt-4o-mini | 200 | TBD |
| Optional extra | gemini-2.5-flash | 100 | TBD |
| Optional extra | kimi-k2-instruct | 100 | TBD |

同时对照论文 Table 3（MID）可写：

- GPT-4o: 50.24
- Kimi-K2-Instruct: 47.83
- Gemini-2.5-Flash: 45.62
- DeepSeek-V3: 51.00

---

## 提交前最终检查

- [ ] baseline 与 modification 都有结果文件与 ACC。
- [ ] 报告里写清楚模型/端点/样本数/参数。
- [ ] 报告里明确“与论文不完全可比”的原因（模型与样本规模不同）。
- [ ] `REPRO_LOG.md` 中已包含主要 bug 与修复路径。
- [ ] 仓库不包含 API key（提交前检查 `.env`）。

