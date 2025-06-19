from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import router as history_router
from config import get_cors_origins

app = FastAPI(
    title="History Service",
    description="Service for recording and retrieving user/system activity history (in-memory version)",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
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
