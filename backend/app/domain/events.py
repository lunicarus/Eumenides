from dataclasses import dataclass
from typing import Any
from datetime import datetime

@dataclass
class DomainEvent:
    name: str
    payload: Any
    occurred_at: datetime

@dataclass
class AccountFlaggedEvent(DomainEvent):
    pass
