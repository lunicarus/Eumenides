from typing import List
import re
from app.domain.entities import AccountMetadata, FlaggedAccount
from app.domain.value_objects import RiskScore, Timestamp, Handle
from datetime import datetime


# Handles that strongly suggest seller activity (high risk)
SELLER_HANDLE_KEYWORDS = [
    "vendo_cp", "cpsel", "psel", "cp_vendo", "cp-seller", "cp.seller", "cpvenda", "cpseller"
]
# Handles that suggest suspicious content (lower risk)
SUSPICIOUS_HANDLE_KEYWORDS = [
    "hotlinks", "new_18+_links", "megalink", "link18", "linkcp", "cpgroup", "cpchat", "cp18", "cpanon", "cpfree"
]
SUSPICIOUS_KEYWORDS = [
    "link in bio","cp","hot","links","estupr0","rape","vendo","psel","megalink"
]
SUSPICIOUS_EMOJI = ["🔥", "💦", "🔞", "🔒","📁","💥","🔗","🥵"]


def _fuzzy_match(word, text):
    # Simple leetspeak/obfuscation: o->0, e->3, a->4, s->$, i->1, etc.
    leet_map = str.maketrans("oeasigbt", "0e4$1937")
    text_norm = text.lower().translate(leet_map)
    word_norm = word.lower().translate(leet_map)
    return word_norm in text_norm

def compute_risk_and_reasons(metadata: AccountMetadata) -> tuple[RiskScore, List[str]]:
    reasons = []
    score = 0.0
    name = (metadata.display_name or "").lower()
    desc = (metadata.description or "").lower()
    handle = (metadata.handle.normalized() or "").lower()

    # Fuzzy/obfuscated keyword matching in display name, handle, and description
    for kw in SUSPICIOUS_KEYWORDS:
        for field, label in [(name, "display name"), (desc, "description"), (handle, "handle")]:
            if kw in field or _fuzzy_match(kw, field):
                score += 0.35
                reasons.append(f"suspicious keyword in {label}: '{kw}'")

    # Emoji/phrase detection in display name and description
    emoji_count = 0
    for em in SUSPICIOUS_EMOJI:
        for field, label in [(metadata.display_name or "", "display name"), (metadata.description or "", "description")]:
            if em in field:
                score += 0.35
                emoji_count += 1
                reasons.append(f"suspicious emoji in {label}: '{em}'")


    # Refined: boost for group/megas/DM/CP GROUP/Data Sellar/DM BEST CONTANT
    HIGH_RISK_PHRASES = [
        "group", "mega", "megas", "dm", "cp group", "data sellar", "dm best contant", "cp status"
    ]
    for phrase in HIGH_RISK_PHRASES:
        if phrase in name or phrase in handle:
            score += 0.5
            reasons.append(f"high-risk phrase detected: '{phrase}'")

    # Phrase detection in display name (e.g., 'best deal', 'promo', 'unlimited', etc.)
    PHRASES = ["best deal", "promo", "unlimited", "status", "group", "mega", "links", "new", "cp", "hot"]
    for phrase in PHRASES:
        if phrase in name:
            score += 0.2
            reasons.append(f"suspicious phrase in display name: '{phrase}'")

    # Check for seller/suspicious keywords in handle and display name (with fuzzy)
    if metadata.platform == "telegram":
        norm_lower = handle
        display_name_lower = name
        # Seller in handle
        if any(kw in norm_lower or _fuzzy_match(kw, norm_lower) for kw in SELLER_HANDLE_KEYWORDS):
            score += 1.0
            reasons.append("account name suggests seller activity (e.g. selling illegal content)")
        # Seller in display name
        elif any(kw in display_name_lower or _fuzzy_match(kw, display_name_lower) for kw in SELLER_HANDLE_KEYWORDS):
            score += 0.8
            reasons.append("display name suggests seller activity (e.g. selling illegal content)")
        # Suspicious in handle
        elif any(kw in norm_lower or _fuzzy_match(kw, norm_lower) for kw in SUSPICIOUS_HANDLE_KEYWORDS):
            score += 0.5
            reasons.append("account name suggests suspicious/illicit content")
        # Suspicious in display name
        elif any(kw in display_name_lower or _fuzzy_match(kw, display_name_lower) for kw in SUSPICIOUS_HANDLE_KEYWORDS):
            score += 0.4
            reasons.append("display name suggests suspicious/illicit content")
        # Generic Telegram handle pattern
        elif re.match(r"^[A-Za-z0-9_]{5,32}$", handle):
            score += 0.25
            reasons.append("account name matches public Telegram handle pattern (potential risk)")

    # Boost risk if repeated patterns in handle and display name
    for kw in SELLER_HANDLE_KEYWORDS + SUSPICIOUS_HANDLE_KEYWORDS:
        if (kw in handle or _fuzzy_match(kw, handle)) and (kw in name or _fuzzy_match(kw, name)):
            score += 0.3
            reasons.append(f"repeated suspicious pattern in handle and display name: '{kw}'")

    # Boost risk for multiple suspicious emojis
    if emoji_count >= 2:
        score += 0.2
        reasons.append("multiple suspicious emojis detected")

    rs = RiskScore(score).clamp()
    return rs, reasons, score  # return both normalized and raw

def create_flagged_from_metadata(metadata: AccountMetadata) -> FlaggedAccount:
    rs, reasons, raw_score = compute_risk_and_reasons(metadata)
    now = Timestamp(datetime.utcnow())
    fa = FlaggedAccount(
        id=None,
        metadata=metadata,
        risk_score=rs,
        reasons=reasons,
        created_at=now,
        last_seen=now
    )
    fa._raw_risk_score = raw_score  # attach for reporting
    return fa
