"""
memory_store.py
---------------
Long-term memory layer for the AI Content Repurposing Agent.

Memory types:
1. style memory
   -> accepted/finalized posts used to preserve writing style

2. content memory
   -> previous source content + generated outputs

Embeddings:
    sentence-transformers/all-MiniLM-L6-v2

Vector database:
    Pinecone
"""

import os
import time
import uuid
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec


# ============================================================
# ENVIRONMENT
# ============================================================

# Load backend/.env
load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

# all-MiniLM-L6-v2 = 384 dimensions
EMBEDDING_DIM = 384

PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "content-agent-memory",
).strip()


# ============================================================
# LAZY SINGLETONS
# ============================================================

_embedder: Optional[HuggingFaceEmbeddings] = None
_pc: Optional[Pinecone] = None
_index = None


# ============================================================
# ENV HELPERS
# ============================================================

def _get_pinecone_api_key() -> str:
    """
    Read Pinecone API key when it is actually needed.

    Reading it lazily is safer during FastAPI startup and makes
    environment changes easier to detect.
    """

    api_key = os.getenv(
        "PINECONE_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "PINECONE_API_KEY is not set in environment variables."
        )

    return api_key


# ============================================================
# EMBEDDINGS
# ============================================================

def get_embedder() -> HuggingFaceEmbeddings:
    """
    Lazily initialize the HuggingFace embedding model.

    Uses the current langchain-huggingface integration.
    """

    global _embedder

    if _embedder is None:

        print(
            f"[memory] Loading embedding model: "
            f"{EMBEDDING_MODEL}"
        )

        _embedder = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL
        )

    return _embedder


def _embed(text: str) -> List[float]:
    """
    Convert text into a 384-dimensional embedding.
    """

    if not text or not text.strip():
        raise ValueError(
            "Cannot create an embedding from empty text."
        )

    vector = get_embedder().embed_query(
        text.strip()
    )

    return vector


# ============================================================
# PINECONE CLIENT
# ============================================================

def get_pinecone_client() -> Pinecone:
    """
    Lazily initialize the Pinecone client.
    """

    global _pc

    if _pc is None:

        api_key = _get_pinecone_api_key()

        print(
            "[memory] Connecting to Pinecone..."
        )

        _pc = Pinecone(
            api_key=api_key
        )

    return _pc


# ============================================================
# PINECONE INDEX
# ============================================================

def get_index():
    """
    Lazily connect to the Pinecone index.

    Creates the index automatically when it does not exist.
    """

    global _index

    if _index is not None:
        return _index

    pc = get_pinecone_client()

    # --------------------------------------------------------
    # Check existing indexes
    # --------------------------------------------------------

    indexes = pc.list_indexes()

    try:
        existing_names = {
            item["name"]
            for item in indexes
        }
    except (TypeError, KeyError):
        existing_names = {
            item.name
            for item in indexes
        }

    # --------------------------------------------------------
    # Create index if necessary
    # --------------------------------------------------------

    if PINECONE_INDEX_NAME not in existing_names:

        print(
            f"[memory] Creating Pinecone index: "
            f"{PINECONE_INDEX_NAME}"
        )

        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1",
            ),
        )

        # ----------------------------------------------------
        # Wait for index
        # ----------------------------------------------------

        print(
            "[memory] Waiting for Pinecone index..."
        )

        while True:

            description = pc.describe_index(
                PINECONE_INDEX_NAME
            )

            try:
                ready = bool(
                    description.status["ready"]
                )
            except (TypeError, KeyError):
                ready = bool(
                    description.status.ready
                )

            if ready:
                break

            time.sleep(1)

        print(
            "[memory] Pinecone index ready."
        )

    # --------------------------------------------------------
    # Connect to index
    # --------------------------------------------------------

    _index = pc.Index(
        PINECONE_INDEX_NAME
    )

    print(
        f"[memory] Connected to index: "
        f"{PINECONE_INDEX_NAME}"
    )

    return _index


# ============================================================
# SAVE MEMORY
# ============================================================

def save_memory(
    namespace: str,
    text: str,
    metadata: Dict[str, Any],
) -> str:
    """
    Save one memory item to Pinecone.
    """

    if not text or not text.strip():
        raise ValueError(
            "Cannot save empty memory."
        )

    index = get_index()

    vector_id = str(
        uuid.uuid4()
    )

    clean_metadata = {
        **metadata,
        "text": text[:4000],
    }

    vector = {
        "id": vector_id,
        "values": _embed(text),
        "metadata": clean_metadata,
    }

    index.upsert(
        vectors=[vector],
        namespace=namespace,
    )

    return vector_id


# ============================================================
# QUERY MEMORY
# ============================================================

def query_memory(
    namespace: str,
    query_text: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Retrieve semantically similar memories.
    """

    if not query_text or not query_text.strip():
        return []

    if top_k < 1:
        return []

    index = get_index()

    result = index.query(
        vector=_embed(query_text),
        top_k=top_k,
        namespace=namespace,
        include_metadata=True,
    )

    try:
        matches = result["matches"]
    except (TypeError, KeyError):
        matches = getattr(
            result,
            "matches",
            [],
        )

    memories: List[Dict[str, Any]] = []

    for match in matches:

        try:
            score = match["score"]
        except (TypeError, KeyError):
            score = getattr(
                match,
                "score",
                0.0,
            )

        try:
            metadata = match["metadata"] or {}
        except (TypeError, KeyError):
            metadata = getattr(
                match,
                "metadata",
                {}
            ) or {}

        memories.append(
            {
                "score": float(score),
                "text": metadata.get(
                    "text",
                    "",
                ),
                "metadata": metadata,
            }
        )

    return memories


# ============================================================
# STYLE MEMORY
# ============================================================

def save_style_example(
    user_id: str,
    post_text: str,
    platform: str = "linkedin",
):
    """
    Save an accepted/finalized post as a style example.
    """

    if not user_id or not user_id.strip():
        user_id = "default_user"

    if not post_text or not post_text.strip():
        raise ValueError(
            "post_text cannot be empty."
        )

    return save_memory(
        namespace=f"style::{user_id}",
        text=post_text,
        metadata={
            "user_id": user_id,
            "platform": platform,
            "type": "style_example",
        },
    )


def recall_style(
    user_id: str,
    draft_context: str,
    top_k: int = 3,
):
    """
    Retrieve previous style examples relevant to
    the current source content.
    """

    if not user_id or not user_id.strip():
        user_id = "default_user"

    return query_memory(
        namespace=f"style::{user_id}",
        query_text=draft_context,
        top_k=top_k,
    )


# ============================================================
# CONTENT MEMORY
# ============================================================

def save_content_record(
    user_id: str,
    source_content: str,
    outputs: Dict[str, str],
):
    """
    Save a source-content record and generated outputs.
    """

    if not user_id or not user_id.strip():
        user_id = "default_user"

    if not source_content or not source_content.strip():
        raise ValueError(
            "source_content cannot be empty."
        )

    combined_text = source_content[:2000]

    output_metadata: Dict[str, str] = {}

    for key, value in outputs.items():

        output_metadata[
            f"output_{key}"
        ] = str(
            value or ""
        )[:1500]

    metadata = {
        "user_id": user_id,
        "type": "content_record",
        **output_metadata,
    }

    return save_memory(
        namespace=f"content::{user_id}",
        text=combined_text,
        metadata=metadata,
    )


def recall_similar_content(
    user_id: str,
    source_content: str,
    top_k: int = 3,
):
    """
    Find previously processed source content
    that is semantically similar.
    """

    if not user_id or not user_id.strip():
        user_id = "default_user"

    return query_memory(
        namespace=f"content::{user_id}",
        query_text=source_content,
        top_k=top_k,
    )


# ============================================================
# MEMORY HEALTH CHECK
# ============================================================

def memory_health_check() -> Dict[str, Any]:
    """
    Check Pinecone configuration without creating
    embeddings or connecting unnecessarily.
    """

    api_key = os.getenv(
        "PINECONE_API_KEY",
        "",
    ).strip()

    return {
        "pinecone_configured": bool(
            api_key
        ),
        "index_name": PINECONE_INDEX_NAME,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimension": EMBEDDING_DIM,
    }


# ============================================================
# FULL PINECONE HEALTH CHECK
# ============================================================

def verify_memory_connection() -> Dict[str, Any]:
    """
    Actually connect to Pinecone and verify that the
    configured index is accessible.
    """

    try:

        index = get_index()

        return {
            "status": "ok",
            "pinecone": True,
            "index": PINECONE_INDEX_NAME,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": EMBEDDING_DIM,
        }

    except Exception as exc:

        return {
            "status": "error",
            "pinecone": False,
            "index": PINECONE_INDEX_NAME,
            "error": str(exc),
        }


# ============================================================
# MEMORY AUTO-PRUNING & CLUSTERING
# ============================================================

def prune_negative_memory(user_id: str, post_text: str) -> Dict[str, Any]:
    """
    Search Pinecone style memory for vectors similar to negative feedback post_text 
    and prune/delete them to prevent corrupting future generation quality.
    """
    if not user_id:
        user_id = "default_user"

    namespace = f"style::{user_id}"
    hits = query_memory(namespace=namespace, query_text=post_text, top_k=3)
    
    pruned_count = 0
    try:
        index = get_index()
        for hit in hits:
            if hit.get("score", 0.0) > 0.82:
                vec_id = hit.get("metadata", {}).get("id")
                if vec_id:
                    index.delete(ids=[vec_id], namespace=namespace)
                    pruned_count += 1
    except Exception as exc:
        print(f"[memory] Auto-pruning error: {exc}")

    return {"status": "pruned", "vectors_deleted": pruned_count}