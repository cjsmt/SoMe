# FTEC5660 Reproducibility Report (English)

## 0. Basic Information

- Course: FTEC5660 Agentic AI for Business and FinTech
- Name: ZHANG Xianglong
- SID: 1155241554
- Project Repo (my reproduction code): `https://github.com/csjmt/SoMe`
- Original Repo (authors): `https://github.com/LivXue/SoMe`
- Paper: *SoMe: A Realistic Benchmark for LLM-based Social Media Agents* (arXiv:2512.14720)
- Reproduction Target: MID ACC (Table 3-related metric) + one controlled modification

---

## 1. Project Summary

This report reproduces the MID (Misinformation Detection) subtask in SoMe.  
Under limited time/compute budget, I run a reproducible 200-sample subset pipeline and then conduct one isolated modification plus multi-model extensions.

---

## 2. Setup Notes

- OS: macOS (darwin 23.6.0)
- Python: 3.12 (conda env: `py312`)
- Hardware: local machine without NVIDIA GPU (CPU/MPS mode)
- API endpoint: OpenAI-compatible (`https://aihubmix.com/v1`)
- Models used: `gpt-4o-mini`, `gemini-2.5-flash`, `kimi-k2-instruct`
- Key packages: `openai`, `sentence-transformers`, `torch`, `tqdm`, `json5`, `python-dotenv`

---

## 3. Reproduction Target and Metric

- Target claim: MID performance reported in Table 3.
- Metric: ACC after answer extraction (`MID_extraction.py`) and score computation (`MID_compute_score.py`).

---

## 4. Reproduction Workflow

1. Fix environment/dependency issues for macOS.
2. Fix runnability blockers in repo code (imports, argparse, eval scripts).
3. Run baseline inference on 200 MID samples.
4. Run extraction + scoring to get baseline ACC.
5. Apply one isolated modification (`retrieval_topk=5`) and rerun.
6. Repeat under the same 200-sample setting for Gemini and Kimi.

---

## 5. Modification

- Type: tool policy parameter ablation.
- Change: add `--retrieval_topk` in `test_misinformation_detection.py` and constrain `knowledge_retrieve` topk in the query instruction.
- Controlled variables: same sample size (200), same scoring pipeline, same retry strategy; only retrieval policy changed.

---

## 6. Results

| Setting | Model | Samples | ACC |
|---|---|---:|---:|
| Baseline | gpt-4o-mini | 200 | 52.0 |
| Modified (topk=5) | gpt-4o-mini | 200 | 52.5 |
| Baseline | gemini-2.5-flash | 200 | 55.5 |
| Modified (topk=5) | gemini-2.5-flash | 200 | 51.5 |
| Baseline | kimi-k2-instruct | 200 | 55.0 |
| Modified (topk=5) | kimi-k2-instruct | 200 | 54.0 |

Reference values from paper Table 3 (MID):
- GPT-4o: 50.24
- Gemini-2.5-Flash: 45.62
- Kimi-K2-Instruct: 47.83
- DeepSeek-V3: 51.00

---

## 7. Discussion

1. **Model-specific sensitivity to retrieval constraints**
   - `gpt-4o-mini`: `52.0 -> 52.5` (slight gain)
   - `gemini-2.5-flash`: `55.5 -> 51.5` (clear drop)
   - `kimi-k2-instruct`: `55.0 -> 54.0` (moderate drop)

2. **No universally best topk**
   The same retrieval constraint behaves differently across models, suggesting interaction between retrieval policy and model-specific reasoning/tool-use behavior. Retrieval hyperparameters should be tuned per model.

3. **Potential noise sources**
   - Non-identical model/provider setup vs paper
   - Subset (200) vs full set (1451)
   - Occasional API 502 instability, partially mitigated by retry/fallback extraction

---

## 8. Key Code Fixes to Original Repo (Summary)

Detailed log is in `REPRO_LOG.md`. Main fixes include:
- argparse and interrupt handling in `test_misinformation_detection.py`
- syntax/import repairs across scripts
- missing module bridge (`qwen_agent/llm/oai.py`)
- eval script fixes for argparse/settings parsing
- robust extraction fallback + retry for 502s
- extraction output persistence fix (indentation bug)
- speed-control and ablation parameters (`max_samples`, `max_retries`, `retrieval_topk`)

---

## 9. Conclusion

- The MID pipeline is successfully reproduced end-to-end on a practical subset.
- Baseline + modification + multi-model extension are all completed with measurable outputs.
- Retrieval policy is not model-agnostic; its effect can reverse across models.
- Results are reproducible under this setup, with full debugging trace available in `REPRO_LOG.md`.
