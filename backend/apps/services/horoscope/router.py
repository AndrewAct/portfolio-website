from functools import lru_cache

from fastapi import APIRouter, Depends

from .schemas import BirthdateRequest, HoroscopeResponse
from .service import HoroscopeService

router = APIRouter()


@lru_cache
def get_horoscope_service():
    return HoroscopeService()


@router.get("/{zodiac_sign}", response_model=HoroscopeResponse)
async def get_horoscope_by_sign(
    zodiac_sign: str,
    gender: str,
    language: str = "en",
    service: HoroscopeService = Depends(get_horoscope_service),  # noqa: B008
):
    """Obtain the specific horoscope of zodiac."""
    return await service.get_daily_horoscope(zodiac_sign, gender, language)


@router.post("", response_model=HoroscopeResponse)
@router.post("/", response_model=HoroscopeResponse, include_in_schema=False)
async def get_horoscope_by_birthdate(
    request: BirthdateRequest,
    service: HoroscopeService = Depends(get_horoscope_service),  # noqa: B008
):
    """Get a daily horoscope by birthdate, with or without a trailing slash."""
    english_name, localized_name = service.get_zodiac_sign(request.birthdate, request.language)
    zodiac_sign = english_name if request.language == "en" else localized_name
    return await service.get_daily_horoscope(zodiac_sign, request.gender, request.language)
