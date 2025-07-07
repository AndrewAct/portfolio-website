from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
import os
from openai import OpenAI

from shared.config import get_settings
settings = get_settings()

client = OpenAI(api_key=settings.openai_api_key)
app = FastAPI()

# persona 配置
PERSONAS = {
    "gentle": {
        "name": {
            "zh_cn": "温柔（御姐）",
            "en": "Gentle (Onee-san style)",
            "ja": "優しい（お姉さん系）",
            "ko": "부드러운(누나 스타일)"
        },
        "desc": "a gentle and mature big-sister style"
    },
    "cool": {
        "name": {
            "zh_cn": "冷酷（霸道总裁）",
            "en": "Cool (CEO style)",
            "ja": "クール（社長系）",
            "ko": "차가운(CEO 스타일)"
        },
        "desc": "a cool, confident, slightly dominant personality"
    },
    "cute": {
        "name": {
            "zh_cn": "可爱（小奶狗）",
            "en": "Cute (puppy style)",
            "ja": "可愛い（子犬系）",
            "ko": "귀여운(강아지 스타일)"
        },
        "desc": "a very cute, puppy-like innocent style"
    },
    "tsundere": {
        "name": {
            "zh_cn": "雌小鬼",
            "en": "Tsundere",
            "ja": "ツンデレ",
            "ko": "츤데레"
        },
        "desc": "a mischievous, teasing tsundere style"
    }
}

class SummaryRequest(BaseModel):
    weather_data: Dict
    language: str
    persona: str  # should be key, e.g. "gentle"

@app.post("/summary")
async def generate_summary(payload: SummaryRequest):
    data = payload.weather_data
    lang = payload.language
    persona_key = payload.persona

    persona_config = PERSONAS.get(persona_key)
    if not persona_config:
        raise ValueError(f"Unknown persona: {persona_key}")

    persona_desc = persona_config["desc"]

    max_temp = data["temp"]["max"]
    min_temp = data["temp"]["min"]
    desc = data["weather"][0]["description"]

    wind_speed = data.get("wind_speed", None)
    humidity = data.get("humidity", None)
    uvi = data.get("uvi", None)

    # If there are alerts, add to the summary
    alerts = data.get("alerts", [])
    alert_text = ""
    if alerts:
        alert_texts = [f"{a.get('event')}: {a.get('description')}" for a in alerts]
        alert_text = " ".join(alert_texts)

    prompt = (
        f"You are acting as {persona_desc}. "
        f"Generate a short (under 70 words/characters if possible) weather summary for today in {lang}. "
        f"Weather description: {desc}, high {max_temp}°C, low {min_temp}°C. "
    )
    if wind_speed:
        prompt += f"Wind speed is around {wind_speed} m/s. "
    if humidity:
        prompt += f"Humidity is about {humidity}%. "
    if uvi:
        prompt += f"UV index is {uvi}. "
    if alert_text:
        prompt += f"There is also an alert: {alert_text} "

    prompt += "Be engaging, informative, and respect the persona style. Feel free to use emoji and Kaomoji."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a creative and concise weather summarizer."},
            {"role": "user", "content": prompt}
        ]
    )

    summary = response.choices[0].message.content

    return {
        "summary": summary,
        "persona_display_name": persona_config["name"].get(lang, persona_config["name"]["en"])
    }
