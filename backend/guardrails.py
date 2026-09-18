"""
guardrails.py
-------------
Concept 2: Guardrails & Content Safety Layer.

Runs before any generated content is returned to the user or saved to
memory. Catches: obvious PII leakage, banned/toxic language, and
brand-unsafe claims (fabricated stats, absolute/legal-risk language).
Flags -> triggers human-in-the-loop review instead of silent auto-publish.
"""

import re
from typing import Dict, List

PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"),
    "ssn_like": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}

TOXIC_TERMS = [
    "idiot", "stupid", "hate you", "kill yourself", "worthless",
]

RISKY_CLAIM_PATTERNS = [
    re.compile(r"\bguaranteed?\b", re.IGNORECASE),
    re.compile(r"\b100%\s*(guarantee|proven|effective)\b", re.IGNORECASE),
    re.compile(r"\bcure[sd]?\b", re.IGNORECASE),
    re.compile(r"\bnever fails?\b", re.IGNORECASE),
]


def run_guardrails(text: str) -> Dict:
    """Returns {passed: bool, flags: [...], severity: 'low'|'medium'|'high'}"""
    flags: List[str] = []

    for label, pattern in PII_PATTERNS.items():
        if pattern.search(text):
            flags.append(f"Possible PII detected: {label}")

    lowered = text.lower()
    for term in TOXIC_TERMS:
        if term in lowered:
            flags.append(f"Toxic/unsafe language detected: '{term}'")

    for pattern in RISKY_CLAIM_PATTERNS:
        if pattern.search(text):
            flags.append(f"Risky absolute/legal-exposure claim detected: '{pattern.pattern}'")

    if not flags:
        return {"passed": True, "flags": [], "severity": "none"}

    severity = "high" if any("PII" in f or "Toxic" in f for f in flags) else "medium"
    return {"passed": False, "flags": flags, "severity": severity}
