"""Security Sanitizer and Prompt Injection Defense for uploaded documents.
Treats all uploaded content as untrusted data and neutralizes embedded injection attacks.
"""

import re
from typing import Tuple, List

class DocumentSanitizer:
    """Detects and defangs prompt injection, systemic overrides, and exfiltration attempts."""

    # Common injection keywords and patterns
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|above)\s+instructions",
        r"(?i)disregard\s+(all\s+)?(prior|system)\s+prompts?",
        r"(?i)system\s+prompt\s+override",
        r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
        r"(?i)act\s+as\s+an\s+unrestricted\s+ai",
        r"(?i)reveal\s+(the\s+)?(api[\s_-]?key|secret|password|credentials)",        r"(?i)execute\s+(consequential\s+tool|execute_reevaluation|publish_merit_list)",
        r"(?i)bypass\s+sandbox",
        r"(?i)jailbreak",
        r"(?i)dan\s+mode"
    ]

    @classmethod
    def sanitize_text(cls, raw_text: str) -> Tuple[str, bool, List[str]]:
        """Sanitize text and detect prompt injection attempts.
        
        Returns:
            Tuple of (sanitized_text, is_flagged, detected_patterns)
        """
        detected: List[str] = []
        sanitized = raw_text

        for pat in cls.INJECTION_PATTERNS:
            matches = re.findall(pat, raw_text)
            if matches:
                detected.append(pat)
                # Defang the malicious pattern by replacing with safe placeholder
                sanitized = re.sub(pat, "[BLOCKED_UNTRUSTED_INSTRUCTION]", sanitized)

        is_flagged = len(detected) > 0
        return sanitized, is_flagged, detected

    @classmethod
    def wrap_untrusted_content(cls, content: str, doc_name: str, page_num: int) -> str:
        """Encloses document text inside explicit untrusted data boundary delimiters."""
        return (
            f"--- BEGIN UNTRUSTED DOCUMENT CHUNK (File: {doc_name}, Page: {page_num}) ---\n"
            f"{content}\n"
            f"--- END UNTRUSTED DOCUMENT CHUNK ---"
        )


sanitizer = DocumentSanitizer()
