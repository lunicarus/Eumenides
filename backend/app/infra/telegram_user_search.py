# backend/app/infra/telegram_user_search.py
import re
import asyncio
import logging
from telethon import functions, types
from telethon.errors import RPCError, FloodWaitError
from datetime import datetime
from app.infra.telegram_client import start_client
from app.domain.value_objects import Handle, Timestamp
from app.domain.entities import AccountMetadata
from app.domain.services import create_flagged_from_metadata  # if you kept domain.services path
from app.application.use_cases import IngestTelegramHandle  # optional usage pattern
from app.infra.sql_repository import SqlAccountRepository
from app.infra.event_bus import event_bus

# conservative patterns (tune in a whitelist/blacklist admin UI)
SUSPICIOUS_PATTERNS = [
    r"cps?ell", r"cp[_\- ]?sell", r"cp_store", r"teen", r"underage",
    r"young(ers)?", r"vids?", r"linkinbio", r"pay", r"giftcard"
]
COMPILED = re.compile("|".join(f"({p})" for p in SUSPICIOUS_PATTERNS), re.IGNORECASE)

repo = SqlAccountRepository()

async def search_users_by_query(query: str, limit: int = 50):
    """
    Search Telegram for entities matching `query`. This returns both users and chats.
    We inspect returned *users* (public usernames / display names) and perform safe metadata-only scoring.
    """
    client = await start_client()
    try:
        res = await client(functions.contacts.SearchRequest(q=query, limit=limit))
    except FloodWaitError as fw:
        logging.warning("FloodWait: sleeping %s", fw.seconds)
        await asyncio.sleep(fw.seconds + 1)
        return
    except RPCError as e:
        logging.exception("Telegram RPC error during search: %s", e)
        return
    except Exception:
        logging.exception("Unexpected error during search")
        return

    users = getattr(res, "users", []) or []
    # iterate users and inspect public metadata
    for u in users:
        try:
            # Telethon User object fields
            username = getattr(u, "username", None)
            first_name = getattr(u, "first_name", None) or ""
            last_name = getattr(u, "last_name", None) or ""
            display = (first_name + " " + last_name).strip() or username or ""
            # NOTE: we avoid fetching private data; GetFullUser may include 'about' for public users
            about = None
            try:
                # safe enrichment: GetFullUser for public profile (may fail if restricted)
                if username:
                    full = await client(functions.users.GetFullUser(id=u))
                    about = getattr(full.full_user, "about", None)
            except Exception:
                about = None

            # Build a metadata object conforming to domain model
            metadata = AccountMetadata(
                platform="telegram",
                handle=Handle(username if username else str(getattr(u, "id", "unknown"))),
                display_name=display,
                description=about,
                extra={"is_bot": getattr(u, "bot", False)},
                fetched_at=Timestamp(datetime.utcnow())
            )

            # quick pattern check on username/display/about
            text_to_check = " ".join(filter(None, [username or "", display or "", about or ""]))
            if COMPILED.search(text_to_check):
                # use domain scoring (pure logic) to create flagged entity
                from app.domain.services import create_flagged_from_metadata  # local import to avoid cycles
                flagged = create_flagged_from_metadata(metadata)
                if flagged.risk_score.value >= 0.2:
                    await repo.save(flagged)
                    # Optionally emit domain event
                    event_bus.publish("AccountFlagged", {
                        "platform": "telegram",
                        "handle": metadata.handle.normalized(),
                        "display_name": metadata.display_name,
                        "description": metadata.description,
                        "risk_score": flagged.risk_score.value,
                        "reasons": flagged.reasons,
                        "first_seen": flagged.created_at.value.isoformat(),
                        "last_seen": flagged.last_seen.value.isoformat(),
                        "crawl_log": [{"query": query, "fetched_at": datetime.utcnow().isoformat()}]
                    })
            # polite small sleep to avoid hitting limits
            await asyncio.sleep(0.15)
        except Exception:
            logging.exception("Error processing user result")

    # done
