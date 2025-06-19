from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import router as history_router
import os

app = FastAPI(
    title="History Service",
    description="Service for recording and retrieving user/system activity history (in-memory version)",
    version="0.2.0"
)

# Optional: CORS settings for frontend or other services
ENV = os.getenv("ENV", "development")
if ENV == "development":
    origins = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost",
    ]
else:
    origins = [
        "https://andrewcee.io",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the router
app.include_router(
    history_router,
    prefix="",
    tags=["History"]
)

@app.get("/")
def root():
    return {"message": "History Service is running", "version": "0.2.0"}
