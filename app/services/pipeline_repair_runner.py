from typing import Dict, Tuple

from app.agents.planner_agent import PlannerAgent
from app.agents.root_cause_agent import RootCauseAgent
from app.services.final_report_service import FinalReportService
from app.services.json_data_service import JsonDataService
from app.services.plan_executor_service import PlanExecutorService
from app.services.plan_quality_critic_service import PlanQualityCriticService
from app.services.plan_validator_service import PlanValidatorService
from app.services.remediation_service import RemediationService
from app.services.root_cause_validator_service import RootCauseValidatorService
from app.state.pipeline_state import PipelineState


class PipelineRepairRunner:
    """
    AegisML MVP supervisor/coordinator.

    This orchestrates:
    alert -> planning -> critique -> validation -> execution ->
    root-cause analysis -> root-cause validation -> remediation -> final report.
    """

    def __init__(self) -> None:
        self.data_service = JsonDataService()
        self.planner = PlannerAgent()
        self.plan_critic = PlanQualityCriticService()
        self.plan_validator = PlanValidatorService()
        self.executor = PlanExecutorService(self.data_service)
        self.root_cause_agent = RootCauseAgent()
        self.root_cause_validator = RootCauseValidatorService()
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

        # 1. Generate diagnostic plan
        state.plan = self.planner.generate_plan(alert)

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

        if not root_cause_validation["is_valid"]:
            state.add_warning(
                f"Root cause validation failed: {root_cause_validation['feedback']}"
            )

        # 7. Recommend human-gated remediation
        state.remediation = self.remediation_service.recommend(state.root_cause)

        # 8. Build and save report
        report = self.report_service.build_report(
            state=state,
            plan_quality=plan_quality,
            plan_validation=plan_validation,
            root_cause_validation=root_cause_validation,
        )
        self.report_service.save_report(report)

        return state, report