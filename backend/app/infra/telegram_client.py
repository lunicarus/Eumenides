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

    # Try to extract username from multiple possible fields
    username = getattr(entity, "username", None)
    if not username and hasattr(entity, "input_peer") and hasattr(entity.input_peer, "user_id"):
        username = str(getattr(entity.input_peer, "user_id", None))
    if not username and hasattr(entity, "id"):
        username = str(getattr(entity, "id", None))

    # Default values
    display_name = None
    description = None
    participants_count = None

    # User or channel/group logic
    from telethon.tl.types import User, Channel, Chat
    if isinstance(entity, User):
        # For users: display_name = first_name + last_name, description = about (bio)
        display_name = ((entity.first_name or "") + (f" {entity.last_name}" if entity.last_name else "")).strip()
        # Try to get bio (about)
        try:
            from telethon.tl.functions.users import GetFullUser
            full = await _client(GetFullUser(entity.id))
            description = getattr(full.full_user, "about", None)
        except Exception:
            description = None
    elif isinstance(entity, (Channel, Chat)):
        # For channels/groups: display_name = title, description = about
        display_name = getattr(entity, "title", None)
        try:
            from telethon.tl.functions.channels import GetFullChannel
            full = await _client(GetFullChannel(entity))
            description = getattr(full.full_chat, "about", None)
            participants_count = getattr(full.full_chat, "participants_count", None)
        except Exception:
            description = None
            participants_count = None

    result = {
        "username": username,
        "title": display_name,
        "id": getattr(entity, "id", None),
        "description": description,
        "participants_count": participants_count,
        "fetched_at": datetime.utcnow().isoformat()
    }
    return result
