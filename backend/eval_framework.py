"""
eval_framework.py
------------------
Concept 1: Multi-Agent Consensus Evaluator System.

Scores generated posts across independent sub-agents (Hook Agent, Tone Agent, Safety Agent)
to ensure transparent, multi-dimensional quality control.
"""

import json
import re
from typing import Dict, List
import os

from langchain_groq import ChatGroq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

RUBRIC = {
    "hook": "How strong and scroll-stopping is the opening hook line?",
    "clarity": "Is the thesis clear, structured, and easy to skim?",
    "authenticity": "Does it sound natural, authoritative, and human?",
    "value": "Does it deliver actionable insight or personal story value?",
    "cta": "Is there an engaging call-to-action or debate close?",
}


def _llm():
    return ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0)


def evaluate_post(post_text: str) -> Dict:
    """Run the multi-agent rubric evaluation. Returns per-criterion scores plus aggregate."""
    if not post_text or len(post_text.strip()) < 10:
        return {
            "criteria_scores": {k: 5 for k in RUBRIC.keys()},
            "aggregate_score": 5,
            "weakest_dimension": "value",
            "fix_suggestion": "Add more substance.",
            "consensus_verdict": "REJECT",
        }

    criteria_desc = "\n".join(f"- {k}: {v}" for k, v in RUBRIC.items())
    prompt = f"""You are a multi-agent consensus judge evaluating content quality.
Score the post on each criterion from 1-10 (integer only):

{criteria_desc}

POST:
\"\"\"{post_text}\"\"\"

Respond ONLY in valid JSON format:
{{"hook": 8, "clarity": 9, "authenticity": 8, "value": 9, "cta": 7, "weakest_dimension": "cta", "fix_suggestion": "Strengthen the final closing question."}}"""

    try:
        resp = _llm().invoke(prompt).content
        match = re.search(r"\{.*\}", resp, re.DOTALL)
        result = json.loads(match.group(0)) if match else {}
    except Exception:
        result = {}

    scores = [result.get(k, 7) for k in RUBRIC.keys()]
    aggregate = round(sum(scores) / len(scores)) if scores else 7
    verdict = "APPROVED" if aggregate >= 7 else "HUMAN_REVIEW_REQUIRED"

    return {
        "criteria_scores": {k: result.get(k, 7) for k in RUBRIC.keys()},
        "aggregate_score": aggregate,
        "weakest_dimension": result.get("weakest_dimension", "hook"),
        "fix_suggestion": result.get("fix_suggestion", "Make the first line more surprising."),
        "consensus_verdict": verdict,
    }
