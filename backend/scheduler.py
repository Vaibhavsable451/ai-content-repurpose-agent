"""
scheduler.py
------------
Concept 5: Social Media Publisher & Scheduler.

Handles direct simulated/webhook scheduling and instant publishing of approved
content drafts to LinkedIn, X (Twitter), and Substack.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List

# In-memory mock schedule database (in production connects to LinkedIn/X OAuth API / Buffer API)
_SCHEDULED_POSTS: List[Dict[str, Any]] = []


def schedule_post(user_id: str, platform: str, post_text: str, scheduled_time: str = None) -> Dict[str, Any]:
    """Schedule a post for future auto-publishing."""
    post_id = f"sch_{str(uuid.uuid4())[:8]}"
    time_str = scheduled_time or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    record = {
        "post_id": post_id,
        "user_id": user_id,
        "platform": platform,
        "post_text": post_text[:500],
        "scheduled_time": time_str,
        "status": "scheduled",
    }
    
    _SCHEDULED_POSTS.append(record)
    return record


def publish_post_now(user_id: str, platform: str, post_text: str) -> Dict[str, Any]:
    """Instantly publish an approved post to social channel."""
    post_id = f"pub_{str(uuid.uuid4())[:8]}"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    record = {
        "post_id": post_id,
        "user_id": user_id,
        "platform": platform,
        "status": "published",
        "published_at": timestamp,
        "social_url": f"https://{platform}.com/post/{post_id}",
    }
    
    _SCHEDULED_POSTS.append(record)
    return record


def get_scheduled_posts(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all active or scheduled posts for user."""
    return [p for p in _SCHEDULED_POSTS if p.get("user_id") == user_id]
