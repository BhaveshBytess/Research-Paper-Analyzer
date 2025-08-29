# schema/models.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

class DatasetSplit(BaseModel):
    train: Optional[int] = None
    val: Optional[int] = None
    test: Optional[int] = None

class Dataset(BaseModel):
    name: str
    size: Optional[int] = None
    split: Optional[DatasetSplit] = None

class Method(BaseModel):
    name: str
    category: Optional[str] = None
    components: Optional[List[str]] = Field(default_factory=list)
    description: Optional[str] = None

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
            raise ValueError("confidence must be in [0,1]")
        return v

class EvidenceItem(BaseModel):
    page: int
    snippet: str

class Paper(BaseModel):
    title: str
    authors: List[str]
    year: int
    venue: Optional[str] = None
    arxiv_id: Optional[str] = None
    tasks: Optional[List[str]] = Field(default_factory=list)
    datasets: Optional[List[Dataset]] = Field(default_factory=list)
    methods: Optional[List[Method]] = Field(default_factory=list)
    results: Optional[List[ResultRecord]] = Field(default_factory=list)
    ablations: Optional[List[str]] = Field(default_factory=list)
    limitations: Optional[str] = None
    ethics: Optional[str] = None
    open_source: Optional[Dict[str, Optional[str]]] = None
    novelty: Optional[str] = None
    summary: str
    evidence: Dict[str, List[EvidenceItem]]
    confidence: Optional[Dict[str, Optional[float]]] = None

    class Config:
        anystr_strip_whitespace = True
