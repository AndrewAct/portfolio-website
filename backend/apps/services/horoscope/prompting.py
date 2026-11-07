"""Seeded daily writing briefs with warm, coherent horoscope guidance.

A date-seeded weekly draw favors editorial sign preferences without excluding any topic.
Each reading develops one selected scene; warnings and personality judgments are optional
and discouraged, respectively. The same sign/date has the same material in either language.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date

from .writing_material import (
    BANNED_PHRASES_EN,
    BANNED_PHRASES_ZH,
    FOCUS_AREAS,
    READING_APPROACHES,
    SIGN_PROFILES,
    FocusArea,
    ReadingApproach,
    Scene,
)

ZODIAC_EN = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)
ZODIAC_ZH = (
    "白羊座",
    "金牛座",
    "双子座",
    "巨蟹座",
    "狮子座",
    "处女座",
    "天秤座",
    "天蝎座",
    "射手座",
    "摩羯座",
    "水瓶座",
    "双鱼座",
)

# Body length per language (CJK characters for zh, words otherwise); eval checks the same.
READING_LENGTH = {"zh": (150, 200), "en": (100, 150)}


@dataclass(frozen=True)
class ReadingAngle:
    """The writing brief: a topic, one concrete scene and an editorial approach."""

    primary: FocusArea
    scene: Scene
    approach: ReadingApproach


def sign_index(zodiac_sign: str) -> int:
    """Map an English or Chinese sign name to 0-11; unknown names map to Aries."""
    if zodiac_sign in ZODIAC_EN:
        return ZODIAC_EN.index(zodiac_sign)
    if zodiac_sign in ZODIAC_ZH:
        return ZODIAC_ZH.index(zodiac_sign)
    return 0


def _weekly_topics(index: int, week: int) -> list[FocusArea]:
    """Weighted draw without replacement. Preferred topics are twice as likely per draw.

    This raw schedule's last item must stay unchanged: the boundary correction below
    uses it to avoid repeating a topic across weeks without storing reading history.
    """
    rng = random.Random(f"horoscope:topics:v2:{week}:{index}")
    preferred = SIGN_PROFILES[index].preferred_topics
    pool = list(FOCUS_AREAS)
    topics = []
    for _ in range(7):
        weights = [2 if area.key in preferred else 1 for area in pool]
        selected = rng.choices(pool, weights=weights, k=1)[0]
        topics.append(selected)
        pool.remove(selected)
    return topics


def pick_reading_angle(zodiac_sign: str, day: date) -> ReadingAngle:
    """Stable per sign/date, independent of language, call order and global RNG state.

    Each Monday-Sunday week has seven different topics. Only the first two slots can
    swap to avoid repeating Sunday's topic on Monday; the final slot stays unchanged.
    Different signs may share a topic, but have independently selected scenes/approaches.
    """
    index = sign_index(zodiac_sign)
    week, offset = divmod(day.toordinal() - 1, 7)
    topics = _weekly_topics(index, week)
    if topics[0] == _weekly_topics(index, week - 1)[-1]:
        topics[0], topics[1] = topics[1], topics[0]
    primary = topics[offset]
    rng = random.Random(f"horoscope:scene:v2:{day.isoformat()}:{index}")
    return ReadingAngle(primary, rng.choice(primary.scenes), rng.choice(READING_APPROACHES))


def build_prompt(language: str, zodiac_sign: str, gender: str, day: date) -> str:
    angle = pick_reading_angle(zodiac_sign, day)
    if language == "zh":
        return _build_zh_prompt(zodiac_sign, gender, day, angle)
    return _build_en_prompt(zodiac_sign, gender, day, angle)


def _build_zh_prompt(zodiac_sign: str, gender: str, day: date, angle: ReadingAngle) -> str:
    low, high = READING_LENGTH["zh"]
    banned = "、".join(BANNED_PHRASES_ZH)
    return f"""你是每日星座专栏作者，为一位{gender}的{zodiac_sign}写{day.isoformat()}的中文运势。
这是轻松的娱乐内容，语气像熟悉的朋友顺口提一句：温和、平等、实在。

今天的素材（只是方向，不是关于读者的事实，用得上的再用）：
- 主题：{angle.primary.zh}
- 场景：{angle.scene.zh}
- 切入角度：{angle.approach.zh}
- 星座倾向（可不用）：{SIGN_PROFILES[sign_index(zodiac_sign)].zh}

篇幅不长，每句话都要有用：
- 正文{low}-{high}个汉字，不少于{low}字也不超过{high}字，5-6句。从今天在这件事上的大致状态写起，
  用一两个具体情形展开，最后落到一个方向或小期待。自然地串起来，不要用"值得注意的是"
  "容易忽略的是"这类提示语给内容分层。篇幅不够时，从同一件事延伸出一个相关的小方面，
  不用描写和空话凑字数。
- 多用直接的陈述句，少用转折和劝解的口气。
- 说人话，像给朋友发消息：口语、具体、有温度。可以用一件日常小事点题，但只提一笔，不展开描写；
  不写画面、声音和感官细节，不用比喻，不写散文。
- 也不要写成工作汇报：不用"即可""维持""有效""高效""节奏""状态"这类书面词和职场词。
- 建议给方向就够，不教具体做法和时机，也不解释显而易见的好处。
- 场景只用来定话题，不写成已经发生的事；不假定读者有工作、伴侣或某样东西。
  切入角度是写法提示，不要把它本身写进正文。
- 不训人：不贴性格标签，不用命令、反问或"要是你再……就会……"的句式，不编造坏后果。
- 不预言具体坏事，不做医疗判断，也不保证好事发生。
- 避免这些套话：{banned}

输出要求：
- 正文用自己的话，不照抄素材，不提"主题""角度"等写作术语。
- mood 是2-4个字的具体情绪词，不用"自在""从容""闲适"；compatibility 是另一个星座的中文名。"""


def _build_en_prompt(zodiac_sign: str, gender: str, day: date, angle: ReadingAngle) -> str:
    low, high = READING_LENGTH["en"]
    banned = ", ".join(f'"{phrase}"' for phrase in BANNED_PHRASES_EN)
    return f"""Write a daily horoscope for a {gender} {zodiac_sign} for {day.isoformat()}.
It's light entertainment, in the voice of a friend mentioning something in passing:
kind, equal and plain.

Material for today (directions, not facts about the reader; use what helps):
- Topic: {angle.primary.en}
- Scene: {angle.scene.en}
- Way in: {angle.approach.en}
- Sign lens (optional): {SIGN_PROFILES[sign_index(zodiac_sign)].en}

Every sentence has to earn its place:
- {low}-{high} words, at least {low}, in five or six sentences. Start from how this is likely
  to feel today, develop it through one or two concrete situations, and land on a direction
  or a small hope. Weave it together instead of signposting parts ("What's worth noticing
  is...", "The detail that's easy to miss...", "Something to look forward to:"). If you need more to say, extend to one related aspect of the same
  subject rather than padding with description or filler.
- Include only what the reader would care about: mood, feelings, what would make the day
  go smoother. No scene-setting, physical or sensory description, or metaphors.
- Suggestions give a direction, not instructions: don't spell out steps or timing, and don't
  explain obvious benefits.
- Use the scene only to pick the subject; don't narrate it as a story or as something that
  already happened. Don't assume a job, partner or possession.
- Don't lecture: no personality labels, commands, rhetorical questions or "if you keep doing
  X, Y will happen" lines, and no invented bad consequences.
- No predictions of specific bad events, no medical claims, no guaranteed good events.
- Use contractions. Vary the opening: don't start with a forecast of how the reader will feel
  ("You'll likely feel..."), "You might find yourself" or "It is", and don't default to ending on
  the afternoon or evening feeling lighter. The way in is a hint, not a sentence to include.
- Avoid therapy-speak and these stock phrases: {banned}

Output requirements:
- Use your own words; don't copy the material or mention topics or angles.
- mood is one short phrase of 1-3 words, not a comma-separated list, and not "calm", "content"
  or "grounded"; compatibility is another zodiac sign; both in English."""
