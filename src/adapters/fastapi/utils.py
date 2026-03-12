import uvicorn
from fastapi import FastAPI

from src.config import FastAPISettings
from .v1 import car, rental


async def serve_fastapi(app, settings: FastAPISettings) -> None:
    server = uvicorn.Server(uvicorn.Config(
        app=app,
        host=settings.address,
        port=settings.port,
    ))
    await server.serve()


def app_factory() -> FastAPI:
    app_ = FastAPI()
    app_.include_router(router=car.router, prefix="/api/v1")
    app_.include_router(router=rental.router, prefix="/api/v1")
    return app_
