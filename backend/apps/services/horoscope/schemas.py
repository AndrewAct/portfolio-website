from datetime import date
from typing import Optional
from pydantic import BaseModel

class HoroscopeResponse(BaseModel):
    """Define the response model for Horoscope"""
    zodiac_sign: str
    zodiac_sign_chinese: Optional[str] = None
    daily_horoscope: str
    lucky_number: int
    compatibility: str
    mood: str

class BirthdateRequest(BaseModel):
    """Request model: get Horoscope with birthdate and gender,
    language is optional for now"""
    birthdate: date
    gender: str = "neutral"
    language: str = "en"