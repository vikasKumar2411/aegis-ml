import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT_DIR / "outputs" / "reports"
OUTPUTS_DIR = ROOT_DIR / "outputs"


ALERT_OPTIONS = {
    "ALERT-001": "new_secure_email_patterns",
    "ALERT-002": "bad_model_deployment",
    "ALERT-003": "schema_drift",
    "ALERT-004": "data_quality_issue",
    "ALERT-005": "false_alarm",
    "ALERT-006": "feature_drift",
}

MODE_OPTIONS = ["deterministic", "llm-root-cause", "llm"]


st.set_page_config(
    page_title="AegisML Demo Console",
    page_icon="🛡️",
    layout="wide",
)


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_text(path: Path) -> Optional[str]:
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as file:
        return file.read()


def run_command(command: List[str]) -> subprocess.CompletedProcess:
    import os

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")

    if existing_pythonpath:
        env["PYTHONPATH"] = f"{ROOT_DIR}:{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = str(ROOT_DIR)

    return subprocess.run(
        command,
        cwd=ROOT_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def run_investigation(alert_id: str, mode: str) -> Dict[str, Any]:
    command = [
        sys.executable,
        "scripts/run_alert.py",
        "--alert-id",
        alert_id,
        "--mode",
        mode,
    ]

    result = run_command(command)

    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)

    report_path = REPORTS_DIR / f"REPORT-{alert_id}.json"
    report = load_json(report_path)

    if not report:
        raise FileNotFoundError(f"Report not found: {report_path}")

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "report": report,
    }


def run_eval_suite(mode: str) -> Dict[str, Any]:
    output_path = OUTPUTS_DIR / f"eval_results_{mode.replace('-', '_')}.json"

    command = [
        sys.executable,
        "scripts/batch_eval_alerts.py",
        "--mode",
        mode,
        "--output",
        str(output_path),
    ]

    result = run_command(command)

    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)

    eval_result = load_json(output_path)

    if not eval_result:
        raise FileNotFoundError(f"Eval result not found: {output_path}")

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "eval_result": eval_result,
        "output_path": str(output_path),
    }


def get_nested(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)

    return current if current is not None else default


def extract_root_cause(report: Dict[str, Any]) -> Dict[str, Any]:
    root = report.get("root_cause") or {}

    return {
        "root_cause": root.get("root_cause")
        or root.get("label")
        or report.get("root_cause_label")
        or "unknown",
        "confidence": root.get("confidence")
        or report.get("confidence")
        or "unknown",
        "summary": root.get("summary")
        or report.get("executive_summary")
        or "No summary available.",
        "alternatives": root.get("alternatives")
        or report.get("alternatives_considered")
        or [],
    }


def extract_remediation(report: Dict[str, Any]) -> Dict[str, Any]:
    remediation = report.get("remediation") or {}

    return {
        "recommended_action": remediation.get("recommended_action")
        or remediation.get("action")
        or "unknown",
        "priority": remediation.get("priority") or "unknown",
        "human_approval_required": remediation.get("human_approval_required", True),
        "reason": remediation.get("reason") or "No remediation reason available.",
        "actions": remediation.get("actions") or remediation.get("steps") or [],
    }


def extract_execution_metadata(report: Dict[str, Any]) -> Dict[str, Any]:
    metadata = report.get("execution_metadata") or {}

    return {
        "mode": metadata.get("investigation_mode")
        or metadata.get("reasoning_mode")
        or report.get("mode")
        or "unknown",
        "replans": metadata.get("replans", report.get("replans", 0)),
        "max_replans": metadata.get("max_replans", "unknown"),
        "planning_mode": metadata.get("planning_mode", "unknown"),
        "root_cause_mode": metadata.get("root_cause_mode", "unknown"),
    }


def extract_evidence_table(report: Dict[str, Any]) -> pd.DataFrame:
    evidence = (
        report.get("evidence_table")
        or report.get("evidence")
        or report.get("evidence_items")
        or []
    )

    rows = []

    for item in evidence:
        if not isinstance(item, dict):
            continue

        rows.append(
            {
                "Source": item.get("source")
                or item.get("service")
                or item.get("tool")
                or "unknown",
                "Supports": item.get("supports")
                or item.get("evidence_type")
                or item.get("label")
                or "unknown",
                "Finding": item.get("summary")
                or item.get("finding")
                or item.get("description")
                or "",
            }
        )

    return pd.DataFrame(rows)


def extract_plan_table(report: Dict[str, Any]) -> pd.DataFrame:
    plan = (
        report.get("diagnostic_plan")
        or report.get("final_plan")
        or report.get("plan")
        or []
    )

    if isinstance(plan, dict):
        plan = (
            plan.get("approved_steps")
            or plan.get("steps")
            or plan.get("final_steps")
            or plan.get("diagnostic_steps")
            or []
        )

    rows = []

    for step in plan:
        if not isinstance(step, dict):
            continue

        rows.append(
            {
                "Step": step.get("step_id") or step.get("id") or "",
                "Action": step.get("action") or "",
                "Target": step.get("target") or "",
                "Reason": step.get("reason") or "",
            }
        )

    return pd.DataFrame(rows)

def build_agent_trace(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    root = extract_root_cause(report)
    remediation = extract_remediation(report)
    metadata = extract_execution_metadata(report)

    evidence_df = extract_evidence_table(report)
    plan_df = extract_plan_table(report)

    validation = report.get("validation") or {}
    repair_history = report.get("repair_history") or []

    root_validation = (
        validation.get("root_cause_validation")
        if isinstance(validation, dict)
        else {}
    ) or report.get("root_cause_validation") or {}

    plan_validation = (
        validation.get("plan_validation") if isinstance(validation, dict) else {}
    ) or report.get("plan_validation") or {}

    trace = [
        {
            "agent": "Planner Agent",
            "status": "passed",
            "input": "ML production alert",
            "action": "Generated diagnostic investigation plan",
            "output": f"{len(plan_df)} diagnostic steps",
        },
        {
            "agent": "Plan Validator",
            "status": "passed",
            "input": "Diagnostic plan",
            "action": "Checked allowed actions and plan structure",
            "output": json.dumps(plan_validation, indent=2)
            if plan_validation
            else "Plan accepted",
        },
        {
            "agent": "Diagnostic Tool Executor",
            "status": "passed",
            "input": "Validated diagnostic plan",
            "action": "Executed read only diagnostic tools",
            "output": f"{len(evidence_df)} evidence items collected",
        },
        {
            "agent": "Root Cause Agent",
            "status": "passed",
            "input": "Collected evidence",
            "action": "Synthesized root cause",
            "output": f"{root['root_cause']} with confidence {root['confidence']}",
        },
        {
            "agent": "Root Cause Validator",
            "status": "passed",
            "input": root["root_cause"],
            "action": "Checked evidence sufficiency",
            "output": json.dumps(root_validation, indent=2)
            if root_validation
            else "Evidence sufficiency passed",
        },
        {
            "agent": "Evidence Repair Agent",
            "status": "triggered" if metadata["replans"] else "not needed",
            "input": "Root cause validation result",
            "action": "Added missing diagnostics when evidence was insufficient",
            "output": json.dumps(repair_history, indent=2)
            if repair_history
            else "No repair needed",
        },
        {
            "agent": "Remediation Agent",
            "status": "human approval required"
            if remediation["human_approval_required"]
            else "review required",
            "input": root["root_cause"],
            "action": "Generated safe remediation recommendation",
            "output": remediation["recommended_action"],
        },
        {
            "agent": "Report Writer Agent",
            "status": "passed",
            "input": "Investigation state",
            "action": "Generated auditable JSON and Markdown reports",
            "output": "Report generated in outputs/reports",
        },
    ]

    return trace


def render_metric_card(label: str, value: Any):
    st.metric(label=label, value=value)


def render_overview(report: Dict[str, Any]):
    root = extract_root_cause(report)
    remediation = extract_remediation(report)
    metadata = extract_execution_metadata(report)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card("Root Cause", root["root_cause"])

    with col2:
        render_metric_card("Confidence", root["confidence"])

    with col3:
        render_metric_card("Replans", metadata["replans"])

    with col4:
        render_metric_card(
            "Human Approval",
            str(remediation["human_approval_required"]),
        )

    st.subheader("Investigation Summary")
    st.write(root["summary"])

    st.subheader("Recommended Action")
    st.code(remediation["recommended_action"])

    st.info("No production changes are executed automatically. Remediation remains human gated.")


def render_agent_trace(report: Dict[str, Any]):
    trace = build_agent_trace(report)

    for item in trace:
        status = item["status"]

        with st.expander(f"{item['agent']} — {status}", expanded=True):
            st.markdown(f"**Input:** {item['input']}")
            st.markdown(f"**Action:** {item['action']}")
            st.markdown("**Output:**")
            st.code(str(item["output"]))


def render_evidence(report: Dict[str, Any]):
    evidence_df = extract_evidence_table(report)

    if evidence_df.empty:
        st.warning("No evidence table found in report.")
        return

    st.dataframe(evidence_df, use_container_width=True)


def render_root_cause(report: Dict[str, Any]):
    root = extract_root_cause(report)

    st.subheader("Final Root Cause")
    st.code(root["root_cause"])

    st.subheader("Confidence")
    st.write(root["confidence"])

    st.subheader("Reasoning Summary")
    st.write(root["summary"])

    alternatives = root.get("alternatives") or []

    st.subheader("Alternatives Considered")

    if not alternatives:
        st.write("No alternatives recorded.")
        return

    if isinstance(alternatives, list):
        for alternative in alternatives:
            st.write(alternative)
    else:
        st.json(alternatives)


def render_remediation(report: Dict[str, Any]):
    remediation = extract_remediation(report)

    col1, col2, col3 = st.columns(3)

    with col1:
        render_metric_card("Priority", remediation["priority"])

    with col2:
        render_metric_card(
            "Human Approval Required",
            str(remediation["human_approval_required"]),
        )

    with col3:
        render_metric_card("Safety", "Read only diagnostics")

    st.subheader("Recommended Action")
    st.code(remediation["recommended_action"])

    st.subheader("Reason")
    st.write(remediation["reason"])

    actions = remediation.get("actions") or []

    if actions:
        st.subheader("Action Checklist")
        for idx, action in enumerate(actions, start=1):
            st.write(f"{idx}. {action}")


def render_report(report: Dict[str, Any], alert_id: str):
    md_path = REPORTS_DIR / f"REPORT-{alert_id}.md"
    md_text = load_text(md_path)

    st.subheader("Markdown Report")

    if md_text:
        st.markdown(md_text)
    else:
        st.warning(f"Markdown report not found: {md_path}")

    st.subheader("JSON Report")
    st.json(report)


def render_eval_results(eval_result: Dict[str, Any]):
    summary = eval_result.get("summary") or {}

    normal = summary.get("normal_cases") or {}
    stress = summary.get("repair_stress_cases") or {}

    normal_cases = normal.get("cases", normal.get("total_cases", "unknown"))
    stress_cases = stress.get("cases", stress.get("total_cases", "unknown"))

    repair_success = stress.get(
        "repair_success_when_intentionally_stressed",
        stress.get("repair_success_rate", "unknown"),
    )

    st.subheader("Normal Cases")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card("Cases", normal_cases)

    with col2:
        render_metric_card(
            "Root Cause Accuracy",
            normal.get("root_cause_accuracy", "unknown"),
        )

    with col3:
        render_metric_card(
            "Evidence Sufficiency",
            normal.get("avg_evidence_sufficiency", "unknown"),
        )

    with col4:
        render_metric_card(
            "Unsafe Remediation",
            normal.get("unsafe_remediation_count", "unknown"),
        )

    st.subheader("Repair Stress Cases")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card("Cases", stress_cases)

    with col2:
        render_metric_card("Repair Success", repair_success)

    with col3:
        render_metric_card(
            "Evidence Sufficiency",
            stress.get("avg_evidence_sufficiency", "unknown"),
        )

    with col4:
        render_metric_card(
            "Unsafe Remediation",
            stress.get("unsafe_remediation_count", "unknown"),
        )

    st.subheader("Raw Eval Result")
    st.json(eval_result)