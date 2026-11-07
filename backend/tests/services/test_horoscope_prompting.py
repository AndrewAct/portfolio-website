from datetime import date, timedelta

import pytest

from apps.services.horoscope.prompting import (
    BANNED_PHRASES_EN,
    BANNED_PHRASES_ZH,
    FOCUS_AREAS,
    ZODIAC_EN,
    ZODIAC_ZH,
    build_prompt,
    pick_reading_angle,
    sign_index,
)

DAY = date(2026, 11, 6)


def test_angle_is_deterministic_and_language_independent():
    assert pick_reading_angle("Aries", DAY) == pick_reading_angle("Aries", DAY)
    assert pick_reading_angle("Aries", DAY) == pick_reading_angle("白羊座", DAY)


@pytest.mark.parametrize("offset", range(30))
def test_twelve_signs_never_share_a_primary_topic_on_one_day(offset):
    day = DAY + timedelta(days=offset)
    primaries = {pick_reading_angle(sign, day).primary for sign in ZODIAC_EN}

    assert len(primaries) == len(ZODIAC_EN)


@pytest.mark.parametrize("sign", ZODIAC_EN)
def test_a_sign_cycles_through_every_topic_before_repeating(sign):
    window = [pick_reading_angle(sign, DAY + timedelta(days=d)).primary for d in range(14)]

    assert set(window) == set(FOCUS_AREAS)


def test_secondary_topic_differs_from_primary():
    for offset in range(60):
        angle = pick_reading_angle("Leo", DAY + timedelta(days=offset))
        assert angle.secondary != angle.primary


def test_sign_index_accepts_both_languages_and_defaults_to_aries():
    assert sign_index("Pisces") == sign_index("双鱼座") == 11
    assert sign_index("unknown") == 0
    assert len(ZODIAC_EN) == len(ZODIAC_ZH) == 12


def test_zh_prompt_carries_angle_length_and_banned_phrases():
    angle = pick_reading_angle("白羊座", DAY)
    prompt = build_prompt("zh", "白羊座", "女性", DAY)

    assert "白羊座" in prompt and DAY.isoformat() in prompt
    assert angle.primary.zh in prompt and angle.primary.zh_hints in prompt
    assert angle.secondary.zh in prompt
    assert angle.device.zh in prompt
    assert "100-150个汉字" in prompt
    assert "不要照抄" in prompt
    assert all(phrase in prompt for phrase in BANNED_PHRASES_ZH)


def test_en_prompt_carries_angle_length_and_banned_phrases():
    angle = pick_reading_angle("Aries", DAY)
    prompt = build_prompt("en", "Aries", "male", DAY)

    assert angle.primary.en in prompt and angle.device.en in prompt
    assert "never copy wording" in prompt
    assert "100-150 words" in prompt
    assert all(phrase in prompt for phrase in BANNED_PHRASES_EN)


def test_unknown_language_uses_english_prompt():
    assert "100-150 words" in build_prompt("fr", "Aries", "neutral", DAY)
