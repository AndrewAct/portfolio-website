from fastapi import APIRouter, Query, HTTPException
from services.weather_report.service import get_weather_report
from typing import Optional

router = APIRouter()

@router.get("/")
async def feath_weather_report(
        city: Optional[str] = Query(None),
        zip_code: Optional[str] = Query(None),
        language: str = "en"
):
    if not city and not zip_code:
        raise HTTPException(status_code=400, detail="Missing city info. Please provide city or zip code")
    return await get_weather_report(city=city, zip_code=zip_code, language=language)