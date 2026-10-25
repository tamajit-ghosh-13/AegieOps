"""LLM Prompt-Injection Defense & Telemetry Sanitizer (AegisOps Sprint 4).

Shields agent reasoning nodes (Triage, Propose) against adversarial prompt injections
embedded within untrusted telemetry (logs, exception stack traces, HTTP request headers,
and external alert messages):

Defense Pipeline:
1. Control Token Stripping: Eliminates special chat tokens (<|im_start|>, [INST], SYSTEM:).
2. Adversarial Directive Neutralization: Regex neutralization of jailbreak phrases
   (e.g., "ignore previous instructions", "system override", "return action=...").
3. Structural Data Boundary Isolation: Wraps external telemetry in JSON-escaped delimiters.
4. Schema Boundary Enforcement: Enforces strict Pydantic enum validation for actions.
"""

from __future__ import annotations

import html
import re
from typing import Any

# Special tokens commonly used to hijack chat model role boundaries
CONTROL_TOKENS = [
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"<\|system\|>",
    r"<\|user\|>",
    r"<\|assistant\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"<s>",
    r"</s>",
    r"<system>",
    r"</system>",
    r"<script[\s\S]*?</script>",
]

# High-risk adversarial injection patterns
ADVERSARIAL_PATTERNS = [
    (re.compile(r"(?i)\b(ignore|disregard|forget)\s+(all\s+)?(previous\s+|prior\s+|above\s+|system\s+)?(instructions|prompts|rules|directives|commands)\b"), "[SANITIZED_PROMPT_INJECTION: IGNORE_PREVIOUS_INSTRUCTIONS]"),
    (re.compile(r"(?i)\b(system\s+override|admin\s+override|emergency\s+override|root\s+override)\b"), "[SANITIZED_PROMPT_INJECTION: SYSTEM_OVERRIDE]"),
    (re.compile(r"(?i)\b(jailbreak|dan\s+mode|developer\s+mode|god\s+mode)\b"), "[SANITIZED_PROMPT_INJECTION: JAILBREAK_ATTEMPT]"),
    (re.compile(r"(?i)\b(you\s+are\s+now|act\s+as\s+a|pretend\s+to\s+be)\s+(an?\s+)?(unrestricted|evil|different|hacked)\s+(ai|assistant|model)\b"), "[SANITIZED_PROMPT_INJECTION: ROLE_HIJACK]"),
    (re.compile(r"(?i)\b(return|output|respond\s+with)\s*:\s*(action\s*=|format\s*=|json\s*=)"), "[SANITIZED_PROMPT_INJECTION: FORCED_OUTPUT]"),
    (re.compile(r"(?i)\b(classify\s+this\s+incident\s+as|propose\s+action\s*=)\b"), "[SANITIZED_PROMPT_INJECTION: DIRECTIVE_HIJACK]"),
]


def strip_control_tokens(text: str) -> str:
    """Strip chat model control tokens and raw HTML scripts."""
    cleaned = text
    for token_pattern in CONTROL_TOKENS:
        cleaned = re.sub(token_pattern, "[STRIPPED_TOKEN]", cleaned, flags=re.IGNORECASE)
    return cleaned


def neutralize_prompt_injections(text: str) -> tuple[str, list[str]]:
    """Detect and neutralize prompt-injection phrases, preserving harmless diagnostic context.

    Returns (sanitized_text, detected_attack_categories).
    """
    detected: list[str] = []
    sanitized = text

    for pattern, replacement in ADVERSARIAL_PATTERNS:
        matches = pattern.findall(sanitized)
        if matches:
            category = replacement.strip("[]").split(": ")[-1]
            detected.append(category)
            sanitized = pattern.sub(replacement, sanitized)

    return sanitized, detected


def contain_telemetry_boundary(text: str) -> str:
    """Enclose untrusted diagnostic text within explicit data boundaries."""
    escaped = html.escape(text)
    return f"<<<UNTRUSTED_TELEMETRY_LOG_CONTENT>>>\n{escaped}\n<<<END_UNTRUSTED_CONTENT>>>"


def sanitize_text(text: str | None) -> str:
    """Full-pipeline sanitization for log lines, exception messages, and alerts."""
    if not text:
        return ""
    # 1. Strip special tokens
    s = strip_control_tokens(text)
    # 2. Neutralize adversarial directives
    s, _ = neutralize_prompt_injections(s)
    # 3. Clean excessive whitespace
    s = " ".join(s.split())
    return s


def sanitize_telemetry_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize dictionary values before feeding into LLM context."""
    sanitized: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, str):
            sanitized[k] = sanitize_text(v)
        elif isinstance(v, dict):
            sanitized[k] = sanitize_telemetry_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [
                sanitize_text(item) if isinstance(item, str)
                else sanitize_telemetry_dict(item) if isinstance(item, dict)
                else item
                for item in v
            ]
        else:
            sanitized[k] = v
    return sanitized
