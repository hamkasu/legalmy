from pydantic import BaseModel
from typing import Optional

class CaseSearchResult(BaseModel):
    id: str
    case_number: Optional[str]
    citation: Optional[str]
    title: str
    court_name: Optional[str]
    judge_name: Optional[str]
    date_decided: Optional[str]
    practice_area: str
    outcome: str
    language: str
    snippet: Optional[str]

    class Config:
        from_attributes = True

class CaseDetail(BaseModel):
    id: str
    case_number: Optional[str]
    citation: Optional[str]
    title: str
    plaintiff: Optional[str]
    defendant: Optional[str]
    date_filed: Optional[str]
    date_decided: Optional[str]
    practice_area: str
    outcome: str
    full_text: Optional[str]
    summary: Optional[str]
    source_url: Optional[str]
    source: str
    language: str
    court_name: Optional[str]
    judge_name: Optional[str]

    class Config:
        from_attributes = True

class SaveCaseRequest(BaseModel):
    notes: Optional[str] = None

class SavedCaseResponse(BaseModel):
    id: str
    case_id: str
    notes: Optional[str]
    case: CaseDetail

    class Config:
        from_attributes = True
