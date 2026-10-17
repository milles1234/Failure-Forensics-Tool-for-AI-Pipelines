import openai
from pydantic import BaseModel, Field
from tracing.schemas import Trace, Span


client = openai.client()


class StepJudgement(BaseModel):
    is_reasonable_transformation: bool = Field(description="True of output corectly derives from input wiout introducing corruption o rhallucination")
    quality_score: int = Field(ge=1, le=5, description="1 to 5 quality score of this specific transformation step.")
    reasoning: str = Field(description="Explanation for why this step failed or passed inspection.")


class RootCauseAnalysisResult(BaseModel.model_config, total=False):
    root_cause_step: Optional[str]
    explanation: str
    suspect_spans: List[dict]


def analyze_trace_root_cause(trace: Trace) -> dict:
       """
    Walks backward through trace spans when a trace fails or has low confidence,
    using an LLM-as-judge to identify the exact root cause step.
    """

    if trace.status == "success" and trace.confidence_score > 3:
        return {
            "root_cause_step": None,
            "explanation": "Trace completed successfully with acceptable confidence across all steps.",
            "suspect_spans": []
        }

suspects = []
root_cause = None
explanation = ""

# Walk backward through the spans (from last step to first step)

reversed_spans = list(reversed(trace.spans))


for span in reversed_spans:
    if span.error or (span.confidence_score and span.confidence_score <= 3):
            
            # Use LLM-as-Judge to evaluate transformation quality
            judge_prompt = f"""
            You are a Failure Forensics AI Judge. Evaluate whether the output of this pipeline step is a reasonable transformation of its input.
            
            Step Name: {span.step_name}
            Input Data: {span.input_data}
            Output Data: {span.output_data}
            Error (if any): {span.error}
            Self-Reported Confidence: {span.confidence_score}/5
            
            Analyze if this step introduced the core error or if it merely propagated a failure from an upstream step.
            """
            
            StepJudgment = None
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You analyze pipeline step failures rigorously."},
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
            # The first step encountered going backward that is deemed unreasonable/low-quality is the root cause
            if not judgment.is_reasonable_transformation or judgment.quality_score <= 2:
                root_cause = span.step_name
                explanation = judgment.reasoning

    # If we walked all the way back, the earliest suspect is the ultimate root cause
    if not root_cause and suspects:
        oldest_suspect = suspects[-1]
        root_cause = oldest_suspect["step_name"]
        explanation = f"Root cause traced back to initial failure point in {root_cause}."

    return {
        "root_cause_step": root_cause,
        "explanation": explanation,
        "suspect_spans": suspects
    }
