from pipeline.steps._intake import step_1_intake
from pipeline.steps._extraction import step_2_extraction
from pipeline.steps._classification import step_3_classification
from pipeline.steps._summarization import step_4_summarization

def run_pipeline(raw_text: str) -> dict:
    intake_data = step_1_intake(raw_text)

    entities = step_2_extraction(intake_data)

    classification = step_3_classification(intake_data, entities)

    summary = step_4_summarization(intake_data, classification) 



    return { 
        "final_output": summary.model_dump(),
        "intermediate_state": {
            "intake": intake_data.model_dump(),
            "extraction": entities.model_dump(),
            "classification": classification.model_dump()
        } 
    }