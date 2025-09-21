from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime
from app.domain.value_objects import Handle, RiskScore, Timestamp

@dataclass
class AccountMetadata:
    platform: str
    handle: Handle
    display_name: Optional[str]
    description: Optional[str]
    extra: Dict
    fetched_at: Timestamp

@dataclass
class FlaggedAccount:
    id: Optional[int]
    metadata: AccountMetadata
    risk_score: RiskScore
    reasons: List[str]
    created_at: Optional[Timestamp] = None
    last_seen: Optional[Timestamp] = None

    def mark_seen(self, at: Timestamp):
        self.last_seen = at
