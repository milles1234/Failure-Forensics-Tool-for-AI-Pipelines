from backend.tracing.decorator import trace_step
import uuid
from models import IntakeOutput

@trace_step("Intake")
def step_1_intake(raw_text: str) -> IntakeOutput:
    return IntakeOutput(
        document_id=str(uuid.uuid4()),
        raw_text=raw_text
    )

    