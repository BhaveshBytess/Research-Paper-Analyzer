# schema/head_models.py
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator

class MetadataOutput(BaseModel):
    title: Optional[str]
    authors: List[str] = Field(default_factory=list)
    year: Optional[int]
    venue: Optional[str]
    arxiv_id: Optional[str]

class MethodItem(BaseModel):
    name: str
    category: Optional[str] = None
    components: List[str] = Field(default_factory=list)
    description: Optional[str] = None

class MethodsOutput(BaseModel):
    methods: List[MethodItem] = Field(default_factory=list)

class ResultRecord(BaseModel):
    dataset: str
    metric: str
    value: float
    unit: Optional[str] = None
    split: Optional[str] = None
    higher_is_better: Optional[bool] = None
    baseline: Optional[str] = None
    ours_is: Optional[str] = None
    confidence: Optional[float] = None

    @validator("confidence")
    def conf_range(cls, v):
        if v is None:
            return v
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0 and 1")
        return v

class ResultsOutput(BaseModel):
    __root__: List[ResultRecord]

class LimitationsOutput(BaseModel):
    limitations: Optional[str] = None
    ethics: Optional[str] = None

class SummaryOutput(BaseModel):
    summary: str
