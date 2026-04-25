import re

from pydantic import BaseModel, field_validator


URL_REGEX = re.compile(
    r"^(https?)://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d{1,5})?(?:/[^\s]*)?$"
)


class ShortenRequest(BaseModel):
    long_url: str

    @field_validator("long_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not URL_REGEX.match(value):
            raise ValueError("Invalid URL format")
        return value


class ShortenResponse(BaseModel):
    short_url: str
    short_code: str


class ErrorResponse(BaseModel):
    detail: str
