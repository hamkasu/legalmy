from pydantic import BaseModel
from typing import Optional

class JudgeListItem(BaseModel):
    id: str
    name: str
    state: Optional[str]
    court_name: Optional[str]
    court_type: Optional[str]

    class Config:
        from_attributes = True

class JudgeProfileData(BaseModel):
    total_decisions: int
    plaintiff_favourable_rate: Optional[float]
    avg_disposal_days: Optional[float]
    interlocutory_grant_rate: Optional[float]
    costs_awarded_rate: Optional[float]
    top_practice_areas: Optional[str]

    class Config:
        from_attributes = True

class JudgeDetail(BaseModel):
    id: str
    name: str
    state: Optional[str]
    court_name: Optional[str]
    court_type: Optional[str]
    profile: Optional[JudgeProfileData]

    class Config:
        from_attributes = True

class JudgeCaseResult(BaseModel):
    id: str
    case_number: Optional[str]
    title: str
    date_decided: Optional[str]
    practice_area: str
    outcome: str

    class Config:
        from_attributes = True
