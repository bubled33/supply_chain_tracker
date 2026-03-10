from typing import Type
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def register_domain_exception_handlers(app: FastAPI, not_found_errors: list[Type[Exception]], conflict_errors: list[Type[Exception]] = None) -> None:

    for exc_class in not_found_errors:
        @app.exception_handler(exc_class)
        async def handle_not_found(request: Request, exc: exc_class) -> JSONResponse:
            return JSONResponse(status_code=404, content={"detail": str(exc)})

    for exc_class in (conflict_errors or []):
        @app.exception_handler(exc_class)
        async def handle_conflict(request: Request, exc: exc_class) -> JSONResponse:
            return JSONResponse(status_code=409, content={"detail": str(exc)})
