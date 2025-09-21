from pydantic import BaseModel
from typing import Optional, List

class FlaggedOut(BaseModel):
    id: int
    platform: str
    handle: str
    display_name: Optional[str]
    description: Optional[str]
    risk_score: float
    reasons: Optional[List[str]]
    created_at: Optional[str]
    last_seen: Optional[str]

    class Config:
        orm_mode = True
