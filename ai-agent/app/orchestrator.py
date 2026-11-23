"""Agent Orchestrator for EXAMFLOW AI.

Coordinates the seven-step workflow, role-checked tool execution, evidence-based
shift investigations, and response synthesis. Llama remains the natural-language
reasoning layer; deterministic handlers cover a few well-defined requests when
the Llama API is not configured.
"""

import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from app.models import (
    UserRole,
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ToolCallResult,
    InvestigationPlan,
    InvestigationReport,
    AnomalyReport,
    PreparedAction,
    DocumentCitation,
    PermissionLevel,
)
from app.context_manager import context_manager, SessionContext
from app.tool_registry import tool_registry
from app.services.exam_backend import exam_backend
from app.services.proactive_analytics import proactive_analytics
from app.llama_client import llama_client
from app.prompts.system_prompts import SYSTEM_PROMPT


class AgentOrchestrator:
    """Coordinates tool execution, investigations, and verified responses."""

    DEFAULT_EXAM_ID = "EXAM-2026-GATE"
    SHIFT_IDS = ("SHIFT-1", "SHIFT-2", "SHIFT-3")

    async def process_turn(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or f"sess_{int(time.time() * 1000)}"
        session = context_manager.get_or_create_session(
            session_id=session_id,
            user_id=request.user_id or "default_user",
            user_role=request.user_role,
        )

        # Apply request context before analytics, planning, or prompt construction.
        if request.active_exam_id:
            session.active_exam_id = request.active_exam_id
        if request.active_candidate_id:
            session.active_candidate_id = request.active_candidate_id
        if request.attached_doc_ids:
            # The IDs are passed to document-search tools. Do not fabricate metadata.
            pass

        user_text = (request.message or "").strip()
        session.add_message(ChatMessage(role="user", content=user_text))

        plan, is_shift_investigation, target_shift = self._understand_and_plan(
            user_text, session
        )

        try:
            anomalies = proactive_analytics.detect_anomalies(session.active_exam_id)
        except Exception:
            anomalies = []

        if is_shift_investigation:
            return await self._execute_shift_investigation(
                shift_id=target_shift or "SHIFT-2",
                session=session,
                plan=plan,
                anomalies=anomalies,
            )

        messages = self._build_llm_messages(
            session, user_text, request.attached_doc_ids
        )
        schemas = tool_registry.get_schemas_for_role(session.user_role)

        try:
            completion = await llama_client.generate_chat_completion(
                messages=messages, tools=schemas
            )
        except Exception as exc:
            fallback = await self._handle_without_llama(
                user_text, request, session, plan, anomalies
            )
            if fallback is not None:
                return fallback
            return self._error_response(
                session, plan, anomalies,
                f"Llama request failed: {exc}"
            )

        if not isinstance(completion, dict):
            return self._error_response(
                session, plan, anomalies,
                "Llama returned an invalid response."
            )

        content = completion.get("content") or ""
        if self._is_llama_unconfigured(content):
            fallback = await self._handle_without_llama(
                user_text, request, session, plan, anomalies
            )
            if fallback is not None:
                return fallback
            return self._error_response(session, plan, anomalies, content)

        raw_tool_calls = completion.get("tool_calls") or []
        tool_results: List[ToolCallResult] = []
        citations: List[DocumentCitation] = []
        prepared_action: Optional[PreparedAction] = None

        for index, tool_call in enumerate(raw_tool_calls):
            result = self._execute_llm_tool_call(
                tool_call, index, session, request.attached_doc_ids
            )
            tool_results.append(result)

            if (
                result.status == "success"
                and isinstance(result.data, dict)
                and "preparation_id" in result.data
            ):
                try:
                    prepared_action = PreparedAction(**result.data)
                    session.pending_actions[prepared_action.preparation_id] = prepared_action
                except Exception:
                    # Preserve the successful tool result; do not fabricate a card.
                    prepared_action = None

            if result.status == "success" and result.tool_name == "search_documents":
                citations.extend(self._citations_from_search_result(result.data))

        if raw_tool_calls:
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": raw_tool_calls,
            })
            for result in tool_results:
                tool_payload = (
                    result.data if result.status == "success" and result.data is not None
                    else {"status": result.status, "error": result.error}
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": result.call_id,
                    "content": json.dumps(tool_payload, default=str),
                })

            try:
                final_completion = await llama_client.generate_chat_completion(
                    messages=messages, tools=None
                )
                final_reply = (final_completion or {}).get("content") or ""
            except Exception as exc:
                final_reply = f"Tool execution completed, but response synthesis failed: {exc}"
        else:
            final_reply = content

        if not final_reply.strip():
            final_reply = "I couldn't generate a response for that request."

        session.add_message(ChatMessage(
            role="assistant",
            content=final_reply,
            citations=citations or None,
        ))

        return ChatResponse(
            session_id=session.session_id,
            user_role=session.user_role,
            plan=plan,
            tool_executions=tool_results,
            reply=final_reply,
            citations=citations,
            anomalies=anomalies,
            prepared_action=prepared_action,
            verified=bool(tool_results) and all(
                result.status == "success" and result.verified
                for result in tool_results
            ),
        )

    def _understand_and_plan(
        self, message: str, session: SessionContext
    ) -> Tuple[Optional[InvestigationPlan], bool, Optional[str]]:
        """Detects a shift-disparity investigation and its target shift."""
        text = message.lower()
        mentions_investigation = any(
            term in text for term in (
                "investigate", "investigation", "root cause",
                "why is", "why does", "disparity", "anomalous",
            )
        )
        mentions_shift_issue = (
            "shift" in text
            and any(term in text for term in (
                "qualification", "qualified", "rate", "performance",
                "low", "difference", "disparity", "compare", "anomal",
            ))
        )
        if not (mentions_investigation and mentions_shift_issue):
            return None, False, None

        match = re.search(r"shift[\s-]*([123])", text)
        target = f"SHIFT-{match.group(1)}" if match else "SHIFT-2"
        plan = InvestigationPlan(
            objective=f"Investigate the qualification and performance pattern for {target} against the other examination shifts.",
            planned_steps=[
                "Understand the requested shift and examination context.",
                "Plan a comparison using authoritative shift statistics and examination rules.",
                "Investigate the target shift and retrieve statistics for all available shifts.",
                "Retrieve the target shift's answer-key status and configured cut-offs.",
                "Execute only authorized read-only examination tools.",
                "Verify every finding against successful tool results and record unavailable evidence.",
                "Respond with findings, uncertainties, and evidence-based next steps.",
            ],
            tools_to_invoke=[
                "get_exam_details",
                "get_shift_statistics",
                "get_category_cutoffs",
                "get_answer_key",
            ],
        )
        return plan, True, target

    async def _execute_shift_investigation(
        self,
        shift_id: str,
        session: SessionContext,
        plan: Optional[InvestigationPlan],
        anomalies: List[AnomalyReport],
    ) -> ChatResponse:
        """Compares all known shifts and reports only facts supported by tool results."""
        results: List[ToolCallResult] = []

        def run_tool(name: str, args: Dict[str, Any], call_id: str) -> ToolCallResult:
            result = tool_registry.execute_tool(
                tool_name=name,
                arguments=args,
                user_role=session.user_role,
                user_id=session.user_id,
                call_id=call_id,
            )
            results.append(result)
            return result

        exam_result = run_tool(
            "get_exam_details",
            {"exam_id": session.active_exam_id},
            "call_inv_exam_details",
        )
        cutoff_result = run_tool(
            "get_category_cutoffs",
            {"exam_id": session.active_exam_id},
            "call_inv_cutoffs",
        )

        shift_results: Dict[str, ToolCallResult] = {}
        for shift in self.SHIFT_IDS:
            shift_results[shift] = run_tool(
                "get_shift_statistics",
                {"exam_id": session.active_exam_id, "shift_id": shift},
                f"call_inv_stats_{shift.lower().replace('-', '_')}",
            )

        answer_key_result = run_tool(
            "get_answer_key",
            {"exam_id": session.active_exam_id, "shift_id": shift_id},
            "call_inv_answer_key_target",
        )

        def data_of(result: Optional[ToolCallResult]) -> Dict[str, Any]:
            if result and result.status == "success" and isinstance(result.data, dict):
                return result.data
            return {}

        exam_data = data_of(exam_result)
        cutoff_data = data_of(cutoff_result)
        target_data = data_of(shift_results.get(shift_id))
        answer_data = data_of(answer_key_result)

        successful_shift_data = {
            name: data_of(result)
            for name, result in shift_results.items()
            if result.status == "success" and data_of(result)
        }

        findings: List[str] = []
        uncertainties: List[str] = []
        evidence: Dict[str, Any] = {
            "exam_id": session.active_exam_id,
            "target_shift": shift_id,
            "successful_shift_statistics": successful_shift_data,
        }
        data_examined: List[str] = []

        if exam_data:
            data_examined.append("Authoritative examination details")
            evidence["exam_details"] = exam_data
        else:
            uncertainties.append("Examination details could not be retrieved.")

        if cutoff_data:
            data_examined.append("Configured sectional and category cut-offs")
            evidence["cutoff_rules"] = cutoff_data
        else:
            uncertainties.append("Configured cut-off rules could not be retrieved.")

        if target_data:
            data_examined.append(f"{shift_id} shift statistics")
            findings.append(
                f"{shift_id} recorded a qualification rate of "
                f"{target_data.get('qualification_rate_percent', 'not reported')}% "
                f"and a mean raw score of {target_data.get('mean_raw_score', 'not reported')}."
            )
            failures = target_data.get("sectional_failure_counts", {})
            if isinstance(failures, dict):
                findings.append(
                    f"{shift_id} sectional failure counts (including Section B): "
                    + ", ".join(f"{section}={count}" for section, count in failures.items())
                    + "."
                )
            findings.append(
                f"{shift_id} recorded "
                f"{target_data.get('minimum_attempt_failure_count', 'an unreported number')} "
                "minimum-attempt failures and "
                f"{target_data.get('proctoring_disqualification_count', 'an unreported number')} "
                "Proctoring disqualifications."
            )
        else:
            uncertainties.append(f"Statistics for {shift_id} were unavailable or failed.")

        comparison_rows = []
        for other_shift, other_data in successful_shift_data.items():
            if other_shift == shift_id:
                continue
            if target_data:
                target_rate = target_data.get("qualification_rate_percent")
                other_rate = other_data.get("qualification_rate_percent")
                target_mean = target_data.get("mean_raw_score")
                other_mean = other_data.get("mean_raw_score")
                row = {"shift_id": other_shift}
                if isinstance(target_rate, (int, float)) and isinstance(other_rate, (int, float)):
                    row["qualification_rate_difference_percentage_points"] = round(
                        target_rate - other_rate, 2
                    )
                if isinstance(target_mean, (int, float)) and isinstance(other_mean, (int, float)):
                    row["mean_raw_score_difference"] = round(target_mean - other_mean, 2)
                comparison_rows.append(row)
        evidence["comparisons_against_target"] = comparison_rows
        if comparison_rows:
            findings.append(
                f"Comparative statistics were retrieved for {shift_id} and "
                f"{len(comparison_rows)} other shift(s). Differences are recorded in the evidence."
            )

        dropped_questions = answer_data.get("dropped_questions")
        if answer_data:
            data_examined.append(f"{shift_id} answer-key status")
            evidence["answer_key"] = {
                "shift_id": shift_id,
                "dropped_questions": dropped_questions,
                "total_questions": answer_data.get("total_questions"),
            }
            if dropped_questions is not None:
                if dropped_questions:
                    findings.append(
                        f"The answer-key service reports dropped question(s) in {shift_id}: "
                        f"{', '.join(map(str, dropped_questions))}. The returned data does not establish "
                        "how individual candidate ledgers were credited."
                    )
                else:
                    findings.append(f"The answer-key service reports no dropped questions in {shift_id}.")
        else:
            uncertainties.append(f"Answer-key information for {shift_id} was unavailable.")

        if not findings:
            findings.append("No findings could be verified because the required backend data was unavailable.")

        uncertainties.extend([
            "Shift-level aggregate statistics do not identify which individual candidates caused each failure count.",
            "The answer-key response lists dropped questions but does not prove candidate-level score adjustments.",
            "No item-difficulty analysis or raw webcam telemetry was returned by the tools used in this investigation.",
        ])

        next_steps = [
            "Review candidate-level scorecards for the target shift to identify the exact qualification blockers.",
            "Review candidate-level proctoring reports and source telemetry before making individual malpractice conclusions.",
            "Have the examination committee review question-level difficulty and answer-key decisions where shift disparities are observed.",
        ]

        report = InvestigationReport(
            objective=f"Evidence-based performance and qualification investigation for {shift_id}.",
            data_examined=data_examined,
            findings=findings,
            evidence=evidence,
            uncertainties=uncertainties,
            recommended_next_steps=next_steps,
        )

        reply_lines = [
            f"## Investigation Report: {shift_id}",
            "",
            f"**Objective:** {report.objective}",
            "",
            "### Findings",
        ]
        reply_lines.extend(f"- {item}" for item in findings)
        reply_lines.extend(["", "### Comparative shift data"])
        for shift, data in successful_shift_data.items():
            reply_lines.append(
                f"- **{shift}:** qualification rate "
                f"{data.get('qualification_rate_percent', 'N/A')}%; mean raw score "
                f"{data.get('mean_raw_score', 'N/A')}; appeared "
                f"{data.get('total_appeared', 'N/A')}."
            )
        if not successful_shift_data:
            reply_lines.append("- No shift statistics were successfully retrieved.")
        reply_lines.extend(["", "### Uncertainties and limitations"])
        reply_lines.extend(f"- {item}" for item in uncertainties)
        reply_lines.extend(["", "### Recommended next steps"])
        reply_lines.extend(f"- {item}" for item in next_steps)
        reply = "\n".join(reply_lines)

        session.add_message(ChatMessage(role="assistant", content=reply))
        verified = (
            bool(target_data)
            and bool(cutoff_data)
            and answer_key_result.status == "success"
            and all(
                result.status == "success" and result.verified
                for result in results
            )
        )

        return ChatResponse(
            session_id=session.session_id,
            user_role=session.user_role,
            plan=plan,
            tool_executions=results,
            reply=reply,
            anomalies=anomalies,
            investigation_report=report,
            verified=verified,
        )

    async def _handle_without_llama(
        self,
        message: str,
        request: ChatRequest,
        session: SessionContext,
        plan: Optional[InvestigationPlan],
        anomalies: List[AnomalyReport],
    ) -> Optional[ChatResponse]:
        """Provides transparent, deterministic responses for well-defined requests."""
        text = message.lower()
        results: List[ToolCallResult] = []
        citations: List[DocumentCitation] = []

        # Explicit candidate scorecard request.
        candidate_match = re.search(r"\bCAND-\d+\b", message, re.IGNORECASE)
        if candidate_match and any(word in text for word in ("scorecard", "score card", "score")):
            candidate_id = candidate_match.group(0).upper()
            result = self._run_tool(
                "get_candidate_scorecard",
                {"candidate_id": candidate_id, "exam_id": session.active_exam_id},
                session,
                "call_fallback_scorecard",
            )
            results.append(result)
            if result.status == "success" and isinstance(result.data, dict):
                reply = self._format_scorecard(result.data)
            else:
                reply = f"I couldn't retrieve the scorecard for {candidate_id}: {result.error or result.status}."
            return self._response(session, plan, results, reply, anomalies, citations)

        # Document question: perform a real retrieval even without Llama.
        if any(word in text for word in ("pdf", "document", "uploaded file")):
            query = message.strip() or "document contents"
            result = self._run_tool(
                "search_documents",
                {"query": query, "doc_ids": request.attached_doc_ids},
                session,
                "call_fallback_document_search",
            )
            results.append(result)
            chunks = []
            if result.status == "success" and isinstance(result.data, dict):
                chunks = result.data.get("chunks", []) or []
                citations = self._citations_from_search_result(result.data)
            if chunks:
                reply = "I found relevant document excerpts:\n" + "\n".join(
                    f"- {item.get('doc_name', 'Document')}, page {item.get('page_number', '?')}: "
                    f"{str(item.get('content', ''))[:350]}"
                    for item in chunks if isinstance(item, dict)
                )
            else:
                reply = (
                    "No relevant document chunks were found in the indexed document store. "
                    "Please upload the PDF and ensure it has finished processing before searching again."
                )
            return self._response(session, plan, results, reply, anomalies, citations)

        # Ground rule questions in the authoritative backend.
        if any(word in text for word in ("negative marking", "sectional cutoff", "sectional cut-off", "cutoff", "cut-off")):
            result = self._run_tool(
                "get_category_cutoffs",
                {"exam_id": session.active_exam_id},
                session,
                "call_fallback_cutoffs",
            )
            results.append(result)
            if result.status == "success" and isinstance(result.data, dict):
                reply = self._format_rules(result.data)
            else:
                reply = f"I couldn't retrieve the configured examination rules: {result.error or result.status}."
            return self._response(session, plan, results, reply, anomalies, citations)

        if any(greeting in text for greeting in ("hello", "hi", "hey", "good morning", "good afternoon")):
            reply = (
                "Hello! I'm EXAMFLOW AI. I can help explain examination rules, retrieve candidate "
                "scorecards, search uploaded examination documents, and investigate shift-level "
                "qualification patterns. What would you like to examine?"
            )
            return self._response(session, plan, results, reply, anomalies, citations)

        if "seven-step" in text or "7-step" in text or "seven step" in text:
            reply = (
                "EXAMFLOW AI follows the PS-072 seven-step operating cycle:\n\n"
                "1. **Understand:** identify the request, user role, exam, candidate, and shift. "
                "Example: recognize a request to investigate SHIFT-2 qualification rates.\n"
                "2. **Plan:** select the read-only tools and evidence needed. Example: plan to retrieve "
                "all shift statistics, cut-offs, and the target shift answer-key status.\n"
                "3. **Investigate:** execute the planned investigation. Example: compare SHIFT-2 with "
                "SHIFT-1 and SHIFT-3.\n"
                "4. **Retrieve:** obtain authoritative records. Example: retrieve scorecards, "
                "proctoring reports, and answer-key data where the relevant identifiers are known.\n"
                "5. **Execute:** run only role-authorized operations. Example: execute read-only "
                "statistics tools; consequential changes require the separate approval workflow.\n"
                "6. **Verify:** check tool status and evidence before making claims. Example: do not "
                "claim that a dropped question was credited without candidate-ledger evidence.\n"
                "7. **Respond:** present findings, evidence, uncertainties, and next steps. Example: "
                "report the shift comparison and recommend item-level review where warranted."
            )
            return self._response(session, plan, results, reply, anomalies, citations)

        return None

    def _execute_llm_tool_call(
        self,
        tool_call: Dict[str, Any],
        index: int,
        session: SessionContext,
        attached_doc_ids: Optional[List[str]],
    ) -> ToolCallResult:
        call_id = tool_call.get("id") or f"call_{int(time.time() * 1000)}_{index}"
        function = tool_call.get("function") or {}
        tool_name = function.get("name") or "unknown_tool"
        raw_args = function.get("arguments", "{}")

        if isinstance(raw_args, dict):
            args = raw_args
        else:
            try:
                args = json.loads(raw_args or "{}")
            except (TypeError, ValueError):
                return ToolCallResult(
                    call_id=call_id,
                    tool_name=tool_name,
                    status="error",
                    data=None,
                    error="Tool arguments were not valid JSON; no tool was executed.",
                    level=PermissionLevel.LEVEL_1_DIRECT,
                    verified=False,
                )

        if not isinstance(args, dict):
            return ToolCallResult(
                call_id=call_id,
                tool_name=tool_name,
                status="error",
                data=None,
                error="Tool arguments must be a JSON object; no tool was executed.",
                level=PermissionLevel.LEVEL_1_DIRECT,
                verified=False,
            )

        if tool_name in ("search_documents",) and attached_doc_ids and not args.get("doc_ids"):
            args["doc_ids"] = attached_doc_ids

        return self._run_tool(tool_name, args, session, call_id)

    def _run_tool(
        self, tool_name: str, arguments: Dict[str, Any],
        session: SessionContext, call_id: str
    ) -> ToolCallResult:
        return tool_registry.execute_tool(
            tool_name=tool_name,
            arguments=arguments,
            user_role=session.user_role,
            user_id=session.user_id,
            call_id=call_id,
        )

    @staticmethod
    def _citations_from_search_result(data: Any) -> List[DocumentCitation]:
        citations: List[DocumentCitation] = []
        chunks = data.get("chunks", []) if isinstance(data, dict) else (
            data if isinstance(data, list) else []
        )
        for item in chunks:
            if not isinstance(item, dict):
                continue
            required = ("doc_id", "doc_name", "page_number")
            if all(key in item for key in required):
                citations.append(DocumentCitation(
                    doc_id=str(item["doc_id"]),
                    doc_name=str(item["doc_name"]),
                    page_number=int(item["page_number"]),
                    snippet=str(item.get("content", ""))[:200],
                ))
        return citations

    @staticmethod
    def _format_scorecard(data: Dict[str, Any]) -> str:
        sections = data.get("sectional_scores") or {}
        return (
            f"## Candidate Scorecard: {data.get('candidate_name', data.get('candidate_id'))}\n\n"
            f"- Candidate ID: {data.get('candidate_id')}\n"
            f"- Shift: {data.get('shift_id')}\n"
            f"- Raw score: {data.get('raw_score')}\n"
            f"- Normalized score: {data.get('normalized_score')}\n"
            f"- Sectional scores: " + ", ".join(
                f"{name}={score}" for name, score in sections.items()
            ) + "\n"
            f"- Negative-marking penalty: {data.get('negative_penalties')}\n"
            f"- Proctoring deduction: {data.get('proctoring_deductions')}\n"
            f"- Qualification status: {data.get('qualification_status')}\n"
            f"- Sectional cut-offs cleared: {data.get('sectional_cutoffs_cleared')}\n"
            f"- Minimum attempts cleared: {data.get('minimum_attempts_cleared')}"
        )

    @staticmethod
    def _format_rules(data: Dict[str, Any]) -> str:
        sections = data.get("sectional_cutoffs") or {}
        category = data.get("category_aggregate_cutoffs") or {}
        return (
            "## Configured Examination Rules\n\n"
            "- Negative marking: the backend rule register specifies a penalty ratio of 1/3 "
            "of the question's marks (for example, -1/3 for a 1-mark question and -2/3 "
            "for a 2-mark question).\n"
            f"- Section A minimum: {sections.get('Section_A', 'not available')} marks.\n"
            f"- Section B minimum: {sections.get('Section_B', 'not available')} marks.\n"
            f"- Minimum attempt percentage: {data.get('minimum_attempt_percent', 'not available')}%.\n"
            "- Category aggregate cut-offs: "
            + ", ".join(f"{name}={value}" for name, value in category.items())
        )

    @staticmethod
    def _is_llama_unconfigured(content: str) -> bool:
        return "llama api is not configured" in (content or "").lower()

    def _error_response(
        self, session: SessionContext, plan: Optional[InvestigationPlan],
        anomalies: List[AnomalyReport], message: str
    ) -> ChatResponse:
        reply = message or "The AI service is currently unavailable."
        session.add_message(ChatMessage(role="assistant", content=reply))
        return ChatResponse(
            session_id=session.session_id,
            user_role=session.user_role,
            plan=plan,
            reply=reply,
            anomalies=anomalies,
            verified=False,
        )

    def _response(
        self, session: SessionContext, plan: Optional[InvestigationPlan],
        results: List[ToolCallResult], reply: str,
        anomalies: List[AnomalyReport], citations: List[DocumentCitation]
    ) -> ChatResponse:
        session.add_message(ChatMessage(
            role="assistant", content=reply, citations=citations or None
        ))
        return ChatResponse(
            session_id=session.session_id,
            user_role=session.user_role,
            plan=plan,
            tool_executions=results,
            reply=reply,
            citations=citations,
            anomalies=anomalies,
            verified=bool(results) and all(
                item.status == "success" and item.verified for item in results
            ),
        )

    def _build_llm_messages(
        self,
        session: SessionContext,
        current_user_message: str,
        attached_doc_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Builds the system prompt, current session context, and recent history."""
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        context = (
            "SESSION CONTEXT:\n"
            f"- User Role: {session.user_role.value}\n"
            f"- User ID: {session.user_id}\n"
            f"- Active Exam ID: {session.active_exam_id}\n"
            f"- Active Candidate ID: {session.active_candidate_id or 'None'}\n"
            f"- Result Version: {exam_backend.result_version}\n"
        )
        if session.attached_docs:
            context += "- Attached Indexed Documents: " + ", ".join(
                doc.filename for doc in session.attached_docs.values()
            ) + "\n"
        if attached_doc_ids:
            context += "- Attached Document IDs: " + ", ".join(attached_doc_ids) + "\n"
        messages.append({"role": "system", "content": context})

        for item in session.get_recent_history(limit=8):
            message: Dict[str, Any] = {
                "role": item.role,
                "content": item.content,
            }
            if item.tool_calls:
                message["tool_calls"] = [call.model_dump() for call in item.tool_calls]
            if item.tool_call_id:
                message["tool_call_id"] = item.tool_call_id
            messages.append(message)
        return messages


agent_orchestrator = AgentOrchestrator()
