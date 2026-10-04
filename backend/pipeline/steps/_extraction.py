from backend.tracing.decorator import trace_step
from openai import Client
from backend.pipeline.models import IntakeOutput
import openai
from models import ExtractedEntities

client = openai.Client()

@trace_step("Extraction")
def step_2_extraction(intake: IntakeOutput) -> ExtractedEntities:
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Extract entities and provide a confidence score(1-5)" },
            {"role": "user", "content": intake.raw_text}

        ],
        response_format=ExtractedEntities,

    )

    return response.choices[0].message.parsed
   

