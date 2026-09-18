"""
data_flywheel.py
-----------------
Concept 5: Data Flywheel.

Closes the loop: after a post is published, the user reports back how it
actually performed (qualitatively - "great engagement", "flopped", or a
short note on what worked). That feedback is embedded and saved into the
SAME style memory namespace the agent queries before drafting, tagged as
'performance_feedback' with a signal (positive/negative). Future drafts
therefore pull in not just "how the user writes" but "what has actually
worked for this user before" - a real flywheel, not a one-way memory.
"""

from typing import Dict

from memory_store import save_memory, query_memory, prune_negative_memory


def record_post_performance(user_id: str, post_text: str, performance_note: str, signal: str = "positive"):
    """signal: 'positive' | 'negative' | 'neutral'"""
    if signal == "negative":
        prune_negative_memory(user_id, post_text)

    combined_text = f"POST:\n{post_text}\n\nPERFORMANCE NOTE ({signal}):\n{performance_note}"
    return save_memory(
        namespace=f"style::{user_id}",
        text=combined_text,
        metadata={"type": "performance_feedback", "signal": signal},
    )



def recall_top_performing_patterns(user_id: str, draft_context: str, top_k: int = 3) -> Dict:
    """Pulls past performance feedback relevant to the current draft topic, so the
    agent can lean into patterns that worked and avoid ones that didn't."""
    hits = query_memory(namespace=f"style::{user_id}", query_text=draft_context, top_k=top_k * 2)
    positive = [h for h in hits if h["metadata"].get("signal") == "positive"][:top_k]
    negative = [h for h in hits if h["metadata"].get("signal") == "negative"][:top_k]
    return {"worked_before": positive, "did_not_work_before": negative}
