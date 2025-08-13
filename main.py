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
from app.utils import Log


def get_app():

    settings = get_settings()

    trading_bot_api = FastAPI(
        title="Fast API template",
        description="template for FastApi app",
        version=f"{settings.API_VERSION}-{settings.IMAGE_TAG}",
    )

    trading_bot_api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @trading_bot_api.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        Log.error(str(exc.detail))
        return JSONResponse(str(exc.detail), status_code=exc.status_code)

    @trading_bot_api.exception_handler(RequestValidationError)
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

    @trading_bot_api.exception_handler(ValueError)
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
        return JSONResponse(str(exc), status_code=400)

    return trading_bot_api


application = get_app()


@application.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    Log.setup(log_name="rest-api", application_name="trading-bot-api")
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
