import asyncio
from datetime import datetime
from app.application.use_cases import IngestTelegramHandle
from app.infra.sql_repository import SqlAccountRepository
from app.infra.telegram_client import fetch_public_channel_metadata
from app.application.dtos import IngestHandleDTO
from app.infra.telegram_client import start_client
import logging

async def run_crawl(handles: list):
    repo = SqlAccountRepository()
    usecase = IngestTelegramHandle(account_repo=repo, telegram_adapter=type("A", (), {"fetch_public_channel_metadata": fetch_public_channel_metadata}))

    for h in handles:
        dto = IngestHandleDTO(platform="telegram", raw_handle=h, discovered_at=datetime.utcnow())
        try:
            await usecase.execute(dto)
        except Exception:
            logging.exception("Error ingesting %s", h)
        await asyncio.sleep(0.8)
