"""
agent.py
--------
Core AI Content Repurposing Agent.

Controlled pipeline:

1. Load user style memory
2. Check similar previous content
3. Load performance history
4. Generate LinkedIn post + X thread + blog summary
5. Evaluate LinkedIn post
6. Rewrite once if needed
7. Run safety guardrails
8. Generate A/B hooks
9. Save content memory
10. Return structured result

IMPORTANT:
This version intentionally does NOT use AgentExecutor or
create_tool_calling_agent.

That prevents the previous:
    "Agent stopped due to max iterations"

problem and gives the FastAPI API a predictable runtime.
"""

import json
import os
import re
from typing import Dict, Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from memory_store import (
    recall_style,
    save_style_example,
    recall_similar_content,
    save_content_record,
)

from eval_framework import evaluate_post
from guardrails import run_guardrails
from data_flywheel import recall_top_performing_patterns
from observability import RunTracer


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile",
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_REWRITE_ATTEMPTS = 1
MAX_STYLE_EXAMPLES = 3
MAX_SIMILAR_CONTENT = 3

_CURRENT_USER = {
    "id": "default_user"
}


# ============================================================
# USER CONTEXT
# ============================================================

def set_current_user(user_id: str):
    """
    Set the current user for memory operations.
    """

    _CURRENT_USER["id"] = (
        user_id.strip()
        if user_id and user_id.strip()
        else "default_user"
    )


# ============================================================
# LLM
# ============================================================

def _llm():
    """
    Create the Groq chat model.
    """

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set in environment variables."
        )

    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.4,
        max_tokens=4000,
    )


# ============================================================
# TEXT HELPERS
# ============================================================

def _safe_string(value: Any) -> str:
    """
    Safely convert a value to string.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


def _clean_response_text(content: Any) -> str:
    """
    Convert LangChain response content into plain text.
    """

    if content is None:
        return ""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):

        parts = []

        for item in content:

            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):

                if "text" in item:
                    parts.append(
                        str(item["text"])
                    )

        return "".join(parts).strip()

    return str(content).strip()


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Safely extract JSON from an LLM response.

    Supports:

    - normal JSON
    - ```json blocks
    - surrounding explanatory text
    """

    if not text:
        return {}

    text = text.strip()

    # --------------------------------------------------------
    # Remove markdown fences
    # --------------------------------------------------------

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```\s*",
        "",
        text,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    text = text.strip()

    # --------------------------------------------------------
    # Direct JSON
    # --------------------------------------------------------

    try:

        parsed = json.loads(text)

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # JSON embedded inside other text
    # --------------------------------------------------------

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return {}

    candidate = text[start:end + 1]

    try:

        parsed = json.loads(candidate)

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        return {}

    return {}


# ============================================================
# STYLE MEMORY
# ============================================================

def _get_style_memory(
    user_id: str,
    source_content: str,
) -> str:
    """
    Retrieve accepted writing examples from Pinecone.
    """

    try:

        hits = recall_style(
            user_id,
            source_content,
            top_k=MAX_STYLE_EXAMPLES,
        )

        if not hits:

            return (
                "No previous style examples are available. "
                "Use a clear, confident, natural professional voice."
            )

        examples = []

        for hit in hits:

            text = _safe_string(
                hit.get("text", "")
            )

            if text:
                examples.append(text[:1000])

        if not examples:

            return (
                "No usable style examples found. "
                "Use a clear, confident, natural professional voice."
            )

        return "\n\n--- STYLE EXAMPLE ---\n\n".join(
            examples
        )

    except Exception as exc:

        print(
            f"[memory] style recall failed: {exc}"
        )

        return (
            "Style memory unavailable for this run. "
            "Use a clear, confident, natural professional voice."
        )


# ============================================================
# SIMILAR CONTENT MEMORY
# ============================================================

def _get_similar_content(
    user_id: str,
    source_content: str,
) -> str:
    """
    Check whether similar content already exists.
    """

    try:

        hits = recall_similar_content(
            user_id,
            source_content,
            top_k=MAX_SIMILAR_CONTENT,
        )

        if not hits:
            return "No similar past content found."

        results = []

        for hit in hits:

            score = float(
                hit.get("score", 0)
            )

            text = _safe_string(
                hit.get("text", "")
            )

            if score >= 0.85 and text:

                results.append(
                    f"[HIGH SIMILARITY {score:.2f}] "
                    f"{text[:500]}"
                )

        if not results:

            return (
                "No sufficiently similar content found."
            )

        return "\n".join(results)

    except Exception as exc:

        print(
            f"[memory] similar-content recall failed: {exc}"
        )

        return (
            "Similar-content memory unavailable."
        )


# ============================================================
# PERFORMANCE MEMORY
# ============================================================

def _get_performance_history(
    user_id: str,
    source_content: str,
) -> str:
    """
    Retrieve previous performance patterns.
    """

    try:

        result = recall_top_performing_patterns(
            user_id,
            source_content,
        )

        worked = "\n".join(
            result.get(
                "worked_before",
                [],
            )
        )

        avoid = "\n".join(
            result.get(
                "did_not_work_before",
                [],
            )
        )

        if not worked:

            worked = (
                "No positive performance history yet."
            )

        if not avoid:

            avoid = (
                "No negative performance history yet."
            )

        return (
            "WHAT WORKED BEFORE:\n"
            f"{worked}\n\n"
            "WHAT DID NOT WORK BEFORE:\n"
            f"{avoid}"
        )

    except Exception as exc:

        print(
            f"[memory] performance recall failed: {exc}"
        )

        return (
            "No performance history is available."
        )


# ============================================================
# INITIAL GENERATION
# ============================================================

def _generate_content(
    source_content: str,
    style_memory: str,
    similar_content: str,
    performance_history: str,
) -> Dict[str, Any]:
    """
    Generate all primary content outputs in one Groq call.
    """

    llm = _llm()

    prompt = f"""
You are an expert AI content repurposing assistant.

Transform the SOURCE CONTENT into:

1. LinkedIn post
2. X/Twitter thread with 5-7 posts
3. Short blog summary of 2-3 sentences

The content should sound natural and human.

Do not invent facts that are not supported by the source.

Use STYLE MEMORY only to understand writing voice.
Do not copy previous posts.

Use SIMILAR CONTENT to avoid repeating old ideas.

Use PERFORMANCE HISTORY to understand patterns that
previously worked or did not work.

============================================================
SOURCE CONTENT
============================================================

{source_content}

============================================================
STYLE MEMORY
============================================================

{style_memory}

============================================================
SIMILAR PAST CONTENT
============================================================

{similar_content}

============================================================
PERFORMANCE HISTORY
============================================================

{performance_history}

============================================================
LINKEDIN REQUIREMENTS
============================================================

- Strong opening hook
- Clear value
- Easy to scan
- Natural professional tone
- Avoid generic AI language
- Avoid excessive emojis
- Include a useful CTA when appropriate
- Do not claim unsupported statistics
- Do not invent facts
- Do not mention that AI generated the post

============================================================
X/TWITTER THREAD REQUIREMENTS
============================================================

- 5-7 posts
- Each post should be concise
- Logical progression
- Strong first post
- Useful information
- Natural thread ending
- Do not invent facts

============================================================
BLOG SUMMARY
============================================================

- 2-3 concise sentences
- Preserve the main idea
- No unsupported claims

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

{{
    "linkedin_post": "...",
    "twitter_thread": "...",
    "blog_summary": "..."
}}
"""

    response = llm.invoke(prompt)

    text = _clean_response_text(
        response.content
    )

    result = _extract_json(text)

    if not result:

        raise RuntimeError(
            "Groq returned an invalid content response."
        )

    linkedin_post = _safe_string(
        result.get("linkedin_post")
    )

    twitter_thread = _safe_string(
        result.get("twitter_thread")
    )

    blog_summary = _safe_string(
        result.get("blog_summary")
    )

    if not linkedin_post:

        raise RuntimeError(
            "Groq returned an empty LinkedIn post."
        )

    return {
        "linkedin_post": linkedin_post,
        "twitter_thread": twitter_thread,
        "blog_summary": blog_summary,
        "raw": "",
    }


# ============================================================
# REWRITE
# ============================================================

def _rewrite_linkedin_post(
    current_post: str,
    score_result: Dict[str, Any],
) -> str:
    """
    Rewrite the LinkedIn post once using evaluation feedback.
    """

    llm = _llm()

    weakest = _safe_string(
        score_result.get(
            "weakest_dimension",
            "clarity",
        )
    )

    fix = _safe_string(
        score_result.get(
            "fix_suggestion",
            "Improve clarity and usefulness.",
        )
    )

    prompt = f"""
Improve this LinkedIn post.

============================================================
CURRENT POST
============================================================

{current_post}

============================================================
EVALUATION
============================================================

Weakest dimension:
{weakest}

Required improvement:
{fix}

============================================================
REQUIREMENTS
============================================================

- Rewrite the entire post.
- Preserve the original factual meaning.
- Improve specifically the weakest dimension.
- Make the opening stronger.
- Make the value clearer.
- Keep it natural and human.
- Avoid generic AI wording.
- Avoid unsupported claims.
- Do not invent statistics.
- Do not explain your changes.
- Return ONLY the revised LinkedIn post.
"""

    response = llm.invoke(prompt)

    return _clean_response_text(
        response.content
    ).strip()


# ============================================================
# HOOK VARIANTS
# ============================================================

def _generate_hook_variants(
    post_body: str,
) -> Dict[str, str]:
    """
    Generate two alternative hooks.
    """

    llm = _llm()

    prompt = f"""
Create two different opening hooks for this LinkedIn post.

============================================================
POST
============================================================

{post_body}

============================================================
REQUIREMENTS
============================================================

Variant A:
- Bold insight or claim
- 1-2 lines
- Professional

Variant B:
- Personal/story-driven opening
- 1-2 lines
- Natural

Do not change the meaning of the post.

Return ONLY valid JSON:

{{
    "variant_a": "...",
    "variant_b": "..."
}}
"""

    response = llm.invoke(prompt)

    text = _clean_response_text(
        response.content
    )

    result = _extract_json(text)

    return {
        "variant_a": _safe_string(
            result.get("variant_a")
        ),
        "variant_b": _safe_string(
            result.get("variant_b")
        ),
    }


# ============================================================
# SCORING
# ============================================================

def _score_post(
    post_text: str,
) -> Dict[str, Any]:
    """
    Run the project's evaluation framework.
    """

    if not post_text:

        return {
            "aggregate_score": 0,
            "weakest_dimension": "clarity",
            "fix_suggestion": "Generate a non-empty LinkedIn post.",
        }

    result = evaluate_post(
        post_text
    )

    if not isinstance(result, dict):

        return {
            "aggregate_score": 0,
            "weakest_dimension": "clarity",
            "fix_suggestion": "Evaluation returned an invalid result.",
        }

    return result


# ============================================================
# SAFETY
# ============================================================

def _check_safety(
    post_text: str,
) -> Dict[str, Any]:
    """
    Run server-side safety/PII/content guardrails.
    """

    if not post_text:

        return {
            "passed": False,
            "flags": [
                "LinkedIn post is empty."
            ],
        }

    try:

        result = run_guardrails(
            post_text
        )

        if not isinstance(result, dict):

            return {
                "passed": False,
                "flags": [
                    "Safety system returned an invalid result."
                ],
            }

        return result

    except Exception as exc:

        print(
            f"[guardrails] safety check failed: {exc}"
        )

        return {
            "passed": False,
            "flags": [
                "Safety check failed unexpectedly."
            ],
        }


# ============================================================
# MAIN REPURPOSING PIPELINE
# ============================================================

def repurpose_content(
    user_id: str,
    source_content: str,
    run_id: str = "run",
) -> Dict[str, Any]:
    """
    Main entry point.

    Controlled deterministic pipeline:

        memory
          ↓
        generation
          ↓
        scoring
          ↓
        one rewrite if needed
          ↓
        safety
          ↓
        hooks
          ↓
        memory save
          ↓
        final response
    """

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not source_content:

        raise ValueError(
            "source_content is required."
        )

    if len(source_content.strip()) < 20:

        raise ValueError(
            "source_content is too short. "
            "Minimum 20 characters."
        )

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    user_id = (
        user_id.strip()
        if user_id and user_id.strip()
        else "default_user"
    )

    set_current_user(
        user_id
    )

    # --------------------------------------------------------
    # TRACER
    # --------------------------------------------------------

    tracer = RunTracer(
        run_id=run_id,
        user_id=user_id,
    )

    final_score = 0
    rewrite_attempts = 0
    needs_human_review = False
    review_reason = ""

    linkedin_post = ""
    twitter_thread = ""
    blog_summary = ""
    hook_a = ""
    hook_b = ""
    raw_output = ""

    # --------------------------------------------------------
    # PIPELINE
    # --------------------------------------------------------

    with tracer.span(
        "content_repurpose_pipeline",
        source_len=len(source_content),
    ) as span:

        # ====================================================
        # STEP 1 — MEMORY
        # ====================================================

        style_memory = _get_style_memory(
            user_id,
            source_content,
        )

        similar_content = _get_similar_content(
            user_id,
            source_content,
        )

        performance_history = _get_performance_history(
            user_id,
            source_content,
        )

        # ====================================================
        # STEP 2 — GENERATION
        # ====================================================

        generated = _generate_content(
            source_content=source_content,
            style_memory=style_memory,
            similar_content=similar_content,
            performance_history=performance_history,
        )

        linkedin_post = generated[
            "linkedin_post"
        ]

        twitter_thread = generated[
            "twitter_thread"
        ]

        blog_summary = generated[
            "blog_summary"
        ]

        raw_output = generated.get(
            "raw",
            "",
        )

        # ====================================================
        # STEP 3 — SCORE
        # ====================================================

        score_result = _score_post(
            linkedin_post
        )

        final_score = int(
            score_result.get(
                "aggregate_score",
                0,
            )
        )

        # ====================================================
        # STEP 4 — ONE CONTROLLED REWRITE
        # ====================================================

        if (
            final_score < 10
            and rewrite_attempts < MAX_REWRITE_ATTEMPTS
        ):

            rewrite_attempts += 1

            try:

                revised_post = _rewrite_linkedin_post(
                    linkedin_post,
                    score_result,
                )

                if revised_post:

                    linkedin_post = revised_post

                    # Re-score revised version.
                    score_result = _score_post(
                        linkedin_post
                    )

                    final_score = int(
                        score_result.get(
                            "aggregate_score",
                            0,
                        )
                    )

            except Exception as exc:

                print(
                    f"[{run_id}] rewrite failed: {exc}"
                )

        # ====================================================
        # STEP 5 — SAFETY
        # ====================================================

        safety_result = _check_safety(
            linkedin_post
        )

        if not safety_result.get(
            "passed",
            False,
        ):

            needs_human_review = True

            flags = safety_result.get(
                "flags",
                [],
            )

            if isinstance(flags, list):

                review_reason = "; ".join(
                    str(flag)
                    for flag in flags
                )

            else:

                review_reason = str(
                    flags
                )

            if not review_reason:

                review_reason = (
                    "Content safety checks did not pass."
                )

        # ====================================================
        # STEP 6 — HOOK VARIANTS
        # ====================================================

        if not needs_human_review:

            try:

                hooks = _generate_hook_variants(
                    linkedin_post
                )

                hook_a = hooks.get(
                    "variant_a",
                    "",
                )

                hook_b = hooks.get(
                    "variant_b",
                    "",
                )

            except Exception as exc:

                print(
                    f"[{run_id}] hook generation failed: {exc}"
                )

        # ====================================================
        # STEP 7 — SAVE CONTENT MEMORY
        # ====================================================

        if not needs_human_review:

            try:

                save_content_record(
                    user_id,
                    source_content,
                    {
                        "linkedin":
                            linkedin_post,

                        "twitter":
                            twitter_thread,

                        "blog":
                            blog_summary,
                    },
                )

            except Exception as exc:

                # Memory failure should not destroy
                # an otherwise successful generation.

                print(
                    f"[{run_id}] "
                    f"content memory save failed: {exc}"
                )

        # ====================================================
        # TRACE
        # ====================================================

        span["final_score"] = final_score

        span["rewrite_attempts"] = (
            rewrite_attempts
        )

        span["needs_human_review"] = (
            needs_human_review
        )

    # ========================================================
    # FINISH TRACE
    # ========================================================

    trace_summary = tracer.finish()

    # ========================================================
    # FINAL STRUCTURED RESPONSE
    # ========================================================

    return {
        "linkedin_post": linkedin_post,

        "twitter_thread": twitter_thread,

        "blog_summary": blog_summary,

        "final_score": str(
            final_score
        ),

        "hook_variant_a": hook_a,

        "hook_variant_b": hook_b,

        "needs_human_review":
            needs_human_review,

        "review_reason":
            review_reason,

        "run_id":
            run_id,

        "raw":
            raw_output,

        "_trace": {
            "run_id":
                trace_summary.get(
                    "run_id",
                    run_id,
                ),

            "total_latency_ms":
                trace_summary.get(
                    "total_latency_ms",
                    0,
                ),
        },
    }