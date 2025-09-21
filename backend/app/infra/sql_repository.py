import json
from typing import List, Optional
from sqlalchemy import select, update
from app.db import AsyncSessionLocal, Base, engine
from app.models import FlaggedAccount as ORMFlagged
from app.domain.entities import FlaggedAccount
from app.domain.value_objects import Timestamp, Handle, RiskScore
from datetime import datetime

async def ensure_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class SqlAccountRepository:
    def __init__(self, session_factory=AsyncSessionLocal):
        self._session_factory = session_factory

    async def save(self, entity: FlaggedAccount) -> FlaggedAccount:
        async with self._session_factory() as session:
            stmt = select(ORMFlagged).where(ORMFlagged.platform == entity.metadata.platform,
                                            ORMFlagged.handle == entity.metadata.handle.normalized())
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            reasons_json = json.dumps(entity.reasons, ensure_ascii=False)
            if row:
                row.risk_score = float(entity.risk_score.value)
                row.reasons = reasons_json
                row.display_name = entity.metadata.display_name
                row.description = entity.metadata.description
                row.last_seen = datetime.utcnow()
                session.add(row)
                await session.commit()
                domain = self._orm_to_domain(row)
                return domain
            else:
                new = ORMFlagged(
                    platform=entity.metadata.platform,
                    handle=entity.metadata.handle.normalized(),
                    display_name=entity.metadata.display_name,
                    description=entity.metadata.description,
                    metadata_hash=None,
                    risk_score=float(entity.risk_score.value),
                    reasons=reasons_json
                )
                session.add(new)
                await session.commit()
                await session.refresh(new)
                domain = self._orm_to_domain(new)
                return domain

    async def list_flagged(self, limit: int = 100) -> List[FlaggedAccount]:
        async with self._session_factory() as session:
            stmt = select(ORMFlagged).order_by(ORMFlagged.risk_score.desc()).limit(limit)
            res = await session.execute(stmt)
            rows = res.scalars().all()
            return [self._orm_to_domain(r) for r in rows]

    async def find_by_handle(self, platform: str, handle: str) -> Optional[FlaggedAccount]:
        async with self._session_factory() as session:
            stmt = select(ORMFlagged).where(ORMFlagged.platform == platform, ORMFlagged.handle == handle)
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            if not row:
                return None
            return self._orm_to_domain(row)

    def _orm_to_domain(self, row: ORMFlagged) -> FlaggedAccount:
        created_at = Timestamp(row.created_at) if row.created_at else None
        last_seen = Timestamp(row.last_seen) if row.last_seen else None
        from app.domain.value_objects import Handle, RiskScore
        from app.domain.entities import AccountMetadata
        metadata = AccountMetadata(
            platform=row.platform,
            handle=Handle(row.handle),
            display_name=row.display_name,
            description=row.description,
            extra={},
            fetched_at=Timestamp(row.created_at) if row.created_at else Timestamp(datetime.utcnow())
        )
        reasons = []
        try:
            reasons = json.loads(row.reasons) if row.reasons else []
        except Exception:
            reasons = []
        return FlaggedAccount(
            id=row.id,
            metadata=metadata,
            risk_score=RiskScore(row.risk_score),
            reasons=reasons,
            created_at=created_at,
            last_seen=last_seen
        )
