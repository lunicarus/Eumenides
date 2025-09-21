from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities import FlaggedAccount, AccountMetadata

class AccountRepository(ABC):
    @abstractmethod
    async def save(self, entity: FlaggedAccount) -> FlaggedAccount:
        raise NotImplementedError

    @abstractmethod
    async def list_flagged(self, limit: int = 100) -> List[FlaggedAccount]:
        raise NotImplementedError

    @abstractmethod
    async def find_by_handle(self, platform: str, handle: str) -> Optional[FlaggedAccount]:
        raise NotImplementedError
