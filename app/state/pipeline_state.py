from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DiagnosticStep(BaseModel):
    """
    A single diagnostic action selected by the planner.
    """

    step_id: int
    action: str
    target: str
    reason: str


class EvidenceItem(BaseModel):
    """
    A structured evidence item produced by a diagnostic service.
    """

    evidence_id: str
    source: str
    finding: str
    supports: str
    confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RootCause(BaseModel):
    """
    Root-cause hypothesis produced after evidence synthesis.
    """

    root_cause: str
    confidence: float
    summary: str
    alternative_causes: List[Dict[str, Any]] = Field(default_factory=list)


class RemediationRecommendation(BaseModel):
    """
    Safe remediation recommendation.
    Production-changing actions should remain human-gated.
    """

    recommended_action: str
    priority: str
    human_approval_required: bool = True
    reason: str
    actions: List[str] = Field(default_factory=list)


class PipelineState(BaseModel):
    """
    Global state for one AegisML investigation run.
    This is the object passed across planner, executor, validators,
    root-cause analysis, and report generation.
    """

    alert_id: str
    model_id: str
    goal: str

    alert: Dict[str, Any] = Field(default_factory=dict)

    plan: List[DiagnosticStep] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)

    root_cause: Optional[RootCause] = None
    remediation: Optional[RemediationRecommendation] = None
    final_report: Optional[Dict[str, Any]] = None

    completed_steps: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    replans: int = 0
    max_replans: int = 2

    def add_evidence(self, item: EvidenceItem) -> None:
        self.evidence.append(item)

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def add_error(self, error: str) -> None:
        self.errors.append(error)

    def mark_step_completed(self, action: str) -> None:
        self.completed_steps.append(action)