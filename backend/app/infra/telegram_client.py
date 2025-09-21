import asyncio
from telethon import TelegramClient
from telethon.errors import UsernameNotOccupiedError, ChannelInvalidError
from app.config import settings
from datetime import datetime

_client = TelegramClient(settings.TELEGRAM_SESSION, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)

async def start_client():
    if not _client.is_connected():
        await _client.start()
    return _client

async def fetch_public_channel_metadata(username_or_link: str):
    await start_client()
    handle = username_or_link.strip()
    if handle.startswith("https://t.me/"):
        handle = handle.split("t.me/")[-1]
    if handle.startswith("@"):
        handle = handle[1:]
    try:
        entity = await _client.get_entity(handle)
    except (UsernameNotOccupiedError, ChannelInvalidError, ValueError):
        return None
    except Exception:
        return None

    result = {
        "username": getattr(entity, "username", None),
        "title": getattr(entity, "title", None),
        "id": getattr(entity, "id", None),
        "description": None,
        "participants_count": None,
        "fetched_at": datetime.utcnow().isoformat()
    }

    try:
        from telethon.tl.functions.channels import GetFullChannel
        full = await _client(GetFullChannel(entity))
        result["description"] = getattr(full.full_chat, "about", None)
        result["participants_count"] = getattr(full.full_chat, "participants_count", None)
    except Exception:
        result["description"] = None
        result["participants_count"] = None

    return result
