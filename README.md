# MAGI+: From Diagnosis to Action in Automated Psychiatric Interviews

> **Research Paper Implementation**  
> Extending MAGI (Bi et al., 2025) with Emotion Tracking, Severity Scoring, Treatment Recommendations, Longitudinal Memory, and Clinical Report Generation.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![arXiv](https://img.shields.io/badge/Original_MAGI-arXiv:2504.18260-red.svg)](https://arxiv.org/abs/2504.18260)

---

## Overview

MAGI+ is an extension of the MAGI multi-agent psychiatric interview system. While MAGI conducts structured psychiatric interviews following the MINI protocol and produces binary diagnoses via PsyCoT reasoning, **MAGI+ adds five novel contributions** that transform it into an end-to-end clinical assessment pipeline:

| Extension | Description |
|-----------|-------------|
| 🎭 **EmotionArc** | Per-turn emotion classification and distress escalation detection |
| 📊 **Severity Scoring** | Automatic PHQ-9, GAD-7, C-SSRS mapping from interview evidence |
| 💊 **Recommendation Agent** | Tiered evidence-based treatment guidance + crisis escalation |
| 🗄️ **Longitudinal Memory** | Multi-session trend tracking (improving/stable/worsening) |
| 📄 **Clinical Report** | Auto-generated structured clinician-ready assessment document |

---

## ⚠️ Important Disclaimer

This system is for **research purposes only**. It is NOT a clinical diagnostic tool and does NOT replace evaluation by a licensed mental health professional. All outputs must be reviewed by a qualified clinician. If you or someone you know is in crisis, call **988** (Suicide & Crisis Lifeline) or go to the nearest emergency room.

---

## Original Paper

This work extends:

> **MAGI: Multi-Agent Guided Interview for Psychiatric Assessment**  
> Bi, G., Chen, Z., et al. (2025). arXiv:2504.18260  
> [https://arxiv.org/abs/2504.18260](https://arxiv.org/abs/2504.18260)

---

## Project Structure

```
MAGI+/
├── run.py                     # Main entry point
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
│
├── src/
│   ├── main.py                # Full pipeline orchestrator
│   ├── agents/
│   │   ├── navigation_agent.py    # MINI tree traversal (original MAGI)
│   │   ├── question_agent.py      # Adaptive question generation (original MAGI)
│   │   ├── judgment_agent.py      # Response validation (original MAGI)
│   │   ├── diagnosis_agent.py     # PsyCoT diagnosis (original MAGI)
│   │   └── recommendation_agent.py # Treatment recommendations (MAGI+)
│   ├── extensions/
│   │   ├── emotion_tracker.py     # EmotionArc (MAGI+)
│   │   ├── severity_scorer.py     # PHQ-9/GAD-7/C-SSRS (MAGI+)
│   │   ├── longitudinal_memory.py # Session tracking (MAGI+)
│   │   └── report_generator.py    # Clinical report (MAGI+)
│   └── utils/
│       ├── data_models.py         # Pydantic data models
│       ├── mini_tree.py           # MINI interview decision tree
│       └── llm_client.py          # LLM API wrapper (OpenAI/Groq/DeepSeek)
│
├── data/
│   └── simulated_cases/       # 10 test cases for evaluation
│
├── experiments/
│   ├── reports/               # Generated clinical reports
│   ├── results/               # Experiment results CSV
│   └── run_experiments.py     # Automated evaluation script
│
├── paper/
│   └── our_paper/
│       └── MAGI_Plus_Draft_v1.md  # Research paper draft
│
└── notes/                     # Design docs, checklists, summaries
```

---

## Quick Start

### 1. Clone and set up environment

```bash
git clone https://github.com/YOUR_USERNAME/magi-plus.git
cd magi-plus
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure your API key

Copy `.env.example` to `.env` and add your API key:

```bash
cp .env.example .env
```

Edit `.env`:
```
# Groq (free tier available at console.groq.com)
OPENAI_API_KEY=gsk_your_groq_key_here
DEFAULT_MODEL=qwen/qwen3.8-27b
```

Supported providers (auto-detected from key prefix):
- **Groq** (`gsk_...`) — recommended, fast and free
- **OpenAI** (`sk-...`) — `gpt-4o`, `gpt-4o-mini`
- **DeepSeek** (`sk-` + 35 chars) — `deepseek-chat`
- **NVIDIA NIM** (`nvapi-...`) — various models

### 3. Run a simulated interview

```bash
# Run with built-in demo case (moderate depression)
python run.py --mode simulated

# Run with a specific test case
python run.py --mode simulated --participant P001 --case data/simulated_cases/case_depression_moderate.json

# Run interactive (human input)
python run.py --mode interactive --participant P001
```

### 4. Run all experiments

```bash
python experiments/run_experiments.py
```

Results saved to `experiments/results/` as CSV.  
Clinical reports saved to `experiments/reports/` as Markdown.

---

## Supported Disorders (MINI Sections)

| Section | Disorder | DSM-5 Code |
|---------|----------|-----------|
| A | Major Depressive Episode | F32.x |
| N | Generalized Anxiety Disorder | F41.1 |
| F | Social Anxiety Disorder | F40.10 |
| B | Suicidality | Z91.5x |

*(Extendable to all 17 MINI modules)*

---

## Output Example

Each session produces a full clinical report including:

- Diagnostic results with confidence scores
- PHQ-9 / GAD-7 / C-SSRS severity scores
- EmotionArc timeline (per-turn emotional state)
- Tiered treatment recommendations
- PsyCoT reasoning traces
- Longitudinal comparison (for returning participants)

See `experiments/reports/` for example outputs.

---

## Experimental Results (10 Simulated Cases)

| Metric | Value |
|--------|-------|
| Overall diagnostic accuracy | 90% (36/40 predictions) |
| Full-case accuracy | 90% (9/10 cases) |
| Crisis detection recall | 100% (1/1) |
| True negative specificity | 100% (8/8) |
| Avg. session latency | ~400ms/call (Groq) |

---

## Citation

If you use MAGI+ in your research, please cite both the original MAGI paper and this work:

```bibtex
@article{bi2025magi,
  title={MAGI: Multi-Agent Guided Interview for Psychiatric Assessment},
  author={Bi, Guanqun and Chen, Zhuang and others},
  journal={arXiv preprint arXiv:2504.18260},
  year={2025}
}
```

---

## License

MIT License — see [LICENSE](LICENSE) file.

This project is for research purposes only. Clinical use requires regulatory approval and professional oversight.
