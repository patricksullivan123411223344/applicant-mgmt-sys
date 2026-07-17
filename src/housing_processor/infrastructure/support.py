from datetime import datetime, timezone
from uuid import UUID, uuid4


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class UuidIdGenerator:
    def new_uuid(self) -> UUID:
        return uuid4()
