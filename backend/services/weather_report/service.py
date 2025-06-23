import httpx
import os
from typing import Optional

from shared.logger import setup_logging
logger = setup_logging("Weather Report")

from shared.config import get_settings
settings = get_settings()

WEATHER_API_KEY = settings.open_weather_map_api_key
print("The API key is: ")
print(WEATHER_API_KEY)
logger.info("The weather API key is: ", WEATHER_API_KEY)

BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

async def get_weather_report(city: Optional[str] = None,
                             zip_code: Optional[str] = None,
                             lat: Optional[float] = None,
                             lon: Optional[float] = None,
                             language: str = "en") -> dict:
    params = {
        "appid": WEATHER_API_KEY,
        'units': "metric",
        'lang': language
    }
    logger.info(f"Requesting weather report for {city}, {zip_code}")
    if city:
        params['q'] = city # Open weather map API just take "q" for city in param
    elif zip_code:
        params['zip'] = zip_code
    elif lat and lon:
        params['lat'] = lat
        params['lon'] = lon
    else:
        logger.error(f"Missing city or zip code or lat/lon")


    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Weather report request failed: {e.response.status_code}, {e.response.json()}")
            raise
    data = response.json()

    return data