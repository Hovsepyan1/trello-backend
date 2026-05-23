from fastapi import FastAPI
from app.routers import users, boards, sections

app = FastAPI()

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(boards.router, prefix="/boards", tags=["boards"])
app.include_router(sections.router, prefix="/sections", tags=["sections"])


@app.get("/")
async def get_home():
    return "Hello"