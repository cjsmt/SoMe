# FTEC5660 Reproducibility Report Template (CN/EN)

## 0. Basic Info / 基本信息

- Course: FTEC5660 Agentic AI for Business and FinTech
- Name: ZHANG Xianglong
- SID: 1155241554 
- Project Repo: `https://github.com/LivXue/SoMe`
- Paper: *SoMe: A Realistic Benchmark for LLM-based Social Media Agents* (arXiv:2512.14720)
- Reproduction Target: MID task ACC (Table 3 related result) + one controlled modification

---

## 1. Project Summary / 项目概述

### EN
This report reproduces a subset experiment from **SoMe: A Realistic Benchmark for LLM-based Social Media Agents**.  
I focus on the **MID (Misinformation Detection)** task and reproduce a reported metric (ACC) on a feasible subset under limited compute/time budget.

### 中文
本报告复现论文 **SoMe: A Realistic Benchmark for LLM-based Social Media Agents** 的一个子实验。  
我选择 **MID（虚假信息检测）** 任务，在有限算力和时间预算下复现其指标（ACC）。

---

## 2. Setup Notes / 环境与配置

### EN
- OS: macOS (darwin 23.6.0)
- Python: 3.12 (conda env: `py312`)
- Hardware: local machine without NVIDIA GPU (CPU/MPS mode)
- API provider / endpoint: OpenAI-compatible endpoint (`https://aihubmix.com/v1`)
- Baseline model: `gpt-4o-mini`
- Key packages: `openai`, `sentence-transformers`, `torch`, `tqdm`, `json5`, `python-dotenv`

### 中文
- 操作系统：macOS（darwin 23.6.0）
- Python 版本：3.12（conda 环境 `py312`）
- 硬件环境：本地无 NVIDIA GPU（CPU/MPS）
- API 提供方 / endpoint：OpenAI 兼容接口（`https://aihubmix.com/v1`）
- 基线模型：`gpt-4o-mini`
- 关键依赖：`openai`、`sentence-transformers`、`torch`、`tqdm`、`json5`、`python-dotenv`

---

## 3. Reproduction Target / 复现目标

### EN
Target claim: reproduce MID accuracy (Table 3 related result) using the official repo pipeline.  
Metric: ACC (after answer extraction + score computation).

### 中文
目标声明：使用官方仓库流程复现 MID 任务准确率（对应 Table 3 的结果）。  
指标：ACC（先做答案抽取，再做打分）。

---

## 4. Baseline Reproduction / 基线复现

### EN
Commands (baseline):

```bash
set -a && source .env && set +a && python3 test_misinformation_detection.py \
  --output_path "results/mid_run_01" \
  --max_samples 200 \
  --max_retries 2

python3 eval_scripts/MID_extraction.py \
  --result_path "results/mid_run_01" \
  --output_path "scores/mid_run_01" \
  --setting_path "eval_scripts/settings.json" \
  --api_retry 5

mkdir -p scores/misinformation_detection
cp scores/mid_run_01/*.json scores/misinformation_detection/
python3 eval_scripts/MID_compute_score.py
```

Result:
- Model: `gpt-4o-mini`
- Samples: `200`
- ACC: `52.0`

### 中文
基线命令同上。  
结果：
- 模型：`gpt-4o-mini`
- 样本数：`200`
- ACC：`52.0`

---

## 5. Modification / 小改动实验

### EN
Modification: force retrieval policy with `--retrieval_topk 5` in MID inference script.  
Reason: this is a small, isolated, measurable change on tool-use behavior.

Commands:

```bash
set -a && source .env && set +a && python3 test_misinformation_detection.py \
  --output_path "results/mid_run_mod_topk5" \
  --max_samples 200 \
  --max_retries 2 \
  --retrieval_topk 5

python3 eval_scripts/MID_extraction.py \
  --result_path "results/mid_run_mod_topk5" \
  --output_path "scores/mid_run_mod_topk5" \
  --setting_path "eval_scripts/settings.json" \
  --api_retry 5

cp scores/mid_run_mod_topk5/*.json scores/misinformation_detection/
python3 eval_scripts/MID_compute_score.py
```

### 中文
改动内容：在 MID 推理脚本中增加并启用 `--retrieval_topk 5`，约束工具检索策略。  
选择理由：改动小、变量单一、可以量化。

---

## 6. Results Comparison / 结果对比

| Setting | Model | Samples | ACC |
|---|---|---:|---:|
| Baseline | gpt-4o-mini | 200 | 52.0 |
| Modified (topk=5) | gpt-4o-mini | 200 | 52.5 |
| Baseline | gemini-2.5-flash | 200 | 55.5 |
| Modified (topk=5) | gemini-2.5-flash | 200 | 51.5 |
| Baseline | kimi-k2-instruct | 200 | 55.0 |
| Modified (topk=5) | kimi-k2-instruct | 200 | 54.0 |

Reference from paper Table 3 (MID):
- GPT-4o: 50.24
- Gemini-2.5-Flash: 45.62
- Kimi-K2-Instruct: 47.83
- DeepSeek-V3: 51.00

### Discussion / 结果讨论

#### EN
Two observations are notable from the controlled ablation:

1. **Model-specific sensitivity to retrieval policy**  
   On `gpt-4o-mini`, constraining retrieval to `topk=5` slightly improved ACC (`52.0 -> 52.5`), suggesting that reducing noisy evidence may help this model produce cleaner final labels.  
   On `gemini-2.5-flash`, the same change reduced ACC (`55.5 -> 51.5`), indicating that this model may benefit from broader evidence coverage and suffers when candidate evidence is overly pruned.

2. **No universal best retrieval setting**  
   The opposite trends imply that retrieval hyperparameters are not model-agnostic. A fixed tool policy can improve one model while hurting another. In practice, retrieval settings should be tuned per model rather than hard-coded globally.

With the additional Kimi run (`55.0 -> 54.0`), the same direction as Gemini is observed (performance drop after `topk=5`), while gpt-4o-mini shows a slight gain. This further supports the view that retrieval constraints interact with model-specific reasoning/tool-use patterns.

Potential causes include: (i) different tolerance to noisy context, (ii) different tool-call formatting robustness, and (iii) occasional API instability (502) that may introduce a small amount of extraction noise despite retry/fallback protections.

#### 中文
在本次单变量改动实验中，有两个关键发现：

1. **不同模型对检索策略的敏感性不同**  
   对 `gpt-4o-mini` 来说，将检索约束为 `topk=5` 后 ACC 小幅提升（`52.0 -> 52.5`），说明减少噪声证据可能有助于该模型给出更干净的最终标签。  
   但对 `gemini-2.5-flash`，同样改动导致 ACC 下降（`55.5 -> 51.5`），说明该模型可能更依赖更广覆盖的证据集合，当候选证据被过度裁剪时性能会下降。

2. **不存在对所有模型都最优的统一 topk**  
   两种相反趋势表明检索超参数不是“模型无关”的。固定工具策略可能提升某些模型，却损害另一些模型。因此在实际部署中，retrieval 参数应按模型单独调优，而不是全局硬编码。

补充 Kimi 实验后（`55.0 -> 54.0`），其趋势与 Gemini 一致（topk=5 后下降），而与 gpt-4o-mini 的小幅提升相反，进一步说明检索约束与模型内部推理/工具使用机制存在交互效应。

可能原因包括：  
（i）模型对噪声上下文的容忍度不同；  
（ii）模型工具调用格式稳定性不同；  
（iii）API 偶发 502 仍可能引入少量抽取噪声（尽管已有重试与规则兜底）。

---

## 7. Debug Diary / 排障记录

### EN
Main blockers and fixes are documented in `REPRO_LOG.md`.

### 中文
主要问题与修复过程记录在 `REPRO_LOG.md`（包括环境安装、导入错误、评估脚本 bug、API 502 兜底等）。

---

## 8. Conclusion / 结论

### EN
- What reproduced:
  - The MID task pipeline was successfully executed end-to-end (inference -> extraction -> scoring).
  - On 200 samples, baseline ACC reached `52.0`.
- What did not reproduce perfectly:
  - Full 1451-sample run was not completed due to time and API constraints.
  - Result is not directly one-to-one comparable with paper's full setup.
- Why:
  - Different model/provider endpoint, partial sample subset, and practical API instability (e.g., 502).
- Recommendation for future users:
  - Keep a strict run log, use resumable outputs, and evaluate with fixed folders to avoid mixed-model files.
  - Run controlled ablations (single-variable changes), e.g., retrieval policy.

### 中文
- 成功复现部分：
  - MID 子任务流程已端到端跑通（推理 -> 抽取 -> 评分）。
  - 在 200 样本上，baseline ACC = `52.0`。
  - 小改动实验（`retrieval_topk=5`）后 ACC = `52.5`，较 baseline 提升 `+0.5`。
  - 额外模型对比：`gemini-2.5-flash` 在 200 样本 baseline ACC=`55.5`，modified(topk=5) ACC=`51.5`。
  - 额外模型对比：`kimi-k2-instruct` 在 200 样本 baseline ACC=`55.0`，modified(topk=5) ACC=`54.0`。
- 未完全复现部分：
  - 未完成论文规模的 1451 全量样本复现。
  - 与论文原表格不可做严格一一对齐。
- 原因分析：
  - 使用的模型/服务提供商不同，且仅使用子样本；
  - 现实运行中存在 API 波动（如 502）和工具调用格式问题。
- 对后续使用者建议：
  - 优先保证可恢复与可记录（中间结果持续落盘）；
  - 采用单变量改动做 ablation，避免多个因素同时变化。

---

## 9. Reproduction Workflow / 复现流程

### 中文
1. **环境准备**：修复依赖安装问题，清理不适配 macOS 的 CUDA/triton 依赖。  
2. **代码跑通**：修复仓库中的导入错误、参数解析错误、评估脚本错误。  
3. **Baseline 运行**：`gpt-4o-mini` 跑 `200` 样本并得到原始结果。  
4. **评分流程**：执行 `MID_extraction` 与 `MID_compute_score` 得到 baseline ACC=`52.0`。  
5. **Modification 运行**：仅改动检索策略（`retrieval_topk=5`）并重复同样流程。  
6. **改后评分**：得到 modified ACC=`52.5`，形成改前改后对比。  
7. **扩展验证（可选）**：在相同样本数（200）下运行 `gemini-2.5-flash`，获得 baseline `55.5` 与 modified `51.5`。  
8. **扩展验证（可选）**：在相同样本数（200）下运行 `kimi-k2-instruct`，获得 baseline `55.0` 与 modified `54.0`。  

### EN
1. Environment preparation (dependency fixes for macOS).  
2. Repository runnability fixes (imports/argparse/evaluation scripts).  
3. Baseline run on 200 MID samples (`gpt-4o-mini`).  
4. Extraction + scoring for baseline (ACC=`52.0`).  
5. One isolated modification (`retrieval_topk=5`) and rerun.  
6. Extraction + scoring for modified run (ACC=`52.5`).  
7. Optional extension with `gemini-2.5-flash` on the same 200-sample setup (baseline `55.5`, modified `51.5`).  
8. Optional extension with `kimi-k2-instruct` on the same 200-sample setup (baseline `55.0`, modified `54.0`).  

---

## 10. Modification Point / 改动点说明

### 中文
- **改动类型**：工具策略参数改动（retrieval policy ablation）。  
- **具体改动**：在 `test_misinformation_detection.py` 增加 `--retrieval_topk` 参数，并在 query 中约束 `knowledge_retrieve` 的 `topk`。  
- **控制变量**：模型、样本量（200）、重试策略、评估脚本保持一致，仅修改 retrieval topk。  
- **影响结果**：ACC 从 `52.0` 提升至 `52.5`。  

### EN
- **Type**: tool policy parameter change (retrieval ablation).  
- **Implementation**: added `--retrieval_topk` in `test_misinformation_detection.py` and constrained `knowledge_retrieve` topk in prompt instruction.  
- **Controlled setup**: same model, sample size, retries, and evaluation; only retrieval policy changed.  
- **Measured impact**: ACC improved from `52.0` to `52.5`.  

---

## 11. Key Repository Fixes (from REPRO_LOG) / 对原仓库代码的关键改动

### 中文（摘要）
- 修复 `test_misinformation_detection.py` 的 argparse 错误（`description` -> `help`，补齐参数定义）。  
- 修复多文件 f-string 引号冲突导致的语法错误。  
- 补全缺失模块：新增 `qwen_agent/llm/oai.py`，修复导入链。  
- 修复 `qwen_agent/tools/__init__.py` 中对不存在模块的导入。  
- 避免无关工具导入副作用导致 MID 报错（按需容错导入）。  
- 修复 `eval_scripts` 中 `settings` 读取和 argparse 参数问题。  
- 为 `MID_extraction.py` 增加 API 重试与规则抽取兜底，缓解 502 中断。  
- 修复 `MID_extraction.py` 输出保存缩进 bug（跑完但不落盘的问题）。  
- 新增运行效率参数：`max_samples`、`max_retries`，并修复 `Ctrl+C` 被吞问题。  

### EN (summary)
- Fixed argparse issues in `test_misinformation_detection.py` (`description` -> `help`, restored missing args).  
- Fixed multiple f-string syntax issues.  
- Added missing `qwen_agent/llm/oai.py` to restore import chain.  
- Fixed missing-module imports in `qwen_agent/tools/__init__.py`.  
- Avoided import side effects from unrelated tools that blocked MID.  
- Fixed `settings` loading and argparse issues across evaluation scripts.  
- Added retry + rule-based fallback in `MID_extraction.py` for API 502 robustness.  
- Fixed output persistence indentation bug in `MID_extraction.py`.  
- Added speed-control args (`max_samples`, `max_retries`) and proper KeyboardInterrupt handling.
