"""Data models and schemas for EXAMFLOW AI.
Defines types for users, roles, chat interactions, tools, RAG, and examination data.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import uuid
import time

class UserRole(str, Enum):
    CANDIDATE = "candidate"
    EVALUATOR = "evaluator"
    PROCTOR = "proctor"
    EXAM_ADMIN = "exam_admin"
    SUPER_ADMIN = "super_admin"

class PermissionLevel(int, Enum):
    LEVEL_1_DIRECT = 1          # General answers, rule explanation
    LEVEL_2_READ = 2            # Read-only candidate/exam queries
    LEVEL_3_INVESTIGATION = 3   # Multi-step root cause analysis
    LEVEL_4_PREPARE = 4         # Prepare consequential actions
    LEVEL_5_CONSEQUENTIAL = 5   # Consequential execution (requires token & approval)

class CandidateCategory(str, Enum):
    GEN = "GEN"
    OBC_NCL = "OBC_NCL"
    SC = "SC"
    ST = "ST"
    EWS = "EWS"
    PWD = "PWD"

class QualificationStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    NOT_QUALIFIED = "NOT_QUALIFIED"
    DISQUALIFIED = "DISQUALIFIED"
    PENDING_REVIEW = "PENDING_REVIEW"

class AnomalyClassification(str, Enum):
    CONFIRMED_ISSUE = "CONFIRMED_ISSUE"
    POSSIBLE_ANOMALY = "POSSIBLE_ANOMALY"
    RECOMMENDATION = "RECOMMENDATION"
    UNVERIFIED_OBSERVATION = "UNVERIFIED_OBSERVATION"

class PreparationStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

# --- Document & RAG Models ---

class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    doc_name: str
    page_number: int
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_ocr: bool = False

    # Document security ownership
    owner_id: Optional[str] = None
    session_id: Optional[str] = None

class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    total_pages: int
    file_size_bytes: int
    upload_timestamp: float
    is_scanned: bool = False
    unreadable_pages: List[int] = Field(default_factory=list)
    detected_tables: int = 0
    chunks_count: int = 0
    security_flagged: bool = False
    security_notes: Optional[str] = None

    # Document security ownership
    owner_id: Optional[str] = None
    session_id: Optional[str] = None

class DocumentCitation(BaseModel):
    doc_id: str
    doc_name: str
    page_number: int
    snippet: str
    confidence: float = 1.0

# --- Tool Execution Models ---

class ToolCallRequest(BaseModel):
    call_id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:8]}")
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class ToolCallResult(BaseModel):
    call_id: str
    tool_name: str
    status: str  # "success", "error", "denied"
    data: Optional[Union[Dict[str, Any], List[Any]]] = None
    error: Optional[str] = None
    level: PermissionLevel
    verified: bool = False
    verification_notes: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class PreparedAction(BaseModel):
    preparation_id: str = Field(
        default_factory=lambda: f"prep_{uuid.uuid4().hex[:10]}"
    )
    tool_name: str
    arguments: Dict[str, Any]
    summary: str
    target_identifier: str
    consequences: List[str]
    approver_token: str

    status: PreparationStatus = PreparationStatus.PENDING_APPROVAL
    created_at: float = Field(default_factory=time.time)
    expires_at: float
    required_role: UserRole

    # Approval audit information
    approved_by: Optional[str] = None
    approval_role: Optional[UserRole] = None
    approved_at: Optional[float] = None


class ConsequentialConfirmation(BaseModel):
    preparation_id: str
    approver_token: str
    confirmed: bool
    user_id: str
    user_role: UserRole

# --- Examination & Result Models ---

class CandidateScorecard(BaseModel):
    candidate_id: str
    candidate_name: str
    exam_id: str
    shift_id: str
    category: CandidateCategory
    is_pwd: bool = False
    total_questions: int
    attempted_questions: int
    attempt_percentage: float
    raw_score: float
    sectional_scores: Dict[str, float]
    negative_penalties: float
    proctoring_deductions: float
    normalized_score: float
    sectional_cutoffs_cleared: bool
    minimum_attempts_cleared: bool
    proctoring_integrity_score: float
    proctoring_disqualified: bool
    qualification_status: QualificationStatus
    disqualification_reason: Optional[str] = None
    rank: Optional[int] = None
    category_rank: Optional[int] = None
    result_version: str = "v1.0"

class ShiftStatistics(BaseModel):
    exam_id: str
    shift_id: str
    total_registered: int
    total_appeared: int
    mean_raw_score: float
    std_dev_raw_score: float
    min_score: float
    max_score: float
    total_qualified: int
    qualification_rate_percent: float
    sectional_failure_counts: Dict[str, int]
    minimum_attempt_failure_count: int
    proctoring_disqualification_count: int
    is_pooled: bool = False

class AnomalyReport(BaseModel):
    anomaly_id: str = Field(default_factory=lambda: f"anom_{uuid.uuid4().hex[:8]}")
    classification: AnomalyClassification
    title: str
    description: str
    evidence: Dict[str, Any]
    impact: str
    recommended_action: str

class InvestigationPlan(BaseModel):
    objective: str
    planned_steps: List[str]
    tools_to_invoke: List[str]

class InvestigationReport(BaseModel):
    objective: str
    data_examined: List[str]
    findings: List[str]
    evidence: Dict[str, Any]
    uncertainties: List[str]
    recommended_next_steps: List[str]

# --- Chat & API Models ---

class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[ToolCallRequest]] = None
    tool_call_id: Optional[str] = None
    citations: Optional[List[DocumentCitation]] = None
    timestamp: float = Field(default_factory=time.time)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "default_user"
    user_role: UserRole = UserRole.EXAM_ADMIN
    active_exam_id: Optional[str] = "EXAM-2026-GATE"
    active_candidate_id: Optional[str] = None
    attached_doc_ids: Optional[List[str]] = None
    stream: bool = False

class ChatResponse(BaseModel):
    session_id: str
    user_role: UserRole
    plan: Optional[InvestigationPlan] = None
    tool_executions: List[ToolCallResult] = Field(default_factory=list)
    reply: str
    citations: List[DocumentCitation] = Field(default_factory=list)
    anomalies: List[AnomalyReport] = Field(default_factory=list)
    prepared_action: Optional[PreparedAction] = None
    investigation_report: Optional[InvestigationReport] = None
    verified: bool = True
