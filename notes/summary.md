# MAGI: Multi-Agent Guided Interview for Psychiatric Assessment
## Paper Summary & Analysis

**Original Paper:** MAGI: Multi-Agent Guided Interview for Psychiatric Assessment  
**Authors:** Guanqun Bi, Zhuang Chen, Zhoufu Liu, Hongkai Wang, Xiyao Xiao, Yuqiang Xie, Wen Zhang, Yongkang Huang, Yuxuan Chen, Libiao Peng, Yi Feng, Minlie Huang  
**Institution:** Tsinghua University (CoAI Group), Beijing Institute of Technology, Sichuan University, Lingxin AI  
**ArXiv:** https://arxiv.org/abs/2504.18260  
**Published:** April 25, 2025  

---

## 1. Problem Statement

Mental health disorders are a global crisis. Structured clinical interviews — especially the MINI (Mini International Neuropsychiatric Interview) — are the gold standard for psychiatric diagnosis. However:

- Manual administration is **time-consuming and resource-intensive**
- There is a severe shortage of mental health professionals worldwide
- Existing LLM-based tools have **3 critical failures**:
  1. **Diagnostic framework deviation** — they diverge from DSM-5 standards
  2. **Rigid interaction patterns** — inflexible questioning that fails distressed users
  3. **Limited diagnosis transparency** — black-box reasoning that clinicians can't trust

---

## 2. The MINI Protocol

The Mini International Neuropsychiatric Interview (MINI) is:
- Aligned with **DSM-5** diagnostic criteria
- A **decision-tree** based interview (branching logic)
- Completable in **15–30 minutes**
- Validated across diverse populations
- The **gold standard** for psychiatric evaluation

Disorders covered in the original MAGI paper:
- Depression (Major Depressive Episode)
- Generalized Anxiety Disorder (GAD)
- Social Anxiety Disorder
- Suicide Risk Assessment

---

## 3. MAGI's Architecture — 4 Specialized Agents

### Agent 1: Navigation Agent
- Governs **interview progression**
- Enforces MINI's strict branching/decision-tree logic
- Routes conversation based on responses (e.g., suicidal ideation → deeper risk assessment)
- Prevents skipping critical diagnostic nodes
- Coordinates with all other agents

### Agent 2: Question Agent
- Generates **adaptive, contextual questions**
- Three strategies:
  - **Structure-driven probing** ("How long has this lasted?")
  - **Explaining** (clarifying clinical concepts for the participant)
  - **Empathetic support** (detects distress cues, responds compassionately)
- Rephrases clinical constructs into conversational language
- Example: For anhedonia, adapts based on context — hobbies vs. social habits

### Agent 3: Judgment Agent
- **Validates responses** against MINI criteria in real-time
- Three decision thresholds:
  1. Direct matching of operationalized definitions
  2. Semantic comprehension of clinically equivalent expressions
  3. Ambiguity resolution (after 5 unproductive turns, uses forced-choice)
- Triggers clarification requests when criteria aren't met
- Authorizes state transitions to navigation agent

### Agent 4: Diagnosis Agent
- Implements **PsyCoT (Psychometric Chain-of-Thought)**
- Three reasoning phases:
  1. **Symptom Anchoring** — validates each DSM-5 criterion step by step
  2. **Diagnostic Synthesis** — confirms symptom profile meets threshold
  3. **Evidence Binding** — creates transparent audit trails linking dialogue → diagnosis

---

## 4. Key Innovation: PsyCoT (Psychometric Chain-of-Thought)

PsyCoT is MAGI's core novel contribution. It differs from standard CoT reasoning by:
- Being **DSM-5 aligned** (structured around clinical criteria, not free-form)
- Explicitly mapping **symptoms → diagnostic criteria → conclusion**
- Creating **auditable decision paths** clinicians can review
- Handling temporal verification (e.g., "≥2 weeks" for depression)
- Applying exclusionary condition checks

---

## 5. Dataset & Experiments

- **1,002 real-world participants** from university mental health services
- Simulated participants constructed using LLMs to satisfy ethical constraints
- **Dual-expert annotation** by licensed psychologists (APA-accredited, 10-15 years experience)
- Inter-rater reliability: ICC = 0.78 → 0.87 after calibration, Cohen's κ > 0.85

**LLMs Tested:** GPT-4o, Claude-3.5-Sonnet, GLM-Zero, DeepSeek-R1

**Three configurations per LLM:**
1. Vanilla (end-to-end from transcripts)
2. CoT (free-form reasoning)
3. PsyCoT (MAGI's structured reasoning)

---

## 6. Key Results

### Diagnostic Performance (PsyCoT superiority)
| Disorder | Metric | Vanilla | CoT | PsyCoT |
|----------|--------|---------|-----|--------|
| Suicide Risk | κ | 0.259–0.427 | — | **0.839–0.942** |
| Depression | F1 | 0.679 | — | **0.850** (few-shot) |
| Social Anxiety | F1 | improved +26.3% with few-shot | — | **best** |
| GAD | F1 (zero-shot) | — | — | **0.946** |

### Dialogue Quality (MAGI vs baselines)
- Superior in **Relevance, Completeness, and Guidance**
- Slightly trails Knowledge baseline in Accuracy (acceptable trade-off for adaptability)

---

## 7. Limitations of the Original Paper (Extension Opportunities)

1. **No emotion/affect tracking** — the system detects distress cues but doesn't formally model or score emotional state over time
2. **Text-only input** — no voice, facial expression, or multimodal signals
3. **Limited disorders** — only 4 disorders (depression, GAD, social anxiety, suicide risk); MINI covers 17+
4. **No longitudinal tracking** — single-session assessment, no progress monitoring over time
5. **No treatment recommendation** — diagnoses but doesn't suggest next steps
6. **No personalization** — same approach for all participants regardless of background
7. **No crisis escalation protocol** — when severe risk is detected, no automated escalation
8. **English only** — no multilingual support
9. **No clinician dashboard** — results are not formatted for clinical workflow integration

---

## 8. Questions Answered by the Paper

| Question | Answer |
|----------|--------|
| What problem does it solve? | Automating structured psychiatric interviews (MINI) using LLMs |
| What dataset does it use? | 1,002 university student interviews, expert-annotated |
| What model does it propose? | 4-agent collaborative system + PsyCoT reasoning |
| How is performance evaluated? | Macro-F1, Accuracy, Cohen's κ vs. expert annotations |
