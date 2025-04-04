from fastapi import APIRouter, Depends, Query
from typing import Dict, Any

from .service import HoroscopeService
from .schemas import HoroscopeResponse, BirthdateRequest

router = APIRouter(
    prefix="/horoscope",
    tags=["horoscope"],
)

def get_horoscope_service():
    return HoroscopeService()

@router.get("/{zodiac_sign}", response_model=HoroscopeResponse)
async def get_horoscope_by_sign(
    zodiac_sign: str,
    gender: str,
    language: str = "en",
    service: HoroscopeService = Depends(get_horoscope_service)
):
    """Obtain the specific horoscope of zodiac"""
    horoscope = await service.get_daily_horoscope(zodiac_sign, gender, language)
    return horoscope


@router.post("/", response_model=HoroscopeResponse)
async def get_horoscope_by_birthdate(
    request: BirthdateRequest,
    service: HoroscopeService = Depends(get_horoscope_service)
):
    """Get daily horoscope by birthdate"""
    english_name, localized_name = service.get_zodiac_sign(
        request.birthdate,
        request.language
    )
    horoscope = await service.get_daily_horoscope(
        english_name if request.language == "en" else localized_name,
        request.gender,
        request.language
    )
    return horoscope