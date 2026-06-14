import argparse
from pprint import pprint

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.services.pipeline_repair_runner import PipelineRepairRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AegisML investigation.")
    parser.add_argument("--alert-id", required=True, help="Alert ID to investigate.")
    args = parser.parse_args()

    console = Console()

    runner = PipelineRepairRunner()
    state, report = runner.run(args.alert_id)

    console.print(
        Panel.fit(
            f"[bold]AegisML Investigation Complete[/bold]\n"
            f"Alert: {state.alert_id}\n"
            f"Model: {state.model_id}",
            title="AegisML",
        )
    )

    plan_table = Table(title="Diagnostic Plan")
    plan_table.add_column("Step", style="cyan")
    plan_table.add_column("Action", style="green")
    plan_table.add_column("Reason")

    for step in state.plan:
        plan_table.add_row(str(step.step_id), step.action, step.reason)

    console.print(plan_table)

    evidence_table = Table(title="Evidence")
    evidence_table.add_column("Source", style="cyan")
    evidence_table.add_column("Supports", style="green")
    evidence_table.add_column("Confidence")
    evidence_table.add_column("Finding")

    for item in state.evidence:
        evidence_table.add_row(
            item.source,
            item.supports,
            f"{item.confidence:.2f}",
            item.finding,
        )

    console.print(evidence_table)

    if state.root_cause:
        console.print(
            Panel.fit(
                f"[bold]Root Cause:[/bold] {state.root_cause.root_cause}\n"
                f"[bold]Confidence:[/bold] {state.root_cause.confidence:.2f}\n\n"
                f"{state.root_cause.summary}",
                title="Root Cause",
            )
        )

    if state.remediation:
        console.print(
            Panel.fit(
                f"[bold]Recommended Action:[/bold] {state.remediation.recommended_action}\n"
                f"[bold]Priority:[/bold] {state.remediation.priority}\n"
                f"[bold]Human Approval Required:[/bold] {state.remediation.human_approval_required}\n\n"
                f"{state.remediation.reason}",
                title="Remediation",
            )
        )

    console.print("\n[bold]Report saved:[/bold]")
    console.print(f"outputs/reports/{report['report_id']}.json")

    if state.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        pprint(state.warnings)

    if state.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        pprint(state.errors)


if __name__ == "__main__":
    main()