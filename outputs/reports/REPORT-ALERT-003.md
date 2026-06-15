# AegisML Incident Report: ALERT-003

## Executive Summary
AegisML investigated ALERT-003, a high production ML alert on secure_email_recall. The final root cause is schema_drift with confidence 0.9. Remediation requires human approval before production changes.

## Alert Context
- Model: email_identification_model
- Version: v44
- Environment: production
- Metric: secure_email_recall
- Current Value: 0.74
- Baseline Value: 0.9
- Severity: high
- Window: 2026-06-15T00:00:00Z to 2026-06-18T00:00:00Z
- Description: Secure email recall dropped after an upstream input schema change.

## Execution Metadata
- Planning Mode: llm
- Root Cause Mode: llm
- Replans: 0
- Max Replans: 2
- Human Approval Required: True
- Automated Remediation Executed: False

## Initial Diagnostic Plan
1. `check_model_performance` on `email_identification_model_v44`
   - Reason: To verify if the model's overall performance has degraded.
2. `analyze_prediction_errors` on `secure_email_recall`
   - Reason: To identify specific types of errors that may be contributing to the drop in recall.
3. `check_recent_deployments` on `email_identification_model_v44`
   - Reason: To rule out any recent changes or issues during deployment.
4. `check_schema_drift` on `input schema for email_identification_model_v44`
   - Reason: To confirm if the input data schema has changed, which could affect model performance.
5. `check_data_quality` on `upstream data source for email_identification_model_v44`
   - Reason: To ensure that the upstream data quality is not compromised and causing issues.
6. `check_feature_drift` on `email_identification_model`
   - Reason: Baseline production ML diagnostic to check whether input distribution shift explains the observed metric or prediction-pattern change.

## Final Executed Plan
1. `check_model_performance` on `email_identification_model_v44`
   - Reason: To verify if the model's overall performance has degraded.
2. `analyze_prediction_errors` on `secure_email_recall`
   - Reason: To identify specific types of errors that may be contributing to the drop in recall.
3. `check_recent_deployments` on `email_identification_model_v44`
   - Reason: To rule out any recent changes or issues during deployment.
4. `check_schema_drift` on `input schema for email_identification_model_v44`
   - Reason: To confirm if the input data schema has changed, which could affect model performance.
5. `check_data_quality` on `upstream data source for email_identification_model_v44`
   - Reason: To ensure that the upstream data quality is not compromised and causing issues.
6. `check_feature_drift` on `email_identification_model`
   - Reason: Baseline production ML diagnostic to check whether input distribution shift explains the observed metric or prediction-pattern change.

## Evidence Table
| # | Source | Supports | Summary |
|---|--------|----------|---------|
| 1 | model_performance_service | `model_performance_drop` | secure_email_recall dropped from 0.9 to 0.74, a decline of 0.16. |
| 2 | prediction_error_service | `missing_body_field` | 2 false-negative samples share dominant pattern: missing_body_field. |
| 3 | deployment_service | `deployment_issue_excluded` | No deployment event appears correlated with the alert window. |
| 4 | schema_drift_service | `schema_drift_detected` | Schema drift detected. Missing fields: ['body']. Extra fields: ['message_body']. |
| 5 | data_quality_service | `data_quality_issue_excluded` | No data-quality issues detected in monitored checks. |
| 6 | feature_drift_service | `feature_drift_not_detected` | No significant feature drift detected. |

## Validation
- Plan Validation Passed: True
- Root Cause Validation Passed: True

### Validation Failures
- None

## Repair History
- Replans: 0
- No repair events were required.

## Final Root Cause
- Root Cause: `schema_drift`
- Confidence: 0.9
- Summary: The evidence points to schema drift as the root cause, specifically missing the 'body' field which correlates with the decline in secure_email_recall and the presence of false negatives.

## Alternatives Considered
- `new_secure_email_patterns` confidence=0.1: While there are false negatives, the specific pattern 'missing_body_field' is not indicative of new secure email patterns.
- `bad_model_deployment` confidence=0.05: No correlated deployment events were found during the alert window.

## Remediation Recommendation
- recommended_action: repair_schema_mapping
- priority: high
- human_approval_required: True
- reason: Input schema drift likely broke model feature construction.
- actions: ['Identify missing or changed input fields.', 'Repair upstream schema mapping.', 'Backfill affected prediction logs if needed.', 'Run validation before re-enabling automated scoring.']

## Safety Notes
- No remediation was executed automatically by AegisML.
- Diagnostic actions are read-only investigation steps.
- Production remediation remains human-gated.
- Human approval is required before rollback, retraining, deployment, or production configuration changes.
