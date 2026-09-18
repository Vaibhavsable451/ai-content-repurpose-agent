"""
main.py
-------
FastAPI backend for the AI Content Repurposing & Scoring Agent.
Features:
 - Multi-Agent Consensus Evaluation
 - Pinecone Memory Auto-Pruning Data Flywheel
 - Telemetry & Cost Observability
 - Direct Social Publishing & Scheduling Engine
"""

import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import repurpose_content
from data_flywheel import record_post_performance
from memory_store import save_style_example, get_embedder, get_index
from scheduler import schedule_post, publish_post_now, get_scheduled_posts

app = FastAPI(title="AI Content Repurposing Agent", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RepurposeRequest(BaseModel):
    user_id: str = "default_user"
    source_content: str


class RepurposeResponse(BaseModel):
    linkedin_post: str = ""
    twitter_thread: str = ""
    blog_summary: str = ""
    final_score: str = ""
    hook_variant_a: str = ""
    hook_variant_b: str = ""
    needs_human_review: bool = False
    review_reason: str = ""
    run_id: str = ""
    raw: str = ""


class FeedbackRequest(BaseModel):
    user_id: str = "default_user"
    post_text: str
    performance_note: str
    signal: str = "positive"  # positive | negative | neutral


class ApprovalRequest(BaseModel):
    user_id: str = "default_user"
    post_text: str
    approved: bool
    edited_text: str = ""


class ScheduleRequest(BaseModel):
    user_id: str = "default_user"
    platform: str = "linkedin"
    post_text: str
    scheduled_time: Optional[str] = None


class PublishRequest(BaseModel):
    user_id: str = "default_user"
    platform: str = "linkedin"
    post_text: str


@app.on_event("startup")
def warm_up_models():
    """Pre-load embedding model and Pinecone index at server startup."""
    print("Warming up embedding model and Pinecone index...")
    try:
        get_embedder()
        get_index()
        print("Warm-up complete. Backend ready.")
    except Exception as e:
        print(f"Warm-up failed: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/repurpose", response_model=RepurposeResponse)
def repurpose(req: RepurposeRequest):
    if not req.source_content or len(req.source_content.strip()) < 20:
        raise HTTPException(status_code=400, detail="source_content is too short.")
    run_id = str(uuid.uuid4())[:8]
    try:
        result = repurpose_content(req.user_id, req.source_content, run_id=run_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return RepurposeResponse(
        linkedin_post=result.get("linkedin_post", ""),
        twitter_thread=result.get("twitter_thread", ""),
        blog_summary=result.get("blog_summary", ""),
        final_score=str(result.get("final_score", "")),
        hook_variant_a=result.get("hook_variant_a", ""),
        hook_variant_b=result.get("hook_variant_b", ""),
        needs_human_review=bool(result.get("needs_human_review", False)),
        review_reason=result.get("review_reason", ""),
        run_id=run_id,
        raw=result.get("raw", "") if "raw" in result else "",
    )


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    """Data Flywheel & Auto-Pruning feedback endpoint."""
    try:
        record_post_performance(req.user_id, req.post_text, req.performance_note, req.signal)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "recorded", "signal": req.signal}


@app.post("/approve")
def approve_flagged_post(req: ApprovalRequest):
    """Human-in-the-Loop review endpoint."""
    if not req.approved:
        return {"status": "rejected", "saved": False}
    final_text = req.edited_text.strip() or req.post_text
    try:
        save_style_example(req.user_id, final_text, platform="linkedin")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "approved", "saved": True}


@app.post("/publish")
def publish_now(req: PublishRequest):
    """Direct instant publishing to social platform."""
    try:
        result = publish_post_now(req.user_id, req.platform, req.post_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/schedule")
def schedule(req: ScheduleRequest):
    """Schedule post for auto-publishing."""
    try:
        result = schedule_post(req.user_id, req.platform, req.post_text, req.scheduled_time)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scheduled-posts/{user_id}")
def list_scheduled(user_id: str):
    """Get all scheduled posts for user."""
    return {"user_id": user_id, "posts": get_scheduled_posts(user_id)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)