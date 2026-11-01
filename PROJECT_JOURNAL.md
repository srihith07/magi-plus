# PROJECT JOURNAL
## MAGI+ — Plain English Guide to Everything

> This is your go-to document. It explains everything happening in this project
> in simple, clear language. Updated every session. Read this first whenever
> you want to catch up on where we are.

---

## 📌 THE BIG PICTURE (Read This First)

### What are we building?
We are building an **AI system that can conduct psychiatric interviews** — like
the kind a psychologist would do — and then go further by:
- Tracking how the person's emotions change during the conversation
- Scoring how severe their condition is (mild / moderate / severe)
- Recommending appropriate next steps (therapy, self-help, or emergency help)
- Remembering past sessions and tracking progress over time
- Generating a professional clinical report at the end

### Why are we building this?
There is a massive global shortage of mental health professionals. Most people
who need psychiatric evaluation never get it — either because it's too expensive,
too far away, or there aren't enough doctors. An AI system that can conduct
these interviews accessibly could help millions of people.

### Are we inventing this from scratch?
No. We are building on top of a research paper called **MAGI** (published in
April 2025 by researchers at Tsinghua University). They built the foundation —
an AI that conducts structured psychiatric interviews. We are extending their
work with 5 new features they didn't build, and then publishing our extended
version as a new research paper.

### Will this replace psychiatrists?
No. This is a **screening and support tool**, not a replacement. Every output
will carry a disclaimer that a licensed clinician must review it. Think of it
like a smart intake form that helps clinicians by doing the time-consuming
initial assessment work.

---

## 📚 THE ORIGINAL PAPER: MAGI

### What is MAGI?
MAGI stands for **Multi-Agent Guided Interview**. It was created by researchers
at Tsinghua University (China) in 2025. The core idea: use 4 AI agents working
together to conduct a psychiatric interview following the MINI protocol.

### What is the MINI protocol?
The **Mini International Neuropsychiatric Interview (MINI)** is a standardized
clinical interview used by psychiatrists worldwide. It follows a decision-tree
structure — the questions asked depend on how you answer previous questions.
It covers conditions like depression, anxiety, and suicide risk. It's aligned
with **DSM-5** (the official psychiatric diagnostic manual).

### MAGI's 4 agents:
1. **Navigation Agent** — Controls which question comes next (follows the MINI
   decision tree). Ensures no critical questions are skipped.
2. **Question Agent** — Actually asks the questions. It adapts — sometimes
   probing for more detail, sometimes explaining confusing terms, sometimes
   being empathetic when the person seems upset.
3. **Judgment Agent** — Evaluates the person's answer. Did it meet the criteria
   for that diagnostic node? Yes / No / Unclear?
4. **Diagnosis Agent** — At the end, puts all the collected evidence together
   and produces a diagnosis using a special reasoning process called **PsyCoT**.

### What is PsyCoT?
**Psychometric Chain-of-Thought** — instead of the AI just saying "you have
depression," it shows its reasoning step by step: which symptoms were confirmed,
how long they lasted, whether exclusion criteria were ruled out. This makes the
diagnosis transparent and trustworthy for clinicians.

### How well did MAGI perform?
Very well. On 1,002 real-world participants:
- Suicide risk detection: Cohen's κ of 0.839–0.942 (clinical-grade agreement)
- Depression F1 score: 0.850
- Generalized Anxiety F1 score: 0.946
- These results are on par with trained clinicians

### What MAGI doesn't do (our opportunity):
1. Doesn't track emotions during the interview
2. Doesn't give severity scores (mild/moderate/severe)
3. Doesn't recommend treatment after diagnosis
4. Doesn't remember previous sessions
5. Doesn't produce a formatted clinical report

---

## 🆕 OUR 5 EXTENSIONS (What We're Adding)

### Extension 1: EmotionArc 📊
**What it does:** After every message the participant sends, we classify their
emotional state (neutral, anxious, sad, distressed, hopeful, avoidant). We
build a timeline of these emotions across the entire interview.

**Why it matters:** A sudden spike in distress when asked about a specific topic
is clinically meaningful. Seeing the emotional journey helps clinicians understand
the person beyond just the Yes/No diagnostic answers.

**Example output:** "Participant showed neutral emotions for the first 10
exchanges, then escalated to distressed during the suicide risk section, and
returned to anxious by the end."

---

### Extension 2: Severity Scoring 📋
**What it does:** Maps the symptoms collected during the interview to standardized
clinical severity scales:
- **PHQ-9** for depression (score 0–27, categorized as minimal/mild/moderate/severe)
- **GAD-7** for anxiety (score 0–21)
- **C-SSRS** for suicide risk (Columbia Suicide Severity Rating Scale)
- **LSAS-SR** for social anxiety

**Why it matters:** A binary "yes, you have depression" is not enough for
treatment planning. Knowing the severity determines whether someone needs
self-help resources, weekly therapy, or immediate hospitalization.

---

### Extension 3: Recommendation Agent 💊
**What it does:** A brand new 5th agent that takes the diagnosis and severity
as input and recommends appropriate next steps:
- **Mild:** Self-help apps, psychoeducation, mindfulness exercises
- **Moderate:** Outpatient CBT or DBT therapy, online counseling
- **Moderate-Severe:** Psychiatric consultation, possible medication evaluation
- **Severe/Crisis:** Immediate crisis intervention, hotline numbers, emergency referral

**Why it matters:** Closing the loop from "what's wrong" to "what to do" is
what makes this system actually useful for people. This is the most directly
impactful extension.

**Crisis escalation:** If severe suicide risk is detected, the system
automatically flags this for immediate attention.

---

### Extension 4: Longitudinal Memory 🗄️
**What it does:** Stores each session and compares it to previous sessions for
the same person. Tracks whether conditions are improving, stable, or worsening
over time.

**Why it matters:** Mental health care is ongoing. A single assessment is a
snapshot. Trend data over multiple sessions is what tells you if the treatment
is working.

**Example output:** "Session 3 compared to Session 1: PHQ-9 score decreased
from 18 to 11 (moderate improvement). New social anxiety symptoms emerged."

---

### Extension 5: Clinical Report Generator 📄
**What it does:** At the end of every session, automatically generates a
professional clinical report containing:
- Session date, duration, disorders screened
- Diagnosis results with PsyCoT reasoning trace
- Emotion arc timeline
- Severity scores
- Recommended next steps
- Longitudinal comparison (if not first session)
- AI disclaimer

**Why it matters:** Makes the output directly usable by clinicians. Instead of
raw AI output, they get a structured document they can attach to a patient record.

---

## 🗂️ PROJECT STRUCTURE (What Each File Does)

```
AI Research paper/
│
├── PROJECT_JOURNAL.md     ← YOU ARE HERE. Read this to understand everything.
├── CHANGELOG.md           ← Full history of every change made to the project
├── README.md              ← Technical overview (for developers/GitHub)
├── requirements.txt       ← List of Python libraries needed
│
├── paper/
│   └── original/          ← Put the MAGI paper PDF here (download from arXiv)
│
├── notes/
│   ├── summary.md         ← Deep technical analysis of the original MAGI paper
│   ├── implementation_checklist.md  ← 43 tasks, ordered easiest to hardest
│   ├── extensions_design.md         ← Technical design of our 5 extensions
│   └── paper_outline.md             ← Outline of the paper we will write
│
├── src/
│   ├── utils/
│   │   ├── data_models.py  ← Defines the data structures (what a "session" looks like)
│   │   ├── mini_tree.py    ← The MINI interview tree (the decision logic)
│   │   └── llm_client.py   ← Handles communication with the AI (GPT-4o etc.)
│   │
│   ├── agents/
│   │   ├── navigation_agent.py    ← Controls interview flow (ORIGINAL)
│   │   ├── question_agent.py      ← Asks adaptive questions (ORIGINAL)
│   │   ├── judgment_agent.py      ← Validates responses (ORIGINAL)
│   │   ├── diagnosis_agent.py     ← PsyCoT diagnosis (ORIGINAL)
│   │   └── recommendation_agent.py ← Treatment recommendations (OUR EXTENSION)
│   │
│   └── extensions/
│       ├── emotion_tracker.py      ← EmotionArc module (OUR EXTENSION)
│       ├── severity_scorer.py      ← PHQ-9/GAD-7/C-SSRS scoring (OUR EXTENSION)
│       ├── longitudinal_memory.py  ← Session memory & trends (OUR EXTENSION)
│       └── report_generator.py     ← Clinical report output (OUR EXTENSION)
│
├── data/
│   ├── mini_protocol/
│   │   └── mini_tree.json          ← The MINI interview questions & logic
│   ├── simulated_cases/            ← Test cases for evaluating the system
│   └── knowledge_base/
│       └── treatment_recommendations.json  ← What to recommend for each diagnosis
│
└── experiments/
    ├── baseline_results/   ← Results reproducing original MAGI
    └── extension_results/  ← Results with our extensions added
```

---

## 📅 SESSION LOG (What We Did Each Session)

### Session 1 — 2026-10-20
**Status: Phase 1 & 2 Core Complete ✅**

What happened:
1. Decided to build on the MAGI paper (AI + Psychiatry / Psychology)
2. Analyzed the full MAGI paper in detail
3. Identified 5 gaps in MAGI that we will fill with our extensions
4. Scaffolded the entire project folder structure
5. Created all planning documents (summary, checklist, design doc, paper outline)
6. Built `data_models.py` — all data structures (Sessions, Turns, Diagnoses,
   Emotions, Severity Scores, Recommendations)
7. Built `mini_tree.py` — the MINI decision tree (34 nodes, 4 disorders)
8. Built `llm_client.py` — clean LLM API wrapper with retry and token tracking
9. Built `navigation_agent.py` — Agent 1: interview flow control
10. Built `question_agent.py` — Agent 2: adaptive question generation
11. Built `judgment_agent.py` — Agent 3: response validation
12. Built `diagnosis_agent.py` — Agent 4: PsyCoT diagnosis reasoning
13. Built `emotion_tracker.py` — Extension 1: per-turn emotion timeline
14. Built `severity_scorer.py` — Extension 2: PHQ-9/GAD-7/C-SSRS scoring

### Session 2 — 2026-10-31
**Status: First Successful End-to-End Run ✅**

What happened:
1. Installed all dependencies (tinydb, openai 1.109.1)
2. Discovered API key is NVIDIA NIM (nvapi-...), not OpenAI
3. Updated LLM client to auto-detect NIM and use correct base URL
4. Found 2 working models: Nemotron (conversation) + Mistral-large (JSON)
5. Fixed simulated case loading bug (responses sub-key)
6. Solved reasoning model JSON leak — switched diagnosis to rule-based
7. Added rule-based judgment + emotion detection (fast, no LLM needed)
8. Ran full pipeline successfully: Depression case correctly diagnosed
9. Generated first complete clinical report with all 5 extension sections

**First test result (case_depression_moderate):**
- Depression: ✅ POSITIVE (85% confidence, 8/5 symptoms)
- PHQ-9: 21/27 Severe
- Recommendation: Urgent Psychiatric Care (24-48h)
- EmotionArc: sad/distressed detected
- Full clinical report generated

**Currently working on: Phase 5 — Paper Writing**

---

## 🔬 CURRENT STATUS

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Setup & Foundation | ✅ Complete |
| Phase 2 | Core MAGI Reproduction (4 agents) | ✅ Complete |
| Phase 3 | Our 5 Extensions | ✅ Complete |
| Phase 4 | Evaluation & Experiments | ✅ Complete (10 cases) |
| Phase 5 | Paper Writing | ✅ Complete |
| Phase 6 | GitHub + Submission | ✅ GitHub live · JMIR submitted (JMH ms#115892) |

---

## ❓ FREQUENTLY ASKED QUESTIONS

**Q: Do I need a GPU for this?**
A: No. We are using LLM APIs (GPT-4o / DeepSeek) rather than training models
from scratch. A regular laptop with internet access is sufficient.

**Q: How long will this take?**
A: Roughly 8–9 weeks for a full implementation and paper draft.

**Q: Where does the training data come from?**
A: Following the original MAGI paper, we use LLM-simulated patient cases. We
construct synthetic participants with specific conditions and use them for testing.

**Q: Is this ethical?**
A: Yes, with care. We use simulated data (not real patient data). Our system
includes explicit disclaimers that it is not a replacement for clinical care.
We follow the ethical framework of the original paper.

**Q: Where will we publish this?**
A: Target venues: ACL, EMNLP (top NLP conferences), AAAI, or
Nature Digital Medicine / JMIR (medical AI journals).
