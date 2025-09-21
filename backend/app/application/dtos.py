from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime

@dataclass
class IngestHandleDTO:
    platform: str
    raw_handle: str
    discovered_at: datetime

@dataclass
class FlaggedDTO:
    id: int
    platform: str
    handle: str
    display_name: Optional[str]
    description: Optional[str]
    risk_score: float
    reasons: List[str]
    created_at: str
    last_seen: str
