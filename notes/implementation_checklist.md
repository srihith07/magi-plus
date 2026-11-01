# Implementation Checklist
## MAGI Extended — From Easiest to Hardest

This checklist follows the original MAGI paper reproduction first,
then adds our unique extensions on top.

---

## PHASE 1: Setup & Foundation (Week 1)

- [ ] 1. Set up Python environment (LangChain / LlamaIndex / OpenAI SDK)
- [ ] 2. Define the MINI interview tree as a JSON/YAML data structure
- [ ] 3. Create base data models (InterviewSession, Node, Response, Diagnosis)
- [ ] 4. Set up LLM client (OpenAI GPT-4o or local model via Ollama)
- [ ] 5. Create a basic conversation loop (input → LLM → output)

---

## PHASE 2: Core MAGI Reproduction (Week 2–3)

- [ ] 6. Implement Navigation Agent (tree traversal + branching logic)
- [ ] 7. Implement Question Agent (3 strategies: probe / explain / empathize)
- [ ] 8. Implement Judgment Agent (response validation against MINI criteria)
- [ ] 9. Implement Diagnosis Agent with PsyCoT (3 phases: anchor / synthesize / bind)
- [ ] 10. Wire all 4 agents together into the full MAGI pipeline
- [ ] 11. Test with simulated participants (manually crafted cases)
- [ ] 12. Evaluate against original paper's baseline metrics (F1, κ)

---

## PHASE 3: Our Unique Extensions (Week 4–6)

### Extension A: Emotion Tracking Module
- [ ] 13. Build real-time sentiment/emotion classifier per turn
- [ ] 14. Maintain an emotion timeline across the session
- [ ] 15. Generate an "Emotional Arc Report" as part of the output
- [ ] 16. Use emotion data to influence Question Agent strategy

### Extension B: Severity Scoring
- [ ] 17. Implement PHQ-9 scoring for depression (mapped from collected symptoms)
- [ ] 18. Implement GAD-7 scoring for anxiety
- [ ] 19. Implement Columbia Suicide Severity Rating Scale (C-SSRS) mapping
- [ ] 20. Output severity level (mild / moderate / severe) per disorder

### Extension C: Treatment Recommendation Layer
- [ ] 21. Build a knowledge base of evidence-based treatment options per diagnosis
- [ ] 22. Implement a Recommendation Agent that suggests next steps
- [ ] 23. Differentiate between: self-help resources / therapy / medication / emergency
- [ ] 24. Add crisis escalation logic (severe suicide risk → immediate alert)

### Extension D: Session Memory & Longitudinal Tracking
- [ ] 25. Implement session persistence (store sessions to database/JSON)
- [ ] 26. Build a progress comparison across multiple sessions
- [ ] 27. Generate a longitudinal trend report (improving / stable / worsening)

### Extension E: Clinician Dashboard Output
- [ ] 28. Generate a structured clinical report (PDF/Markdown)
- [ ] 29. Include: diagnosis, PsyCoT trace, severity scores, emotion arc, recommendations
- [ ] 30. Format report for clinical workflow integration

---

## PHASE 4: Evaluation of Extensions (Week 7)

- [ ] 31. Design evaluation metrics for new extensions
- [ ] 32. Compare extended MAGI vs original MAGI on same test cases
- [ ] 33. Document all results in experiments/ folder
- [ ] 34. Write ablation study (which extension contributes most)

---

## PHASE 5: Paper Writing (Week 8–9)

- [ ] 35. Write Introduction (problem, gap, our contribution)
- [ ] 36. Write Related Work section
- [ ] 37. Write Methodology section (original MAGI + our extensions)
- [ ] 38. Write Experiments section (setup, results, analysis)
- [ ] 39. Write Discussion & Conclusion
- [ ] 40. Prepare figures and tables
- [ ] 41. Write abstract
- [ ] 42. Prepare GitHub repository for submission
- [ ] 43. Submit to target venue (ACL / EMNLP / AAAI / Nature Digital Medicine)
