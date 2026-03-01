# SoMe MID 复现说明（中文）

本仓库基于 SoMe 原仓库进行课程复现实验改造：
- 原始仓库：`https://github.com/LivXue/SoMe`
- 本人复现仓库：`https://github.com/<your-username>/SoMe`

作业报告见：
- `REPORT_CN.md`
- `REPORT_EN.md`

## 1）复现范围

本项目聚焦 SoMe 的一个子实验：
- 任务：`MID`（虚假信息检测）
- 指标：`ACC`（先 extraction，再 compute score）
- 受控改动：`--retrieval_topk`

## 2）环境安装

### 前置条件
- Python 3.12
- 可用的 OpenAI 兼容 API

### 安装命令

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3）配置 `.env`

在仓库根目录创建 `.env`：

```env
OPENAI_API_KEY="YOUR_API_KEY"
OPENAI_BASE_URL="https://your-openai-compatible-endpoint/v1"
LLM_PROVIDER="openai"
LLM_MODEL_NAME="gpt-4o-mini"
LLM_TEMPERATURE=0
```

## 4）数据准备

确保 MID 相关文件存在：
- `datasets/misinformation_detection/ground_truth.json`
- `database/knowledge_data/knowledge_base.json`
- `database/emb_data/knowledge_base.npy`

### 方案 A：仅下载 MID 必需子集（推荐）

```bash
python3 - <<'PY'
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="LivXue/SoMe",
    repo_type="dataset",
    local_dir=".",
    local_dir_use_symlinks=False,
    resume_download=True,
    allow_patterns=[
        "datasets/misinformation_detection/*",
        "database/knowledge_data/*",
        "database/emb_data/knowledge_base.npy",
    ],
)
print("MID required data downloaded.")
PY
```

如果你所在地区网络较慢，可先设置镜像：

```bash
export HF_ENDPOINT="https://hf-mirror.com"
```

然后再次运行上述下载命令。

### 方案 B：下载完整数据包（官方链接）

- Hugging Face：`https://huggingface.co/datasets/LivXue/SoMe`
- Google Drive：`https://drive.google.com/file/d/1sD2EaZStK5nODQWlJTHZ8WfFb5QHgwMN/view?usp=drive_link`
- 百度网盘：`https://pan.baidu.com/s/1DugTyLR5AaQHeOdXG6wqQQ?pwd=SoMe`（提取码：`SoMe`）

下载后请将文件解压到项目根目录，使脚本路径与文档保持一致。

## 5）运行实验

### A. Baseline（200样本）

```bash
set -a && source .env && set +a && python3 test_misinformation_detection.py \
  --output_path "results/mid_run_01" \
  --max_samples 200 \
  --max_retries 2
```

### B. Modified（topk=5，200样本）

```bash
set -a && source .env && set +a && python3 test_misinformation_detection.py \
  --output_path "results/mid_run_mod_topk5" \
  --max_samples 200 \
  --max_retries 2 \
  --retrieval_topk 5
```

### C. 一键整夜运行

按 `.env` 的 `LLM_MODEL_NAME` 自动跑 baseline + modified：

```bash
bash run_mid_overnight.sh
```

脚本按模型名和时间戳分目录输出，默认不覆盖历史结果。

## 6）评估流程

### Baseline 评估

```bash
python3 eval_scripts/MID_extraction.py \
  --result_path "results/mid_run_01" \
  --output_path "scores/mid_run_01" \
  --setting_path "eval_scripts/settings.json" \
  --api_retry 5

mkdir -p scores/misinformation_detection
cp scores/mid_run_01/*.json scores/misinformation_detection/
python3 eval_scripts/MID_compute_score.py
```

### Modified 评估

```bash
python3 eval_scripts/MID_extraction.py \
  --result_path "results/mid_run_mod_topk5" \
  --output_path "scores/mid_run_mod_topk5" \
  --setting_path "eval_scripts/settings.json" \
  --api_retry 5

cp scores/mid_run_mod_topk5/*.json scores/misinformation_detection/
python3 eval_scripts/MID_compute_score.py
```

## 7）已复现结果（200样本）

| 设置 | 模型 | ACC |
|---|---|---:|
| Baseline | gpt-4o-mini | 52.0 |
| Modified (topk=5) | gpt-4o-mini | 52.5 |
| Baseline | gemini-2.5-flash | 55.5 |
| Modified (topk=5) | gemini-2.5-flash | 51.5 |
| Baseline | kimi-k2-instruct | 55.0 |
| Modified (topk=5) | kimi-k2-instruct | 54.0 |

## 8）说明

- 排障过程详见：`REPRO_LOG.md`
- 请勿提交 `.env` 与任何密钥
- 本仓库以 MID 子任务复现为主，不覆盖 SoMe 全任务全量复现
