# tracing/schemas.py
from openai import default_headers
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class Span(BaseModel):
    span_id: str
    step_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    latency_ms: Optional[float] = None
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[int] = Field(default=None, ge=1, le=5)
    error: Optional[str] = None
    
    # Optional fields for LLM token tracking (Phase 3)
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

class Trace(BaseModel):
    trace_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_latency_ms: Optional[float] = None
    status: str = "running" # success, failed, degraded
    spans: List[Span] = Field(default_factory=list)
    confidence_score: int = Field(ge=1, le=5, description="confidence scrore after each LLM call find the output confidence score for its own response")
    final_output: Optional[Dict[str, Any]] = None