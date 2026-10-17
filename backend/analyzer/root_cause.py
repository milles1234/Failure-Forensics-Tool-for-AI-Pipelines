# analyzer/root_cause.py
import openai
from pydantic import BaseModel, Field
from typing import List, Optional
from tracing.schemas import Trace, Span
from .taxonomy import FailureType

client = openai.Client()

class StepJudgment(BaseModel):
    is_reasonable_transformation: bool = Field(description="True if output correctly derives from input without corruption or hallucination.")
    quality_score: int = Field(ge=1, le=5, description="1 to 5 quality score of this specific transformation step.")
    failure_type: FailureType = Field(description="Categorize the primary failure type if this step is flawed, otherwise choose None.")
    reasoning: str = Field(description="Explanation for why this step failed or passed inspection.")

class RootCauseAnalysisResult(BaseModel):
    root_cause_step: Optional[str] = None
    failure_category: Optional[FailureType] = None
    explanation: str
    suspect_spans: List[dict] = Field(default_factory=list)

def analyze_trace_root_cause(trace: Trace) -> RootCauseAnalysisResult:
    """
    Walks backward through trace spans, using an LLM-as-judge to pinpoint
    the root cause step and categorize its exact failure type.
    """
    if trace.status == "success" and all(s.confidence_score is None or s.confidence_score > 3 for s in trace.spans):
        return RootCauseAnalysisResult(
            explanation="Trace completed successfully with acceptable confidence across all steps.",
        )

    suspects = []
    root_cause_step = None
    failure_category = FailureType.NONE
    explanation = ""

    # Walk backward through spans (from last step to first step)
    for span in reversed(trace.spans):
        if span.error or (span.confidence_score and span.confidence_score <= 3):
            
            judge_prompt = f"""
            You are a Failure Forensics AI Judge. Evaluate whether the output of this pipeline step is a reasonable transformation of its input, and classify any failure into one of these strict categories:
            - Extraction Hallucination: Extracted entities that don't exist in the source.
            - Misclassification: Wrong document type assigned.
            - Propagation Error: Step N was correct, but step N+1 misinterpreted its output.
            - Prompt Failure: The LLM ignored system instructions or formatting rules.
            - Context Loss: Important information from earlier steps was dropped.

            Step Name: {span.step_name}
            Input Data: {span.input_data}
            Output Data: {span.output_data}
            Error (if any): {span.error}
            Self-Reported Confidence: {span.confidence_score}/5
            """
            
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You analyze pipeline step failures rigorously and categorize them."},
                    {"role": "user", "content": judge_prompt}
                ],
                response_format=StepJudgment
            )
            judgment = response.choices[0].message.parsed
            
            suspects.append({
                "step_name": span.step_name,
                "span_id": span.span_id,
                "confidence_score": span.confidence_score,
                "judgment": judgment.model_dump()
            })
            
            # The first step going backward that is deemed flawed is the root cause
            if not judgment.is_reasonable_transformation or judgment.quality_score <= 2:
                root_cause_step = span.step_name
                failure_category = judgment.failure_type
                explanation = judgment.reasoning
                break

    if not root_cause_step and suspects:
        oldest_suspect = suspects[-1]
        root_cause_step = oldest_suspect["step_name"]
        failure_category = FailureType.CONTEXT_LOSS
        explanation = f"Root cause traced back to initial failure point in {root_cause_step}."
    
    # Build the structured evidence chain narrative
    evidence_chain = []
    root_cause_found = False
    
    for span in trace.spans:
        is_root = (span.step_name == root_cause_step)
        if is_root:
            root_cause_found = True
            evidence_chain.append(
                f"🚨 **Root Cause Identified at {span.step_name}**: Confidence score reported as {span.confidence_score}/5. "
                f"The step produced invalid or flawed output given its input.\n"
                f"   - **Input Evidence**: {span.input_data}\n"
                f"   - **Output Evidence**: {span.output_data}"
            )
        elif root_cause_found:
            evidence_chain.append(
                f"⚠️ **Downstream Propagation**: The flaw from {root_cause_step} propagated into **{span.step_name}**, "
                f"incorporating the compromised data into its own output.\n"
                f"   - **Input Evidence**: {span.input_data}\n"
                f"   - **Output Evidence**: {span.output_data}"
            )


    return RootCauseAnalysisResult(
        root_cause_step=root_cause_step,
        failure_category=failure_category,
        explanation=explanation,
        suspect_spans=suspects
    )