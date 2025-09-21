from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass(frozen=True)
class Handle:
    value: str

    def normalized(self) -> str:
        v = self.value.strip()
        if v.startswith("https://t.me/"):
            v = v.split("t.me/")[-1]
        if v.startswith("@"):
            v = v[1:]
        return v.lower()

@dataclass(frozen=True)
class RiskScore:
    value: float

    def clamp(self) -> "RiskScore":
        v = max(0.0, min(1.0, float(self.value)))
        return RiskScore(round(v, 3))

@dataclass(frozen=True)
class Timestamp:
    value: datetime
