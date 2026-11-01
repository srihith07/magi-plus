"""
run_experiments.py
------------------
Evaluation script for MAGI+ experiments.

Runs all simulated test cases and computes:
  - Diagnosis accuracy (vs. expected ground truth)
  - Crisis detection accuracy
  - Severity score ranges
  - Generates a consolidated results CSV

Run from project root:
  python experiments/run_experiments.py
"""

from __future__ import annotations
import os
import sys
import json
import csv
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)  # Ensure relative paths resolve from project root

from src.main import MAGIPlusPipeline


CASES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "simulated_cases")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")


def load_case(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def run_all_cases(model: str = "gpt-4o") -> list[dict]:
    """Run all simulated cases and return evaluation results."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    case_files = [
        f for f in os.listdir(CASES_DIR)
        if f.endswith(".json")
    ]

    results = []

    for case_file in sorted(case_files):
        case_path = os.path.join(CASES_DIR, case_file)
        case = load_case(case_path)

        print(f"\n{'='*60}")
        print(f"Running case: {case['case_id']}")
        print(f"Description: {case['description']}")
        print("="*60)

        # Create a unique participant ID per case run
        participant_id = f"EXP_{case['case_id']}_{datetime.utcnow().strftime('%H%M%S')}"

        try:
            pipeline = MAGIPlusPipeline(
                participant_id=participant_id,
                model=model,
                verbose=True,
                reports_dir=REPORT_DIR,
            )

            report_path = pipeline.run_simulated(case["responses"])
            session = pipeline.session

            # ── Evaluate results ──────────────────
            eval_result = {
                "case_id": case["case_id"],
                "participant_id": participant_id,
                "report_path": report_path,
                "diagnosis_results": {},
                "diagnosis_correct": {},
                "crisis_flag_actual": False,
                "crisis_flag_expected": case.get("expected_crisis_flag", False),
                "crisis_flag_correct": True,
                "phq9_score": None,
                "gad7_score": None,
                "overall_severity": None,
                "total_turns": session.total_turns,
            }

            # Check each disorder diagnosis
            expected = case.get("expected_diagnoses", {})
            all_correct = True
            for disorder_key, trace in session.diagnoses.items():
                actual = trace.result.value
                expected_val = expected.get(disorder_key, "unknown")
                correct = (actual == expected_val)
                if not correct:
                    all_correct = False
                eval_result["diagnosis_results"][disorder_key] = actual
                eval_result["diagnosis_correct"][disorder_key] = correct

            eval_result["all_diagnoses_correct"] = all_correct

            # Crisis flag
            if session.recommendations:
                eval_result["crisis_flag_actual"] = session.recommendations.crisis_flag
                eval_result["crisis_flag_correct"] = (
                    eval_result["crisis_flag_actual"] == eval_result["crisis_flag_expected"]
                )

            # Severity scores
            if session.severity_report:
                if session.severity_report.phq9:
                    eval_result["phq9_score"] = session.severity_report.phq9.score
                if session.severity_report.gad7:
                    eval_result["gad7_score"] = session.severity_report.gad7.score
                eval_result["overall_severity"] = session.severity_report.overall_severity.value

            results.append(eval_result)

            # Print result
            print(f"\nResults for {case['case_id']}:")
            print(f"  Diagnoses: {eval_result['diagnosis_results']}")
            print(f"  All correct: {eval_result['all_diagnoses_correct']}")
            print(f"  Crisis flag: {eval_result['crisis_flag_actual']} (expected: {eval_result['crisis_flag_expected']})")
            print(f"  PHQ-9: {eval_result['phq9_score']}, GAD-7: {eval_result['gad7_score']}")

        except Exception as e:
            print(f"ERROR running case {case['case_id']}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "case_id": case["case_id"],
                "error": str(e),
                "all_diagnoses_correct": False,
            })

    return results


def save_results_csv(results: list[dict]) -> str:
    """Save experiment results to CSV."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RESULTS_DIR, f"experiment_results_{timestamp}.csv")

    if not results:
        return filepath

    # Collect all keys
    all_keys = set()
    for r in results:
        all_keys.update(r.keys())
    fieldnames = sorted(all_keys)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            # Flatten nested dicts
            flat = {}
            for k, v in result.items():
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        flat[f"{k}_{sub_k}"] = sub_v
                else:
                    flat[k] = v
            writer.writerow(flat)

    print(f"\nResults saved to: {filepath}")
    return filepath


def print_summary(results: list[dict]) -> None:
    """Print a summary of experiment results."""
    print(f"\n{'='*60}")
    print("EXPERIMENT SUMMARY")
    print("="*60)

    total = len(results)
    errors = sum(1 for r in results if "error" in r)
    successful = total - errors

    print(f"Total cases: {total}")
    print(f"Successful: {successful}")
    print(f"Errors: {errors}")

    if successful > 0:
        correct_diag = sum(1 for r in results if r.get("all_diagnoses_correct", False))
        correct_crisis = sum(1 for r in results if r.get("crisis_flag_correct", False))
        print(f"Diagnosis accuracy: {correct_diag}/{successful} ({correct_diag/successful:.0%})")
        print(f"Crisis flag accuracy: {correct_crisis}/{successful} ({correct_crisis/successful:.0%})")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run MAGI+ experiments")
    parser.add_argument("--model", default="gpt-4o", help="LLM model to use")
    parser.add_argument("--case", default=None, help="Run a specific case file only")
    args = parser.parse_args()

    print("MAGI+ Experiment Runner")
    print(f"Model: {args.model}")
    print(f"Cases directory: {CASES_DIR}")

    results = run_all_cases(model=args.model)
    csv_path = save_results_csv(results)
    print_summary(results)
