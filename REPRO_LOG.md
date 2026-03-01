# Reproduction Fix Log (SoMe)

Date: 2026-02-28
Scope: one-pass blocker bug fixing for fast MID reproduction and evaluation

## 1) Blocking issues identified

- `test_misinformation_detection.py` had `argparse` variable misuse (`parser` and `args` mixed before parse), causing immediate runtime failure.
- Multiple `test_*.py` scripts had invalid f-string quoting in `strftime(...)` log lines, causing syntax errors.
- `tools/en/knowledge_retrieve.py` had invalid f-string quoting when accessing dictionary keys (`doc["content"]` inside double-quoted f-string), causing import/syntax failure.
- `eval_scripts/*_extraction.py` and `eval_scripts/*_scoring.py` loaded `settings.json` as dict but accessed with attribute style (e.g., `settings.api_key`), causing runtime attribute errors.
- Some scripts assumed output directories already existed, which could cause file write failures on fresh runs.

## 2) Files modified and what was fixed

### A. MID main execution path

- `test_misinformation_detection.py`
  - Fixed argument registration to use `parser.add_argument(...)`.
  - Added `os.makedirs(args.output_path, exist_ok=True)` before writing outputs.
  - Fixed off-peak wait log f-string quoting (`strftime('%Y-%m-%d %H:%M:%S')`).

- `tools/en/knowledge_retrieve.py`
  - Fixed dictionary key access quoting inside f-string:
    - from `doc["content"]` / `doc["link"]`
    - to `doc['content']` / `doc['link']`

### B. Global syntax blockers in test scripts

The following files all had the same f-string quoting syntax bug and were fixed to single quotes in `strftime(...)`:

- `test_user_emotion_analysis.py`
- `test_user_comment_simulation.py`
- `test_user_behavior_prediction.py`
- `test_streaming_event_summary.py`
- `test_social_media_question_answering.py`
- `test_realtime_event_detection.py`
- `test_media_content_recommend.py`

### C. Evaluation settings loading blockers

For each file below:
- added `from types import SimpleNamespace`
- changed settings loading to:
  - `settings = SimpleNamespace(**json.load(open(args.setting_path, 'r')))`
- added `os.makedirs(args.output_path, exist_ok=True)` to avoid output-path missing errors

Modified files:

- `eval_scripts/MID_extraction.py`
- `eval_scripts/MCR_extraction.py`
- `eval_scripts/UBP_extraction.py`
- `eval_scripts/UCS_extraction.py`
- `eval_scripts/UEA_extraction.py`
- `eval_scripts/RED_scoring.py`
- `eval_scripts/SES_scoring.py`
- `eval_scripts/SMQ_scoring.py`

## 3) Validation

Ran syntax compilation check on all patched files:

- Command:
  - `python3 -m py_compile test_misinformation_detection.py test_user_emotion_analysis.py test_user_comment_simulation.py test_user_behavior_prediction.py test_streaming_event_summary.py test_social_media_question_answering.py test_realtime_event_detection.py test_media_content_recommend.py tools/en/knowledge_retrieve.py eval_scripts/MID_extraction.py eval_scripts/MCR_extraction.py eval_scripts/UBP_extraction.py eval_scripts/UCS_extraction.py eval_scripts/UEA_extraction.py eval_scripts/RED_scoring.py eval_scripts/SES_scoring.py eval_scripts/SMQ_scoring.py`
- Result:
  - passed with exit code `0`

## 4) Notes for report writing

- This fix batch focused on **execution blockers** (syntax/runtime) only, to maximize DDL-time reliability.
- Reproduction should now proceed in this order:
  1) run task script (`test_misinformation_detection.py`)
  2) run extraction (`eval_scripts/MID_extraction.py`)
  3) run scoring (`eval_scripts/MID_compute_score.py`)

## 5) Dependency installation fix (macOS)

- Issue observed during `pip install -r requirements.txt`:
  - `qwen_agent` editable git dependency points to the SoMe repo root, which is not a Python package root (`setup.py` / `pyproject.toml` missing), causing installation failure.
  - CUDA-specific packages (`nvidia-*` and `+cu128` torch wheels) are not suitable for macOS CPU/MPS environment.

- Actions taken in `requirements.txt`:
  - Removed:
    - `-e git+https://github.com/LivXue/SoMe.git@...#egg=qwen_agent`
    - all `nvidia-*` package lines
    - `torch==2.7.1+cu128`, `torchaudio==2.7.1+cu128`, `torchvision==0.22.1+cu128`
  - Added generic torch stack for cross-platform install:
    - `torch`
    - `torchaudio`
    - `torchvision`

- Rationale:
  - The project already contains local source code under `qwen_agent/`, so editable installation from the repo URL is unnecessary for this reproduction task.
  - Generic torch packages allow pip to resolve platform-compatible wheels on macOS.

## 6) Dependency fix round 2 (triton / cu tags)

- New install error observed:
  - `No matching distribution found for triton==3.3.1`
  - This is expected on macOS because `triton` is Linux/CUDA-oriented for most prebuilt distributions.

- Additional actions taken in `requirements.txt`:
  - Removed `triton==3.3.1`
  - Replaced CUDA-pinned torch entries with a single generic `torch`
  - Removed `torchaudio` and `torchvision` from requirements (not required for MID path; reduces platform/version conflicts)

- Current recommendation:
  - Re-run `pip install -r requirements.txt`
  - If environment has partially installed conflicting torch family packages, run:
    - `pip uninstall -y torch torchaudio torchvision triton`
    - `pip install -r requirements.txt`

## 7) Runtime import fix (`qwen_agent.llm.oai` missing)

- New runtime error observed when launching MID script:
  - `ModuleNotFoundError: No module named 'qwen_agent.llm.oai'`
- Root cause:
  - Local repository contains `qwen_agent/` source, but file `qwen_agent/llm/oai.py` was missing, while `qwen_agent/llm/__init__.py` and `azure.py` import it.
- Action taken:
  - Added `qwen_agent/llm/oai.py` with a minimal OpenAI-compatible adapter:
    - registered as `@register_llm('oai')`
    - implemented `TextChatAtOAI` inheriting `BaseFnCallModel`
    - supports stream/non-stream chat via `openai.OpenAI(...).chat.completions.create(...)`
    - maps responses into `Message(role='assistant', content=...)`
- Validation:
  - `python3 -m py_compile qwen_agent/llm/oai.py qwen_agent/llm/__init__.py qwen_agent/llm/azure.py test_misinformation_detection.py`
  - compilation passed.

## 8) Runtime import fix (`extract_doc_vocabulary` missing)

- New runtime error observed:
  - `ModuleNotFoundError: No module named 'qwen_agent.tools.extract_doc_vocabulary'`
- Root cause:
  - `qwen_agent/tools/__init__.py` imported `extract_doc_vocabulary`, but the file does not exist in the repository.
- Action taken:
  - Removed:
    - `from .extract_doc_vocabulary import ExtractDocVocabulary`
    - `'ExtractDocVocabulary'` in `__all__`
  - This avoids import-time crash while keeping MID-required toolchain unaffected.

## 9) Runtime import fix (`topic_data.npy` required by unrelated tool)

- New runtime error observed in MID launch:
  - `FileNotFoundError: ./database/emb_data/topic_data.npy`
- Root cause:
  - Python imports package `tools` before loading submodule `tools.en`.
  - `tools/__init__.py` imported `data_retrieve`, and `tools/data_retrieve.py` loads `topic_data.npy` at import time.
  - MID task does not need `RetrievePosts`, but import side effects still triggered the missing-file error.
- Action taken:
  - Updated `tools/__init__.py`:
    - wrapped `from .data_retrieve import RetrievePosts` in `try/except`
    - fallback `RetrievePosts = None`
  - This prevents unrelated data dependency from blocking MID execution.

## 10) MID argparse fix (`description` invalid + missing args)

- Error observed:
  - `TypeError: _StoreAction.__init__() got an unexpected keyword argument 'description'`
- Root cause:
  - `argparse.add_argument(...)` incorrectly used `description=` (should be `help=`).
  - Script had been partially edited to env-only mode, leaving `args.model` referenced but not defined.
- Action taken in `test_misinformation_detection.py`:
  - Reintroduced CLI args with env-based defaults:
    - `--model` (default from `LLM_MODEL_NAME`)
    - `--base_url` (default from `OPENAI_BASE_URL`)
    - `--api_key` (default from `OPENAI_API_KEY`)
    - `--output_path`
  - Replaced all `description=` with `help=`.
  - Switched output filename and `vllm_config` to use parsed args (not raw `os.getenv`).
- Validation:
  - `python3 -m py_compile test_misinformation_detection.py` passed.

## 11) Off-peak waiting logic fix (false positive for relay endpoints)

- Symptom:
  - Script repeatedly printed `Waiting for Deepseek off-peak time`, appearing as request timeout.
- Root cause:
  - Waiting logic was triggered by model name containing `deepseek` only.
  - Current endpoint is a relay (`aihubmix`), not official DeepSeek endpoint, so this wait should not apply.
- Action taken in `test_misinformation_detection.py`:
  - Added CLI flag: `--force_offpeak_wait` (default off)
  - Updated auto condition to:
    - enable wait only when model contains `deepseek` **and** `base_url` contains `api.deepseek.com`
    - or explicitly forced by `--force_offpeak_wait`
- Validation:
  - `python3 -m py_compile test_misinformation_detection.py` passed.

## 12) DDL speed-up configuration for MID run

- User request:
  - run only 200 samples
  - switch model to `gpt-4o-mini`
  - reduce retries to 2
  - make `Ctrl+C` stop correctly

- Actions taken:
  - Updated `.env`:
    - `LLM_MODEL_NAME="gpt-4o-mini"`
  - Updated `test_misinformation_detection.py`:
    - default `--model` fallback changed to `gpt-4o-mini`
    - added `--max_samples` (default `200`)
    - added `--max_retries` (default `2`)
    - loop now stops early after processing `max_samples` new items
    - changed retry loop from fixed `range(5)` to `range(args.max_retries)`
    - fixed interrupt behavior:
      - added `except KeyboardInterrupt: raise`
      - changed bare `except:` to `except Exception:`

- Why Ctrl+C previously seemed ineffective:
  - bare `except:` captured `KeyboardInterrupt`, then loop continued, so process did not terminate as expected.

- Validation:
  - `python3 -m py_compile test_misinformation_detection.py` passed.

## 13) Evaluation argparse fix (`description` invalid)

- Error observed while running MID extraction:
  - `TypeError: _StoreAction.__init__() got an unexpected keyword argument 'description'`
- Root cause:
  - In `eval_scripts`, `argparse.add_argument(...)` used `description=` instead of `help=`.
- Action taken:
  - Replaced `description=` with `help=` in:
    - `eval_scripts/MID_extraction.py`
    - `eval_scripts/MCR_extraction.py`
    - `eval_scripts/UBP_extraction.py`
    - `eval_scripts/UCS_extraction.py`
    - `eval_scripts/UEA_extraction.py`
    - `eval_scripts/RED_scoring.py`
    - `eval_scripts/SES_scoring.py`
    - `eval_scripts/SMQ_scoring.py`
- Validation:
  - `python3 -m py_compile` on all above scripts passed.

## 14) MID extraction robustness fix for 502 gateway errors

- Error observed:
  - `openai.InternalServerError: Error code: 502` during `eval_scripts/MID_extraction.py`
- Root cause:
  - Extraction step relied on one-shot API calls; transient provider gateway errors interrupted the whole process.
- Action taken in `eval_scripts/MID_extraction.py`:
  - Added `--api_retry` (default `3`) for extraction API retries.
  - Added rule-based local extraction (`try_rule_extract`) before calling API:
    - direct regex match for labels: `pants-fire`, `false`, `barely-true`, `half-true`, `mostly-true`, `true`
  - Added API failure handling with short backoff (`sleep(2)`), and fallback to `"error"` after retries.
  - Normalized extraction output to lowercase before validation.
- Validation:
  - `python3 -m py_compile eval_scripts/MID_extraction.py` passed.

## 15) MID extraction output not saved (indentation bug)

- Symptom:
  - Extraction command showed progress `200/200`, but `scores/mid_run_01` remained empty.
  - Subsequent `cp scores/mid_run_01/*.json ...` failed with no matching files.
- Root cause:
  - Output write block in `eval_scripts/MID_extraction.py` was indented inside the inner sample loop.
  - Since many samples took the `continue` branches (direct/rule extraction), the write block was skipped.
- Action taken:
  - Moved final `with open(output_file, ...)` save block outside the inner loop, so each model file is always persisted after processing.
- Validation:
  - `python3 -m py_compile eval_scripts/MID_extraction.py` passed.

## 16) Final delivery preparation updates

- Added controlled modification switch for assignment requirement ("one small meaningful modification"):
  - `test_misinformation_detection.py`
    - new argument: `--retrieval_topk`
    - when provided, appends a strict tool-use instruction to the query to constrain `knowledge_retrieve` topk.
- Updated and expanded final execution plan:
  - `FAST_REPRO_PLAN.md`
    - converted into submission-oriented checklist with baseline, modification, optional multi-model rows, and final deliverables.
- Added bilingual report template for direct writing:
  - `REPORT_TEMPLATE_CN_EN.md`
    - includes sections required by FTEC5660 rubric (setup, target, baseline, modification, comparison, debug diary, conclusion).
- Validation:
  - `python3 -m py_compile test_misinformation_detection.py` passed.

## 17) One-click overnight script added

- Added `run_mid_overnight.sh` to support unattended runs:
  - baseline (`mid_baseline_200`)
  - modification (`mid_modified_topk5_200`)
  - optional Gemini / Kimi runs via env switches (`RUN_GEMINI=1`, `RUN_KIMI=1`)
- The script runs full pipeline for each experiment:
  1) inference (`test_misinformation_detection.py`)
  2) extraction (`eval_scripts/MID_extraction.py`)
  3) local score computation (inline python)
  4) per-experiment summary json + global markdown summary (`results/mid_overnight_summary.md`)
- Validation:
  - `bash -n run_mid_overnight.sh` passed.

## 18) Script update: single-model controlled runs + no-overwrite guarantee

- User requirement:
  - Use one model controlled by `.env` (`LLM_MODEL_NAME`)
  - Always run one baseline + one modified (topk ablation)
  - Do not overwrite previous results
- Action taken in `run_mid_overnight.sh`:
  - Removed multi-model optional switches from main flow.
  - Enforced `LLM_MODEL_NAME` as required input model.
  - Added run tag mechanism:
    - `RUN_TAG` defaults to timestamp (`YYYYmmdd_HHMMSS`)
  - Output directories now include model + run tag:
    - `results/mid_<model>_<RUN_TAG>_baseline`
    - `results/mid_<model>_<RUN_TAG>_modified_topk<k>`
    - corresponding `scores/...`
  - Added pre-run path existence checks; script exits if target paths exist.
  - Per-run summary file now versioned:
    - `results/mid_overnight_summary_<RUN_TAG>.md`
- Validation:
  - `bash -n run_mid_overnight.sh` passed.
