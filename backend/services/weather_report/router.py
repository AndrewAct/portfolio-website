from fastapi import APIRouter, Query, HTTPException
from services.weather_report.service import get_weather_report
from typing import Optional

import httpx

from shared.logger import setup_logging
logger = setup_logging("Weather Report")

router = APIRouter()

@router.get("/")
async def feath_weather_report(
        city: Optional[str] = Query(None),
        zip_code: Optional[str] = Query(None),
        language: str = "en"
):
    if not city and not zip_code:
        raise HTTPException(status_code=400, detail="Missing city info. Please provide city or zip code")
    try:
        return await get_weather_report(city=city, zip_code=zip_code, language=language)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/summary")
async def fetch_weather_summary(
        city: Optional[str] = Query(None),
        zip_code: Optional[str] = Query(None),
        language: str = "en",
        persona: str = "gentle"
):
    if not city and not zip_code:
        raise HTTPException(status_code=400, detail="Missing city or zip code")

    weather_data = await get_weather_report(city=city, zip_code=zip_code, language=language)

    today = weather_data["daily"][0] # Today's data is the first entry in the weather data

    # Deploy MCP
    async with httpx.AsyncClient() as client:
        mcp_resp = await client.post(
            "http://127.0.0.1:8001/summary", # TODO: Change port because I remember 8001 is occupied
            json={
                "weather_data": today,
                "language": language,
                "persona": persona
            }
        )
        mcp_resp.raise_for_status()
        mcp_data = mcp_resp.json()

    return {
        "summary": mcp_data["summary"],
        "persona_display": mcp_data["persona_display_name"],
        "city": city,
        "today_weather": today
    }