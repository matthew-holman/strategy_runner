import logging

import uvicorn

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from app.core.settings import get_settings
from app.routers.eod_signals import router as signals
from app.routers.indicators import router as indicators
from app.routers.ohlcv_dailies import router as ohlcv_dailies
from app.routers.securities import router as securities
from app.utils import Log
from app.utils.log_setup import configure_logging


def get_app():
    configure_logging(logger_name="stock_picker-api", level=logging.INFO, use_utc=False)

    app_settings = get_settings()

    stock_picker_api = FastAPI(
        title="Stock Picker api",
        description="api for stock picker results",
        version=f"{app_settings.API_VERSION}-{app_settings.IMAGE_TAG}",
    )

    stock_picker_api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    stock_picker_api.include_router(indicators)
    stock_picker_api.include_router(ohlcv_dailies)
    stock_picker_api.include_router(securities)
    stock_picker_api.include_router(signals)

    @stock_picker_api.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        Log.error(str(exc.detail))
        return JSONResponse({"detail": str(exc.detail)}, status_code=exc.status_code)

    @stock_picker_api.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        error_detail = jsonable_encoder(exc.errors())

        Log.error(
            f"Failed request details: {request.method} "
            f"request to {request.url} "
            f"Error message: {error_detail}"
            f"Request metadata\n"
            f"\tPath Params: {request.path_params}\n"
            f"\tQuery Params: {request.query_params}\n"
        )

        return await request_validation_exception_handler(request, exc)

    @stock_picker_api.exception_handler(ValueError)
    async def value_error_exception_handler(request: Request, exc: ValueError):
        error_detail = jsonable_encoder(exc)

        Log.error(
            f"Failed request details: {request.method} "
            f"request to {request.url} "
            f"Error message: {error_detail}"
            f"Request metadata\n"
            f"\tPath Params: {request.path_params}\n"
            f"\tQuery Params: {request.query_params}\n"
        )

        Log.error(str(exc))
        return JSONResponse({"detail": str(exc)}, status_code=400)

    return stock_picker_api


application = get_app()


@application.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "main:application",
        host=settings.BASE_URL,
        port=settings.PORT,
        workers=settings.NUM_WORKERS,
        reload=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
