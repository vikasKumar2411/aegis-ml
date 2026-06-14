from app.state.pipeline_state import RemediationRecommendation, RootCause


class RemediationService:
    """
    Produces safe remediation recommendations.

    MVP principle:
    Investigation can be autonomous, but production-changing remediation
    remains human-gated.
    """

    def recommend(self, root_cause: RootCause) -> RemediationRecommendation:
        if root_cause.root_cause == "new_secure_email_patterns":
            return RemediationRecommendation(
                recommended_action="retrain_model_with_recent_secure_email_examples",
                priority="high",
                human_approval_required=True,
                reason=(
                    "False negatives show new secure-email phrasing that the current model "
                    "does not recognize reliably."
                ),
                actions=[
                    "Add recent false-negative secure email examples to the labeling queue.",
                    "Retrain the email identification model with updated secure-email patterns.",
                    "Run regression evaluation against existing RFP and secure-email test sets.",
                    "Add monitoring for secure phrase drift and false-negative rate.",
                    "Require human approval before production deployment.",
                ],
            )

        if root_cause.root_cause == "bad_model_deployment":
            return RemediationRecommendation(
                recommended_action="rollback_or_compare_recent_deployment",
                priority="critical",
                human_approval_required=True,
                reason=(
                    "A recent deployment appears correlated with the model-performance drop."
                ),
                actions=[
                    "Compare current model version against previous production version.",
                    "Run rollback candidate evaluation.",
                    "Review deployment diff and pipeline changes.",
                    "Require human approval before rollback.",
                ],
            )

        if root_cause.root_cause == "schema_drift":
            return RemediationRecommendation(
                recommended_action="repair_schema_mapping",
                priority="high",
                human_approval_required=True,
                reason="Input schema drift likely broke model feature construction.",
                actions=[
                    "Identify missing or changed input fields.",
                    "Repair upstream schema mapping.",
                    "Backfill affected prediction logs if needed.",
                    "Run validation before re-enabling automated scoring.",
                ],
            )

        if root_cause.root_cause == "data_quality_issue":
            return RemediationRecommendation(
                recommended_action="repair_upstream_data_quality",
                priority="high",
                human_approval_required=True,
                reason="Upstream data-quality checks indicate degraded input quality.",
                actions=[
                    "Open a data-quality incident with the owning data team.",
                    "Identify affected records and time window.",
                    "Repair or filter corrupted inputs.",
                    "Recompute impacted predictions after validation.",
                ],
            )

        return RemediationRecommendation(
            recommended_action="manual_investigation_required",
            priority="medium",
            human_approval_required=True,
            reason="Root cause is inconclusive or confidence is too low.",
            actions=[
                "Escalate to ML engineer for manual investigation.",
                "Collect additional evidence from logs, prediction samples, and data pipelines.",
                "Avoid production-changing remediation until root cause is validated.",
            ],
        )