# AegisML Incident Report: ALERT-004

## Executive Summary
AegisML investigated ALERT-004, a high production ML alert on secure_email_recall. The final root cause is data_quality_issue with confidence 0.85. Remediation requires human approval before production changes.

## Alert Context
- Model: email_identification_model
- Version: v45
- Environment: production
- Metric: secure_email_recall
- Current Value: 0.76
- Baseline Value: 0.9
- Severity: high
- Window: 2026-06-19T00:00:00Z to 2026-06-22T00:00:00Z
- Description: Secure email recall dropped after upstream data-quality degradation.

## Execution Metadata
- Planning Mode: llm
- Root Cause Mode: llm
- Replans: 1
- Max Replans: 2
- Human Approval Required: True
- Automated Remediation Executed: False

## Initial Diagnostic Plan
1. `check_model_performance` on `email_identification_model_v45`
   - Reason: To verify if the model's performance has degraded since the baseline
2. `analyze_prediction_errors` on `secure_email_recall`
   - Reason: To identify specific instances where predictions failed, focusing on recall
3. `check_feature_drift` on `email_identification_model`
   - Reason: Baseline production ML diagnostic to check whether input distribution shift explains the observed metric or prediction-pattern change.

## Final Executed Plan
1. `check_model_performance` on `email_identification_model_v45`
   - Reason: To verify if the model's performance has degraded since the baseline
2. `analyze_prediction_errors` on `secure_email_recall`
   - Reason: To identify specific instances where predictions failed, focusing on recall
3. `check_feature_drift` on `email_identification_model`
   - Reason: Baseline production ML diagnostic to check whether input distribution shift explains the observed metric or prediction-pattern change.
4. `check_data_quality` on `email_identification_model`
   - Reason: Root-cause validation requires data-quality evidence before accepting the hypothesis.
5. `check_recent_deployments` on `email_identification_model`
   - Reason: Root-cause validation requires deployment evidence before accepting the hypothesis.
6. `check_schema_drift` on `email_identification_model`
   - Reason: Root-cause validation requires schema-drift evidence before accepting the hypothesis.

## Evidence Table
| # | Source | Supports | Summary |
|---|--------|----------|---------|
| 1 | model_performance_service | `model_performance_drop` | secure_email_recall dropped from 0.9 to 0.76, a decline of 0.14. |
| 2 | prediction_error_service | `empty_body_due_to_data_quality` | 2 false-negative samples share dominant pattern: empty_body_due_to_data_quality. |
| 3 | feature_drift_service | `feature_drift_not_detected` | No significant feature drift detected. |
| 4 | data_quality_service | `data_quality_issue_detected` | Data-quality issues detected: null_body_rate. |
| 5 | deployment_service | `deployment_issue_excluded` | No deployment event appears correlated with the alert window. |
| 6 | schema_drift_service | `schema_drift_excluded` | No schema drift detected; expected and observed fields match. |

## Validation
- Plan Validation Passed: True
- Root Cause Validation Passed: True

### Validation Failures
- None

## Repair History
- Replans: 1

### Repair Events
- {'replan_number': 1, 'reason': 'root_cause_validation_failed', 'missing_evidence': ['data_quality_issue_detected', 'deployment_issue_excluded', 'schema_drift_excluded'], 'repair_steps': [{'step_id': 4, 'action': 'check_data_quality', 'target': 'email_identification_model', 'reason': 'Root-cause validation requires data-quality evidence before accepting the hypothesis.'}, {'step_id': 5, 'action': 'check_recent_deployments', 'target': 'email_identification_model', 'reason': 'Root-cause validation requires deployment evidence before accepting the hypothesis.'}, {'step_id': 6, 'action': 'check_schema_drift', 'target': 'email_identification_model', 'reason': 'Root-cause validation requires schema-drift evidence before accepting the hypothesis.'}]}
- {'replan_number': 1, 'reason': 'root_cause_revalidated_after_repair', 'root_cause_validation': {'is_valid': True, 'feedback': [], 'missing_evidence': [], 'evidence_supports': ['data_quality_issue_detected', 'deployment_issue_excluded', 'empty_body_due_to_data_quality', 'feature_drift_not_detected', 'model_performance_drop', 'schema_drift_excluded'], 'confidence': 0.85}}

### Warnings
- Plan quality critique found issues: ['Model-performance degradation plan should include check_recent_deployments.']
- Root cause validation failed: ['Missing positive data-quality issue evidence.', 'Missing deployment exclusion evidence.', 'Missing schema-drift exclusion evidence.']
- Adaptive evidence repair triggered with 3 follow-up step(s).

## Final Root Cause
- Root Cause: `data_quality_issue`
- Confidence: 0.85
- Summary: The drop in secure_email_recall is strongly supported by data-quality issues, specifically null_body_rate.

## Alternatives Considered
- `feature_drift` confidence=0.8: No significant feature drift was detected.
- `bad_model_deployment` confidence=0.85: No deployment event appears correlated with the alert window.

## Remediation Recommendation
- recommended_action: repair_upstream_data_quality
- priority: high
- human_approval_required: True
- reason: Upstream data-quality checks indicate degraded input quality.
- actions: ['Open a data-quality incident with the owning data team.', 'Identify affected records and time window.', 'Repair or filter corrupted inputs.', 'Recompute impacted predictions after validation.']

## Safety Notes
- No remediation was executed automatically by AegisML.
- Diagnostic actions are read-only investigation steps.
- Production remediation remains human-gated.
- Human approval is required before rollback, retraining, deployment, or production configuration changes.
