from typing import List
import re
from app.domain.entities import AccountMetadata, FlaggedAccount
from app.domain.value_objects import RiskScore, Timestamp, Handle
from datetime import datetime

SUSPICIOUS_KEYWORDS = [
    "teen", "girl", "boy", "young", "minor", "link in bio", "subscribe", "pay","cp","hot","links","estupr0","rape","vendo","psel"
]
SUSPICIOUS_EMOJI = ["🔥", "💦", "🔞", "🔒"]

def compute_risk_and_reasons(metadata: AccountMetadata) -> tuple[RiskScore, List[str]]:
    reasons = []
    score = 0.0
    name = (metadata.display_name or "").lower()
    desc = (metadata.description or "").lower()


    for kw in SUSPICIOUS_KEYWORDS:
        if kw in name or kw in desc:
            score += 0.35
            reasons.append(f"suspicious keyword in profile: '{kw}'")

    for em in SUSPICIOUS_EMOJI:
        if em in (metadata.display_name or "") or em in (metadata.description or ""):
            score += 0.35
            reasons.append(f"suspicious emoji in profile: '{em}'")

    normalized = metadata.handle.normalized()
    if metadata.platform == "telegram" and re.match(r"^[A-Za-z0-9_]{5,32}$", normalized):
        score += 0.10
        reasons.append("suspicious handle name (public Telegram handle pattern)")

    rs = RiskScore(score).clamp()
    return rs, reasons

def create_flagged_from_metadata(metadata: AccountMetadata) -> FlaggedAccount:
    rs, reasons = compute_risk_and_reasons(metadata)
    now = Timestamp(datetime.utcnow())
    fa = FlaggedAccount(
        id=None,
        metadata=metadata,
        risk_score=rs,
        reasons=reasons,
        created_at=now,
        last_seen=now
    )
    return fa
