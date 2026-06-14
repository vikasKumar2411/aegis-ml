from pprint import pprint

from app.agents.planner_agent import PlannerAgent
from app.services.json_data_service import JsonDataService
from app.services.plan_executor_service import PlanExecutorService
from app.services.plan_quality_critic_service import PlanQualityCriticService
from app.services.plan_validator_service import PlanValidatorService
from app.state.pipeline_state import PipelineState


def main() -> None:
    data_service = JsonDataService()
    alert = data_service.get_alert("ALERT-001")

    if not alert:
        raise ValueError("ALERT-001 not found")

    state = PipelineState(
        alert_id=alert["alert_id"],
        model_id=alert["model_id"],
        goal=f"Investigate alert {alert['alert_id']} for model {alert['model_id']}.",
        alert=alert,
    )

    planner = PlannerAgent()
    plan = planner.generate_plan(alert)
    state.plan = plan

    print("\nGenerated Plan:")
    for step in plan:
        pprint(step.model_dump())

    critic = PlanQualityCriticService()
    quality = critic.critique(alert, plan)

    print("\nPlan Quality:")
    pprint(quality)

    validator = PlanValidatorService()
    validation = validator.validate(plan)

    print("\nPlan Validation:")
    pprint(
        {
            "is_valid": validation["is_valid"],
            "approved_step_count": validation["approved_step_count"],
            "rejected_step_count": validation["rejected_step_count"],
            "invalid_reasons": validation["invalid_reasons"],
        }
    )

    executor = PlanExecutorService(data_service)
    state = executor.execute(state, validation["approved_steps"])

    print("\nCompleted Steps:")
    pprint(state.completed_steps)

    print("\nEvidence:")
    for item in state.evidence:
        pprint(item.model_dump())

    print("\nErrors:")
    pprint(state.errors)


if __name__ == "__main__":
    main()