import random
from datetime import date, timedelta

import pytest

from apps.services.horoscope.prompting import (
    BANNED_PHRASES_EN,
    BANNED_PHRASES_ZH,
    FOCUS_AREAS,
    READING_APPROACHES,
    SIGN_PROFILES,
    ZODIAC_EN,
    ZODIAC_ZH,
    build_prompt,
    pick_reading_angle,
    sign_index,
)

DAY = date(2026, 11, 6)


@pytest.fixture(scope="module")
def reading_year():
    monday = DAY - timedelta(days=DAY.weekday())
    return {
        sign: [pick_reading_angle(sign, monday + timedelta(days=d)) for d in range(420)]
        for sign in ZODIAC_EN
    }


def test_angle_is_deterministic_and_language_independent():
    for english, chinese in zip(ZODIAC_EN, ZODIAC_ZH, strict=True):
        for offset in (0, 1, 7, 30, 365):
            day = DAY + timedelta(days=offset)
            assert pick_reading_angle(english, day) == pick_reading_angle(chinese, day)
            assert pick_reading_angle(english, day) == pick_reading_angle(english, day)


def test_selection_does_not_depend_on_call_order_or_global_random_state():
    initial_state = random.getstate()
    expected = pick_reading_angle("Leo", DAY)
    pick_reading_angle("Pisces", DAY + timedelta(days=40))

    assert pick_reading_angle("Leo", DAY) == expected
    assert random.getstate() == initial_state


@pytest.mark.parametrize("sign", ZODIAC_EN)
def test_weekly_topics_are_unique_and_never_repeat_across_week_boundaries(sign, reading_year):
    readings = reading_year[sign]
    for start in range(0, len(readings), 7):
        assert len({angle.primary for angle in readings[start : start + 7]}) == 7
    assert all(a.primary != b.primary for a, b in zip(readings, readings[1:], strict=False))


@pytest.mark.parametrize("sign", ZODIAC_EN)
def test_all_topics_remain_reachable_and_sign_preferences_influence_selection(sign, reading_year):
    readings = reading_year[sign]
    preferred = SIGN_PROFILES[sign_index(sign)].preferred_topics
    preferred_share = sum(angle.primary.key in preferred for angle in readings) / len(readings)
    uniform_share = len(preferred) / len(FOCUS_AREAS)

    assert {angle.primary for angle in readings} == set(FOCUS_AREAS)
    # A deterministic 60-week sample catches loss or reversal of the intended bias.
    assert preferred_share > uniform_share * 1.25


def test_same_topic_can_use_different_scenes_and_all_approaches_are_used(reading_year):
    readings = [angle for year in reading_year.values() for angle in year]
    for area in FOCUS_AREAS:
        scenes = {angle.scene for angle in readings if angle.primary == area}
        assert scenes == set(area.scenes)
    assert {angle.approach for angle in readings} == set(READING_APPROACHES)


def test_catalog_has_unique_keys_valid_preferences_and_paired_translations():
    topic_keys = {area.key for area in FOCUS_AREAS}
    assert len(topic_keys) == len(FOCUS_AREAS)
    assert len(SIGN_PROFILES) == len(ZODIAC_EN)
    assert len({approach.key for approach in READING_APPROACHES}) == len(READING_APPROACHES)
    for area in FOCUS_AREAS:
        assert area.zh and area.en
        assert len(set(area.scenes)) == len(area.scenes) >= 4
        assert all(scene.zh and scene.en for scene in area.scenes)
    for profile in SIGN_PROFILES:
        assert profile.zh and profile.en
        assert set(profile.preferred_topics) <= topic_keys
    for phrases in (BANNED_PHRASES_ZH, BANNED_PHRASES_EN):
        assert len(set(phrases)) == len(phrases)


@pytest.mark.parametrize("day", [date.min, date.max, date(2028, 2, 29), date(2027, 1, 1)])
def test_selection_handles_calendar_edges(day):
    assert pick_reading_angle("Taurus", day).primary in FOCUS_AREAS


def test_reading_approaches_vary_without_changing_the_daily_topic():
    approaches = set()
    for offset in range(60):
        angle = pick_reading_angle("Leo", DAY + timedelta(days=offset))
        approaches.add(angle.approach)

    assert approaches == set(READING_APPROACHES)


def test_sign_index_accepts_both_languages_and_defaults_to_aries():
    assert sign_index("Pisces") == sign_index("双鱼座") == 11
    assert sign_index("unknown") == 0
    assert len(ZODIAC_EN) == len(ZODIAC_ZH) == 12


def test_zh_prompt_carries_angle_length_and_banned_phrases():
    angle = pick_reading_angle("白羊座", DAY)
    prompt = build_prompt("zh", "白羊座", "女性", DAY)

    assert "白羊座" in prompt and DAY.isoformat() in prompt
    assert angle.primary.zh in prompt and angle.scene.zh in prompt
    assert angle.approach.zh in prompt
    assert SIGN_PROFILES[0].zh in prompt
    assert all(scene.zh not in prompt for scene in angle.primary.scenes if scene != angle.scene)
    assert "150-200个汉字" in prompt
    assert "不照抄素材" in prompt
    assert all(phrase in prompt for phrase in BANNED_PHRASES_ZH)


def test_en_prompt_carries_angle_length_and_banned_phrases():
    angle = pick_reading_angle("Aries", DAY)
    prompt = build_prompt("en", "Aries", "male", DAY)

    assert angle.primary.en in prompt and angle.approach.en in prompt
    assert angle.scene.en in prompt and SIGN_PROFILES[0].en in prompt
    assert all(scene.en not in prompt for scene in angle.primary.scenes if scene != angle.scene)
    assert "don't copy the material" in prompt
    assert "100-150 words" in prompt
    assert all(phrase in prompt for phrase in BANNED_PHRASES_EN)


def test_unknown_language_uses_english_prompt():
    assert "100-150 words" in build_prompt("fr", "Aries", "neutral", DAY)
