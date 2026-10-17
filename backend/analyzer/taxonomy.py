# analyzer/taxonomy.py
from enum import Enum

class FailureType(str, Enum):
    EXTRACTION_HALLUCINATION = "Extraction Hallucination"
    MISCLASSIFICATION = "Misclassification"
    PROPAGATION_ERROR = "Propagation Error"
    PROMPT_FAILURE = "Prompt Failure"
    CONTEXT_LOSS = "Context Loss"
    NONE = "None"