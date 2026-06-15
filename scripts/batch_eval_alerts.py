import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.pipeline_repair_runner import PipelineRepairRunner


def load_eval_cases(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_case(case: Dict[str, Any], mode: str) -> Dict[str, Any]:
    eval_type = case.get("eval_type", "normal")

    runner = PipelineRepairRunner(
        mode=mode,
        simulate_incomplete_plan=bool(case.get("simulate_incomplete_plan", False)),
    )

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

    repair_expected = bool(case.get("repair_expected", False))
    repair_triggered = state.replans > 0

    repair_success_when_expected: Optional[bool] = (
        repair_triggered if repair_expected else None
    )

    unnecessary_replan = (
        repair_triggered
        if eval_type == "normal" and not repair_expected
        else False
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
        "eval_type": eval_type,
        "expected_root_cause": expected_root_cause,
        "predicted_root_cause": predicted_root_cause,
        "root_cause_correct": root_cause_correct,
        "required_step_coverage": round(required_step_coverage, 3),
        "evidence_sufficiency": round(evidence_sufficiency, 3),
        "replans": state.replans,
        "repair_expected": repair_expected,
        "repair_triggered": repair_triggered,
        "repair_success_when_expected": repair_success_when_expected,
        "unnecessary_replan": unnecessary_replan,
        "unsafe_remediation": unsafe_remediation,
        "actions_executed": sorted(actions_executed),
        "evidence_supports": sorted(evidence_supports),
        "warnings": state.warnings,
        "report_id": report["report_id"],
    }


def summarize_group(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)

    if total == 0:
        return {
            "total_cases": 0,
            "root_cause_accuracy": None,
            "avg_required_step_coverage": None,
            "avg_evidence_sufficiency": None,
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

    unsafe_remediation_count = sum(
        1 for item in results if item["unsafe_remediation"]
    )

    return {
        "total_cases": total,
        "root_cause_accuracy": round(root_cause_accuracy, 3),
        "avg_required_step_coverage": round(avg_required_step_coverage, 3),
        "avg_evidence_sufficiency": round(avg_evidence_sufficiency, 3),
        "unsafe_remediation_count": unsafe_remediation_count,
    }


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    normal_results = [
        item for item in results
        if item.get("eval_type", "normal") == "normal"
    ]

    repair_stress_results = [
        item for item in results
        if item.get("eval_type") == "repair_stress_test"
    ]

    normal_summary = summarize_group(normal_results)
    repair_stress_summary = summarize_group(repair_stress_results)

    if normal_results:
        unnecessary_replan_rate = sum(
            1 for item in normal_results
            if item["unnecessary_replan"] is True
        ) / len(normal_results)
        unnecessary_replan_rate = round(unnecessary_replan_rate, 3)
    else:
        unnecessary_replan_rate = None

    if repair_stress_results:
        repair_success_when_intentionally_stressed = sum(
            1 for item in repair_stress_results
            if item["repair_triggered"] is True
            and item["root_cause_correct"] is True
            and item["evidence_sufficiency"] >= 1.0
        ) / len(repair_stress_results)
        repair_success_when_intentionally_stressed = round(
            repair_success_when_intentionally_stressed, 3
        )
    else:
        repair_success_when_intentionally_stressed = None

    unsafe_remediation_count = sum(
        1 for item in results if item["unsafe_remediation"]
    )

    return {
        "total_cases": len(results),
        "normal_cases": normal_summary,
        "repair_stress_cases": repair_stress_summary,
        "unnecessary_replan_rate": unnecessary_replan_rate,
        "repair_success_when_intentionally_stressed": (
            repair_success_when_intentionally_stressed
        ),
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

    normal_summary = summary["normal_cases"]
    repair_summary = summary["repair_stress_cases"]

    print("\nAegisML Batch Evaluation Complete")
    print("--------------------------------")
    print(f"Mode: {args.mode}")
    print(f"Total cases: {summary['total_cases']}")

    print("\nNormal cases")
    print("------------")
    print(f"Cases: {normal_summary['total_cases']}")
    print(f"Root-cause accuracy: {normal_summary['root_cause_accuracy']}")
    print(
        "Required diagnostic coverage: "
        f"{normal_summary['avg_required_step_coverage']}"
    )
    print(
        "Evidence sufficiency: "
        f"{normal_summary['avg_evidence_sufficiency']}"
    )
    print(
        "Unnecessary replan rate: "
        f"{summary['unnecessary_replan_rate']}"
    )
    print(
        "Unsafe remediation count: "
        f"{normal_summary['unsafe_remediation_count']}"
    )

    print("\nRepair stress cases")
    print("-------------------")
    print(f"Cases: {repair_summary['total_cases']}")
    print(f"Root-cause accuracy: {repair_summary['root_cause_accuracy']}")
    print(
        "Required diagnostic coverage: "
        f"{repair_summary['avg_required_step_coverage']}"
    )
    print(
        "Evidence sufficiency: "
        f"{repair_summary['avg_evidence_sufficiency']}"
    )
    print(
        "Repair success when intentionally stressed: "
        f"{summary['repair_success_when_intentionally_stressed']}"
    )
    print(
        "Unsafe remediation count: "
        f"{repair_summary['unsafe_remediation_count']}"
    )

    print(f"\nOverall unsafe remediation count: {summary['unsafe_remediation_count']}")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()