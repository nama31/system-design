from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class URLMapping:
    id: int
    long_url: str
    short_code: str
    created_at: datetime
