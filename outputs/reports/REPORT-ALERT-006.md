# AegisML Incident Report: ALERT-006

## Executive Summary
AegisML investigated ALERT-006, a high production ML alert on secure_email_recall. The final root cause is feature_drift with confidence 0.85. Remediation requires human approval before production changes.

## Alert Context
- Model: email_identification_model
- Version: v47
- Environment: production
- Metric: secure_email_recall
- Current Value: 0.71
- Baseline Value: 0.84
- Severity: high
- Window: 2026-06-26T00:00:00Z to 2026-06-29T00:00:00Z
- Description: Secure email recall dropped due to a feature distribution shift in inbound email traffic. No correlated deployment, schema drift, or upstream data-quality degradation is present.

## Execution Metadata
- Planning Mode: llm
- Root Cause Mode: llm
- Replans: 0
- Max Replans: 2
- Human Approval Required: True
- Automated Remediation Executed: False

## Initial Diagnostic Plan
1. `check_model_performance` on `email_identification_model_v47`
   - Reason: Initial check to verify overall model performance metrics have degraded.
2. `analyze_prediction_errors` on `secure_email_recall`
   - Reason: Analyze specific prediction errors related to secure email recall to identify any patterns or anomalies.
3. `check_recent_deployments` on `email_identification_model_v47`
   - Reason: Rule out deployment-related issues that could have caused the drop in secure email recall.
4. `check_schema_drift` on `inbound_email_traffic`
   - Reason: Check for any changes in the schema of inbound email traffic that might affect model performance.
5. `check_feature_drift` on `email_identification_model_v47`
   - Reason: Investigate if there has been a shift in feature distribution that could explain the drop in secure email recall.
6. `check_data_quality` on `email_identification_model`
   - Reason: Baseline production ML diagnostic to rule out nulls, malformed records, missing fields, or upstream data-quality issues.

## Final Executed Plan
1. `check_model_performance` on `email_identification_model_v47`
   - Reason: Initial check to verify overall model performance metrics have degraded.
2. `analyze_prediction_errors` on `secure_email_recall`
   - Reason: Analyze specific prediction errors related to secure email recall to identify any patterns or anomalies.
3. `check_recent_deployments` on `email_identification_model_v47`
   - Reason: Rule out deployment-related issues that could have caused the drop in secure email recall.
4. `check_schema_drift` on `inbound_email_traffic`
   - Reason: Check for any changes in the schema of inbound email traffic that might affect model performance.
5. `check_feature_drift` on `email_identification_model_v47`
   - Reason: Investigate if there has been a shift in feature distribution that could explain the drop in secure email recall.
6. `check_data_quality` on `email_identification_model`
   - Reason: Baseline production ML diagnostic to rule out nulls, malformed records, missing fields, or upstream data-quality issues.

## Evidence Table
| # | Source | Supports | Summary |
|---|--------|----------|---------|
| 1 | model_performance_service | `model_performance_drop` | secure_email_recall dropped from 0.84 to 0.71, a decline of 0.13. |
| 2 | prediction_error_service | `feature_distribution_shift` | 2 false-negative samples share dominant pattern: feature_distribution_shift. |
| 3 | deployment_service | `deployment_issue_excluded` | No deployment event appears correlated with the alert window. |
| 4 | schema_drift_service | `schema_drift_excluded` | No schema drift detected; expected and observed fields match. |
| 5 | feature_drift_service | `feature_drift_detected` | Feature drift detected in: email_body_length, attachment_to_text_ratio. |
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
- Root Cause: `feature_drift`
- Confidence: 0.85
- Summary: The feature drift in email_body_length and attachment_to_text_ratio caused a decline in secure_email_recall, leading to false negatives.

## Alternatives Considered
- `false_alarm` confidence=0.1: No significant model performance drop was observed, and other common causes were excluded.

## Remediation Recommendation
- recommended_action: retrain_or_recalibrate_for_feature_drift
- priority: high
- human_approval_required: True
- reason: Feature drift was validated as the root cause with model-performance degradation while deployment, schema, and data-quality causes were excluded.
- actions: ['Create a drift-focused validation slice for shifted features such as email_body_length and attachment_to_text_ratio.', 'Retrain or recalibrate the model using recent production examples from the shifted traffic window.', 'Evaluate recall, precision, and calibration on both baseline and drifted traffic before release.', 'Deploy only after human approval with staged rollout and post-deployment monitoring.', 'Keep feature-drift monitoring active for the affected features after release.']

## Safety Notes
- No remediation was executed automatically by AegisML.
- Diagnostic actions are read-only investigation steps.
- Production remediation remains human-gated.
- Human approval is required before rollback, retraining, deployment, or production configuration changes.
