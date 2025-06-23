from fastapi import FastAPI
from services.weather_report.router import router as weather_router
app = FastAPI(title="Weather Report API")
app.include_router(weather_router, prefix="/weather_report", tags=["Weather"])