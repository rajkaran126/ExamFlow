"""Role-Based Access Control (RBAC) and 5-Level Permission Framework."""

import hmac
import hashlib
import time
import secrets

from typing import Dict, Any, Tuple, Optional

from app.models import (
    UserRole,
    PermissionLevel,
    PreparedAction,
    PreparationStatus
)

from app.config import settings


# Mapping of all 21 tools to their permission levels and authorized roles.

TOOL_PERMISSIONS: Dict[str, Dict[str, Any]] = {
    # Level 2: Read-only tools
    "get_exam_details": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.CANDIDATE, UserRole.EVALUATOR, UserRole.PROCTOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve official exam details and schedule"
    },
    "get_candidate_details": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.CANDIDATE, UserRole.EVALUATOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve candidate registration and demographic details"
    },
    "get_candidate_scorecard": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.CANDIDATE, UserRole.EVALUATOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve raw, sectional, and normalized scorecard"
    },
    "get_candidate_responses": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.CANDIDATE, UserRole.EVALUATOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve question-by-question candidate responses"
    },
    "get_answer_key": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.CANDIDATE, UserRole.EVALUATOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve official answer key"
    },
    "get_shift_statistics": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.EVALUATOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve shift statistics"
    },
    "get_proctoring_report": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.PROCTOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve proctoring report"
    },
    "get_qualification_status": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.CANDIDATE, UserRole.EVALUATOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve qualification status"
    },
    "get_merit_list": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.CANDIDATE, UserRole.EVALUATOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve published merit list"
    },
    "get_category_cutoffs": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.CANDIDATE, UserRole.EVALUATOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve category-wise cutoffs"
    },
    "search_documents": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.CANDIDATE, UserRole.EVALUATOR, UserRole.PROCTOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Search examination documents"
    },
    "retrieve_document_chunks": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.CANDIDATE, UserRole.EVALUATOR, UserRole.PROCTOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve document page chunks"
    },
    "compare_examination_documents": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.EVALUATOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Compare examination documents"
    },
    "get_evaluation_history": {
        "level": PermissionLevel.LEVEL_2_READ,
        "allowed_roles": [UserRole.EVALUATOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Retrieve evaluation history"
    },

    # Level 4: Prepared-action tools
    "prepare_result_report": {
        "level": PermissionLevel.LEVEL_4_PREPARE,
        "allowed_roles": [UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Prepare result report"
    },
    "prepare_reevaluation_request": {
        "level": PermissionLevel.LEVEL_4_PREPARE,
        "allowed_roles": [UserRole.EVALUATOR, UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Prepare reevaluation request"
    },
    "prepare_answer_key_update": {
        "level": PermissionLevel.LEVEL_4_PREPARE,
        "allowed_roles": [UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Prepare answer key update"
    },
    "prepare_merit_list_publication": {
        "level": PermissionLevel.LEVEL_4_PREPARE,
        "allowed_roles": [UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Prepare merit list publication"
    },

    # Level 5: Consequential tools
    "execute_reevaluation": {
        "level": PermissionLevel.LEVEL_5_CONSEQUENTIAL,
        "allowed_roles": [UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Execute reevaluation"
    },
    "approve_answer_key_change": {
        "level": PermissionLevel.LEVEL_5_CONSEQUENTIAL,
        "allowed_roles": [UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Approve answer key change"
    },
    "publish_merit_list": {
        "level": PermissionLevel.LEVEL_5_CONSEQUENTIAL,
        "allowed_roles": [UserRole.EXAM_ADMIN, UserRole.SUPER_ADMIN],
        "description": "Publish merit list"
    }
}


class PermissionManager:
    """Enforces RBAC, candidate isolation and approval validation."""

    CANDIDATE_SCOPED_TOOLS = {
        "get_candidate_details",
        "get_candidate_scorecard",
        "get_candidate_responses",
        "get_qualification_status",
    }

    PREPARATION_TO_EXECUTION = {
        "prepare_reevaluation_request": "execute_reevaluation",
        "prepare_answer_key_update": "approve_answer_key_change",
        "prepare_merit_list_publication": "publish_merit_list",
    }

    @staticmethod
    def check_tool_permission(
        tool_name: str,
        user_role: UserRole,
        user_id: str,
        arguments: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Check role authorization and candidate-level data isolation."""

        if tool_name not in TOOL_PERMISSIONS:
            return False, f"Tool '{tool_name}' is not registered in the system."

        if not isinstance(user_role, UserRole):
            return False, "Permission Denied: Invalid user role."

        if not isinstance(user_id, str) or not user_id.strip():
            return False, "Permission Denied: Valid user identity is required."

        if not isinstance(arguments, dict):
            return False, "Permission Denied: Invalid tool arguments."

        tool_meta = TOOL_PERMISSIONS[tool_name]

        if user_role not in tool_meta["allowed_roles"]:
            return (
                False,
                f"Permission Denied: Role '{user_role.value}' "
                f"is not authorized to use tool '{tool_name}'."
            )

        # Candidate privacy isolation.
        if user_role == UserRole.CANDIDATE:
            if tool_name in PermissionManager.CANDIDATE_SCOPED_TOOLS:
                candidate_id = arguments.get("candidate_id")

                if not isinstance(candidate_id, str) or not candidate_id.strip():
                    return (
                        False,
                        "Permission Denied: Candidate ID is required "
                        "for candidate-specific data access."
                    )

                if not hmac.compare_digest(candidate_id, user_id):
                    return (
                        False,
                        "Permission Denied: Candidates can only access "
                        "their own records."
                    )

        return True, None

    @staticmethod
    def generate_approval_token(
        target_id: str,
        tool_name: str
    ) -> str:
        """Generate an unpredictable approval token."""

        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError("A valid action target is required.")

        if tool_name not in TOOL_PERMISSIONS:
            raise ValueError("Cannot generate token for an unknown tool.")

        if TOOL_PERMISSIONS[tool_name]["level"] != PermissionLevel.LEVEL_4_PREPARE:
            raise ValueError("Approval tokens can only be generated for prepared actions.")

        if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
            raise RuntimeError("A secure SECRET_KEY is required.")

        nonce = secrets.token_urlsafe(32)
        timestamp = str(time.time())

        payload = f"{tool_name}:{target_id}:{timestamp}:{nonce}"

        signature = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        # The random nonce makes each token unique.
        return f"tok_{nonce}_{signature}"

    
    
    @staticmethod
    def validate_approval(
        prepared_action: PreparedAction,
        provided_token: str,
        user_role: UserRole,
        approver_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate approval and record the authorized approver."""

        if not isinstance(prepared_action, PreparedAction):
            return False, "Security Error: Invalid prepared action."

        # 1. Check action lifecycle to prevent replay.
        if prepared_action.status == PreparationStatus.EXECUTED:
            return False, (
                "Consequential Action Error: Action has already been "
                "executed (replay prevented)."
            )

        if prepared_action.status == PreparationStatus.REJECTED:
            return False, "Consequential Action Error: Action was rejected."

        if prepared_action.status == PreparationStatus.EXPIRED:
            return False, (
                "Consequential Action Error: Approval token has expired."
            )

        if prepared_action.status != PreparationStatus.PENDING_APPROVAL:
            return False, "Security Error: Invalid preparation status."

        # 2. Validate approver identity.
        if not isinstance(approver_id, str) or not approver_id.strip():
            return False, "Security Error: Valid approver identity is required."

        # 3. Validate approver role.
        if not isinstance(user_role, UserRole):
            return False, "Permission Denied: Invalid approver role."

        if user_role not in (
            UserRole.EXAM_ADMIN,
            UserRole.SUPER_ADMIN
        ):
            return False, (
                f"Permission Denied: Role '{user_role.value}' "
                "cannot authorize consequential actions."
            )

        # 4. Validate preparation-to-execution mapping.
        expected_execution = (
            PermissionManager.PREPARATION_TO_EXECUTION.get(
                prepared_action.tool_name
            )
        )

        if expected_execution is None:
            return False, (
                "Security Error: No authorized execution mapping exists."
            )

        if expected_execution not in TOOL_PERMISSIONS:
            return False, "Security Error: Execution tool is not registered."

        if (
            TOOL_PERMISSIONS[expected_execution]["level"]
            != PermissionLevel.LEVEL_5_CONSEQUENTIAL
        ):
            return False, (
                "Security Error: Invalid consequential execution level."
            )

        # 5. Validate required approval role.
        if prepared_action.required_role not in (
            UserRole.EXAM_ADMIN,
            UserRole.SUPER_ADMIN
        ):
            return False, "Security Error: Invalid required approval role."

        if (
            user_role != UserRole.SUPER_ADMIN
            and user_role != prepared_action.required_role
        ):
            return False, (
                "Permission Denied: Required approval role not satisfied."
            )

        # 6. Validate expiration.
        if not isinstance(prepared_action.expires_at, (int, float)):
            return False, "Security Error: Invalid action expiry."

        if time.time() > prepared_action.expires_at:
            prepared_action.status = PreparationStatus.EXPIRED
            return False, (
                "Consequential Action Error: Approval token has expired."
            )

        # 7. Validate approval token.
        if not isinstance(provided_token, str) or not provided_token:
            return False, "Security Error: Approval token is required."

        stored_token = prepared_action.approver_token

        if not isinstance(stored_token, str) or not stored_token:
            return False, (
                "Security Error: Prepared action has no valid approval token."
            )

        if not hmac.compare_digest(stored_token, provided_token):
            return False, "Security Error: Invalid approval token supplied."

        # 8. Authorization is valid.
        # Approval metadata is recorded by the backend only
        # after the consequential operation succeeds.
        return True, None


permission_manager = PermissionManager()
