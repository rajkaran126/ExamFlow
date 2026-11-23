
"""Context and Memory Manager for EXAMFLOW AI.

Maintains isolated per-session conversation state, attached document
references, examination context, and pending consequential actions.

Security:
- A session belongs to exactly one user.
- Existing session ownership and role cannot be overwritten.
- Identity must come from a trusted authentication layer.
"""

import time
from typing import Dict, List, Optional

from app.models import ChatMessage, DocumentMetadata, PreparedAction, UserRole


class SessionContext:
    """Encapsulates isolated state for a single user conversation session."""

    def __init__(self, session_id: str, user_id: str, user_role: UserRole):
        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty.")

        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty.")

        if not isinstance(user_role, UserRole):
            raise ValueError("A valid authenticated user role is required.")

        self.session_id = session_id
        self.user_id = user_id
        self.user_role = user_role

        self.active_exam_id: str = "EXAM-2026-GATE"
        self.active_candidate_id: Optional[str] = None
        self.active_shift_id: Optional[str] = None

        self.history: List[ChatMessage] = []
        self.attached_docs: Dict[str, DocumentMetadata] = {}
        self.pending_actions: Dict[str, PreparedAction] = {}

        self.last_accessed = time.time()

    def touch(self) -> None:
        """Update the last-accessed timestamp."""
        self.last_accessed = time.time()

    def add_message(self, message: ChatMessage) -> None:
        self.history.append(message)
        self.touch()

    def attach_document(self, metadata: DocumentMetadata) -> None:
        self.attached_docs[metadata.doc_id] = metadata
        self.touch()

    def remove_document(self, doc_id: str) -> bool:
        if doc_id not in self.attached_docs:
            return False

        del self.attached_docs[doc_id]
        self.touch()
        return True

    def get_recent_history(self, limit: int = 12) -> List[ChatMessage]:
        if limit <= 0:
            return []

        self.touch()
        return self.history[-limit:]

    def clear(self) -> None:
        """Clear session data without changing its owner or identity."""
        self.history.clear()
        self.attached_docs.clear()
        self.pending_actions.clear()

        self.active_candidate_id = None
        self.active_shift_id = None

        self.touch()


class ContextManager:
    """Manages sessions with strict ownership and role isolation."""

    def __init__(self):
        self.sessions: Dict[str, SessionContext] = {}

    def get_or_create_session(
        self,
        session_id: str,
        user_id: str = "default_user",
        user_role: UserRole = UserRole.EXAM_ADMIN
    ) -> SessionContext:

        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty.")

        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty.")

        if not isinstance(user_role, UserRole):
            raise ValueError("A valid authenticated user role is required.")

        session = self.sessions.get(session_id)

        if session is None:
            session = SessionContext(
                session_id=session_id,
                user_id=user_id,
                user_role=user_role
            )

            self.sessions[session_id] = session
            return session

        # SECURITY: Never allow an existing session's owner or role
        # to be overwritten by a later request.
        if session.user_id != user_id:
            raise PermissionError(
                "Session access denied: this session belongs to another user."
            )

        if session.user_role != user_role:
            raise PermissionError(
                "Session access denied: authenticated role does not match "
                "the role associated with this session."
            )

        session.touch()
        return session

    def get_session(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[SessionContext]:
        """Retrieve a session only when the requesting user owns it."""

        session = self.sessions.get(session_id)

        if session is None:
            return None

        if session.user_id != user_id:
            raise PermissionError(
                "Session access denied: this session belongs to another user."
            )

        session.touch()
        return session

    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a session only when the requesting user owns it."""

        session = self.sessions.get(session_id)

        if session is None:
            return False

        if session.user_id != user_id:
            raise PermissionError(
                "Session deletion denied: this session belongs to another user."
            )

        del self.sessions[session_id]
        return True

    def cleanup_expired_sessions(self, max_idle_hours: float = 24.0) -> int:
        """Remove expired in-memory sessions and return the removal count."""

        if max_idle_hours <= 0:
            raise ValueError("Session expiry must be greater than zero.")

        now = time.time()
        expiry_seconds = max_idle_hours * 3600

        expired = [
            session_id
            for session_id, session in self.sessions.items()
            if now - session.last_accessed > expiry_seconds
        ]

        for session_id in expired:
            del self.sessions[session_id]

        return len(expired)


context_manager = ContextManager()
