from urllib.error import HTTPError

import httpx
import os
from typing import Optional, Tuple

from shared.logger import setup_logging
logger = setup_logging("Weather Report")

from shared.config import get_settings
settings = get_settings()

WEATHER_API_KEY = settings.open_weather_map_api_key

BASE_URL = "https://api.openweathermap.org/data/2.5/forecast" # Base Open Weather API endpoint

GEO_ZIP_URL= "http://api.openweathermap.org/geo/1.0/zip"
GEO_DIRECT_URL = "http://api.openweathermap.org/geo/1.0/direct" # URL to convert current location to lat and long

ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall" # Specific URL get all information in one call


class GeoResolver:
    """
    Need to convert city/zip code to longitude and latitude
    because one call API only take geo data
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient()

    async def resolve(self, city: Optional[str], zip_code: Optional[str]) -> Tuple[float, float]:
        if zip_code:
            try:
                resp = await self.client.get(
                    GEO_ZIP_URL,
                    params={"zip": f"{zip_code}",
                            "appid": self.api_key}
                )
                resp.raise_for_status()
                data = resp.json()
                return data["lat"], data["lon"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning("zip fallback to city")
                    # Open Weather geo zip API does not support zip code outside of US currently
                    # Fall back to city if zip failed
                    if not city:
                        raise ValueError("Zip failed, no city fallback")
                else:
                    raise
        if city:
            resp = await self.client.get(
                GEO_DIRECT_URL,
                params={"q": city, "limit": 1, "appid": self.api_key}
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                raise ValueError(f"City {city} not found")
            # In OpenWeather API, we may have multiple results when we use city, so fetch the first one, i.e. [0]
            return data[0]["lat"], data[0]["lon"]

        raise ValueError("No city or zip code provided")

    async def close(self):
        await self.client.aclose()


async def get_weather_report(city: Optional[str] = None,
                             zip_code: Optional[str] = None,
                             lat: Optional[float] = None,
                             lon: Optional[float] = None,
                             language: str = "en") -> dict:
    async with httpx.AsyncClient() as client:
        geo = GeoResolver(WEATHER_API_KEY)
        if not lat and not lon:
            lat, lon = await geo.resolve(city, zip_code)

        onecall_params = {
            "lat": lat,
            "lon": lon,
            "exclude": "minutely,hourly", # Don't fetch data on minute/hour basis for now. May Change later
            "units": "metric",
            "lang": language,
            "appid": WEATHER_API_KEY,
        }
        logger.info(f"Fetching weather report for {city}, {zip_code}, {lat}, {lon}")
        try:
            response = await client.get(ONECALL_URL, params=onecall_params)
            response.raise_for_status()
        except HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            raise

        data = response.json()
        return data
