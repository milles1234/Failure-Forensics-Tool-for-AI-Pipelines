from pydantic import FileUrl
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class DocumentType(str, Enum):
    CONTRACT = "contract"
    INVOICE = "invoice"
    REPORT = "report"
    CORRESPONDENCE = "correspondence"
    UNKNOWN = "unknown"



class IntakeOutput(BaseModel):
    document_id: str
    raw_text: str
    metadata: dict = Field(default_factory=dict)

class ExtractedEntities(BaseModel):
    names: List[str] = Field(default_factory=list, description="People or comapny names")
    dates: List[str] = Field(default_factory=list, description="All dates meantioned")

    amounts: List[str] = Field(default_factory=list, description="Monetary values")
    key_terms: List[str] = Field(default_factory=list, description="Important legal or business terms")
    confidence_score:int = Field(ge=1, le=5, description="Model's confidence in extraction (1-5)")


class ClassificatioOutput(BaseModel):
    doc_type: DocumentType
    reasoning: str
    confidence_score: int = Field(ge=1, le=5)



class SummarizationOutput(BaseModel):
    summary: str
    key_takeways: List[str]
    confidence_score: int = Field(ge=1, le=5)






