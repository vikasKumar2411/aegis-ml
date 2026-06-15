# AegisML — Bounded Autonomous ML Incident Investigation Platform

AegisML is an agentic ML operations system that investigates production model-performance alerts, executes diagnostic tools, validates evidence sufficiency, adaptively repairs incomplete investigations, and generates evidence-backed root-cause reports with human-gated remediation recommendations.

The goal of AegisML is to demonstrate a production-style pattern for safe autonomous AI systems:

> LLMs reason and plan, but deterministic validators, tool guards, evidence checks, and human approval gates control execution.

---

## Why AegisML Exists

Production ML systems fail in many ways:

* Model performance drops
* Feature distributions drift
* Prediction errors shift
* Input schemas change
* Data quality degrades
* Recent deployments introduce regressions
* Multiple causes interact

Traditional monitoring systems can alert when something goes wrong, but they usually do not investigate the incident end to end.

AegisML turns an ML alert into a structured investigation:

```text
Alert
  ↓
Planner Agent
  ↓
Plan Critic + Plan Validator
  ↓
Diagnostic Tool Execution
  ↓
Evidence Store
  ↓
Root-Cause Agent
  ↓
Root-Cause Validator
  ↓
Adaptive Evidence Repair / Replanning
  ↓
Human-Gated Remediation
  ↓
Final Root-Cause Report
```

---

## Current Capabilities

AegisML currently supports:

* Deterministic and LLM-backed investigation modes
* Diagnostic planning from production ML alerts
* Plan critique and validation before execution
* Tool-based diagnostic execution
* Evidence-backed root-cause synthesis
* Root-cause evidence validation
* Adaptive evidence repair and replanning
* Human-gated remediation recommendations
* Auditable JSON reports
* Multi-incident evaluation harness

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
→ deterministic root-cause agent
```

### 2. LLM Root-Cause Mode

```bash
PYTHONPATH=. python scripts/run_alert.py --alert-id ALERT-001 --mode llm-root-cause
```

Uses:

```text
Deterministic planner
→ LLM-backed root-cause agent
```

### 3. Full LLM Mode

```bash
PYTHONPATH=. python scripts/run_alert.py --alert-id ALERT-001 --mode llm
```

Uses:

```text
LLM-backed planner
→ LLM-backed root-cause agent
```

Even in full LLM mode, deterministic validation controls:

* Allowed actions
* Plan quality
* Tool execution
* Evidence sufficiency
* Root-cause acceptance
* Remediation safety

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

Supported local models tested during development:

```text
qwen2.5:7b-instruct
qwen2.5:14b
llama3
```

The LLM client records provider/model metadata in the final report.

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

## Adaptive Evidence Repair

AegisML does not blindly accept an initial root-cause hypothesis.

If root-cause validation detects missing evidence, the system can:

1. Identify the missing evidence
2. Generate follow-up diagnostic steps
3. Validate those steps
4. Execute additional tools
5. Re-run root-cause synthesis
6. Revalidate the final root cause
7. Preserve the full repair trace in the report

Example:

```text
Initial LLM plan:
- check_model_performance
- analyze_prediction_errors
- check_feature_drift
- check_recent_deployments

Root-cause validator detects missing evidence:
- schema_drift_excluded
- data_quality_issue_excluded

Adaptive repair adds:
- check_schema_drift
- check_data_quality

Final root cause is revalidated successfully.
```

---

## Diagnostic Tools

AegisML currently includes deterministic diagnostic services for:

| Diagnostic Service          | Purpose                                    |
| --------------------------- | ------------------------------------------ |
| `model_performance_service` | Confirms production metric degradation     |
| `prediction_error_service`  | Analyzes false positives / false negatives |
| `feature_drift_service`     | Detects feature distribution drift         |
| `deployment_service`        | Checks deployment correlation              |
| `schema_drift_service`      | Detects input schema changes               |
| `data_quality_service`      | Checks upstream data-quality issues        |

---

## Example Run

```bash
PYTHONPATH=. python scripts/run_alert.py --alert-id ALERT-001 --mode llm
```

Example output:

```text
AegisML Investigation Complete
Alert: ALERT-001
Model: email_identification_model
Mode: llm
Replans: 1

Root Cause: new_secure_email_patterns
Confidence: 0.95
Recommended Action: retrain_model_with_recent_secure_email_examples
Human Approval Required: True
```

---

## Report Output

Reports are saved to:

```text
outputs/reports/
```

Example:

```text
outputs/reports/REPORT-ALERT-001.json
```

The report includes:

* Alert metadata
* Execution mode metadata
* Initial diagnostic plan
* Final diagnostic plan
* Plan quality results
* Plan validation results
* Evidence items
* Root-cause hypothesis
* Root-cause validation
* Repair history
* Replan count
* Human-gated remediation recommendation
* Warnings and errors

Example report sections:

```json
{
  "execution_metadata": {
    "investigation_mode": "llm",
    "planning_mode": "llm",
    "root_cause_mode": "llm",
    "replans": 1,
    "max_replans": 2
  },
  "initial_plan": [],
  "final_plan": [],
  "repair_history": []
}
```

---

## Evaluation Harness

AegisML includes a batch evaluation harness for measuring agentic investigation quality.

Run:

```bash
PYTHONPATH=. python scripts/batch_eval_alerts.py --mode llm
```

Evaluation output is saved to:

```text
outputs/eval_results.json
```

Current metrics include:

| Metric                       | Meaning                                                  |
| ---------------------------- | -------------------------------------------------------- |
| `root_cause_accuracy`        | Whether predicted root cause matches expected root cause |
| `avg_required_step_coverage` | Whether required diagnostics were executed               |
| `avg_evidence_sufficiency`   | Whether required evidence was collected                  |
| `replan_success_rate`        | Whether adaptive repair succeeded when expected          |
| `unsafe_remediation_count`   | Number of recommendations that bypassed human approval   |

Example result:

```json
{
  "summary": {
    "total_cases": 1,
    "root_cause_accuracy": 1.0,
    "avg_required_step_coverage": 1.0,
    "avg_evidence_sufficiency": 1.0,
    "replan_success_rate": 1.0,
    "unsafe_remediation_count": 0
  }
}
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
    └── eval_results.json
```

---

## Safety and Guardrails

AegisML is intentionally designed as a bounded autonomous system.

The LLM is allowed to:

* Suggest diagnostic plans
* Synthesize root-cause hypotheses
* Summarize evidence

The LLM is not allowed to:

* Execute arbitrary tools
* Modify production systems
* Deploy models
* Bypass validation
* Approve remediation automatically

All production-changing recommendations require human approval.

---

## Current Status

Completed:

* Adaptive evidence repair
* Deterministic planner/root-cause mode
* LLM-backed root-cause synthesis
* LLM-backed diagnostic planning
* Local Ollama support
* Evidence sufficiency validation
* Human-gated remediation
* Auditable final reports
* Initial evaluation harness

Next planned work:

* Add 5–7 synthetic incident types
* Expand evaluation coverage
* Add API layer with FastAPI
* Add persistence with Postgres
* Add async investigation worker
* Add dashboard for investigation traces and eval results

---

## Target Use Case

AegisML is designed as a prototype for autonomous ML incident investigation in production ML platforms.

Example incidents:

* Recall degradation
* Precision degradation
* Bad model deployment
* Schema drift
* Data-quality regression
* Feature drift
* False alarm
* Mixed-cause incidents

---

## Resume Summary

AegisML demonstrates a bounded autonomous AI system for ML operations:

> Built a supervisor-worker agentic ML incident investigation platform that uses LLM-backed planning and root-cause synthesis, deterministic diagnostic tools, evidence-sufficiency validation, adaptive replanning, human-gated remediation, and an evaluation harness measuring root-cause accuracy, diagnostic coverage, evidence sufficiency, replan success, and unsafe-remediation prevention.
