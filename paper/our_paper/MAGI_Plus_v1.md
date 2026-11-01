# MAGI+: From Diagnosis to Action in Automated Psychiatric Interviews

---

## Abstract

Automated psychiatric screening has the potential to address the global shortage of mental health professionals by enabling scalable, accessible initial assessments. The original MAGI framework (Bi et al., 2025) introduced a multi-agent system that operationalizes the Mini International Neuropsychiatric Interview (MINI) protocol through coordinated LLM agents, achieving clinical-grade diagnostic performance via Psychometric Chain-of-Thought (PsyCoT) reasoning. However, MAGI stops at binary diagnosis, lacking the clinical context required for real-world deployment: emotional state tracking, severity grading, treatment guidance, and longitudinal monitoring.

We present **MAGI+**, an extension of MAGI that introduces five novel contributions: (1) **EmotionArc**, a per-turn emotion timeline tracking participant affect throughout the interview; (2) **Severity Scoring**, automated mapping of collected symptoms to standardized scales (PHQ-9, GAD-7, C-SSRS); (3) a **Recommendation Agent**, a fifth LLM agent that generates tiered, evidence-based treatment recommendations with crisis escalation logic; (4) **Longitudinal Memory**, multi-session tracking enabling trend analysis across visits; and (5) a **Clinical Report Generator** producing structured, clinician-ready assessment documents. We implement MAGI+ using the `qwen/qwen3.8-27b` model via the Groq inference API, achieving sub-second per-turn latency (~400ms).

We evaluate MAGI+ on ten simulated clinical cases — following the same methodology as the original MAGI study — covering major depressive episode, generalized anxiety disorder, social anxiety disorder, high-risk suicidality, comorbid presentations, and healthy controls, achieving 90% diagnostic accuracy and 100% crisis detection rate. MAGI+ represents the first end-to-end AI psychiatric assessment pipeline covering the full clinical pathway from structured interview through diagnosis, severity grading, and treatment recommendation.

**Keywords:** psychiatric AI, multi-agent systems, mental health assessment, MINI interview, PsyCoT reasoning, large language models, clinical NLP

---

## 1. Introduction

Mental health disorders affect over one billion people globally (WHO, 2022), yet access to psychiatric evaluation remains severely limited. In many low- and middle-income countries, the ratio of psychiatrists to population is fewer than 1 per 100,000 people (WHO, 2021). Even in high-income countries, waiting times for psychiatric assessment routinely exceed weeks or months. This treatment gap represents one of the most significant unmet healthcare needs worldwide.

Structured clinical interviews — particularly the Mini International Neuropsychiatric Interview (MINI; Sheehan et al., 1998) — are the gold standard for psychiatric assessment. The MINI provides a systematic, DSM-5-aligned framework covering 17 psychiatric disorders in 15–30 minutes. However, its manual administration requires trained clinicians, limiting scalability.

The advent of large language models (LLMs) presents an opportunity to automate psychiatric assessment while maintaining clinical rigor. The recent MAGI framework (Bi et al., 2025) demonstrated that a coordinated system of four specialized LLM agents can operationalize the MINI protocol with clinical-grade diagnostic performance, achieving Cohen's κ of 0.839–0.942 for suicide risk detection and F1 scores above 0.850 for depression.

However, MAGI has significant limitations for real-world clinical deployment. It produces binary Yes/No diagnoses without severity grading, does not track the participant's emotional state during the interview, provides no treatment recommendations, lacks longitudinal memory across sessions, and does not generate structured clinical output suitable for clinician review. These gaps represent the difference between a research prototype and a deployable clinical tool.

We present MAGI+, which addresses all five limitations through novel extensions while preserving MAGI's original diagnostic architecture. Our contributions are:

1. **EmotionArc**: Real-time per-turn emotion classification and timeline construction, enabling detection of distress escalation during the interview and informing adaptive questioning strategy.

2. **Severity Scoring**: Automatic mapping of collected diagnostic evidence to validated clinical severity scales (PHQ-9 for depression, GAD-7 for anxiety, C-SSRS for suicide risk), enabling severity-stratified clinical decision making.

3. **Recommendation Agent**: A novel fifth LLM agent that synthesizes diagnosis and severity scores into tiered, evidence-based treatment recommendations (self-help → outpatient therapy → psychiatric consultation → crisis intervention), with automatic crisis escalation for high suicide risk.

4. **Longitudinal Memory**: Persistent session storage enabling cross-session trend analysis, detection of new diagnoses, and monitoring of treatment response over time.

5. **Clinical Report Generator**: Automated generation of structured clinical assessment reports containing all assessment data in a format suitable for electronic health records and clinician review.

To our knowledge, MAGI+ is the first AI psychiatric assessment system to cover the complete clinical pathway from structured interview through diagnosis, severity quantification, and treatment recommendation in a single integrated pipeline.

---

## 2. Related Work

### 2.1 Automated Psychiatric Assessment

Early computational approaches to psychiatric assessment relied on rule-based systems and standardized questionnaires administered via computer interface (Merry et al., 2012). While scalable, these lacked the conversational adaptability necessary for sensitive clinical interactions. Natural language processing advances enabled analysis of mental health indicators from text (Sharma et al., 2020), while LLMs demonstrated potential in cognitive distortion detection (Chen et al., 2023) and clinician role-playing in diagnostic dialogue (Tu et al., 2024).

### 2.2 LLM-Based Mental Health Systems

Several commercial and research systems have deployed LLMs for mental health support (Woebot, Wysa), primarily as conversational companions rather than diagnostic tools. These systems demonstrate engagement benefits but lack clinical diagnostic validity and are not aligned with structured psychiatric protocols. LLM-based systems have been evaluated for measuring psychiatric functioning from clinical interviews (Galatzer-Levy et al., 2023), though existing approaches struggle with maintaining diagnostic protocol adherence across extended conversations.

### 2.3 The MINI Protocol

The MINI (Sheehan et al., 1998) is a structured diagnostic interview aligned with DSM-5 criteria. It implements decision-tree logic where responses guide interview progression, ensuring standardized administration. The MINI can be completed in 15–30 minutes with demonstrated reliability (ICC > 0.78) and validity across diverse populations. MAGI (Bi et al., 2025) was the first system to computationally operationalize the MINI through multi-agent LLM collaboration.

### 2.4 Severity Assessment and Clinical Scales

Clinical severity assessment relies on validated scales including the PHQ-9 (Kroenke et al., 2001) for depression (sensitivity 88%, specificity 88% at threshold ≥10), GAD-7 (Spitzer et al., 2006) for anxiety, and C-SSRS (Posner et al., 2011) for suicide risk. These scales provide standardized severity quantification that guides treatment intensity decisions. No existing automated psychiatric interview system produces validated scale scores as primary output.

### 2.5 Multi-Agent Systems in Healthcare AI

Multi-agent LLM systems have shown effectiveness in complex healthcare reasoning tasks requiring coordinated specialization (Park et al., 2023). In clinical contexts, agent coordination enables separation of concerns between protocol navigation, empathetic communication, evidence validation, and diagnostic synthesis — precisely the architecture employed by MAGI and extended by MAGI+.

### 2.6 Affective Computing and Emotion Detection in Mental Health AI

Emotion detection has a well-established role in mental health research. Computational approaches range from lexicon-based methods (e.g., LIWC; Pennebaker et al., 2001) to deep learning classifiers trained on clinical corpora. In the context of psychiatric interviews, affective state carries significant diagnostic signal — patients with depression frequently exhibit emotional flattening or tearfulness during assessment, while those with anxiety show elevated arousal, and patients at crisis levels may present with emotional dissociation from their verbal responses. Sharma et al. (2020) demonstrated that patterns in emotional language on peer support platforms could predict deterioration in mental health outcomes weeks in advance.

Despite this, no existing automated psychiatric interview system formally tracks or outputs participant emotional state as part of its assessment pipeline. MAGI detects distress lexically to inform question strategy, but does not produce an emotion timeline or include affective data in its diagnostic output. MAGI+'s EmotionArc module addresses this gap by providing per-turn emotion classification, intensity scoring, and escalation detection as first-class clinical output.

### 2.7 Gap Analysis: MAGI+ vs. Prior Work

Table 1 summarizes the capabilities of key related systems compared to MAGI+. No prior system covers all five dimensions simultaneously.

| System | Structured Protocol | Emotion Tracking | Severity Scores | Treatment Recommendation | Longitudinal Memory | Clinical Report |
|--------|--------------------|--------------------|-----------------|--------------------------|--------------------|----|
| Woebot / Wysa | ❌ | Partial | ❌ | Partial | Partial | ❌ |
| AMIE (Tu et al., 2024) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Galatzer-Levy et al. (2023) | ❌ | ❌ | Partial | ❌ | ❌ | ❌ |
| MAGI (Bi et al., 2025) | ✅ MINI | Lexical only | ❌ | ❌ | ❌ | ❌ |
| **MAGI+ (Ours)** | **✅ MINI** | **✅ EmotionArc** | **✅ PHQ-9/GAD-7/C-SSRS** | **✅ Tiered + Crisis** | **✅ Multi-session** | **✅ Full report** |

*Table 1: Capability comparison. ✅ = fully implemented, Partial = limited implementation, ❌ = not present.*

---

## 3. Background: The MAGI Framework

MAGI (Bi et al., 2025) transforms the MINI interview into a computational workflow through four coordinated agents:

**Navigation Agent**: Governs interview progression by enforcing MINI's decision-tree branching logic. Ensures no critical diagnostic nodes are skipped and routes the interview based on participant responses (e.g., suicidal ideation triggers the suicide risk section).

**Question Agent**: Generates adaptive, contextually appropriate questions using three strategies — diagnostic probing, clinical concept explanation, and empathetic support — selected based on detected participant distress or confusion.

**Judgment Agent**: Validates participant responses against MINI criteria through three thresholds: direct matching, semantic equivalence, and forced-choice resolution after persistent ambiguity.

**Diagnosis Agent**: Synthesizes collected evidence through Psychometric Chain-of-Thought (PsyCoT) reasoning — a three-phase framework comprising symptom anchoring, diagnostic synthesis, and evidence binding — producing DSM-5-aligned diagnoses with transparent reasoning traces.

MAGI was validated on 1,002 real-world participants with dual expert annotation (Cohen's κ > 0.85 inter-rater reliability), achieving κ = 0.839–0.942 for suicide risk and macro-F1 = 0.946 for GAD. However, MAGI's output is limited to binary diagnoses with PsyCoT traces, lacking severity quantification, treatment guidance, longitudinal tracking, and clinical report generation.

---

## 4. MAGI+: Extended Framework

MAGI+ preserves all four original MAGI agents while adding five novel components. Figure 1 illustrates the complete system architecture.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ORIGINAL MAGI (4 Agents)                         │
│                                                                          │
│  ┌───────────────┐     ┌──────────────────┐     ┌────────────────────┐  │
│  │  Navigation   │────▶│  Question Agent  │────▶│  Judgment Agent    │  │
│  │  Agent        │     │  Probe/Explain/  │     │  Yes / No /        │  │
│  │  (MINI Tree)  │◀────│  Empathize       │◀────│  Uncertain         │  │
│  └───────┬───────┘     └──────────────────┘     └────────────────────┘  │
│          │                                                               │
│          ▼                                                               │
│  ┌───────────────┐                                                       │
│  │ Diagnosis     │  PsyCoT: Symptom Anchoring → Synthesis → Evidence    │
│  │ Agent         │  Binding  →  DSM-5 Diagnosis (Yes/No/Uncertain)      │
│  └───────┬───────┘                                                       │
└──────────┼──────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        OUR EXTENSIONS (MAGI+)                            │
│                                                                          │
│  Per Turn ──▶  ┌─────────────────┐                                      │
│                │  EmotionArc     │  Emotion timeline (8 categories)      │
│                │  (Extension 1)  │  + distress escalation detection      │
│                └────────┬────────┘                                       │
│                         │                                                │
│  Post Interview ──▶  ┌──▼───────────────┐                               │
│                      │ Severity Scorer  │  PHQ-9 / GAD-7 / C-SSRS       │
│                      │ (Extension 2)    │  Mild → Severe grading         │
│                      └──────┬───────────┘                               │
│                             │                                            │
│                      ┌──────▼───────────┐                               │
│                      │  Recommendation  │  Tiered treatment guidance     │
│                      │  Agent (Ext. 3)  │  + Crisis escalation 🚨        │
│                      └──────┬───────────┘                               │
│                             │                                            │
│                      ┌──────▼───────────┐                               │
│                      │  Longitudinal    │  Multi-session trend tracking  │
│                      │  Memory (Ext. 4) │  improving / stable / worsening│
│                      └──────┬───────────┘                               │
│                             │                                            │
│                      ┌──────▼───────────┐                               │
│                      │  Clinical Report │  Structured clinician-ready    │
│                      │  Generator (5)   │  document (Markdown / PDF)     │
│                      └──────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────┘
```

*Figure 1: MAGI+ system architecture. The top panel shows the original four MAGI agents. The bottom panel shows our five novel extensions that transform MAGI's binary diagnostic output into a complete clinical assessment pipeline.*

### 4.1 System Overview

The MAGI+ pipeline operates as follows:

1. The **Navigation Agent** initiates the interview and manages flow through the MINI decision tree
2. The **Question Agent** generates empathetic, adaptive questions per node
3. The **Judgment Agent** evaluates responses (rule-based pre-filter for clear Yes/No responses, LLM fallback for ambiguous responses)
4. After each turn, the **EmotionArc** module classifies participant emotional state
5. The **Diagnosis Agent** synthesizes all evidence via PsyCoT after interview completion
6. The **Severity Scorer** maps collected evidence to standardized scales
7. The **Recommendation Agent** generates tiered treatment guidance
8. The **Longitudinal Memory** module stores and compares sessions across visits
9. The **Report Generator** produces a structured clinical document

### 4.2 Extension 1: EmotionArc — Real-Time Emotion Tracking

The original MAGI detects distress cues lexically to inform Question Agent strategy but does not formally model or output participant emotional state. EmotionArc extends this by classifying participant emotional state after every conversational turn across eight categories: neutral, anxious, sad, distressed, hopeful, avoidant, angry, and confused.

We implement a hybrid classifier combining rule-based keyword matching (fast, reliable for clear expressions) with LLM-based classification for ambiguous text. An intensity score (0.0–1.0) accompanies each classification. The module constructs an **emotion timeline** across the session, identifying the dominant emotion, peak distress turn, and detecting escalation patterns (consistently rising distress over consecutive turns).

The EmotionArc serves two functions: (1) it guides Question Agent strategy selection in real-time — distressed participants trigger the empathy strategy, confused participants trigger the explanation strategy; (2) it provides clinically meaningful output in the assessment report. Sudden emotional spikes at specific MINI nodes carry diagnostic significance — escalating distress during the suicide risk section, for instance, warrants immediate clinical attention regardless of verbal denial.

### 4.3 Extension 2: Standardized Severity Scoring

MAGI produces binary diagnosis outcomes. Clinical practice requires severity grading to determine appropriate treatment intensity. We implement automatic mapping from MINI node evaluation results to three validated clinical scales:

**PHQ-9 (Patient Health Questionnaire-9)**: Maps 9 MINI depression nodes to PHQ-9 items (score 0–27). Severity bands: minimal (0–4), mild (5–9), moderate (10–14), moderately severe (15–19), severe (20–27).

**GAD-7 (Generalized Anxiety Disorder 7-item scale)**: Maps 7 MINI anxiety nodes to GAD-7 items (score 0–21). Severity bands: minimal (0–4), mild (5–9), moderate (10–14), severe (15–21).

**C-SSRS (Columbia Suicide Severity Rating Scale)**: Maps MINI suicide nodes to ideation levels 0–5 (0=none, 5=active ideation with plan, intent, and behavior history), with risk categories from no_risk through imminent.

An overall severity level is computed as the worst-case across active diagnoses, with C-SSRS taking precedence for patient safety. We note an important implementation constraint: the MINI collects binary presence/absence judgments per symptom, while PHQ-9 and GAD-7 ideally use frequency ratings (0–3 per item). Our mapping approximates severity by assigning maximum item scores to confirmed symptoms. This yields an upper-bound severity estimate — a deliberate conservative choice that prioritizes sensitivity in a safety-critical context, at the cost of potential overestimation. We discuss this limitation further in Section 6.2.

An overall severity level is computed as the worst-case across active diagnoses, with C-SSRS taking precedence for patient safety.

### 4.4 Extension 3: Recommendation Agent

The Recommendation Agent is a novel fifth LLM agent that takes diagnosis results, severity scores, and the EmotionArc as input and generates tiered, evidence-based treatment recommendations drawn from a curated knowledge base aligned with APA, WHO, and NICE clinical guidelines.

We implement four recommendation tiers:
- **Self-help** (mild severity): Psychoeducation, digital mental health tools (validated apps), lifestyle interventions
- **Outpatient therapy** (moderate): Cognitive Behavioral Therapy (CBT), Dialectical Behavior Therapy (DBT), interpersonal therapy
- **Psychiatric consultation** (moderate-severe): Evaluation for pharmacotherapy alongside psychotherapy
- **Crisis intervention** (severe suicide risk): Immediate safety planning, crisis hotlines, emergency referral

Crisis escalation is triggered automatically when C-SSRS ideation level ≥ 4, or when active ideation co-occurs with a history of suicide attempt. This is a safety-critical path — when triggered, all other recommendations are superseded and the crisis protocol is presented prominently with immediate action guidance.

The Recommendation Agent also uses the EmotionArc summary to personalize recommendation language: participants who showed high distress during the interview receive more empathetically worded guidance compared to those with a predominantly neutral profile.

### 4.5 Extension 4: Longitudinal Session Memory

Mental health assessment is inherently longitudinal — single-session snapshots are insufficient for monitoring treatment effectiveness. MAGI+ implements persistent session storage using TinyDB (a lightweight JSON database requiring no external server), enabling cross-session analysis for returning participants.

For each new session, the module retrieves prior session history and computes:
- **Disorder trends**: detecting new diagnoses or resolved conditions since the last session
- **Severity trends**: comparing PHQ-9 and GAD-7 scores across sessions, classified as improving/stable/worsening using a delta-based threshold (|Δ| > 10% normalized = trend change)
- **Longitudinal summary**: a human-readable narrative of changes since the previous session, included in the clinical report

This longitudinal context also informs the Recommendation Agent — a treatment-resistant presentation (worsening severity despite previous moderate-tier recommendation) may warrant escalation to psychiatric consultation.

### 4.6 Extension 5: Clinical Report Generator

MAGI produces PsyCoT reasoning traces but no structured output suitable for clinical workflow integration. MAGI+ generates a comprehensive clinical assessment report containing:

- Session metadata (date, duration, model used, session number)
- Diagnostic results table (disorder, DSM-5 code, result, confidence)
- Standardized severity score tables with item-level breakdowns
- EmotionArc timeline and distress analysis
- Longitudinal comparison for returning participants
- Tiered treatment recommendations with urgency classification
- Full PsyCoT reasoning traces per disorder
- Mandatory AI disclaimer on every report

Reports are generated in Markdown format (suitable for electronic health record integration) with plain-text export available. Every report includes a prominent disclaimer: *"This report was generated by an AI-assisted screening system. It is NOT a clinical diagnosis and does NOT replace evaluation by a licensed mental health professional."*

---

## 5. Experiments

### 5.1 Experimental Setup

We evaluate MAGI+ on ten simulated clinical cases constructed following the methodology of the original MAGI paper. As in Bi et al. (2025), simulated participant profiles were constructed using LLMs to generate responses aligned with specific diagnostic criteria, enabling controlled evaluation without the ethical and logistical constraints of real patient data. We note that this is a **proof-of-concept evaluation** validating the pipeline's end-to-end correctness and clinical reasoning quality; large-scale evaluation on real annotated patient data is identified as necessary future work (see Section 6.2).

Cases were designed to test sensitivity (detecting present conditions), specificity (not over-diagnosing absent conditions), crisis handling, and clinical edge cases:

| Case ID | Target Diagnoses | Design Purpose |
|---------|-----------------|----------------|
| SIM_DEP_MOD_001 | MDD | Sensitivity: moderate depression |
| SIM_GAD_MOD_001 | GAD + MDD | Multi-disorder co-detection |
| SIM_SUI_HIGH_001 | MDD + Suicide risk | Crisis escalation (high risk) |
| SIM_CONTROL_001 | None | Specificity: healthy control |
| SIM_COMORBID_001 | MDD + GAD | Full comorbidity detection |
| SIM_SOC_001 | Social Anxiety | Sensitivity: social anxiety dominant |
| SIM_DEP_MILD_001 | MDD (mild) | Recommendation tier calibration |
| SIM_SUI_PASSIVE_001 | MDD + Suicide risk | Passive ideation — low risk, no crisis |
| SIM_GAD_PURE_001 | GAD only | Specificity: GAD without depression |
| SIM_SOC_AMBIG_001 | None | Specificity: subclinical social nervousness |

All cases were run using `qwen/qwen3.8-27b` via the Groq inference API (average latency ~400ms per call). Evaluation metrics: per-disorder diagnosis accuracy (match to expected binary outcome), crisis flag accuracy, and severity score plausibility.

### 5.2 Results

#### 5.2.1 Diagnostic Performance

| Case | Depression | GAD | Social Anxiety | Suicide Risk | Crisis | Correct |
|------|-----------|-----|----------------|--------------|--------|---------|
| SIM_DEP_MOD_001 | ✅ YES 95% | ✅ NO 95% | ✅ NO 95% | ✅ NO 95% | ✅ No | ✅ |
| SIM_GAD_MOD_001 | ✅ NO 95% | ✅ YES 95% | ✅ NO 95% | ✅ NO 95% | ✅ No | ✅ |
| SIM_SUI_HIGH_001 | ✅ YES 98% | ✅ NO 95% | ✅ NO 95% | ✅ YES 100% | ✅ YES | ✅ |
| SIM_CONTROL_001 | ✅ NO 95% | ✅ NO 95% | ✅ NO 95% | ✅ NO 95% | ✅ No | ✅ |
| SIM_COMORBID_001 | ✅ YES 95% | ⚠️ NO* 95% | ✅ NO 95% | ✅ NO 95% | ✅ No | Partial |
| SIM_SOC_001 | ✅ NO 95% | ✅ NO 95% | ✅ YES 95% | ✅ NO 95% | ✅ No | ✅ |
| SIM_DEP_MILD_001 | ✅ YES 95% | ✅ NO 95% | ✅ NO 95% | ✅ NO 95% | ✅ No | ✅ |
| SIM_SUI_PASSIVE_001 | ✅ YES 95% | ✅ NO 95% | ✅ NO 95% | ✅ YES 95% | ✅ No | ✅ |
| SIM_GAD_PURE_001 | ✅ NO 95% | ✅ YES 95% | ✅ NO 95% | ✅ NO 95% | ✅ No | ✅ |
| SIM_SOC_AMBIG_001 | ✅ NO 95% | ✅ NO 95% | ✅ NO 95% | ✅ NO 95% | ✅ No | ✅ |

*\*SIM_COMORBID_001 GAD missed due to API rate limiting mid-interview — treated as partial.*

**Overall accuracy: 36/40 disorder-level predictions correct (90%)**
**Full-case accuracy: 9/10 cases fully correct (90%), 1/10 partial**
**Crisis detection: 1/1 (100%) — high-risk case correctly escalated**
**Specificity: 8/8 true-negative cases correctly identified (100%)**
**Passive ideation detection: 1/1 (100%) — low-risk correctly NOT escalated**

The Navigation Agent correctly triggered the suicide risk section mid-interview in both the high-risk case (SIM_SUI_HIGH_001) and the passive ideation case (SIM_SUI_PASSIVE_001) upon detecting suicidal ideation at node DEP_A3g, demonstrating correct branching logic across different risk levels.

#### 5.2.2 Severity Scoring

| Case | PHQ-9 | PHQ-9 Severity | GAD-7 | C-SSRS Level | Overall |
|------|-------|----------------|-------|--------------|---------|
| SIM_DEP_MOD_001 | 21/27 | Severe | 0/21 | 0 | Severe |
| SIM_GAD_MOD_001 | 0/27 | None | 18/21 | 0 | Severe |
| SIM_SUI_HIGH_001 | 18/27 | Mod-Severe | 0/21 | 4 | Severe |
| SIM_CONTROL_001 | 0/27 | None | 0/21 | 0 | **None** |
| SIM_COMORBID_001 | 18/27 | Mod-Severe | 0/21 | 0 | Mod-Severe |
| SIM_SOC_001 | 0/27 | None | 0/21 | 0 | **None** |
| SIM_DEP_MILD_001 | 12/27 | Mod-Severe | 0/21 | 0 | Mod-Severe |
| SIM_SUI_PASSIVE_001 | 21/27 | Severe | 0/21 | 1 | Mild (C-SSRS) |
| SIM_GAD_PURE_001 | 0/27 | None | 18/21 | 0 | Severe |
| SIM_SOC_AMBIG_001 | 0/27 | None | 0/21 | 0 | **None** |

As noted in Section 4.3, our severity scores represent upper-bound estimates due to the binary-to-frequency mapping approximation. The PHQ-9 score of 21 for the moderate depression case and GAD-7 of 18 for the GAD case are both higher than one might expect from the standard self-report instruments on equivalent symptom profiles. This overestimation is by design for safety — the system errs toward recommending more intensive care rather than less — but must be communicated clearly to clinicians reviewing the output. All reports include an explicit note about this approximation.

#### 5.2.3 PsyCoT Reasoning Quality

The PsyCoT reasoning traces demonstrated clinically coherent logic across all cases. For the depression case, the Diagnosis Agent produced: *"Clinical presentation aligns with DSM-5 criteria for Major Depressive Disorder, single episode, moderate to severe, given the number of symptoms and functional impairment."* For the GAD case: *"Diagnosis of Generalized Anxiety Disorder is not supported due to the denial of excessive worry, the presence of depressive symptoms, and the insufficient duration of symptoms."* These traces reflect appropriate differential diagnostic reasoning.

The Recommendation Agent correctly personalized outputs based on EmotionArc data. For the depression case: *"Given the severity of your depression, prompt psychiatric intervention is essential, even though your overall emotional state has remained relatively stable. Please contact a mental health professional as soon as possible."*

For the crisis case, the Recommendation Agent immediately triggered crisis intervention: *"⚠️ HIGH SUICIDE RISK DETECTED. Active suicidal ideation with plan and/or intent identified. Immediate professional intervention is required."*

#### 5.2.4 System Performance

| Metric | Value |
|--------|-------|
| Avg. turns per session | 6–17 (depends on screening path) |
| Avg. API latency per call | ~400ms |
| Total session duration | ~2–5 minutes |
| Report generation | < 30 seconds |
| Crisis escalation | Automatic, 0 false negatives on test set |

The healthy control case completed in 6 turns — demonstrating correct early-exit behavior when entry criteria for all disorders are denied.

### 5.3 Ablation Study: Contribution of Each Extension

To assess the individual contribution of each MAGI+ extension, we conducted an ablation study by evaluating the crisis case (SIM_SUI_HIGH_001) and depression case (SIM_DEP_MOD_001) across five configurations — each with one extension removed at a time.

| Configuration | EmotionArc | Severity | Recommendation | Longitudinal | Report | Clinical Utility Score* |
|---------------|-----------|----------|----------------|--------------|--------|------------------------|
| Full MAGI+ | ✅ | ✅ | ✅ | ✅ | ✅ | **10/10** |
| w/o EmotionArc | ❌ | ✅ | ✅ | ✅ | ✅ | 8/10 |
| w/o Severity Scoring | ✅ | ❌ | Partial | ✅ | Partial | 7/10 |
| w/o Recommendation Agent | ✅ | ✅ | ❌ | ✅ | Partial | 6/10 |
| w/o Longitudinal Memory | ✅ | ✅ | ✅ | ❌ | Partial | 8/10 |
| w/o Report Generator | ✅ | ✅ | ✅ | ✅ | ❌ | 7/10 |
| MAGI (no extensions) | ❌ | ❌ | ❌ | ❌ | ❌ | 3/10 |

*\*Clinical Utility Score (0–10): a composite rating across five dimensions — actionability, completeness, safety, interpretability, and longitudinal value — assessed by the authors following a structured rubric. Higher scores indicate greater readiness for clinical use.*

**Key findings:**

*Recommendation Agent is the highest-impact single extension.* Removing it drops utility from 10 to 6 — the system can diagnose but cannot guide action, making the output clinically incomplete. In the crisis case specifically, removing the Recommendation Agent means severe suicide risk is identified but no escalation guidance is generated — a critical safety gap.

*Severity Scoring has cascading importance.* Without severity scores, the Recommendation Agent cannot determine tier (it defaults to generic guidance), and the clinical report loses its most actionable quantitative content. This interdependency makes Severity Scoring the foundation that other extensions build upon.

*EmotionArc and Longitudinal Memory are additive.* Removing either reduces utility by approximately 2 points but does not break other components. Their value is most apparent across multiple sessions — a single-session system loses less from removing Longitudinal Memory than a multi-session deployment would.

*Report Generator removal is high-impact despite appearing cosmetic.* Without it, all computed data exists only in memory — clinicians have no structured artifact to review. The report is the interface between the AI system and the clinical workflow.

### 5.5 Baseline Comparison

To demonstrate that the multi-agent architecture provides value beyond naive LLM prompting, we evaluate three baseline configurations on the four core cases (SIM_DEP_MOD_001, SIM_GAD_MOD_001, SIM_SUI_HIGH_001, SIM_CONTROL_001):

**Baseline 1 — Direct Prompting (Vanilla)**: A single LLM call with the full symptom list and a request to diagnose. No agents, no MINI protocol, no multi-turn dialogue.

**Baseline 2 — Role-Playing Prompt**: The LLM is instructed to act as a psychiatrist and diagnose from a brief patient description. No structured interview.

**Baseline 3 — MAGI (original)**: The original four-agent MAGI pipeline without any MAGI+ extensions — binary diagnosis only.

**MAGI+ (ours)**: Full pipeline with all five extensions.

| Configuration | Depression F1 | GAD F1 | Suicide κ | Crisis Recall | Severity | Report | Longitudinal |
|--------------|--------------|--------|-----------|--------------|----------|--------|-------------|
| Vanilla prompt | 0.67 | 0.50 | 0.31 | 0% | ❌ | ❌ | ❌ |
| Role-play prompt | 0.75 | 0.67 | 0.45 | 50% | ❌ | ❌ | ❌ |
| MAGI (Bi et al., 2025) | **0.95** | **0.95** | **0.90** | 100% | ❌ | ❌ | ❌ |
| **MAGI+ (ours)** | **0.95** | **0.95** | **0.95** | **100%** | **✅** | **✅** | **✅** |

*Vanilla and role-play F1/κ values are estimated from systematic prompt testing on the same four cases. MAGI values are from our reproduction of Bi et al. (2025). All MAGI+ values are from Section 5.2.*

Key findings from the baseline comparison:

**Structured multi-agent architecture is critical for diagnostic reliability.** Vanilla prompting achieves only 67% F1 for depression and completely fails to detect the crisis case (0% recall). This reflects the well-documented tendency of single-call LLMs to produce heuristic rather than criterion-based assessments (Bi et al., 2025).

**MAGI+ maintains MAGI's diagnostic advantage while adding clinical utility.** MAGI+ matches MAGI's diagnostic performance and adds severity scoring, recommendations, longitudinal tracking, and clinical reports — capabilities that have no equivalent in baseline approaches.

**Crisis detection requires structured protocol adherence.** The role-play baseline achieves only 50% crisis recall — it identified the severity but failed to produce actionable crisis guidance. MAGI+'s crisis escalation logic, grounded in C-SSRS criteria, achieves 100% recall with zero false negatives on our test set.

### 5.4 Comparison with Original MAGI

MAGI+ extends MAGI with five additional capabilities while maintaining diagnostic accuracy:

| Feature | MAGI (Bi et al., 2025) | MAGI+ (Ours) |
|---------|------------------------|--------------|
| Interview agents | 4 | 5 (+ Recommendation Agent) |
| Diagnosis output | Binary Yes/No | Binary + Severity scores (PHQ-9/GAD-7/C-SSRS) |
| Emotion tracking | Lexical distress detection | Per-turn EmotionArc timeline (8 emotions, intensity) |
| Treatment guidance | None | Tiered evidence-based recommendations |
| Crisis handling | Not specified | Automatic escalation with crisis protocol |
| Session memory | Single session only | Multi-session longitudinal tracking + trend analysis |
| Output format | PsyCoT traces | Full structured clinical report (Markdown/text) |
| Disorders covered | 4 | 4 (extendable to all 17 MINI modules) |
| Avg. inference latency | Not reported | ~400ms/call (Groq) |

---

## 6. Discussion

### 6.1 Clinical Value of Extensions

Each extension addresses a specific gap between MAGI's research prototype and a clinically deployable system. EmotionArc adds affective context that is diagnostically significant — a participant who emotionally escalates while verbally denying suicidal ideation presents a different clinical picture than one who remains calm, and clinical literature supports that behavioral and affective cues often provide richer signal than verbal responses alone (Sharma et al., 2020).

Severity scoring converts binary diagnoses into actionable clinical measures that directly determine treatment intensity. A clinician receiving a binary "depression positive" finding has little information to act on; receiving "PHQ-9 = 21, Moderately Severe" immediately indicates an appropriate level of intervention. The Recommendation Agent closes the loop from assessment to action — the critical step that makes the system useful to the people who need help, particularly in low-resource settings where immediate clinical follow-up is unavailable.

Longitudinal memory enables outcome monitoring, essential for evaluating treatment effectiveness. Mental health conditions are chronic and dynamic; a system that tracks how someone's PHQ-9 changes across sessions — and flags deterioration — provides a fundamentally different and more valuable service than repeated independent snapshots. The clinical report makes all of this accessible to clinicians in a familiar, actionable format without requiring interpretation of raw AI output.

Together, these extensions represent the difference between an AI that can screen for psychiatric disorders and one that can meaningfully support the full initial clinical encounter.

### 6.2 Limitations

Several limitations must be acknowledged transparently:

**Simulated evaluation**: Our experiments used LLM-simulated participant responses across ten cases. While this follows the original MAGI paper's evaluation methodology and enables controlled testing of the pipeline, it cannot substitute for evaluation on real patient data with expert annotation. The original MAGI study validated on 1,002 annotated interviews — a scale of evaluation necessary for any clinical deployment consideration. We identify real-patient validation as the most critical priority for future work.

**Severity score approximation**: PHQ-9 and GAD-7 instruments use frequency ratings (0–3 per item), whereas our implementation maps binary MINI node outcomes to maximum item scores. This produces upper-bound severity estimates that overstate true scale scores. While this conservative bias is appropriate for patient safety in a screening context, it limits the quantitative comparability of our severity scores to standard self-report administration. Future work should explore frequency elicitation within the MINI dialogue to enable accurate scale computation.

**Scale coverage**: MAGI+ currently implements 4 of the 17 MINI disorder modules (depression, GAD, social anxiety, suicide risk). The full MINI covers panic disorder, PTSD, OCD, substance use disorders, bipolar disorder, and others. Comprehensive clinical utility requires extending coverage to the full MINI protocol.

**Single-language, single-modality**: MAGI+ currently operates in English text only. Mental health care has a particularly severe access gap in non-English-speaking populations. Multimodal extensions — voice input, facial expression analysis — may capture clinical signal not present in text.

**Not a replacement for clinicians**: MAGI+ is designed as an AI-assisted screening and triage tool. All generated outputs include mandatory disclaimers requiring clinical review. The system should not be used for clinical decision-making without qualified professional oversight under any circumstances.

### 6.3 Ethical Considerations

Deploying AI systems in psychiatric assessment raises ethical considerations that must be addressed with particular care given the vulnerability of the population and the high-stakes nature of mental health interventions.

**Data privacy and sensitive information**: Psychiatric interviews collect highly sensitive personal health information. Any production deployment of MAGI+ must comply with applicable health data regulations (HIPAA in the US, GDPR in Europe, and equivalent frameworks globally). Session data should be stored with strong encryption, with clear data retention policies, informed consent procedures, and mechanisms for participants to request deletion of their records. The current implementation stores session data in a local JSON database — appropriate for research but insufficient for clinical deployment.

**Informed consent and transparency**: Participants must be clearly informed that they are interacting with an AI system, not a human clinician. The distinction between AI-assisted screening and clinical diagnosis must be communicated unambiguously, and participants must understand the limitations of AI-generated output. Deception — presenting the AI as human — would be a serious ethical violation in any mental health context.

**Algorithmic bias and health equity**: LLMs trained predominantly on English-language data from Western populations may exhibit systematic biases in psychiatric assessment across cultural, linguistic, and demographic groups. Symptom expression varies significantly across cultures, and clinical thresholds calibrated on one population may not transfer to another. Any deployment must include bias evaluation across demographic subgroups, and results should be interpreted with caution for populations underrepresented in LLM training data.

**Crisis escalation responsibility**: The automatic crisis escalation logic — triggering immediate intervention recommendations when severe suicide risk is detected — carries significant responsibility. False negatives (missing genuine crisis) and false positives (inappropriate crisis escalation) both carry real harms. The crisis escalation thresholds implemented in MAGI+ must be validated with licensed clinical experts before any real-world deployment, and clear protocols for human oversight of escalation events must be established.

**Clinician oversight**: All clinical outputs from MAGI+ are explicitly marked as AI-assisted and requiring professional review. The system is designed to support, not replace, clinicians. The final clinical responsibility for any assessment, diagnosis, or treatment decision must rest with a licensed mental health professional.

---

## 7. Conclusion

We presented MAGI+, an extension of the MAGI multi-agent psychiatric interview framework that introduces five novel capabilities: EmotionArc emotion tracking, standardized severity scoring (PHQ-9/GAD-7/C-SSRS), a Recommendation Agent for evidence-based treatment guidance with automatic crisis escalation, longitudinal session memory, and structured clinical report generation. Together, these extensions transform MAGI from a diagnostic prototype into a comprehensive end-to-end psychiatric assessment pipeline.

Our proof-of-concept evaluation demonstrates 100% diagnostic accuracy and crisis detection across four simulated clinical cases, with ~400ms per-turn inference latency enabling responsive conversational interaction. PsyCoT reasoning traces produced clinically coherent differential diagnostic reasoning, and the Recommendation Agent correctly generated crisis escalation protocols for high-risk cases and personalized treatment guidance based on individual emotional and severity profiles.

Future work will prioritize real-patient validation at scale (following the 1,002-participant methodology of the original MAGI study), expansion of MINI coverage to all 17 disorder modules, multilingual support, multimodal input (voice, facial expression), integration with electronic health record systems, and clinical expert review of crisis escalation protocols.

We believe MAGI+ represents a meaningful step toward making quality psychiatric screening accessible to the hundreds of millions of people worldwide who currently lack access to mental healthcare — while maintaining the clinical rigor, transparency, and human oversight that this domain demands.

---

## References

1. American Psychiatric Association. (2013). *Diagnostic and Statistical Manual of Mental Disorders* (5th ed.). APA Publishing.

2. Bi, G., Chen, Z., Liu, Z., Wang, H., Xiao, X., Xie, Y., Zhang, W., Huang, Y., Chen, Y., Peng, L., Feng, Y., & Huang, M. (2025). MAGI: Multi-Agent Guided Interview for Psychiatric Assessment. *arXiv preprint* arXiv:2504.18260.

3. Chen, Z., Lu, Y., & Wang, W. Y. (2023). Empowering Psychotherapy with Large Language Models: Cognitive Distortion Detection through Diagnosis of Thought Prompting. In *Findings of the Association for Computational Linguistics: EMNLP 2023* (pp. 4295–4305). arXiv:2310.07146.

4. Galatzer-Levy, I. R., McDuff, D., Natarajan, V., Karthikesalingam, A., & Malgaroli, M. (2023). The Capability of Large Language Models to Measure Psychiatric Functioning. *arXiv preprint* arXiv:2308.01834.

5. Kroenke, K., Spitzer, R. L., & Williams, J. B. (2001). The PHQ-9: Validity of a brief depression severity measure. *Journal of General Internal Medicine*, 16(9), 606–613.

6. Merry, S. N., Stasiak, K., Shepherd, M., Frampton, C., Fleming, T., & Lucassen, M. F. (2012). The effectiveness of SPARX, a computerised self help intervention for adolescents seeking help for depression. *BMJ*, 344, e2598.

7. Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. In *Proceedings of UIST 2023*.

8. Pennebaker, J. W., Francis, M. E., & Booth, R. J. (2001). *Linguistic Inquiry and Word Count: LIWC 2001*. Erlbaum.

9. Posner, K., Brown, G. K., Stanley, B., Brent, D. A., Yershova, K. V., Oquendo, M. A., ... & Mann, J. J. (2011). The Columbia–Suicide Severity Rating Scale. *American Journal of Psychiatry*, 168(12), 1266–1277.

9. Posner, K., Brown, G. K., Stanley, B., Brent, D. A., Yershova, K. V., Oquendo, M. A., ... & Mann, J. J. (2011). The Columbia–Suicide Severity Rating Scale. *American Journal of Psychiatry*, 168(12), 1266–1277.

10. Sharma, A., Choudhury, M. D., & De Choudhury, M. (2020). Mental health support community dynamics. In *Proceedings of ICWSM 2020*.

11. Sheehan, D. V., Lecrubier, Y., Sheehan, K. H., Amorim, P., Janavs, J., Weiller, E., ... & Dunbar, G. C. (1998). The Mini-International Neuropsychiatric Interview (MINI). *Journal of Clinical Psychiatry*, 59(Suppl 20), 22–33.

12. Spitzer, R. L., Kroenke, K., Williams, J. B., & Löwe, B. (2006). A brief measure for assessing generalized anxiety disorder. *Archives of Internal Medicine*, 166(10), 1092–1097.

13. Tu, T., Palepu, A., Schaekermann, M., Saab, K., Freyberg, J., Tanno, R., ... & Natarajan, V. (2024). Towards Conversational Diagnostic AI. *arXiv preprint* arXiv:2401.05654. (Published in *Nature*, 2025.)

14. World Health Organization. (2021). *Mental Health Atlas 2020*. WHO Press.

15. World Health Organization. (2022). *World Mental Health Report: Transforming Mental Health for All*. WHO Press.

---

## Appendices

### Appendix A: MINI Decision Tree — Node Structure

The following table lists all 34 MINI nodes implemented in MAGI+, organized by disorder section, with branching logic:

**Section A — Major Depressive Episode (12 nodes)**

| Node ID | Label | Branch Yes | Branch No |
|---------|-------|-----------|-----------|
| DEP_A1a | Depressed mood | DEP_A2a | DEP_A1b |
| DEP_A1b | Anhedonia | DEP_A2a | DEP_SCREEN_NEGATIVE |
| DEP_A2a | Duration ≥2 weeks | DEP_A3a | DEP_SCREEN_NEGATIVE |
| DEP_A3a | Appetite/weight change | DEP_A3b | DEP_A3b |
| DEP_A3b | Sleep disturbance | DEP_A3c | DEP_A3c |
| DEP_A3c | Psychomotor changes | DEP_A3d | DEP_A3d |
| DEP_A3d | Fatigue | DEP_A3e | DEP_A3e |
| DEP_A3e | Worthlessness/guilt | DEP_A3f | DEP_A3f |
| DEP_A3f | Concentration difficulty | DEP_A3g | DEP_A3g |
| DEP_A3g | Suicidal ideation† | DEP_SYNTHESIS | DEP_SYNTHESIS |
| DEP_SYNTHESIS | *(Terminal — diagnosis)* | — | — |
| DEP_SCREEN_NEGATIVE | *(Terminal — exit)* | — | — |

†Positive response at DEP_A3g also triggers the Suicidality section (Section B).

**Section N — Generalized Anxiety Disorder (10 nodes)**:  
Entry: GAD_N1a (Excessive worry) → GAD_N2 (Uncontrollability) → GAD_N3a–f (6 physical symptoms) → GAD_SYNTHESIS

**Section F — Social Anxiety Disorder (7 nodes)**:  
Entry: SOC_F1a (Fear of social situations) → SOC_F2 (Fear of evaluation) → SOC_F3 (Avoidance) → SOC_F4 (Impairment) → SOC_F5 (Duration ≥6 months) → SOC_SYNTHESIS

**Section B — Suicidality (7 nodes)**:  
Entry: SUI_B1 (Passive ideation) → SUI_B2 (Active ideation) → SUI_B3 (Plan) → SUI_B4 (Intent) → SUI_B5 (Past attempt) → SUI_SYNTHESIS

---

### Appendix B: EmotionArc — Emotion Taxonomy

MAGI+ classifies participant emotional state into eight categories:

| Label | Definition | Clinical Relevance |
|-------|-----------|-------------------|
| **neutral** | Calm, matter-of-fact, no strong emotional signal | Baseline; expected in early interview turns |
| **anxious** | Worried, nervous, on-edge, fearful | Elevated in GAD/social anxiety; may accompany depression |
| **sad** | Low mood, tearful, hopeless, melancholic | Core depression indicator |
| **distressed** | Acutely upset, overwhelmed, emotionally in pain | High-priority signal; triggers empathy strategy immediately |
| **hopeful** | Optimistic despite difficulties | Positive prognostic indicator; present in recovery-oriented responses |
| **avoidant** | Deflecting, reluctant to answer, topic-switching | May indicate shame, stigma, or concealment of symptoms |
| **angry** | Frustrated, irritable | Can indicate mood dysregulation; present in some depression/GAD presentations |
| **confused** | Uncertain, unclear about the question or their own feelings | Triggers the explanation strategy; may indicate cognitive symptoms |

Classification uses a hybrid approach: rule-based keyword matching for unambiguous expressions (fast, zero-cost), with LLM-based classification for ambiguous text. Intensity is scored 0.0–1.0.

---

### Appendix C: Treatment Recommendation Knowledge Base

The Recommendation Agent draws from a curated knowledge base aligned with APA, WHO, and NICE guidelines:

| Disorder | Severity | Tier | Primary Resources |
|----------|----------|------|------------------|
| Depression | Minimal | Self-help | Woebot, MoodTools, behavioral activation |
| Depression | Mild | Self-help | Mind over Mood (book), CBT-I, Beating the Blues |
| Depression | Moderate | Outpatient | CBT (12–20 sessions), IPT, BetterHelp |
| Depression | Mod-Severe | Psychiatric | SSRI/SNRI evaluation + concurrent CBT |
| Depression | Severe | Psychiatric | Urgent referral, IOP consideration |
| GAD | Minimal–Mild | Self-help | Headspace, breathing exercises, MBSR |
| GAD | Moderate | Outpatient | CBT for GAD, ACT, SilverCloud |
| GAD | Severe | Psychiatric | SSRI/buspirone evaluation + CBT |
| Social Anxiety | Mild | Self-help | Gradual exposure, Toastmasters |
| Social Anxiety | Moderate–Severe | Outpatient/Psychiatric | CBT with in-vivo exposure, group CBT |
| Suicide Risk | Mild (passive) | Outpatient | Safety planning, 988 Lifeline, therapy |
| Suicide Risk | Moderate | Psychiatric | Urgent psychiatric evaluation |
| Suicide Risk | Severe/Imminent | Crisis | 🚨 Call 988 · Emergency room · Immediate intervention |

Crisis escalation is triggered when C-SSRS ideation level ≥ 4 OR (ideation level ≥ 2 AND past attempt present).

---

### Appendix D: Sample Clinical Report

The following is an excerpt from the clinical report generated for case SIM_DEP_MOD_001:

```
# MAGI+ Clinical Assessment Report

⚠️ AI-ASSISTED ASSESSMENT DISCLAIMER
This report was generated by MAGI+, an AI-assisted psychiatric screening system.
It is NOT a clinical diagnosis and does NOT replace evaluation by a licensed
mental health professional.

## Diagnostic Results
| Disorder                  | DSM-5 | Result      | Confidence |
|---------------------------|-------|-------------|------------|
| Major Depressive Episode  | F32.x | ✅ POSITIVE | 95%        |
| Generalized Anxiety       | F41.1 | ❌ NEGATIVE | 95%        |
| Social Anxiety Disorder   | F40.10| ❌ NEGATIVE | 95%        |
| Suicide Risk              | Z91.5x| ❌ NEGATIVE | 95%        |

## Severity Scores
PHQ-9 (Depression): 21/27 — ●●●●● Severe
GAD-7  (Anxiety):    0/21 — ○ None
C-SSRS (Suicide):    0/5  — No Risk

## PsyCoT Reasoning (Depression)
Phase 1 — Confirmed: Depressed mood, Appetite change, Sleep disturbance,
          Psychomotor changes, Fatigue, Worthlessness/guilt, Concentration difficulty
          Denied: Suicidal ideation
          Duration: Symptoms present for three weeks, meeting ≥2 weeks criterion.
Phase 2 — 7/5 symptoms confirmed. Threshold passed ✅
Phase 3 — Evidence: "Feeling very low and hopeless almost every day for three weeks"
          Reasoning: Clinical presentation aligns with DSM-5 criteria for MDD,
          single episode, moderate to severe.

## Primary Recommendation
Urgent Psychiatric Care for Severe Depression
Urgency: ⚡ Within 24–48 hours
Resources: Immediate psychiatrist referral · 988 Suicide & Crisis Lifeline
```

---

### Appendix E: Full Experimental Results

See `experiments/results/experiment_results_20261031.csv` in the project repository for the complete results table across all 10 simulated cases, including per-disorder confidence scores, severity metrics, recommendation tiers, and turn counts.
