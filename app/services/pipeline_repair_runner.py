from typing import Dict, Tuple

from app.agents.llm_planner_agent import LLMPlannerAgent
from app.agents.llm_root_cause_agent import LLMRootCauseAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.root_cause_agent import RootCauseAgent
from app.services.final_report_service import FinalReportService
from app.services.json_data_service import JsonDataService
from app.services.plan_executor_service import PlanExecutorService
from app.services.plan_quality_critic_service import PlanQualityCriticService
from app.services.plan_validator_service import PlanValidatorService
from app.services.remediation_service import RemediationService
from app.services.root_cause_evidence_repair_service import (
    RootCauseEvidenceRepairService,
)
from app.services.root_cause_validator_service import RootCauseValidatorService
from app.state.pipeline_state import PipelineState


class PipelineRepairRunner:
    """
    AegisML MVP supervisor/coordinator.

    This orchestrates:
    alert -> planning -> critique -> validation -> execution ->
    root-cause analysis -> root-cause validation -> adaptive evidence repair ->
    remediation -> final report.
    """

    def __init__(
        self,
        simulate_incomplete_plan: bool = False,
        mode: str = "deterministic",
    ) -> None:
        self.mode = mode

        self.data_service = JsonDataService()

        if mode == "llm":
            self.planner = LLMPlannerAgent(
                simulate_incomplete_plan=simulate_incomplete_plan
            )
        else:
            self.planner = PlannerAgent(
                simulate_incomplete_plan=simulate_incomplete_plan
            )

        self.plan_critic = PlanQualityCriticService()
        self.plan_validator = PlanValidatorService()
        self.executor = PlanExecutorService(self.data_service)

        if mode in {"llm", "llm-root-cause"}:
            self.root_cause_agent = LLMRootCauseAgent()
        else:
            self.root_cause_agent = RootCauseAgent()

        self.root_cause_validator = RootCauseValidatorService()
        self.evidence_repair_service = RootCauseEvidenceRepairService()
        self.remediation_service = RemediationService()
        self.report_service = FinalReportService()

    def run(self, alert_id: str) -> Tuple[PipelineState, Dict]:
        alert = self.data_service.get_alert(alert_id)

        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")

        state = PipelineState(
            alert_id=alert["alert_id"],
            model_id=alert["model_id"],
            goal=(
                f"Investigate production ML alert {alert['alert_id']} for "
                f"model {alert['model_id']} and produce an evidence-backed "
                "root-cause report with safe remediation recommendations."
            ),
            alert=alert,
        )

        state.alert["investigation_mode"] = self.mode

        if self.mode == "llm":
            state.planning_mode = "llm"
            state.root_cause_mode = "llm"
        elif self.mode == "llm-root-cause":
            state.planning_mode = "deterministic"
            state.root_cause_mode = "llm"
        else:
            state.planning_mode = "deterministic"
            state.root_cause_mode = "deterministic"

        if self.mode == "llm":
            state.planning_mode = "llm"
            state.root_cause_mode = "llm"
        elif self.mode == "llm-root-cause":
            state.planning_mode = "deterministic"
            state.root_cause_mode = "llm"
        else:
            state.planning_mode = "deterministic"
            state.root_cause_mode = "deterministic"

        # 1. Generate diagnostic plan
        state.plan = self.planner.generate_plan(alert)
        state.initial_plan = list(state.plan)

        # 2. Critique plan quality
        plan_quality = self.plan_critic.critique(alert, state.plan)
        if not plan_quality["is_sufficient"]:
            state.add_warning(
                f"Plan quality critique found issues: {plan_quality['feedback']}"
            )

        # 3. Validate plan executability
        plan_validation = self.plan_validator.validate(state.plan)
        if not plan_validation["is_valid"]:
            state.add_warning(
                f"Plan validation failed: {plan_validation['invalid_reasons']}"
            )

        # 4. Execute approved diagnostic steps
        state = self.executor.execute(state, plan_validation["approved_steps"])

        # 5. Infer root cause
        state.root_cause = self.root_cause_agent.infer(state.evidence)

        # 6. Validate root cause evidence
        root_cause_validation = self.root_cause_validator.validate(
            state.root_cause,
            state.evidence,
        )

        # 7. Adaptive evidence repair if validation fails
        if not root_cause_validation["is_valid"]:
            state.add_warning(
                f"Root cause validation failed: {root_cause_validation['feedback']}"
            )

            repair_steps = self.evidence_repair_service.build_repair_plan(
                state=state,
                root_cause_validation=root_cause_validation,
            )

            if repair_steps and state.replans < state.max_replans:
                state.replans += 1

                state.add_repair_record(
                    {
                        "replan_number": state.replans,
                        "reason": "root_cause_validation_failed",
                        "missing_evidence": root_cause_validation.get(
                            "missing_evidence", []
                        ),
                        "repair_steps": [
                            step.model_dump() for step in repair_steps
                        ],
                    }
                )

                state.add_warning(
                    f"Adaptive evidence repair triggered with {len(repair_steps)} follow-up step(s)."
                )

                # Add follow-up repair steps to the global plan trace.
                state.plan.extend(repair_steps)

                repair_validation = self.plan_validator.validate(repair_steps)

                if not repair_validation["is_valid"]:
                    state.add_warning(
                        f"Repair plan validation failed: {repair_validation['invalid_reasons']}"
                    )
                else:
                    state = self.executor.execute(
                        state,
                        repair_validation["approved_steps"],
                    )

                    # Re-run root-cause inference and validation after repair evidence.
                    state.root_cause = self.root_cause_agent.infer(state.evidence)

                    root_cause_validation = self.root_cause_validator.validate(
                        state.root_cause,
                        state.evidence,
                    )

                    state.add_repair_record(
                        {
                            "replan_number": state.replans,
                            "reason": "root_cause_revalidated_after_repair",
                            "root_cause_validation": root_cause_validation,
                        }
                    )
            else:
                state.add_warning(
                    "Root cause evidence repair was not executed because no repair steps were available or max replans was reached."
                )

        # 8. Recommend human-gated remediation
        state.remediation = self.remediation_service.recommend(state.root_cause)

        state.status = "completed"

        # 9. Build and save report
        report = self.report_service.build_report(
            state=state,
            plan_quality=plan_quality,
            plan_validation=plan_validation,
            root_cause_validation=root_cause_validation,
        )
        self.report_service.save_report(report)

        return state, report