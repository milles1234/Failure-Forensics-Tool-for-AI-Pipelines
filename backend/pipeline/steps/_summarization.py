from backend.tracing.decorator import trace_step
import openai
from models import IntakeOutput, ClassificationOutput, SummarizationOutput

client = openai.Client()

@trace_step("Summarization")

def step_4_summarization(intake: IntakeOutput, classification: ClassificationOutput) -> SummarizationOutput:
    """Summarizes based on the document type."""
    prompt = f"Write a summary tailored to a {classification.doc_type.value}. Text: {intake.raw_text}"
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize the document and provide a confidence score (1-5)."},
            {"role": "user", "content": prompt}
        ],
        response_format=SummarizationOutput,
    )
    return response.choices[0].message.parsed