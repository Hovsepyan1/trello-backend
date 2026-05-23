from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.routers import auth, users, boards, sections, tickets

@asynccontextmanager
async def lifespan(app: FastAPI):

    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(boards.router, prefix="/boards", tags=["boards"])
app.include_router(sections.router, prefix="/sections", tags=["sections"])
app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])

@app.get("/")
async def get_home():
    return "Hello"