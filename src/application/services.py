from application.errors import LinkNotFoundError
from domain.models import URLMapping
from domain.repositories import URLRepository
from infrastructure.cache import CacheClient


class URLShortenerService:
    def __init__(self, repository: URLRepository, cache: CacheClient, base_url: str):
        self._repository = repository
        self._cache = cache
        self._base_url = base_url.rstrip("/")

    def shorten(self, long_url: str) -> tuple[str, str]:
        mapping: URLMapping = self._repository.create(long_url)
        self._cache.set(mapping.short_code, mapping.long_url)
        short_url = f"{self._base_url}/{mapping.short_code}"
        return short_url, mapping.short_code

    def resolve(self, short_code: str) -> str:
        cached_url = self._cache.get(short_code)
        if cached_url:
            return cached_url

        mapping = self._repository.get_by_code(short_code)
        if mapping is None:
            raise LinkNotFoundError("Short URL not found")

        self._cache.set(short_code, mapping.long_url)
        return mapping.long_url
