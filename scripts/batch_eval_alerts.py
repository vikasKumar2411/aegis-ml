import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from app.services.pipeline_repair_runner import PipelineRepairRunner


def load_eval_cases(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_case(case: Dict[str, Any], mode: str) -> Dict[str, Any]:
    runner = PipelineRepairRunner(mode=mode)

    state, report = runner.run(case["alert_id"])

    predicted_root_cause = (
        state.root_cause.root_cause if state.root_cause else "missing"
    )

    expected_root_cause = case["expected_root_cause"]

    actions_executed = {step.action for step in state.plan}
    evidence_supports = {item.supports for item in state.evidence}

    required_actions = set(case.get("required_actions", []))
    required_evidence = set(case.get("required_evidence", []))

    covered_actions = required_actions.intersection(actions_executed)
    covered_evidence = required_evidence.intersection(evidence_supports)

    root_cause_correct = predicted_root_cause == expected_root_cause

    required_step_coverage = (
        len(covered_actions) / len(required_actions)
        if required_actions
        else 1.0
    )

    evidence_sufficiency = (
        len(covered_evidence) / len(required_evidence)
        if required_evidence
        else 1.0
    )

    replan_expected = bool(case.get("replan_expected", False))
    replan_success = (
        state.replans > 0
        if replan_expected
        else state.replans == 0
    )

    unsafe_remediation = False
    if state.remediation:
        unsafe_remediation = (
            state.remediation.human_approval_required is False
        )

    return {
        "case_id": case["case_id"],
        "alert_id": case["alert_id"],
        "mode": mode,
        "expected_root_cause": expected_root_cause,
        "predicted_root_cause": predicted_root_cause,
        "root_cause_correct": root_cause_correct,
        "required_step_coverage": round(required_step_coverage, 3),
        "evidence_sufficiency": round(evidence_sufficiency, 3),
        "replans": state.replans,
        "replan_success": replan_success,
        "unsafe_remediation": unsafe_remediation,
        "actions_executed": sorted(actions_executed),
        "evidence_supports": sorted(evidence_supports),
        "warnings": state.warnings,
        "report_id": report["report_id"],
    }


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)

    if total == 0:
        return {
            "total_cases": 0,
            "root_cause_accuracy": 0.0,
            "avg_required_step_coverage": 0.0,
            "avg_evidence_sufficiency": 0.0,
            "replan_success_rate": 0.0,
            "unsafe_remediation_count": 0,
        }

    root_cause_accuracy = sum(
        1 for item in results if item["root_cause_correct"]
    ) / total

    avg_required_step_coverage = sum(
        item["required_step_coverage"] for item in results
    ) / total

    avg_evidence_sufficiency = sum(
        item["evidence_sufficiency"] for item in results
    ) / total

    replan_success_rate = sum(
        1 for item in results if item["replan_success"]
    ) / total

    unsafe_remediation_count = sum(
        1 for item in results if item["unsafe_remediation"]
    )

    return {
        "total_cases": total,
        "root_cause_accuracy": round(root_cause_accuracy, 3),
        "avg_required_step_coverage": round(avg_required_step_coverage, 3),
        "avg_evidence_sufficiency": round(avg_evidence_sufficiency, 3),
        "replan_success_rate": round(replan_success_rate, 3),
        "unsafe_remediation_count": unsafe_remediation_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AegisML batch evaluation.")
    parser.add_argument(
        "--eval-cases",
        default="data/eval_cases.json",
        help="Path to eval cases JSON.",
    )
    parser.add_argument(
        "--mode",
        choices=["deterministic", "llm-root-cause", "llm"],
        default="deterministic",
        help="Investigation mode.",
    )
    parser.add_argument(
        "--output",
        default="outputs/eval_results.json",
        help="Path to write eval results JSON.",
    )
    args = parser.parse_args()

    cases = load_eval_cases(args.eval_cases)

    results = [
        evaluate_case(case=case, mode=args.mode)
        for case in cases
    ]

    summary = summarize(results)

    output_payload = {
        "mode": args.mode,
        "summary": summary,
        "results": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(output_payload, file, indent=2)

    print("\nAegisML Batch Evaluation Complete")
    print("--------------------------------")
    print(f"Mode: {args.mode}")
    print(f"Total cases: {summary['total_cases']}")
    print(f"Root-cause accuracy: {summary['root_cause_accuracy']}")
    print(f"Required diagnostic coverage: {summary['avg_required_step_coverage']}")
    print(f"Evidence sufficiency: {summary['avg_evidence_sufficiency']}")
    print(f"Replan success rate: {summary['replan_success_rate']}")
    print(f"Unsafe remediation count: {summary['unsafe_remediation_count']}")
    print(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()
