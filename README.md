# AegisML — Bounded Autonomous ML Incident Investigation Platform

AegisML is a bounded autonomous ML operations system that investigates production model performance alerts, creates diagnostic plans, executes read only investigation tools, validates evidence sufficiency, adaptively repairs incomplete investigations, identifies root cause, recommends human gated remediation, and generates auditable incident reports.

The core design principle is simple:

> LLMs can reason, plan, and synthesize, but deterministic validators, tool guards, evidence checks, and human approval gates control execution.

AegisML is built to demonstrate a production style pattern for safe agentic AI systems in ML operations.

---

## Why AegisML Exists

Production ML systems fail in many ways:

* Model performance drops
* Feature distributions drift
* Prediction error patterns shift
* Input schemas change
* Data quality degrades
* Recent deployments introduce regressions
* Monitoring alerts fire without a true incident

Traditional monitoring systems can alert when something goes wrong, but they usually do not investigate the incident end to end.

AegisML turns an ML alert into a structured autonomous investigation:

```text
Alert
  ↓
Planner Agent
  ↓
Plan Critic and Plan Validator
  ↓
Diagnostic Tool Execution
  ↓
Evidence Store
  ↓
Root Cause Agent
  ↓
Root Cause Validator
  ↓
Adaptive Evidence Repair
  ↓
Human Gated Remediation
  ↓
Final Incident Report
```

---

## What AegisML Does

AegisML converts production ML alerts into evidence backed incident reports.

Current capabilities include:

* Deterministic and LLM backed investigation modes
* Diagnostic planning from production ML alerts
* Deterministic baseline completion for LLM generated plans
* Plan critique and validation before execution
* Tool based diagnostic execution
* Evidence backed root cause synthesis
* Root cause evidence sufficiency validation
* Adaptive evidence repair and replanning
* Human gated remediation recommendations
* Auditable JSON and Markdown reports
* Batch evaluation harness with normal and repair stress cases

---

## Supported Incident Types

AegisML currently supports six normal ML incident categories:

| Alert       | Root Cause                  | Description                                                          |
| ----------- | --------------------------- | -------------------------------------------------------------------- |
| `ALERT-001` | `new_secure_email_patterns` | Recall degradation caused by new secure email language patterns      |
| `ALERT-002` | `bad_model_deployment`      | Precision degradation caused by a correlated model deployment        |
| `ALERT-003` | `schema_drift`              | Recall degradation caused by upstream input schema drift             |
| `ALERT-004` | `data_quality_issue`        | Recall degradation caused by upstream data quality degradation       |
| `ALERT-005` | `false_alarm`               | Low severity alert with no significant model performance degradation |
| `ALERT-006` | `feature_drift`             | Recall degradation caused by feature distribution shift              |

AegisML also includes repair stress cases that intentionally create incomplete investigations to verify that the validator and repair loop recover missing diagnostics.

---

## Reasoning Modes

AegisML supports three execution modes.

### 1. Deterministic Mode

```bash
PYTHONPATH=. python scripts/run_alert.py --alert-id ALERT-001 --mode deterministic
```

Uses:

```text
Deterministic planner
→ deterministic root cause agent
```

### 2. LLM Root Cause Mode

```bash
PYTHONPATH=. python scripts/run_alert.py --alert-id ALERT-001 --mode llm-root-cause
```

Uses:

```text
Deterministic planner
→ LLM backed root cause agent
```

### 3. Full LLM Mode

```bash
PYTHONPATH=. python scripts/run_alert.py --alert-id ALERT-001 --mode llm
```

Uses:

```text
LLM backed planner
→ deterministic baseline completion
→ LLM backed root cause agent
```

Even in full LLM mode, deterministic services control:

* Allowed actions
* Plan quality
* Plan validation
* Tool execution
* Evidence sufficiency
* Root cause acceptance
* Repair planning
* Remediation safety

The LLM proposes and synthesizes. Deterministic guardrails decide what is allowed, what evidence is sufficient, and whether remediation remains safe.

---

## Local LLM Support

AegisML supports local LLM execution through Ollama.

Example setup:

```bash
ollama serve
```

```bash
export AEGIS_LLM_PROVIDER=ollama
export AEGIS_LLM_MODEL=qwen2.5:7b-instruct
```

Models tested during development:

```text
qwen2.5:7b-instruct
qwen2.5:14b
llama3
```

The LLM client records provider and model metadata in the final report.

Example report metadata:

```json
{
  "reasoning_mode": "llm",
  "llm_provider": "ollama",
  "llm_model": "qwen2.5:7b-instruct",
  "used_fallback": false,
  "llm_warning": null
}
```

---

## Diagnostic Tools

AegisML includes deterministic diagnostic services for common ML production failure modes.

| Diagnostic Service          | Purpose                                      |
| --------------------------- | -------------------------------------------- |
| `model_performance_service` | Confirms production metric degradation       |
| `prediction_error_service`  | Analyzes false positives and false negatives |
| `feature_drift_service`     | Detects feature distribution drift           |
| `deployment_service`        | Checks deployment correlation                |
| `schema_drift_service`      | Detects input schema changes                 |
| `data_quality_service`      | Checks upstream data quality issues          |

The system reasons over structured evidence, not raw LLM guesses.

Example evidence labels include:

```text
model_performance_drop
no_significant_model_performance_drop
new_secure_email_patterns
bad_model_deployment_possible
schema_drift_detected
schema_drift_excluded
data_quality_issue_detected
data_quality_issue_excluded
deployment_issue_excluded
feature_drift_detected
feature_drift_not_detected
feature_distribution_shift
```

---

## Adaptive Evidence Repair

AegisML does not blindly accept an initial root cause hypothesis.

If root cause validation detects missing evidence, the system can:

1. Identify the missing evidence
2. Generate follow up diagnostic steps
3. Validate those steps
4. Execute additional tools
5. Re run root cause synthesis
6. Revalidate the final root cause
7. Preserve the full repair trace in the report

Example:

```text
Initial LLM plan:
- check_model_performance
- analyze_prediction_errors
- check_feature_drift

Root cause validator detects missing evidence:
- deployment_issue_excluded
- schema_drift_excluded
- data_quality_issue_excluded

Adaptive repair adds:
- check_recent_deployments
- check_schema_drift
- check_data_quality

Final root cause is revalidated successfully.
```

This makes the system self correcting within bounded rules.

---

## Human Gated Remediation

AegisML can recommend remediation, but it does not modify production systems automatically.

Examples:

| Root Cause                  | Recommended Action                                     |
| --------------------------- | ------------------------------------------------------ |
| `new_secure_email_patterns` | Retrain model with recent secure email examples        |
| `bad_model_deployment`      | Roll back or compare recent deployment                 |
| `schema_drift`              | Repair schema mapping                                  |
| `data_quality_issue`        | Repair upstream data quality                           |
| `feature_drift`             | Retrain or recalibrate for feature drift               |
| `false_alarm`               | Continue monitoring with no production changing action |

Every remediation recommendation includes:

```text
human_approval_required = true
```

AegisML is autonomous in investigation, not autonomous in production modification.

---

## Example Run

```bash
PYTHONPATH=. python scripts/run_alert.py --alert-id ALERT-006 --mode llm
```

Example result:

```text
AegisML Investigation Complete
Alert: ALERT-006
Model: email_identification_model
Mode: llm
Replans: 0

Root Cause: feature_drift
Confidence: 0.85
Recommended Action: retrain_or_recalibrate_for_feature_drift
Human Approval Required: True
```

---

## Report Output

Reports are saved to:

```text
outputs/reports/
```

Each investigation produces both JSON and Markdown reports.

Example files:

```text
outputs/reports/REPORT-ALERT-006.json
outputs/reports/REPORT-ALERT-006.md
```

Reports include:

* Executive summary
* Alert context
* Execution metadata
* Initial diagnostic plan
* Final executed plan
* Evidence table
* Plan validation results
* Root cause validation results
* Repair history
* Final root cause
* Alternatives considered
* Human gated remediation recommendation
* Safety notes
* Warnings and errors

Example report summary:

```text
AegisML investigated ALERT-006, a high production ML alert on secure_email_recall.
The final root cause is feature_drift with confidence 0.85.
Remediation requires human approval before production changes.
```

Example evidence table:

```text
model_performance_drop
feature_distribution_shift
deployment_issue_excluded
schema_drift_excluded
feature_drift_detected
data_quality_issue_excluded
```

---

## Evaluation Harness

AegisML includes a batch evaluation harness for measuring agentic investigation quality.

Run deterministic evaluation:

```bash
PYTHONPATH=. python scripts/batch_eval_alerts.py \
  --mode deterministic \
  --output outputs/eval_results_deterministic.json
```

Run LLM evaluation:

```bash
PYTHONPATH=. python scripts/batch_eval_alerts.py \
  --mode llm \
  --output outputs/eval_results_llm.json
```

The evaluation suite separates normal correctness from repair stress testing.

### Normal Cases

Normal cases measure whether the system can investigate standard ML incidents without unnecessary repair.

Metrics:

| Metric                       | Meaning                                                  |
| ---------------------------- | -------------------------------------------------------- |
| `root_cause_accuracy`        | Whether predicted root cause matches expected root cause |
| `avg_required_step_coverage` | Whether required diagnostics were executed               |
| `avg_evidence_sufficiency`   | Whether required evidence was collected                  |
| `unnecessary_replan_rate`    | Whether repair was triggered when it should not be       |
| `unsafe_remediation_count`   | Number of recommendations that bypassed human approval   |

### Repair Stress Cases

Repair stress cases intentionally create incomplete investigations.

Metrics:

| Metric                                       | Meaning                                                          |
| -------------------------------------------- | ---------------------------------------------------------------- |
| `repair_success_when_intentionally_stressed` | Whether the validator and repair loop recovered missing evidence |
| `root_cause_accuracy`                        | Whether final root cause is correct after repair                 |
| `avg_evidence_sufficiency`                   | Whether required evidence was eventually collected               |
| `unsafe_remediation_count`                   | Number of unsafe remediation recommendations                     |

---

## Current Evaluation Results

Current deterministic results:

```text
Mode: deterministic
Total cases: 8

Normal cases
Cases: 6
Root-cause accuracy: 1.0
Required diagnostic coverage: 1.0
Evidence sufficiency: 1.0
Unnecessary replan rate: 0.0
Unsafe remediation count: 0

Repair stress cases
Cases: 2
Root-cause accuracy: 1.0
Required diagnostic coverage: 1.0
Evidence sufficiency: 1.0
Repair success when intentionally stressed: 1.0
Unsafe remediation count: 0
```

Current LLM results:

```text
Mode: llm
Total cases: 8

Normal cases
Cases: 6
Root-cause accuracy: 1.0
Required diagnostic coverage: 1.0
Evidence sufficiency: 1.0
Unnecessary replan rate: 0.0
Unsafe remediation count: 0

Repair stress cases
Cases: 2
Root-cause accuracy: 1.0
Required diagnostic coverage: 1.0
Evidence sufficiency: 1.0
Repair success when intentionally stressed: 1.0
Unsafe remediation count: 0
```

---

## Project Structure

```text
aegis-ml/
├── app/
│   ├── agents/
│   │   ├── planner_agent.py
│   │   ├── llm_planner_agent.py
│   │   ├── root_cause_agent.py
│   │   └── llm_root_cause_agent.py
│   ├── services/
│   │   ├── llm_client.py
│   │   ├── plan_validator_service.py
│   │   ├── plan_quality_critic_service.py
│   │   ├── plan_executor_service.py
│   │   ├── root_cause_validator_service.py
│   │   ├── root_cause_evidence_repair_service.py
│   │   ├── remediation_service.py
│   │   └── final_report_service.py
│   └── state/
│       └── pipeline_state.py
├── data/
│   ├── alerts.json
│   ├── eval_cases.json
│   ├── model_metrics.json
│   ├── prediction_samples.json
│   ├── feature_drift_results.json
│   ├── deployment_events.json
│   ├── schema_profiles.json
│   └── data_quality_results.json
├── scripts/
│   ├── run_alert.py
│   └── batch_eval_alerts.py
└── outputs/
    ├── reports/
    ├── eval_results_deterministic.json
    └── eval_results_llm.json
```

---

## Safety and Guardrails

AegisML is intentionally designed as a bounded autonomous system.

The LLM is allowed to:

* Suggest diagnostic plans
* Synthesize root cause hypotheses
* Summarize evidence

The LLM is not allowed to:

* Execute arbitrary tools
* Modify production systems
* Deploy models
* Bypass validation
* Approve remediation automatically

Deterministic guardrails enforce:

* Allowed diagnostic actions
* Required diagnostic baselines
* Plan validation
* Evidence sufficiency
* Root cause taxonomy normalization
* Repair step validation
* Human approval for remediation

---

## Current Status

Completed:

* Deterministic planner and root cause mode
* LLM backed root cause synthesis
* LLM backed diagnostic planning
* Deterministic baseline completion for LLM plans
* Local Ollama support
* Six incident categories
* Two repair stress tests
* Evidence sufficiency validation
* Adaptive evidence repair
* Human gated remediation
* Feature drift remediation path
* JSON and Markdown incident reports
* Split evaluation harness for normal and repair stress cases

Next planned work:

* Add FastAPI investigation endpoint
* Add persistence with Postgres
* Add async investigation worker
* Add dashboard for investigation traces and eval results
* Add mixed cause incident scenarios
* Add CI workflow for eval regression testing

---

## Target Use Case

AegisML is a prototype for autonomous ML incident investigation in production ML platforms.

Example incidents:

* Recall degradation
* Precision degradation
* Bad model deployment
* Schema drift
* Data quality regression
* Feature drift
* New pattern emergence
* False alarm
* Mixed cause incidents

---

## Resume Summary

AegisML demonstrates a bounded autonomous AI system for ML operations:

> Built a bounded autonomous ML incident investigation platform that uses LLM backed planning and root cause synthesis, deterministic diagnostic tools, evidence sufficiency validation, adaptive repair, human gated remediation, and an evaluation harness measuring root cause accuracy, diagnostic coverage, evidence sufficiency, repair success, unnecessary replan rate, and unsafe remediation prevention.


