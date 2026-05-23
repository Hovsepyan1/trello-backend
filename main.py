from fastapi import FastAPI
from app.routers import users

app = FastAPI()

app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/")
async def get_home():
    return "Hello"