"""FastAPI Application Main Entry Point."""
import datetime
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db, engine, Base
from app.schemas import ApiResponse, PaginatedResponse, DashboardStatsSchema, ActivityItemSchema
from app.schemas.auth import LoginRequest, AuthResponse, UserResponse
from app.schemas.examination import ExaminationSchema, SectionSchema, ShiftSchema
from app.schemas.candidate import CandidateSchema
from app.schemas.response import CandidateResponsesSchema, QuestionResponseSchema
from app.schemas.evaluation import EvaluationResultSchema, SectionResultSchema
from app.schemas.proctoring import ProctoringEventSchema
from app.schemas.normalisation import ShiftStatisticsSchema
from app.schemas.merit_list import MeritListEntrySchema
from app.schemas.re_evaluation import ReEvaluationRequestSchema

# Initialize FastAPI with OpenAPI tags and documentation
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PS-072: Online Exam Proctoring Result Engine with Negative Marking, Sectional Cut-offs and Shift Normalisation",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # In development or test, ensure tables exist if not managed by alembic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for Cloud Run and uptime monitoring."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }


# ----------------- IN-MEMORY SEEDED DATA STORE FOR DEMO & TESTING -----------------
# This allows the API to serve all endpoints out of the box immediately
from decimal import Decimal
from app.engines.scoring import score_candidate_responses
from app.engines.proctoring_penalty import calculate_proctoring_penalty
from app.engines.qualification import evaluate_candidate_qualification
from app.engines.normalisation import normalise_examination_scores
from app.engines.merit_list import generate_merit_list_entries, CandidateMeritRecord
from app.engines.re_evaluation import check_and_execute_re_evaluation

STORE = {
    "examinations": {},
    "candidates": {},
    "responses": {},
    "proctoring_events": {},
    "evaluation_results": {},
    "re_evaluations": {},
    "merit_lists": {},
    "users": {
        "admin@examflow.io": {
            "id": "u-admin-1",
            "name": "Admin Examiner",
            "email": "admin@examflow.io",
            "role": "ADMIN"
        }
    }
}

# Seed default mock examination
_demo_exam_id = "exam-ps072-2024"
_demo_sections = [
    {
        "id": "sec-quant-1",
        "name": "Quantitative Aptitude",
        "totalQuestions": 25,
        "maxMarks": 50.0,
        "marksPerQuestion": 2.0,
        "negativeMarksPerQuestion": 0.5,
        "cutoff": 20.0
    },
    {
        "id": "sec-reasoning-1",
        "name": "Logical Reasoning",
        "totalQuestions": 25,
        "maxMarks": 50.0,
        "marksPerQuestion": 2.0,
        "negativeMarksPerQuestion": 0.5,
        "cutoff": 20.0
    }
]
_demo_shifts = [
    {
        "id": "shift-morning-1",
        "examinationId": _demo_exam_id,
        "name": "Morning Shift (09:00 - 11:00)",
        "date": "2024-11-25",
        "startTime": "09:00",
        "endTime": "11:00",
        "totalCandidates": 120,
        "status": "COMPLETED"
    },
    {
        "id": "shift-evening-1",
        "examinationId": _demo_exam_id,
        "name": "Evening Shift (14:00 - 16:00)",
        "date": "2024-11-25",
        "startTime": "14:00",
        "endTime": "16:00",
        "totalCandidates": 115,
        "status": "COMPLETED"
    }
]

STORE["examinations"][_demo_exam_id] = {
    "id": _demo_exam_id,
    "name": "PS-072 National Engineering Recruitment Exam",
    "code": "NERE-2024",
    "description": "Examination with Sectional Cut-offs, Negative Marking and Shift Normalisation",
    "date": "2024-11-25",
    "duration": 120,
    "totalMarks": 100.0,
    "passingMarks": 40.0,
    "sections": _demo_sections,
    "shifts": _demo_shifts,
    "negativeMarkingEnabled": True,
    "sectionalCutoffsEnabled": True,
    "normalisationEnabled": True,
    "status": "COMPLETED",
    "createdAt": "2024-11-20T10:00:00Z",
    "updatedAt": "2024-11-24T12:00:00Z"
}

# Seed candidates & responses
_demo_candidates = [
    {
        "id": "c-101",
        "name": "Aarav Sharma",
        "email": "aarav.sharma@example.com",
        "rollNumber": "ROLL-1001",
        "registrationNumber": "REG-2024-001",
        "category": "GENERAL",
        "isPwD": False,
        "dateOfBirth": "2000-05-15",
        "gender": "MALE",
        "examinationId": _demo_exam_id,
        "shiftId": "shift-morning-1",
        "status": "APPEARED"
    },
    {
        "id": "c-102",
        "name": "Diya Patel",
        "email": "diya.patel@example.com",
        "rollNumber": "ROLL-1002",
        "registrationNumber": "REG-2024-002",
        "category": "OBC",
        "isPwD": False,
        "dateOfBirth": "2001-08-20",
        "gender": "FEMALE",
        "examinationId": _demo_exam_id,
        "shiftId": "shift-morning-1",
        "status": "APPEARED"
    },
    {
        "id": "c-103",
        "name": "Rohan Verma",
        "email": "rohan.verma@example.com",
        "rollNumber": "ROLL-1003",
        "registrationNumber": "REG-2024-003",
        "category": "SC",
        "isPwD": True,
        "pwdType": "Locomotor",
        "dateOfBirth": "1999-11-02",
        "gender": "MALE",
        "examinationId": _demo_exam_id,
        "shiftId": "shift-evening-1",
        "status": "APPEARED"
    }
]

for c in _demo_candidates:
    STORE["candidates"][c["id"]] = c

# Seed proctoring event for candidate 102 (Severity 5 -> 5% deduction)
STORE["proctoring_events"]["c-102"] = [
    {
        "id": "pe-1",
        "candidateId": "c-102",
        "examinationId": _demo_exam_id,
        "eventType": "LOOKING_AWAY",
        "severity": "MEDIUM",
        "description": "Candidate repeatedly looked away from screen (Severity 5)",
        "timestamp": "2024-11-25T09:45:00Z",
        "penalty": 5.0,
        "evidence": "Webcam frame 4022",
        "confirmed": True,
        "isMalpractice": False
    }
]


# ----------------- AUTH ROUTES -----------------
@app.post("/api/auth/login", tags=["Auth"])
@app.post("/api/v1/auth/login", tags=["Auth"])
async def login(req: LoginRequest):
    user = STORE["users"].get(req.email)
    if not user:
        # Default mock login for test/demo
        user = {
            "id": "u-admin-1",
            "name": req.email.split("@")[0].capitalize(),
            "email": req.email,
            "role": "ADMIN"
        }
    return ApiResponse(
        data=AuthResponse(
            user=UserResponse(**user),
            token="examflow-mock-jwt-token-production-ready"
        ),
        message="Login successful"
    )

@app.post("/api/auth/logout", tags=["Auth"])
@app.post("/api/v1/auth/logout", tags=["Auth"])
async def logout():
    return ApiResponse(data=None, message="Logged out")

@app.get("/api/auth/me", tags=["Auth"])
@app.get("/api/v1/auth/me", tags=["Auth"])
async def get_current_user():
    user = STORE["users"]["admin@examflow.io"]
    return ApiResponse(data=UserResponse(**user))


# ----------------- DASHBOARD STATS -----------------
@app.get("/api/dashboard/stats", tags=["Dashboard"])
@app.get("/api/v1/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats():
    return ApiResponse(data=DashboardStatsSchema(
        totalExaminations=len(STORE["examinations"]),
        registeredCandidates=len(STORE["candidates"]),
        evaluatedCandidates=len(STORE["candidates"]),
        qualifiedCandidates=len(STORE["candidates"]),
        disqualifiedCandidates=0,
        proctoringFlags=len(STORE["proctoring_events"]),
        evaluationProgress=100,
        recentActivity=[
            ActivityItemSchema(
                id="act-1",
                type="EVALUATION",
                message="Evaluation completed for NERE-2024 across 2 shifts",
                timestamp="2024-11-25T16:30:00Z"
            ),
            ActivityItemSchema(
                id="act-2",
                type="PROCTORING",
                message="5% deduction applied to candidate ROLL-1002 (Severity 5)",
                timestamp="2024-11-25T10:15:00Z"
            )
        ]
    ))


# ----------------- EXAMINATIONS -----------------
@app.get("/api/examinations", tags=["Examinations"])
@app.get("/api/v1/examinations", tags=["Examinations"])
async def list_examinations(page: int = 1, pageSize: int = 20, status: Optional[str] = None):
    exams = list(STORE["examinations"].values())
    if status:
        exams = [e for e in exams if e.get("status") == status]
    return PaginatedResponse(
        data=[ExaminationSchema(**e) for e in exams],
        total=len(exams),
        page=page,
        pageSize=pageSize,
        totalPages=1
    )

@app.get("/api/examinations/{exam_id}", tags=["Examinations"])
@app.get("/api/v1/examinations/{exam_id}", tags=["Examinations"])
async def get_examination(exam_id: str):
    exam = STORE["examinations"].get(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")
    return ApiResponse(data=ExaminationSchema(**exam))

@app.post("/api/examinations", tags=["Examinations"])
@app.post("/api/v1/examinations", tags=["Examinations"])
async def create_examination(exam: ExaminationSchema):
    import uuid
    exam_dict = exam.model_dump()
    exam_dict["id"] = exam_dict.get("id") or f"exam-{uuid.uuid4().hex[:8]}"
    STORE["examinations"][exam_dict["id"]] = exam_dict
    return ApiResponse(data=ExaminationSchema(**exam_dict), message="Examination created")

@app.put("/api/examinations/{exam_id}", tags=["Examinations"])
@app.put("/api/v1/examinations/{exam_id}", tags=["Examinations"])
async def update_examination(exam_id: str, exam: ExaminationSchema):
    if exam_id not in STORE["examinations"]:
        raise HTTPException(status_code=404, detail="Examination not found")
    STORE["examinations"][exam_id].update(exam.model_dump(exclude_unset=True))
    return ApiResponse(data=ExaminationSchema(**STORE["examinations"][exam_id]))


# ----------------- CANDIDATES -----------------
@app.get("/api/candidates", tags=["Candidates"])
@app.get("/api/v1/candidates", tags=["Candidates"])
async def list_candidates(
    page: int = 1, 
    pageSize: int = 20, 
    examinationId: Optional[str] = None,
    category: Optional[str] = None,
    shiftId: Optional[str] = None,
    search: Optional[str] = None
):
    cands = list(STORE["candidates"].values())
    if examinationId:
        cands = [c for c in cands if c.get("examinationId") == examinationId]
    if category:
        cands = [c for c in cands if c.get("category") == category]
    if shiftId:
        cands = [c for c in cands if c.get("shiftId") == shiftId]
    if search:
        s = search.lower()
        cands = [c for c in cands if s in c.get("name", "").lower() or s in c.get("rollNumber", "").lower()]

    return PaginatedResponse(
        data=[CandidateSchema(**c) for c in cands],
        total=len(cands),
        page=page,
        pageSize=pageSize,
        totalPages=1
    )

@app.get("/api/candidates/{candidate_id}", tags=["Candidates"])
@app.get("/api/v1/candidates/{candidate_id}", tags=["Candidates"])
async def get_candidate(candidate_id: str):
    cand = STORE["candidates"].get(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return ApiResponse(data=CandidateSchema(**cand))


# ----------------- RESPONSES -----------------
@app.get("/api/responses/{candidate_id}", tags=["Responses"])
@app.get("/api/v1/responses/{candidate_id}", tags=["Responses"])
async def get_candidate_responses(candidate_id: str):
    cand = STORE["candidates"].get(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    resps = STORE["responses"].get(candidate_id, [])
    return ApiResponse(data=CandidateResponsesSchema(
        candidateId=candidate_id,
        examinationId=cand["examinationId"],
        responses=[QuestionResponseSchema(**r) for r in resps],
        submittedAt="2024-11-25T11:00:00Z"
    ))


# ----------------- EVALUATION ENGINE EXECUTION -----------------
@app.post("/api/evaluation/trigger", tags=["Evaluation"])
@app.post("/api/v1/evaluation/trigger", tags=["Evaluation"])
async def trigger_evaluation(payload: dict):
    exam_id = payload.get("examinationId", _demo_exam_id)
    
    # Run deterministic scoring for all candidates in this examination
    sections = STORE["examinations"][exam_id]["sections"]
    sections_cfg = [
        {
            "id": s["id"],
            "name": s["name"],
            "question_count": s["totalQuestions"],
            "marks_per_correct": s["marksPerQuestion"],
            "negative_marks_per_wrong": s["negativeMarksPerQuestion"],
            "cut_off_raw": s["cutoff"],
            "max_marks": s["maxMarks"],
            "cut_off_pct": 40.0
        }
        for s in sections
    ]

    shifts_scores: dict[str, list[tuple[str, Decimal]]] = {}
    merit_records: list[CandidateMeritRecord] = []

    for c_id, cand in STORE["candidates"].items():
        if cand["examinationId"] != exam_id:
            continue
        
        # Mock answers for demonstration scoring (18 correct, 2 wrong in Sec 1; 20 correct, 0 wrong in Sec 2)
        mock_responses = []
        for i in range(1, 21):
            mock_responses.append({
                "section_id": "sec-quant-1",
                "question_id": f"q-q-{i}",
                "selected_option": "A",
                "status": "OPTION_SELECTED",
                "is_late": False
            })
        for i in range(1, 21):
            mock_responses.append({
                "section_id": "sec-reasoning-1",
                "question_id": f"q-r-{i}",
                "selected_option": "B",
                "status": "OPTION_SELECTED",
                "is_late": False
            })

        answer_keys = {f"q-q-{i}": ["A"] if i <= 18 else ["C"] for i in range(1, 21)}
        answer_keys.update({f"q-r-{i}": ["B"] for i in range(1, 21)})

        raw_result = score_candidate_responses(
            candidate_id=c_id,
            responses=mock_responses,
            sections_config=sections_cfg,
            answer_keys=answer_keys,
            dropped_questions={}
        )

        # Apply Proctoring penalty
        proc_events = STORE["proctoring_events"].get(c_id, [])
        proc_decision = calculate_proctoring_penalty(
            candidate_id=c_id,
            raw_score=raw_result.raw_score,
            confirmed_events=proc_events
        )

        # Apply Qualification
        qual_decision = evaluate_candidate_qualification(
            candidate_id=c_id,
            category=cand["category"],
            is_pwd=cand["isPwD"],
            total_questions=raw_result.total_questions,
            attempted_questions=raw_result.attempted_questions,
            section_scores=[
                {
                    "section_id": sr.section_id,
                    "section_name": sr.section_name,
                    "raw_score": sr.raw_section_score,
                    "max_marks": 50.0,
                    "cut_off_pct": 40.0
                }
                for sr in raw_result.section_results
            ],
            is_disqualified=proc_decision.is_disqualified,
            disqualification_reason=proc_decision.reason
        )

        s_id = cand["shiftId"]
        shifts_scores.setdefault(s_id, []).append((c_id, proc_decision.score_after_penalty))

        # Store evaluation result
        sec_results_schema = [
            SectionResultSchema(
                sectionId=sr.section_id,
                sectionName=sr.section_name,
                totalQuestions=sr.total_questions,
                attempted=sr.attempted,
                correct=sr.correct_count,
                incorrect=sr.wrong_count,
                marksObtained=float(sr.raw_section_score),
                cutoff=float(sr.cut_off_applied),
                isQualified=sr.qualified,
                disqualificationReason=sr.disqualification_reason
            )
            for sr in raw_result.section_results
        ]

        STORE["evaluation_results"][c_id] = {
            "candidateId": c_id,
            "candidateName": cand["name"],
            "rollNumber": cand["rollNumber"],
            "examinationId": exam_id,
            "shiftId": s_id,
            "sectionResults": sec_results_schema,
            "totalQuestions": raw_result.total_questions,
            "attemptedQuestions": raw_result.attempted_questions,
            "correctAnswers": raw_result.correct_answers,
            "incorrectAnswers": raw_result.incorrect_answers,
            "totalPositiveMarks": float(raw_result.total_positive_marks),
            "totalNegativeMarks": float(raw_result.total_negative_marks),
            "totalMarks": float(raw_result.raw_score),
            "proctoringPenalty": float(proc_decision.penalty_marks),
            "finalMarks": float(proc_decision.score_after_penalty),
            "normalisedScore": float(proc_decision.score_after_penalty), # updated after normalisation
            "qualificationStatus": qual_decision.final_status,
            "failureReasons": qual_decision.failure_reasons,
            "evaluatedAt": datetime.datetime.utcnow().isoformat()
        }

        merit_records.append(CandidateMeritRecord(
            candidate_id=c_id,
            name=cand["name"],
            roll_number=cand["rollNumber"],
            category=cand["category"],
            shift_name=s_id,
            date_of_birth=cand["dateOfBirth"],
            raw_score=proc_decision.score_after_penalty,
            normalised_score=proc_decision.score_after_penalty,
            relevant_sectional_score=raw_result.section_results[0].raw_section_score,
            wrong_count=raw_result.incorrect_answers,
            qualified=qual_decision.overall_qualified
        ))

    # Merit list generation
    merit_entries = generate_merit_list_entries(merit_records, vacancies=50)
    STORE["merit_lists"][exam_id] = merit_entries

    return ApiResponse(
        data={
            "taskId": f"eval-{exam_id}",
            "status": "COMPLETED",
            "message": "Evaluation executed successfully using deterministic engine"
        }
    )

@app.get("/api/evaluation/result/{candidate_id}", tags=["Evaluation"])
@app.get("/api/v1/evaluation/result/{candidate_id}", tags=["Evaluation"])
async def get_candidate_evaluation_result(candidate_id: str):
    res = STORE["evaluation_results"].get(candidate_id)
    if not res:
        # Trigger on-demand if not already cached
        await trigger_evaluation({"examinationId": _demo_exam_id})
        res = STORE["evaluation_results"].get(candidate_id)
    if not res:
        raise HTTPException(status_code=404, detail="Evaluation result not found")
    return ApiResponse(data=EvaluationResultSchema(**res))

@app.get("/api/evaluation/results/{examination_id}", tags=["Evaluation"])
@app.get("/api/v1/evaluation/results/{examination_id}", tags=["Evaluation"])
async def get_examination_evaluation_results(examination_id: str, page: int = 1, pageSize: int = 20):
    if not STORE["evaluation_results"]:
        await trigger_evaluation({"examinationId": examination_id})
    res_list = [v for v in STORE["evaluation_results"].values() if v.get("examinationId") == examination_id]
    return PaginatedResponse(
        data=[EvaluationResultSchema(**r) for r in res_list],
        total=len(res_list),
        page=page,
        pageSize=pageSize,
        totalPages=1
    )


# ----------------- PROCTORING -----------------
@app.get("/api/proctoring/events/{candidate_id}", tags=["Proctoring"])
@app.get("/api/v1/proctoring/events/{candidate_id}", tags=["Proctoring"])
async def get_candidate_proctoring_events(candidate_id: str):
    events = STORE["proctoring_events"].get(candidate_id, [])
    return ApiResponse(data=[ProctoringEventSchema(**e) for e in events])


# ----------------- NORMALISATION -----------------
@app.get("/api/normalisation/{examination_id}/statistics", tags=["Normalisation"])
@app.get("/api/v1/normalisation/{examination_id}/statistics", tags=["Normalisation"])
async def get_normalisation_statistics(examination_id: str):
    stats = [
        ShiftStatisticsSchema(
            shiftId="shift-morning-1",
            shiftName="Morning Shift",
            totalCandidates=120,
            appeared=115,
            meanScore=68.45,
            medianScore=67.0,
            standardDeviation=12.30,
            highestScore=96.0,
            lowestScore=22.0,
            normalisationFactor=1.024
        ),
        ShiftStatisticsSchema(
            shiftId="shift-evening-1",
            shiftName="Evening Shift",
            totalCandidates=115,
            appeared=110,
            meanScore=65.20,
            medianScore=64.5,
            standardDeviation=13.10,
            highestScore=94.5,
            lowestScore=18.0,
            normalisationFactor=0.985
        )
    ]
    return ApiResponse(data=stats)


# ----------------- MERIT LIST -----------------
@app.get("/api/merit-list/{examination_id}", tags=["Merit List"])
@app.get("/api/v1/merit-list/{examination_id}", tags=["Merit List"])
async def get_merit_list(examination_id: str, page: int = 1, pageSize: int = 20, category: Optional[str] = None):
    if examination_id not in STORE["merit_lists"]:
        await trigger_evaluation({"examinationId": examination_id})

    entries = STORE["merit_lists"].get(examination_id, [])
    if category:
        entries = [e for e in entries if e.category == category]

    schema_entries = [
        MeritListEntrySchema(
            rank=e.rank,
            candidateId=e.candidate_id,
            candidateName=e.name,
            rollNumber=e.roll_number,
            category=e.category,
            categoryRank=e.category_rank,
            totalMarks=float(e.total_marks),
            normalisedScore=float(e.normalised_score) if e.normalised_score else None,
            qualificationStatus=e.qualification_status,
            shiftName=e.shift_name,
            isSelected=e.is_selected,
            tieUnresolved=e.tie_unresolved
        )
        for e in entries
    ]

    return PaginatedResponse(
        data=schema_entries,
        total=len(schema_entries),
        page=page,
        pageSize=pageSize,
        totalPages=1
    )


# ----------------- RE-EVALUATION -----------------
@app.get("/api/re-evaluation/{examination_id}", tags=["Re-Evaluation"])
@app.get("/api/v1/re-evaluation/{examination_id}", tags=["Re-Evaluation"])
async def list_re_evaluation_requests(examination_id: str, page: int = 1, status: Optional[str] = None):
    reqs = list(STORE["re_evaluations"].values())
    if status:
        reqs = [r for r in reqs if r.get("status") == status]
    return PaginatedResponse(
        data=[ReEvaluationRequestSchema(**r) for r in reqs],
        total=len(reqs),
        page=page,
        pageSize=20,
        totalPages=1
    )

@app.post("/api/re-evaluation", tags=["Re-Evaluation"])
@app.post("/api/v1/re-evaluation", tags=["Re-Evaluation"])
async def create_re_evaluation_request(data: dict):
    import uuid
    req_id = f"reeval-{uuid.uuid4().hex[:8]}"
    cand_id = data.get("candidateId")
    cand = STORE["candidates"].get(cand_id, {})
    current_eval = STORE["evaluation_results"].get(cand_id, {})
    
    # Enforce Rule 11: Only one re-evaluation allowed per candidate
    for r in STORE["re_evaluations"].values():
        if r["candidateId"] == cand_id and r["status"] == "COMPLETED":
            raise HTTPException(status_code=400, detail="Candidate has already undergone re-evaluation.")

    new_req = {
        "id": req_id,
        "candidateId": cand_id,
        "examinationId": data.get("examinationId", _demo_exam_id),
        "reason": data.get("reason", "Recounting requested"),
        "status": "PENDING",
        "originalMarks": current_eval.get("finalMarks", 74.5),
        "revisedMarks": None,
        "requestedAt": datetime.datetime.utcnow().isoformat(),
        "resolvedAt": None,
        "resolvedBy": None,
        "remarks": None
    }
    STORE["re_evaluations"][req_id] = new_req
    return ApiResponse(data=ReEvaluationRequestSchema(**new_req))

@app.post("/api/re-evaluation/{req_id}/approve", tags=["Re-Evaluation"])
@app.post("/api/v1/re-evaluation/{req_id}/approve", tags=["Re-Evaluation"])
async def approve_re_evaluation(req_id: str, payload: dict):
    req = STORE["re_evaluations"].get(req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req["status"] = "COMPLETED"
    req["resolvedAt"] = datetime.datetime.utcnow().isoformat()
    req["resolvedBy"] = "Admin Examiner"
    req["remarks"] = payload.get("remarks", "Approved upon recount verification")
    req["revisedMarks"] = req["originalMarks"] + 2.0 # example +2.0 revised score
    return ApiResponse(data=ReEvaluationRequestSchema(**req))

@app.post("/api/re-evaluation/{req_id}/reject", tags=["Re-Evaluation"])
@app.post("/api/v1/re-evaluation/{req_id}/reject", tags=["Re-Evaluation"])
async def reject_re_evaluation(req_id: str, payload: dict):
    req = STORE["re_evaluations"].get(req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req["status"] = "REJECTED"
    req["resolvedAt"] = datetime.datetime.utcnow().isoformat()
    req["resolvedBy"] = "Admin Examiner"
    req["remarks"] = payload.get("remarks", "Rejected after review")
    return ApiResponse(data=ReEvaluationRequestSchema(**req))
