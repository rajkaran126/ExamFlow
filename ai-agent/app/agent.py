
"""Top-level Agent Interface for EXAMFLOW AI."""

from typing import AsyncGenerator, Dict, Any

from app.models import (
    ChatRequest,
    ChatResponse,
    DocumentMetadata,
    ConsequentialConfirmation,
    PreparationStatus,
    UserRole,
)
from app.orchestrator import agent_orchestrator
from app.context_manager import context_manager
from app.document_processor.pdf_extractor import pdf_extractor
from app.retrieval.vector_store import vector_store
from app.services.exam_backend import exam_backend


class ExamFlowAgent:

    async def chat(self, request: ChatRequest) -> ChatResponse:
        return await agent_orchestrator.process_turn(request)

    async def chat_stream(
        self,
        request: ChatRequest,
    ) -> AsyncGenerator[str, None]:
        response = await agent_orchestrator.process_turn(request)

        # Response chunking, not genuine LLM token streaming.
        for word in response.reply.split(" "):
            yield word + " "

    def upload_and_index_document(
        self,
        file_path: str,
        filename: str,
        session_id: str,
        user_id: str,
        user_role: UserRole,
    ) -> DocumentMetadata:
        """Upload a PDF only into a session owned by the authenticated user."""

        if not user_id or not user_id.strip():
            raise PermissionError("Authenticated user identity is required.")

        if not isinstance(user_role, UserRole):
            raise PermissionError("Authenticated user role is required.")

        session = context_manager.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            user_role=user_role,
        )

        metadata, chunks = pdf_extractor.extract_document(
            file_path,
            filename,
        )

        # Stamp ownership before indexing.
        metadata.owner_id = user_id
        metadata.session_id = session_id

        for chunk in chunks:
            chunk.owner_id = user_id
            chunk.session_id = session_id

        vector_store.add_chunks(
            chunks,
            owner_id=user_id,
            session_id=session_id,
        )

        session.attach_document(metadata)

        return metadata

    def confirm_consequential_action(
        self,
        confirmation: ConsequentialConfirmation,
    ) -> Dict[str, Any]:

        prep_id = confirmation.preparation_id
        prep = exam_backend.prepared_actions.get(prep_id)

        if not prep:
            raise ValueError(
                f"Prepared action '{prep_id}' not found."
            )

        approver_id = confirmation.user_id

        if not isinstance(approver_id, str) or not approver_id.strip():
            raise PermissionError("A valid approver identity is required.")

        if not confirmation.confirmed:
            if prep.status != PreparationStatus.PENDING:
                raise PermissionError(
                    "This prepared action has already been processed."
                )

            prep.status = PreparationStatus.REJECTED

            return {
                "status": "rejected",
                "message": f"Action {prep_id} was rejected.",
                "preparation_id": prep_id,
            }

        if prep.tool_name == "prepare_reevaluation_request":
            return exam_backend.execute_reevaluation(
                preparation_id=prep_id,
                approver_token=confirmation.approver_token,
                user_role=confirmation.user_role,
                approver_id=approver_id,
            )

        if prep.tool_name == "prepare_answer_key_update":
            return exam_backend.approve_answer_key_change(
                preparation_id=prep_id,
                approver_token=confirmation.approver_token,
                user_role=confirmation.user_role,
                approver_id=approver_id,
            )

        if prep.tool_name == "prepare_merit_list_publication":
            return exam_backend.publish_merit_list(
                preparation_id=prep_id,
                approver_token=confirmation.approver_token,
                user_role=confirmation.user_role,
                approver_id=approver_id,
            )

        raise ValueError(
            f"No consequential execution mapping exists for '{prep.tool_name}'."
        )


examflow_agent = ExamFlowAgent()
