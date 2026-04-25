from datetime import datetime, timezone

import pytest

from application.errors import LinkNotFoundError
from application.services import URLShortenerService
from domain.models import URLMapping
from presentation.schemas import ShortenRequest


class FakeRepository:
    def __init__(self):
        self._store: dict[str, URLMapping] = {}
        self._sequence = 1

    def create(self, long_url: str) -> URLMapping:
        code = f"x{self._sequence}"
        mapping = URLMapping(
            id=self._sequence,
            long_url=long_url,
            short_code=code,
            created_at=datetime.now(timezone.utc),
        )
        self._store[code] = mapping
        self._sequence += 1
        return mapping

    def get_by_code(self, short_code: str) -> URLMapping | None:
        return self._store.get(short_code)


class FakeCache:
    def __init__(self):
        self._cache: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._cache.get(key)

    def set(self, key: str, value: str) -> None:
        self._cache[key] = value


def test_service_shorten_and_resolve() -> None:
    service = URLShortenerService(FakeRepository(), FakeCache(), "http://localhost:8000")
    short_url, short_code = service.shorten("https://example.com/abc")

    assert short_url.endswith(f"/{short_code}")
    assert service.resolve(short_code) == "https://example.com/abc"


def test_service_raises_not_found() -> None:
    service = URLShortenerService(FakeRepository(), FakeCache(), "http://localhost:8000")

    with pytest.raises(LinkNotFoundError):
        service.resolve("missing")


def test_url_validation_rejects_invalid_url() -> None:
    with pytest.raises(ValueError):
        ShortenRequest(long_url="invalid-url")
