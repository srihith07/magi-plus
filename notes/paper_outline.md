# Paper Outline: MAGI+
## "From Diagnosis to Action: Extending Multi-Agent Psychiatric Interviews with
## Affective Monitoring, Severity Grading, and Evidence-Based Recommendations"

---

## Abstract (Write Last)
- Problem: Mental health crisis + lack of accessible psychiatric assessment
- Gap: Existing systems (including MAGI) stop at diagnosis, lack emotion tracking,
  severity grading, and treatment guidance
- Our work: MAGI+ extends MAGI with 5 novel modules
- Results: Improved clinical utility, new capabilities, maintained diagnostic performance
- Impact: First end-to-end AI psychiatric assessment → recommendation pipeline

---

## 1. Introduction
1.1 The global mental health crisis (statistics, WHO data)
1.2 Structured clinical interviews as the gold standard (MINI protocol)
1.3 The promise and limitations of LLM-based approaches
1.4 What MAGI achieved (brief summary)
1.5 What MAGI still lacks (our motivation — the 5 gaps)
1.6 Our contributions (list the 5 extensions clearly)
1.7 Paper organization

---

## 2. Background & Related Work
2.1 The MINI Protocol and DSM-5
2.2 LLM-based Mental Health Tools
   - Conversational agents (Woebot, Wysa)
   - Clinical interview automation
   - Diagnostic reasoning with LLMs
2.3 Emotion Detection in Mental Health AI
2.4 Severity Assessment Scales (PHQ-9, GAD-7, C-SSRS)
2.5 Treatment Recommendation Systems
2.6 Multi-Agent Systems in Healthcare AI
2.7 Gap Analysis (table showing what each prior work covers vs. our work)

---

## 3. Original MAGI Framework (Background)
3.1 Architecture overview (4 agents)
3.2 Navigation Agent
3.3 Question Agent
3.4 Judgment Agent
3.5 Diagnosis Agent & PsyCoT
3.6 Limitations we address

---

## 4. MAGI+: Our Extended Framework
4.1 System Overview (architecture diagram)
4.2 Extension 1: EmotionArc — Real-Time Emotion Tracking
   - Emotion classifier design
   - Timeline construction
   - Integration with Question Agent
4.3 Extension 2: Severity Scoring Module
   - PHQ-9 mapping from dialogue
   - GAD-7 mapping
   - C-SSRS mapping
   - Severity tier classification
4.4 Extension 3: Recommendation Agent (5th Agent)
   - Knowledge base design
   - Tiered recommendation logic
   - Crisis escalation protocol
4.5 Extension 4: Longitudinal Session Memory
   - Session storage schema
   - Cross-session comparison
   - Trend detection algorithm
4.6 Extension 5: Clinical Report Generator
   - Report schema
   - Output formats (Markdown, PDF)

---

## 5. Experiments
5.1 Experimental Setup
   - Dataset (simulated cases + original MAGI methodology)
   - LLMs evaluated (GPT-4o, DeepSeek-R1)
   - Evaluation metrics
5.2 Reproduction of Original MAGI Results
   - Validates our implementation is faithful
5.3 Evaluation of EmotionArc
   - Correlation between emotion arc and diagnosis
   - Human evaluation of empathy response quality
5.4 Evaluation of Severity Scoring
   - Comparison with self-report PHQ-9/GAD-7 ground truth
5.5 Evaluation of Recommendation Agent
   - Appropriateness ratings by clinical experts
   - Crisis case handling accuracy
5.6 Evaluation of Longitudinal Memory
   - Accuracy of trend detection across simulated session pairs
5.7 End-to-End Evaluation
   - Full MAGI+ pipeline vs. original MAGI
   - Clinician usability study (qualitative)

---

## 6. Discussion
6.1 What our extensions add to clinical value
6.2 Failure cases and limitations
6.3 Ethical considerations
   - Not a replacement for clinicians
   - Data privacy
   - Bias in LLMs for mental health
   - Crisis escalation responsibilities
6.4 Comparison to existing commercial tools

---

## 7. Conclusion
7.1 Summary of contributions
7.2 Clinical implications
7.3 Future work (multilingual, voice, multimodal, EHR integration)

---

## Appendices
A. MINI protocol decision tree structure
B. Emotion taxonomy used in EmotionArc
C. Treatment recommendation knowledge base sources
D. Sample clinical report output
E. Full experimental results tables
