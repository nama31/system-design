from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from application.errors import LinkNotFoundError
from application.services import URLShortenerService
from config import settings
from infrastructure.cache import CacheClient
from infrastructure.database import Base, engine, get_db
from infrastructure.repositories import SQLAlchemyURLRepository
from presentation.schemas import ErrorResponse, ShortenRequest, ShortenResponse


app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


def get_shortener_service(db: Session = Depends(get_db)) -> URLShortenerService:
    repository = SQLAlchemyURLRepository(db)
    cache_client = CacheClient()
    return URLShortenerService(repository=repository, cache=cache_client, base_url=settings.base_url)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    detail = "; ".join([error["msg"] for error in exc.errors()])
    return JSONResponse(status_code=400, content=ErrorResponse(detail=detail).model_dump())


@app.exception_handler(LinkNotFoundError)
async def not_found_exception_handler(_: Request, exc: LinkNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content=ErrorResponse(detail=str(exc)).model_dump())


@app.post("/shorten", response_model=ShortenResponse, responses={400: {"model": ErrorResponse}})
def shorten_url(
    payload: ShortenRequest,
    service: URLShortenerService = Depends(get_shortener_service),
) -> ShortenResponse:
    short_url, short_code = service.shorten(payload.long_url)
    return ShortenResponse(short_url=short_url, short_code=short_code)


@app.get("/{short_code}", responses={404: {"model": ErrorResponse}})
def redirect_to_original(
    short_code: str,
    permanent: bool = Query(default=False, description="Set true for 301 redirect, false for 302"),
    service: URLShortenerService = Depends(get_shortener_service),
) -> RedirectResponse:
    long_url = service.resolve(short_code)
    status_code = 301 if permanent else 302
    return RedirectResponse(url=long_url, status_code=status_code)
