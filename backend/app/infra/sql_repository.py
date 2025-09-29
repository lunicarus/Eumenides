from typing import List, Optional
from datetime import datetime
from app.db import AsyncSessionLocal, Base, engine
from app.models import FlaggedAccount as ORMFlagged
from app.domain.entities import FlaggedAccount, AccountMetadata
from app.domain.value_objects import Timestamp, Handle, RiskScore
from sqlalchemy import select, update

async def ensure_tables():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class SqlAccountRepository:
    def __init__(self, session_factory=AsyncSessionLocal):
        self._session_factory = session_factory

    async def save(self, entity: FlaggedAccount) -> FlaggedAccount:
        """Insert or update a flagged account."""
        async with self._session_factory() as session:
            # Try to find existing row
            stmt = (
                select(ORMFlagged)
                .where(
                    ORMFlagged.platform == entity.metadata.platform,
                    ORMFlagged.handle == entity.metadata.handle.normalized()
                )
            )
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()

            # Prepare JSONB fields
            metadata_data = {
                "platform": entity.metadata.platform,
                "handle": entity.metadata.handle.normalized(),
                "display_name": entity.metadata.display_name,
                "description": entity.metadata.description,
                "extra": entity.metadata.extra,
                "fetched_at": entity.metadata.fetched_at.value.isoformat() if hasattr(entity.metadata.fetched_at, 'value') else str(entity.metadata.fetched_at)
            }

            if row:
                # Update existing
                row.risk_score = float(entity.risk_score.value)
                row.reasons = entity.reasons
                row.display_name = entity.metadata.display_name
                row.description = entity.metadata.description
                row.account_metadata = metadata_data
                row.last_seen = datetime.utcnow()
                session.add(row)
                await session.commit()
                domain = self._orm_to_domain(row)
                return domain
            else:
                # Create new
                new = ORMFlagged(
                    platform=entity.metadata.platform,
                    handle=entity.metadata.handle.normalized(),
                    display_name=entity.metadata.display_name,
                    description=entity.metadata.description,
                    account_metadata =metadata_data,
                    metadata_hash=None,
                    risk_score=float(entity.risk_score.value),
                    reasons=entity.reasons
                )
                session.add(new)
                await session.commit()
                await session.refresh(new)
                domain = self._orm_to_domain(new)
                return domain

    async def list_flagged(self, limit: int = 100) -> List[FlaggedAccount]:
        """Return top flagged accounts by risk score."""
        async with self._session_factory() as session:
            stmt = select(ORMFlagged).order_by(ORMFlagged.risk_score.desc()).limit(limit)
            res = await session.execute(stmt)
            rows = res.scalars().all()
            return [self._orm_to_domain(r) for r in rows]

    async def find_by_handle(self, platform: str, handle: str) -> Optional[FlaggedAccount]:
        """Find a flagged account by platform and handle."""
        async with self._session_factory() as session:
            stmt = select(ORMFlagged).where(
                ORMFlagged.platform == platform,
                ORMFlagged.handle == handle
            )
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            if not row:
                return None
            return self._orm_to_domain(row)

    def _orm_to_domain(self, row: ORMFlagged) -> FlaggedAccount:
        """Convert ORM object to domain entity."""
        created_at = Timestamp(row.created_at) if row.created_at else None
        last_seen = Timestamp(row.last_seen) if row.last_seen else None

        metadata = AccountMetadata(
            platform=row.platform,
            handle=Handle(row.handle),
            display_name=row.display_name,
            description=row.description,
            extra=row.account_metadata.get("extra", {}) if row.account_metadata else {},
            fetched_at=Timestamp(row.created_at) if row.created_at else Timestamp(datetime.utcnow())
        )

        reasons = row.reasons if row.reasons else []

        return FlaggedAccount(
            id=row.id,
            metadata=metadata,
            risk_score=RiskScore(row.risk_score),
            reasons=reasons,
            created_at=created_at,
            last_seen=last_seen
        )
