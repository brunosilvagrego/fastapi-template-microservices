import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Context manager that handles startup and shutdown of the app."""
    logger.info("Starting up the application.")
    # TODO: initialize resources

    yield

    logger.info("Shutting down the application.")
    # TODO: clean up resources


app = FastAPI(title="Service Name API", lifespan=lifespan)
app.include_router(router)


@app.get("/")
def root():
    logger.info("Serving root endpoint.")
    return {"message": "Hello World"}
