"""Tool Registry for EXAMFLOW AI.
Houses schemas, argument validation, role-permission verification, and execution handlers
for all 14 Read-Only, 4 Prepared-Action, and 3 Consequential tools.
"""

import time
from typing import Dict, Any, List, Optional
from app.models import ToolCallResult, PermissionLevel, UserRole, ToolCallRequest
from app.permissions import permission_manager, TOOL_PERMISSIONS
from app.services.exam_backend import exam_backend
from app.retrieval.rag_engine import rag_engine

class ToolRegistry:
    """Central registry and execution dispatch for all agent tools."""

    def __init__(self):
        self.tools_schema = self._build_schemas()

    def get_schemas_for_role(self, role: UserRole) -> List[Dict[str, Any]]:
        """Returns only the tool schemas that the user's role is authorized to access."""
        authorized_schemas = []
        for name, meta in TOOL_PERMISSIONS.items():
            if role in meta["allowed_roles"]:
                if name in self.tools_schema:
                    authorized_schemas.append(self.tools_schema[name])
        return authorized_schemas

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_role: UserRole,
        user_id: str,
        call_id: Optional[str] = None
    ) -> ToolCallResult:
        """Executes a tool call after strict argument and RBAC authorization verification."""
        start_time = time.time()
        c_id = call_id or f"call_{tool_name}"

        # 1. Permission check
        allowed, reason = permission_manager.check_tool_permission(tool_name, user_role, user_id, arguments)
        if not allowed:
            return ToolCallResult(
                call_id=c_id,
                tool_name=tool_name,
                status="denied",
                data=None,
                error=reason,
                level=TOOL_PERMISSIONS.get(tool_name, {}).get("level", PermissionLevel.LEVEL_1_DIRECT),
                verified=False,
                timestamp=time.time()
            )

        level = TOOL_PERMISSIONS[tool_name]["level"]

        # 2. Execution dispatch
        try:
            res_data: Any = None
            verification_note = "Authoritative engine data retrieved."

            # Read-Only Tools (Level 2)
            if tool_name == "get_exam_details":
                res_data = exam_backend.get_exam_details(arguments.get("exam_id", "EXAM-2026-GATE"))
            elif tool_name == "get_candidate_details":
                res_data = exam_backend.get_candidate_details(arguments["candidate_id"], arguments.get("exam_id"))
            elif tool_name == "get_candidate_scorecard":
                res_data = exam_backend.get_candidate_scorecard(arguments["candidate_id"], arguments.get("exam_id"))
                verification_note = f"Scorecard verified against authoritative result ledger (Version {res_data['result_version']})."
            elif tool_name == "get_candidate_responses":
                res_data = exam_backend.get_candidate_responses(arguments["candidate_id"], arguments.get("exam_id"))
            elif tool_name == "get_answer_key":
                res_data = exam_backend.get_answer_key(arguments.get("exam_id", "EXAM-2026-GATE"), arguments["shift_id"])
            elif tool_name == "get_shift_statistics":
                res_data = exam_backend.get_shift_statistics(arguments.get("exam_id", "EXAM-2026-GATE"), arguments["shift_id"])
            elif tool_name == "get_proctoring_report":
                res_data = exam_backend.get_proctoring_report(arguments["candidate_id"], arguments.get("exam_id"))
            elif tool_name == "get_qualification_status":
                res_data = exam_backend.get_qualification_status(arguments["candidate_id"], arguments.get("exam_id"))
            elif tool_name == "get_merit_list":
                res_data = exam_backend.get_merit_list(arguments.get("exam_id", "EXAM-2026-GATE"), arguments.get("category"))
            elif tool_name == "get_category_cutoffs":
                res_data = exam_backend.get_category_cutoffs(arguments.get("exam_id", "EXAM-2026-GATE"))
            elif tool_name == "search_documents":
                chunks = rag_engine.search_documents(
                    query=arguments["query"],
                    owner_id=user_id,
                    doc_ids=arguments.get("doc_ids"),
                    top_k=arguments.get("top_k", 4),
                )

                res_data = {
                    "query": arguments["query"],
                    "total_results": len(chunks),
                    "chunks": chunks,
                }

                verification_note = (
                    f"Retrieved {len(chunks)} chunks belonging to the "
                    "authenticated user."
                )
            elif tool_name == "retrieve_document_chunks":
                chunks = rag_engine.retrieve_document_chunks(
                    doc_id=arguments["doc_id"],
                    page_numbers=arguments["page_numbers"],
                    owner_id=user_id,
                )

                res_data = {
                    "doc_id": arguments["doc_id"],
                    "page_numbers": arguments["page_numbers"],
                    "total_results": len(chunks),
                    "chunks": chunks,
                }
            elif tool_name == "compare_examination_documents":
                res_data = rag_engine.compare_examination_documents(
                    doc_id_1=arguments["doc_id_1"],
                    doc_id_2=arguments["doc_id_2"],
                    owner_id=user_id,
                    comparison_type=arguments.get("comparison_type", "general"),
                )
            elif tool_name == "get_evaluation_history":
                res_data = exam_backend.get_evaluation_history(arguments.get("candidate_id"), arguments.get("exam_id"))

            # Prepared-Action Tools (Level 4)
            elif tool_name == "prepare_result_report":
                prep = exam_backend.prepare_result_report(
                    arguments.get("exam_id", "EXAM-2026-GATE"), arguments.get("shift_id"), arguments.get("options")
                )
                res_data = prep.model_dump()
                verification_note = "Prepared action generated. Requires explicit administrator authorization token to execute."
            elif tool_name == "prepare_reevaluation_request":
                prep = exam_backend.prepare_reevaluation_request(
                    arguments["candidate_id"],
                    arguments.get("exam_id", "EXAM-2026-GATE"),
                    arguments["justification"],
                    arguments["affected_questions"]
                )
                res_data = prep.model_dump()
                verification_note = f"Re-evaluation request prepared for Candidate {arguments['candidate_id']}. Awaiting confirmation card approval."
            elif tool_name == "prepare_answer_key_update":
                prep = exam_backend.prepare_answer_key_update(
                    arguments.get("exam_id", "EXAM-2026-GATE"),
                    arguments["shift_id"],
                    arguments["question_id"],
                    arguments["proposed_action"],
                    arguments.get("new_correct_options", []),
                    arguments["reason"]
                )
                res_data = prep.model_dump()
            elif tool_name == "prepare_merit_list_publication":
                prep = exam_backend.prepare_merit_list_publication(
                    arguments.get("exam_id", "EXAM-2026-GATE"),
                    arguments["version_tag"],
                    arguments.get("scheduled_time")
                )
                res_data = prep.model_dump()

            # Consequential Action Tools (Level 5)
            elif tool_name == "execute_reevaluation":
                res_data = exam_backend.execute_reevaluation(
                    arguments["preparation_id"],
                    arguments["approver_token"],
                    user_role,
                    approver_id=user_id
                )
                verification_note = f"Re-evaluation successfully executed. Scores re-calculated. Result version updated to {res_data['new_result_version']}."
            elif tool_name == "approve_answer_key_change":
                res_data = exam_backend.approve_answer_key_change(
                    arguments["preparation_id"],
                    arguments["approver_token"],
                    user_role,
                    approver_id=user_id

                )
                verification_note = "Answer key change committed. Global normalisation refreshed."
            elif tool_name == "publish_merit_list":
                res_data = exam_backend.publish_merit_list(
                    arguments["preparation_id"],
                    arguments["approver_token"],
                    user_role,
                    approver_id=user_id
                )
                verification_note = "Merit list officially published and locked."
            else:
                return ToolCallResult(
                    call_id=c_id,
                    tool_name=tool_name,
                    status="error",
                    data=None,
                    error=f"Unrecognized tool '{tool_name}'.",
                    level=level,
                    verified=False,
                    timestamp=time.time()
                )

            # Normalize result data to ensure it conforms to dictionary structure
            if isinstance(res_data, list):
                res_data = {"results": res_data, "total": len(res_data)}
            elif res_data is None:
                res_data = {}

            return ToolCallResult(
                call_id=c_id,
                tool_name=tool_name,
                status="success",
                data=res_data,
                level=level,
                verified=True,
                verification_notes=verification_note,
                timestamp=time.time()
            )

        except Exception as e:
            return ToolCallResult(
                call_id=c_id,
                tool_name=tool_name,
                status="error",
                data=None,
                error=str(e),
                level=level,
                verified=False,
                timestamp=time.time()
            )

    def _build_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Constructs OpenAPI / OpenAI-compatible tool specifications for Llama."""
        return {
            "get_exam_details": {
                "type": "function",
                "function": {
                    "name": "get_exam_details",
                    "description": "Retrieve comprehensive details for an examination, including shifts, rules, cutoffs, and scoring policies.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "exam_id": {"type": "string", "description": "Examination identifier (e.g. 'EXAM-2026-GATE')."}
                        },
                        "required": ["exam_id"]
                    }
                }
            },
            "get_candidate_details": {
                "type": "function",
                "function": {
                    "name": "get_candidate_details",
                    "description": "Retrieve candidate demographic and registration details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "candidate_id": {"type": "string", "description": "Unique candidate identifier (e.g. 'CAND-1001')."},
                            "exam_id": {"type": "string", "description": "Examination ID."}
                        },
                        "required": ["candidate_id"]
                    }
                }
            },
            "get_candidate_scorecard": {
                "type": "function",
                "function": {
                    "name": "get_candidate_scorecard",
                    "description": "Retrieve complete official candidate scorecard including raw marks, sectional marks, negative penalties, proctoring deductions, normalized score, and qualification status.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "candidate_id": {"type": "string", "description": "Candidate ID."},
                            "exam_id": {"type": "string", "description": "Examination ID."}
                        },
                        "required": ["candidate_id"]
                    }
                }
            },
            "get_candidate_responses": {
                "type": "function",
                "function": {
                    "name": "get_candidate_responses",
                    "description": "Retrieve candidate question responses, attempts, and correctness breakdown.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "candidate_id": {"type": "string", "description": "Candidate ID."}
                        },
                        "required": ["candidate_id"]
                    }
                }
            },
            "get_answer_key": {
                "type": "function",
                "function": {
                    "name": "get_answer_key",
                    "description": "Retrieve official answer key for an exam and specific shift, including dropped questions and question types.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "exam_id": {"type": "string", "description": "Exam ID."},
                            "shift_id": {"type": "string", "description": "Shift ID (e.g. 'SHIFT-1', 'SHIFT-2', 'SHIFT-3')."}
                        },
                        "required": ["exam_id", "shift_id"]
                    }
                }
            },
            "get_shift_statistics": {
                "type": "function",
                "function": {
                    "name": "get_shift_statistics",
                    "description": "Retrieve statistical summary for a shift: appearances, mean, standard deviation, qualification rate, sectional failures, and proctoring disqualifications.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "exam_id": {"type": "string", "description": "Exam ID."},
                            "shift_id": {"type": "string", "description": "Shift ID (e.g. 'SHIFT-2')."}
                        },
                        "required": ["exam_id", "shift_id"]
                    }
                }
            },
            "get_proctoring_report": {
                "type": "function",
                "function": {
                    "name": "get_proctoring_report",
                    "description": "Retrieve proctoring integrity telemetry, violation events, and penalty deductions for a candidate.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "candidate_id": {"type": "string", "description": "Candidate ID."}
                        },
                        "required": ["candidate_id"]
                    }
                }
            },
            "get_qualification_status": {
                "type": "function",
                "function": {
                    "name": "get_qualification_status",
                    "description": "Check candidate's qualification status and the exact reason for failure or disqualification.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "candidate_id": {"type": "string", "description": "Candidate ID."}
                        },
                        "required": ["candidate_id"]
                    }
                }
            },
            "get_merit_list": {
                "type": "function",
                "function": {
                    "name": "get_merit_list",
                    "description": "Retrieve the official category or aggregate merit list with tie-broken candidate ranks.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "exam_id": {"type": "string", "description": "Exam ID."},
                            "category": {"type": "string", "description": "Optional category filter (e.g. 'GEN', 'OBC_NCL', 'SC', 'ST')."}
                        },
                        "required": ["exam_id"]
                    }
                }
            },
            "get_category_cutoffs": {
                "type": "function",
                "function": {
                    "name": "get_category_cutoffs",
                    "description": "Retrieve official sectional and category-wise aggregate cut-off requirements.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "exam_id": {"type": "string", "description": "Exam ID."}
                        },
                        "required": ["exam_id"]
                    }
                }
            },
            "search_documents": {
                "type": "function",
                "function": {
                    "name": "search_documents",
                    "description": "Semantically search uploaded PDF documents for questions, guidelines, rules, or text snippets.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query or concept."},
                            "doc_ids": {"type": "array", "items": {"type": "string"}, "description": "Optional list of document IDs to restrict search to."},
                            "top_k": {"type": "integer", "description": "Number of chunks to return (default 4)."}
                        },
                        "required": ["query"]
                    }
                }
            },
            "retrieve_document_chunks": {
                "type": "function",
                "function": {
                    "name": "retrieve_document_chunks",
                    "description": "Retrieve text chunks from specific page numbers in an uploaded document.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doc_id": {"type": "string", "description": "Document ID."},
                            "page_numbers": {"type": "array", "items": {"type": "integer"}, "description": "List of page numbers (e.g. [1, 2])."}
                        },
                        "required": ["doc_id", "page_numbers"]
                    }
                }
            },
            "compare_examination_documents": {
                "type": "function",
                "function": {
                    "name": "compare_examination_documents",
                    "description": "Perform cross-comparison between two uploaded PDFs (e.g. Master Question Paper vs Provisional Answer Key).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doc_id_1": {"type": "string", "description": "First document ID."},
                            "doc_id_2": {"type": "string", "description": "Second document ID."},
                            "comparison_type": {"type": "string", "description": "Type of comparison (e.g. 'answer_key_alignment', 'discrepancy_check')."}
                        },
                        "required": ["doc_id_1", "doc_id_2"]
                    }
                }
            },
            "get_evaluation_history": {
                "type": "function",
                "function": {
                    "name": "get_evaluation_history",
                    "description": "Retrieve re-evaluation history and result version audits.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "candidate_id": {"type": "string", "description": "Optional candidate ID."}
                        }
                    }
                }
            },
            "prepare_result_report": {
                "type": "function",
                "function": {
                    "name": "prepare_result_report",
                    "description": "Prepare a formal result report for a shift or entire exam (Level 4 Prepared Action).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "exam_id": {"type": "string", "description": "Exam ID."},
                            "shift_id": {"type": "string", "description": "Optional shift ID."}
                        },
                        "required": ["exam_id"]
                    }
                }
            },
            "prepare_reevaluation_request": {
                "type": "function",
                "function": {
                    "name": "prepare_reevaluation_request",
                    "description": "Prepare a formal re-evaluation petition for a candidate (Level 4 Prepared Action).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "candidate_id": {"type": "string", "description": "Candidate ID."},
                            "justification": {"type": "string", "description": "Detailed justification for re-evaluation."},
                            "affected_questions": {"type": "array", "items": {"type": "string"}, "description": "List of affected questions (e.g. ['Q42'])."}
                        },
                        "required": ["candidate_id", "justification", "affected_questions"]
                    }
                }
            },
            "prepare_answer_key_update": {
                "type": "function",
                "function": {
                    "name": "prepare_answer_key_update",
                    "description": "Prepare an answer key amendment (DROP question, change option, add multi-correct) (Level 4 Prepared Action).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "exam_id": {"type": "string", "description": "Exam ID."},
                            "shift_id": {"type": "string", "description": "Shift ID."},
                            "question_id": {"type": "string", "description": "Question ID (e.g. 'Q42')."},
                            "proposed_action": {"type": "string", "enum": ["DROP", "CHANGE_OPTION"], "description": "Proposed action."},
                            "new_correct_options": {"type": "array", "items": {"type": "string"}, "description": "New correct option(s)."},
                            "reason": {"type": "string", "description": "Justification for answer key amendment."}
                        },
                        "required": ["exam_id", "shift_id", "question_id", "proposed_action", "reason"]
                    }
                }
            },
            "prepare_merit_list_publication": {
                "type": "function",
                "function": {
                    "name": "prepare_merit_list_publication",
                    "description": "Prepare official publication of merit list for an exam (Level 4 Prepared Action).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "exam_id": {"type": "string", "description": "Exam ID."},
                            "version_tag": {"type": "string", "description": "Version tag (e.g. 'v1.0')."}
                        },
                        "required": ["exam_id", "version_tag"]
                    }
                }
            },
            "execute_reevaluation": {
                "type": "function",
                "function": {
                    "name": "execute_reevaluation",
                    "description": "Execute re-evaluation and recalculate candidate scores (Level 5 Consequential Tool - Requires Valid Approval Token).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "preparation_id": {"type": "string", "description": "ID of previously prepared reevaluation action."},
                            "approver_token": {"type": "string", "description": "Cryptographic approval token."}
                        },
                        "required": ["preparation_id", "approver_token"]
                    }
                }
            },
            "approve_answer_key_change": {
                "type": "function",
                "function": {
                    "name": "approve_answer_key_change",
                    "description": "Commit answer key change and trigger global re-normalisation (Level 5 Consequential Tool - Requires Valid Approval Token).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "preparation_id": {"type": "string", "description": "Preparation ID."},
                            "approver_token": {"type": "string", "description": "Cryptographic approval token."}
                        },
                        "required": ["preparation_id", "approver_token"]
                    }
                }
            },
            "publish_merit_list": {
                "type": "function",
                "function": {
                    "name": "publish_merit_list",
                    "description": "Permanently publish merit list to public view (Level 5 Consequential Tool - Requires Valid Approval Token).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "preparation_id": {"type": "string", "description": "Preparation ID."},
                            "approver_token": {"type": "string", "description": "Cryptographic approval token."}
                        },
                        "required": ["preparation_id", "approver_token"]
                    }
                }
            }
        }


tool_registry = ToolRegistry()
