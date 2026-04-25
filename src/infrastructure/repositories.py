from sqlalchemy.orm import Session

from domain.base62 import Base62Encoder
from domain.models import URLMapping
from domain.repositories import URLRepository
from infrastructure.models import ShortURLRecord


class SQLAlchemyURLRepository(URLRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, long_url: str) -> URLMapping:
        record = ShortURLRecord(long_url=long_url)
        self._session.add(record)
        self._session.flush()

        record.short_code = Base62Encoder.encode(record.id)
        self._session.commit()
        self._session.refresh(record)

        return URLMapping(
            id=record.id,
            long_url=record.long_url,
            short_code=record.short_code,
            created_at=record.created_at,
        )

    def get_by_code(self, short_code: str) -> URLMapping | None:
        record = (
            self._session.query(ShortURLRecord)
            .filter(ShortURLRecord.short_code == short_code)
            .first()
        )
        if record is None:
            return None

        return URLMapping(
            id=record.id,
            long_url=record.long_url,
            short_code=record.short_code,
            created_at=record.created_at,
        )
