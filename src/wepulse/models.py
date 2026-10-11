from dataclasses import dataclass
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Account:
    id: int
    name: str
    connector: str
    source_id: str | None
    feed_url: str | None
    enabled: bool
    last_checked_at: str | None = None
    last_error: str | None = None


@dataclass(slots=True)
class ArticleCandidate:
    external_id: str
    title: str
    url: str
    published_at: datetime
    summary: str = ""
    content: str = ""
    cover_url: str = ""
