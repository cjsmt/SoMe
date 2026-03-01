# FTEC5660 复现实验报告（中文版）

## 0. 基本信息

- 课程：FTEC5660 Agentic AI for Business and FinTech
- 姓名：ZHANG Xianglong
- 学号：1155241554
- 项目仓库：`https://github.com/LivXue/SoMe`
- 论文：*SoMe: A Realistic Benchmark for LLM-based Social Media Agents* (arXiv:2512.14720)
- 复现目标：MID 任务 ACC（Table 3 相关指标）+ 一个可测量的小改动

---

## 1. 项目概述

本报告复现 SoMe 基准中的 MID（Misinformation Detection）子任务。在有限算力与截止时间下，我选择 200 样本子集完成可复现实验，并基于同一流程进行可控改动实验与多模型扩展对比。

---

## 2. 环境与配置

- 操作系统：macOS (darwin 23.6.0)
- Python：3.12（conda: `py312`）
- 硬件：本地无 NVIDIA GPU（CPU/MPS）
- API 接口：OpenAI-compatible (`https://aihubmix.com/v1`)
- 使用模型：`gpt-4o-mini`、`gemini-2.5-flash`、`kimi-k2-instruct`
- 关键依赖：`openai`、`sentence-transformers`、`torch`、`tqdm`、`json5`、`python-dotenv`

---

## 3. 复现目标与指标

- 目标：复现 MID 的 ACC，并与论文 Table 3 做量级对照。
- 指标定义：对 agent 原始输出先做答案抽取（extraction），再按 ground truth 计算准确率（ACC）。

---

## 4. 复现流程

1. 环境与依赖修复（适配 macOS）。
2. 修复仓库运行阻塞（导入、argparse、评估脚本保存逻辑等）。
3. baseline 推理（200 样本）并保存中间结果。
4. 执行 `MID_extraction` 和 `MID_compute_score` 获得 ACC。
5. 做单变量改动（`retrieval_topk=5`）并重复相同流程。
6. 扩展到 Gemini/Kimi 同样 200 样本设置，保持可比性。

---

## 5. 小改动（Modification）

- 改动类型：工具策略参数改动（retrieval policy ablation）。
- 具体实现：在 `test_misinformation_detection.py` 增加 `--retrieval_topk`，并在 query 中约束 `knowledge_retrieve` 的 `topk`。
- 控制变量：样本量（200）、评估流程、运行脚本一致，仅修改 retrieval 策略。

---

## 6. 结果对比

| 设置 | 模型 | 样本数 | ACC |
|---|---|---:|---:|
| Baseline | gpt-4o-mini | 200 | 52.0 |
| Modified (topk=5) | gpt-4o-mini | 200 | 52.5 |
| Baseline | gemini-2.5-flash | 200 | 55.5 |
| Modified (topk=5) | gemini-2.5-flash | 200 | 51.5 |
| Baseline | kimi-k2-instruct | 200 | 55.0 |
| Modified (topk=5) | kimi-k2-instruct | 200 | 54.0 |

论文 Table 3 参考（MID）：
- GPT-4o: 50.24
- Gemini-2.5-Flash: 45.62
- Kimi-K2-Instruct: 47.83
- DeepSeek-V3: 51.00

---

## 7. 结果讨论

1. **检索约束对不同模型影响不同**  
   - `gpt-4o-mini`：`52.0 -> 52.5`（小幅提升）  
   - `gemini-2.5-flash`：`55.5 -> 51.5`（明显下降）  
   - `kimi-k2-instruct`：`55.0 -> 54.0`（小幅下降）  

2. **不存在统一最优的 retrieval topk**  
   相同改动在不同模型上表现不同，说明工具策略与模型内部推理/工具调用行为存在耦合。实际部署应按模型单独调参，而非使用全局固定值。

3. **误差来源与稳定性因素**  
   - 模型与论文设定不完全一致；
   - 子样本（200）与全量（1451）存在方差；
   - API 端偶发 502，虽有重试与规则兜底，仍可能引入少量噪声。

---

## 8. 对原仓库代码的关键改动（摘要）

详见 `REPRO_LOG.md`。核心包括：
- 修复 `test_misinformation_detection.py` 参数解析与中断处理；
- 修复多处语法错误和缺失模块导入；
- 修复 `eval_scripts` 的 argparse / settings 读取问题；
- 增加 `MID_extraction` 的 API 重试与规则抽取兜底；
- 修复 extraction 结果不落盘的缩进 bug；
- 增加 `max_samples`、`max_retries`、`retrieval_topk` 以支持可控实验。

---

## 9. 结论

- 成功在本地环境复现了 SoMe 的 MID 子任务流程，并完成 baseline + modification + 多模型扩展。
- 在 200 样本设置下，复现结果与论文表中对应模型分数处于可比较量级。
- 实验显示 retrieval 策略并非模型无关超参数，需要按模型单独调优。
- 本报告结果可复核，且完整排障过程已在 `REPRO_LOG.md` 留痕。
