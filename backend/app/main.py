from fastapi import FastAPI
from contextlib import asynccontextmanager
# from app.api import router


asynccontextmanager
async def lifespan(_: FastAPI):
    """Context manager that handles startup and shutdown of the app."""
    # TODO: initialize resources
    yield
    # TODO: clean up resources

app = FastAPI(title="Service Name API", lifespan=lifespan)

# app.include_router(router)

@app.get("/")
def root():
    return {"message": "Hello World"}
