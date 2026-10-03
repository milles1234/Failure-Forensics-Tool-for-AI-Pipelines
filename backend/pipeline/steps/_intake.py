import uuid
from models import IntakeOutput

def step_1_intake(raw_text: str) -> IntakeOutput:
    return IntakeOutput(
        document_id=str(uuid.uuid4()),
        raw_text=raw_text
    )

    