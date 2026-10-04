from backend.tracing.decorator import trace_step
import openai
from models import IntakeOutput, ExtractedEntities, ClassificationOutput

client = openai.Client()

@trace_step("Classification")
def step_3_classification(intake: IntakeOutput, entities: ExtractedEntities) -> ClassificationOutput:
    """Classifies the document based on text and extracted entities."""
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Classify this document type and provide a confidence score (1-5)."},
            {"role": "user", "content": f"Text: {intake.raw_text}\nEntities: {entities.model_dump_json()}"}
        ],
        response_format=ClassificationOutput,
    )
    return response.choices[0].message.parsed