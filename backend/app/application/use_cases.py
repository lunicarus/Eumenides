from typing import List
from datetime import datetime
from app.domain.value_objects import Handle, Timestamp
from app.domain.services import create_flagged_from_metadata
from app.domain.entities import AccountMetadata, FlaggedAccount
from app.domain.repositories import AccountRepository
from app.infra.event_bus import event_bus
from app.application.dtos import IngestHandleDTO, FlaggedDTO
import logging

class IngestTelegramHandle:
    def __init__(self, account_repo: AccountRepository, telegram_adapter):
        self.repo = account_repo
        self.telegram = telegram_adapter

    async def execute(self, dto: IngestHandleDTO) -> None:
        md = await self.telegram.fetch_public_channel_metadata(dto.raw_handle)
        if not md:
            return
        metadata = AccountMetadata(
            platform="telegram",
            handle=Handle(md.get("username") or str(md.get("id"))),
            display_name=md.get("title"),
            description=md.get("description"),
            extra={"participants": md.get("participants_count")},
            fetched_at=Timestamp(datetime.utcnow())
        )
        flagged = create_flagged_from_metadata(metadata)
        if flagged.risk_score.value >= 0.2:
            saved = await self.repo.save(flagged)
            event_bus.publish("AccountFlagged", {
                "platform": saved.metadata.platform,
                "handle": saved.metadata.handle.normalized(),
                "display_name": saved.metadata.display_name,
                "description": saved.metadata.description,
                "risk_score": saved.risk_score.value,
                "reasons": saved.reasons,
                "first_seen": saved.created_at.value.isoformat() if saved.created_at else None,
                "last_seen": saved.last_seen.value.isoformat() if saved.last_seen else None,
                "crawl_log": []
            })
            logging.info("Flagged saved: %s %s", saved.metadata.platform, saved.metadata.handle.normalized())

class ListFlaggedUseCase:
    def __init__(self, account_repo: AccountRepository):
        self.repo = account_repo

    async def execute(self, limit: int = 100):
        rows = await self.repo.list_flagged(limit=limit)
        result = []
        for r in rows:
            result.append(FlaggedDTO(
                id=r.id,
                platform=r.metadata.platform,
                handle=r.metadata.handle.normalized(),
                display_name=r.metadata.display_name,
                description=r.metadata.description,
                risk_score=r.risk_score.value,
                reasons=r.reasons,
                created_at=r.created_at.value.isoformat() if r.created_at else None,
                last_seen=r.last_seen.value.isoformat() if r.last_seen else None
            ))
        return result
