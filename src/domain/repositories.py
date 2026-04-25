from typing import Protocol

from domain.models import URLMapping


class URLRepository(Protocol):
    def create(self, long_url: str) -> URLMapping:
        ...

    def get_by_code(self, short_code: str) -> URLMapping | None:
        ...
