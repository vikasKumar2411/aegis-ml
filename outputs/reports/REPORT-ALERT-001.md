# AegisML Incident Report: ALERT-001

## Executive Summary
AegisML investigated ALERT-001, a high production ML alert on secure_email_recall. The final root cause is new_secure_email_patterns with confidence 0.95. Remediation requires human approval before production changes.

## Alert Context
- Model: email_identification_model
- Version: v42
- Environment: production
- Metric: secure_email_recall
- Current Value: 0.78
- Baseline Value: 0.91
- Severity: high
- Window: 2026-06-01T00:00:00Z to 2026-06-14T00:00:00Z
- Description: Secure email recall dropped significantly in production.

## Execution Metadata
- Planning Mode: llm
- Root Cause Mode: llm
- Replans: 0
- Max Replans: 2
- Human Approval Required: True
- Automated Remediation Executed: False

## Initial Diagnostic Plan
1. `check_model_performance` on `email_identification_model_v42`
   - Reason: Ruling out model performance degradation as the cause of the drop in secure_email_recall.
2. `analyze_prediction_errors` on `secure_email_classification`
   - Reason: Identifying specific types of prediction errors that may be contributing to the decrease in recall.
3. `check_recent_deployments` on `email_identification_model_v42`
   - Reason: Verifying if any recent deployments introduced regressions affecting model performance.
4. `check_schema_drift` on `input_data_schema`
   - Reason: Ensuring that the input data schema has not changed, which could affect model predictions.
5. `check_feature_drift` on `email_features`
   - Reason: Checking for shifts in feature distribution that might explain changes in model behavior and metric performance.
6. `check_data_quality` on `email_identification_model`
   - Reason: Baseline production ML diagnostic to rule out nulls, malformed records, missing fields, or upstream data-quality issues.

## Final Executed Plan
1. `check_model_performance` on `email_identification_model_v42`
   - Reason: Ruling out model performance degradation as the cause of the drop in secure_email_recall.
2. `analyze_prediction_errors` on `secure_email_classification`
   - Reason: Identifying specific types of prediction errors that may be contributing to the decrease in recall.
3. `check_recent_deployments` on `email_identification_model_v42`
   - Reason: Verifying if any recent deployments introduced regressions affecting model performance.
4. `check_schema_drift` on `input_data_schema`
   - Reason: Ensuring that the input data schema has not changed, which could affect model predictions.
5. `check_feature_drift` on `email_features`
   - Reason: Checking for shifts in feature distribution that might explain changes in model behavior and metric performance.
6. `check_data_quality` on `email_identification_model`
   - Reason: Baseline production ML diagnostic to rule out nulls, malformed records, missing fields, or upstream data-quality issues.

## Evidence Table
| # | Source | Supports | Summary |
|---|--------|----------|---------|
| 1 | model_performance_service | `model_performance_drop` | secure_email_recall dropped from 0.91 to 0.78, a decline of 0.13. |
| 2 | prediction_error_service | `new_secure_email_patterns` | 2 false-negative samples share dominant pattern: new_secure_email_patterns. |
| 3 | deployment_service | `deployment_issue_excluded` | No deployment event appears correlated with the alert window. |
| 4 | schema_drift_service | `schema_drift_excluded` | No schema drift detected; expected and observed fields match. |
| 5 | feature_drift_service | `feature_drift_detected` | Feature drift detected in: secure_phrase_count. |
| 6 | data_quality_service | `data_quality_issue_excluded` | No data-quality issues detected in monitored checks. |

## Validation
- Plan Validation Passed: True
- Root Cause Validation Passed: True

### Validation Failures
- None

## Repair History
- Replans: 0
- No repair events were required.

## Final Root Cause
- Root Cause: `new_secure_email_patterns`
- Confidence: 0.95
- Summary: The drop in secure email recall is directly correlated with the presence of new secure email patterns in false-negative samples.

## Alternatives Considered
- `feature_drift` confidence=0.85: Feature drift was detected, but it did not significantly impact model performance.

## Remediation Recommendation
- recommended_action: retrain_model_with_recent_secure_email_examples
- priority: high
- human_approval_required: True
- reason: False negatives show new secure-email phrasing that the current model does not recognize reliably.
- actions: ['Add recent false-negative secure email examples to the labeling queue.', 'Retrain the email identification model with updated secure-email patterns.', 'Run regression evaluation against existing RFP and secure-email test sets.', 'Add monitoring for secure phrase drift and false-negative rate.', 'Require human approval before production deployment.']

## Safety Notes
- No remediation was executed automatically by AegisML.
- Diagnostic actions are read-only investigation steps.
- Production remediation remains human-gated.
- Human approval is required before rollback, retraining, deployment, or production configuration changes.
