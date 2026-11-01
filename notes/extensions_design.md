# Our Unique Extensions to MAGI
## Design Document

This document outlines the novel contributions we are adding on top of the
original MAGI framework. These extensions form the basis of our research paper.

---

## Extension 1: Real-Time Emotion Tracking (EmotionArc)

### Problem it solves
The original MAGI detects distress cues lexically but does not formally model or
track emotional state across the session. There is no structured output of how
the participant's emotional state evolved during the interview.

### Our Approach
- After each participant turn, run a lightweight emotion classifier
- Track emotions across: neutral / anxious / sad / distressed / hopeful / avoidant
- Build an "EmotionArc" — a timeline of emotional states per session
- Feed EmotionArc into the Question Agent to dynamically adjust empathy level

### Clinical Value
- Clinicians can see emotional patterns, not just diagnostic outcomes
- A sudden spike in distress at a specific node is clinically significant
- Helps differentiate chronic emotional states from situational reactions

### Novel Contribution
No existing psychiatric interview AI system produces a per-turn emotional
timeline integrated with diagnostic output.

---

## Extension 2: Standardized Severity Scoring

### Problem it solves
MAGI produces a binary Yes/No diagnosis. Clinical practice requires severity
grading (mild/moderate/severe) which determines treatment intensity.

### Our Approach
Map collected symptoms to validated clinical scales:
- **PHQ-9** (Patient Health Questionnaire-9) for Depression
- **GAD-7** (Generalized Anxiety Disorder 7-item) for Anxiety
- **C-SSRS** (Columbia Suicide Severity Rating Scale) for Suicide Risk
- **LSAS-SR** (Liebowitz Social Anxiety Scale Self-Report) for Social Anxiety

### Clinical Value
- Severity scores are required for treatment planning
- Makes the system's output directly usable in clinical settings
- Provides a quantitative baseline for longitudinal comparison

### Novel Contribution
First MAGI-style system to automatically produce clinically validated severity
scores as part of the diagnostic output.

---

## Extension 3: Evidence-Based Treatment Recommendation Agent

### Problem it solves
MAGI stops at diagnosis. In real clinical practice, diagnosis is always followed
by a treatment plan. Patients need to know "what now?"

### Our Approach
A new 5th agent: the **Recommendation Agent**
- Takes: diagnosis + severity score + emotional arc as input
- Outputs: tiered, evidence-based recommendations
- Recommendation tiers:
  1. **Self-help** (apps, psychoeducation, exercises) — mild cases
  2. **Outpatient therapy** (CBT, DBT, mindfulness) — moderate cases
  3. **Psychiatric consultation** (medication evaluation) — moderate-severe
  4. **Crisis intervention** (immediate referral, hotline) — severe suicide risk
- Knowledge base sourced from APA, WHO, and NICE guidelines

### Clinical Value
- Closes the loop from assessment to action
- Especially valuable in low-resource settings with limited clinician access
- Crisis escalation could literally save lives

### Novel Contribution
The first end-to-end psychiatric AI system covering assessment → diagnosis →
severity → treatment recommendation in a single pipeline.

---

## Extension 4: Longitudinal Session Memory

### Problem it solves
Mental health assessment is not a one-time event. Progress monitoring over time
is essential for treatment effectiveness evaluation.

### Our Approach
- Store each session with timestamp, diagnosis, severity scores, emotion arc
- On subsequent sessions, load prior session history
- Generate a **Longitudinal Report** comparing:
  - Symptom changes between sessions
  - Severity score trends (improving / stable / worsening)
  - New disorders emerging or resolving
- Adjust interview focus based on prior session (don't re-ask fully settled nodes)

### Clinical Value
- Enables outcome monitoring — critical for insurance, research, and care quality
- Allows early detection of deterioration (severity worsening between sessions)
- Reduces interview burden on returning participants

### Novel Contribution
First psychiatric interview AI system with multi-session memory and longitudinal
trend analysis.

---

## Extension 5: Structured Clinical Report Generation

### Problem it solves
MAGI's output (PsyCoT traces) is not formatted for clinical workflow. Clinicians
need a structured document they can attach to a patient record.

### Our Approach
Auto-generate a **Clinical Assessment Report** containing:
- Patient pseudonym / session ID
- Date and duration of interview
- Disorders screened and results (Yes/No + severity)
- PsyCoT reasoning trace (evidence summary)
- Emotion Arc visualization (text-based timeline)
- Standardized severity scores (PHQ-9, GAD-7, C-SSRS)
- Recommended next steps
- Clinician notes field (editable)
- Disclaimer (AI-assisted, requires clinical review)

### Output formats
- Markdown (for digital records)
- PDF (for printing / formal documentation)

### Novel Contribution
First AI psychiatric interview system producing a clinician-ready structured
report as standard output.

---

## Summary: Our 5 Extensions vs Original MAGI

| Feature | Original MAGI | Our Extension |
|---------|--------------|---------------|
| Interview agents | 4 agents | 4 + Recommendation Agent (5th) |
| Emotion tracking | Lexical distress detection | Per-turn EmotionArc timeline |
| Diagnosis output | Binary Yes/No | Binary + Severity score (PHQ-9/GAD-7/C-SSRS) |
| Post-diagnosis | None | Evidence-based treatment recommendations |
| Session memory | Single session | Multi-session longitudinal tracking |
| Output format | PsyCoT trace | Full structured clinical report |
| Crisis handling | Not specified | Automated crisis escalation tier |

---

## Proposed Paper Title

**"MAGI+: Extending Multi-Agent Psychiatric Assessment with Emotion Tracking,
Severity Scoring, and Treatment Recommendation for End-to-End Mental Health Support"**

or

**"From Diagnosis to Action: Enhancing Automated Psychiatric Interviews with
Affective Monitoring, Severity Grading, and Evidence-Based Recommendations"**
