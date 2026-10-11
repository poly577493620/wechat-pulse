from abc import ABC, abstractmethod

from ..models import Account, ArticleCandidate


class CollectorError(RuntimeError):
    pass


class Collector(ABC):
    @abstractmethod
    async def collect(self, account: Account) -> list[ArticleCandidate]:
        raise NotImplementedError
