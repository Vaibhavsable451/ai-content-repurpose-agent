"""
observability.py
-----------------
Concept 3: Observability, Tracing & Cost Telemetry.

Lightweight structured tracer for agent runs: logs each tool call,
its inputs/outputs, latency, token usage, and Groq API cost estimates.
"""

import json
import time
import os
from contextlib import contextmanager
from typing import Any, Dict, List

TRACE_LOG_PATH = os.environ.get("TRACE_LOG_PATH", "agent_traces.jsonl")

# Cost constants for Llama-3.3-70B-versatile ($0.00059 / 1K input, $0.00079 / 1K output)
COST_PER_1K_INPUT_TOKENS = 0.00059
COST_PER_1K_OUTPUT_TOKENS = 0.00079


class RunTracer:
    def __init__(self, run_id: str, user_id: str):
        self.run_id = run_id
        self.user_id = user_id
        self.events: List[Dict[str, Any]] = []
        self.start_time = time.time()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    @contextmanager
    def span(self, name: str, input_text: str = "", **metadata):
        start = time.time()
        in_tokens = self.estimate_tokens(input_text)
        self.total_input_tokens += in_tokens
        
        event = {
            "span": name,
            "metadata": metadata,
            "run_id": self.run_id,
            "user_id": self.user_id,
            "input_tokens": in_tokens,
        }
        try:
            yield event
            event["status"] = "ok"
        except Exception as e:
            event["status"] = "error"
            event["error"] = str(e)
            raise
        finally:
            event["latency_ms"] = round((time.time() - start) * 1000, 1)
            out_tokens = self.estimate_tokens(str(event.get("output", "")))
            self.total_output_tokens += out_tokens
            event["output_tokens"] = out_tokens
            self.events.append(event)

    def estimate_tokens(self, text: str) -> int:
        """Rough heuristic (~4 chars per token)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def calculate_cost(self) -> float:
        """Calculate estimated Groq LLM cost in USD."""
        input_cost = (self.total_input_tokens / 1000.0) * COST_PER_1K_INPUT_TOKENS
        output_cost = (self.total_output_tokens / 1000.0) * COST_PER_1K_OUTPUT_TOKENS
        return round(input_cost + output_cost, 6)

    def finish(self) -> Dict:
        total_latency = round((time.time() - self.start_time) * 1000, 1)
        summary = {
            "run_id": self.run_id,
            "user_id": self.user_id,
            "total_latency_ms": total_latency,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "estimated_cost_usd": self.calculate_cost(),
            "num_spans": len(self.events),
            "spans": self.events,
        }
        try:
            with open(TRACE_LOG_PATH, "a") as f:
                f.write(json.dumps(summary, default=str) + "\n")
        except OSError:
            pass
        return summary
