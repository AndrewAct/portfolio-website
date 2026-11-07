"""Horoscope prompt construction with deterministic per-day angle rotation.

Craft rules are adapted from published horoscope-writing practice rather than invented:
- Rick Levine (syndicated columnist, The Astrology Podcast ep. 80): pick ONE focus per sign
  per day, warn with if/then framing instead of predicting, never end on a negative note.
- Bertram Forer (1948) / Ian Rowland (The Full Facts Book of Cold Reading): Barnum
  statements, the Rainbow Ruse, the Pollyanna Pearl; "you"-addressed, hedged with "at times".
- 唐绮阳 daily/weekly columns: short concrete clauses, a warning names a specific behavior,
  its consequence and an alternative ("别把责任全揽身上", "说错话引发连锁效应").

Variety comes from code, not from model temperature: the focus area is a rotation so the 12
signs never share a primary topic on the same day and a sign never repeats it day to day.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date

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


@dataclass(frozen=True)
class FocusArea:
    key: str
    zh: str
    zh_hints: str
    en: str
    en_hints: str


# 14 > 12 signs, so a same-day rotation always yields 12 distinct primary topics.
# Hints are scene ideas, not wording: the prompt tells the model to pick one and rephrase.
FOCUS_AREAS = (
    FocusArea(
        "sleep", "睡眠与作息", "熬夜、睡不踏实、作息被打乱", "sleep", "late nights, broken sleep"
    ),
    FocusArea(
        "body",
        "身体的小信号",
        "肩颈、眼睛、久坐、喝水太少",
        "small body signals",
        "neck and shoulders, tired eyes, sitting too long",
    ),
    FocusArea(
        "eating",
        "饮食",
        "随便对付的一餐、咖啡因、外卖",
        "eating",
        "skipped meals, too much caffeine, takeout",
    ),
    FocusArea(
        "partner",
        "亲密关系",
        "没说出口的话、对方的冷淡或试探",
        "a partner or crush",
        "something unsaid, a cooler reply than usual",
    ),
    FocusArea(
        "family",
        "家人",
        "很久没联系、长辈唠叨背后的担心",
        "family",
        "a call you keep postponing, worry hidden in nagging",
    ),
    FocusArea(
        "friends",
        "朋友",
        "慢慢变淡的关系、一直没回的消息",
        "friendships",
        "a friendship going quiet, an unanswered message",
    ),
    FocusArea(
        "coworkers",
        "同事协作",
        "分工不清、替别人收拾烂摊子、功劳被模糊",
        "coworkers",
        "blurry ownership, cleaning up someone else's mess, credit",
    ),
    FocusArea(
        "authority",
        "上级与评价",
        "汇报、被打分、领导随口一句话",
        "a boss or being evaluated",
        "a review, a status update, an offhand remark from above",
    ),
    FocusArea(
        "money",
        "钱",
        "冲动消费、自动续费、借出去还没还的钱",
        "money",
        "impulse buys, forgotten subscriptions, money lent out",
    ),
    FocusArea(
        "postponed",
        "拖着的事",
        "一直推迟的决定、邮件或预约",
        "something postponed",
        "a decision, an email, an appointment you keep pushing",
    ),
    FocusArea(
        "past",
        "旧人旧事",
        "一段没有好好结束的关系",
        "the past",
        "a chapter that never got a proper ending",
    ),
    FocusArea(
        "self_talk",
        "自我苛责",
        "和别人比较、对自己太严格",
        "self-criticism",
        "comparing yourself, holding yourself to an unfair standard",
    ),
    FocusArea(
        "boundaries",
        "边界感",
        "不好意思拒绝、替别人的情绪买单",
        "boundaries",
        "struggling to say no, absorbing other people's moods",
    ),
    FocusArea(
        "overload",
        "过劳",
        "答应得太多、事事亲力亲为",
        "overcommitment",
        "saying yes too often, doing everything yourself",
    ),
)


@dataclass(frozen=True)
class ColdReadDevice:
    key: str
    zh: str
    en: str


# Phrased as technique descriptions with no quotable sentence: an early version embedded
# example lines and every model pasted them verbatim as the opening of the reading.
COLD_READ_DEVICES = (
    ColdReadDevice(
        "barnum_contrast",
        "写出读者外在表现和内心真实状态之间的一个反差",
        "name a gap between how the reader comes across and what they privately feel",
    ),
    ColdReadDevice(
        "rainbow_ruse",
        "点出一个性格特点，同时承认它偶尔会走向反面",
        "name a trait and admit it sometimes flips into its opposite",
    ),
    ColdReadDevice(
        "conditional_warning",
        "用条件句点出一个今天容易犯的具体做法和它带来的后果",
        "use an if/then: one specific habit today and what it leads to",
    ),
    ColdReadDevice(
        "unspoken",
        "点破一件读者心里有数、却一直没说或没做的事",
        "point at something the reader already knows but hasn't said or done",
    ),
    ColdReadDevice(
        "pollyanna",
        "指出一件拖了一阵的别扭事今天有松动的迹象，但需要读者先迈一步",
        "suggest a stuck situation is loosening today, if the reader moves first",
    ),
)

BANNED_PHRASES_ZH = (
    "创造力",
    "闪耀",
    "光芒",
    "新的开始",
    "新开始",
    "相信你的直觉",
    "跟随内心",
    "正能量",
    "能量",
    "宇宙",
    "星象",
    "好运",
    "机遇",
    "挑战",
    "绽放",
    "美好的一天",
    "一切都会好",
)
BANNED_PHRASES_EN = (
    "creativity",
    "creative",
    "shine",
    "new beginning",
    "trust your intuition",
    "follow your heart",
    "the universe",
    "energy",
    "the stars",
    "opportunities and challenges",
    "embrace",
    "journey",
    "good fortune",
)


@dataclass(frozen=True)
class ReadingAngle:
    primary: FocusArea
    secondary: FocusArea
    device: ColdReadDevice


def sign_index(zodiac_sign: str) -> int:
    """Map an English or Chinese sign name to 0-11; unknown names map to Aries."""
    if zodiac_sign in ZODIAC_EN:
        return ZODIAC_EN.index(zodiac_sign)
    if zodiac_sign in ZODIAC_ZH:
        return ZODIAC_ZH.index(zodiac_sign)
    return 0


def pick_reading_angle(zodiac_sign: str, day: date) -> ReadingAngle:
    """Deterministic for (sign, day) and independent of language, so zh/en readers of one
    sign get the same topic. The primary topic rotates; secondary/device are seeded draws
    (str seeds hash via sha512, so the choice is stable across processes)."""
    index = sign_index(zodiac_sign)
    primary = FOCUS_AREAS[(index + day.toordinal()) % len(FOCUS_AREAS)]
    rng = random.Random(f"horoscope:{day.isoformat()}:{index}")
    secondary = rng.choice([area for area in FOCUS_AREAS if area != primary])
    return ReadingAngle(primary, secondary, rng.choice(COLD_READ_DEVICES))


def build_prompt(language: str, zodiac_sign: str, gender: str, day: date) -> str:
    angle = pick_reading_angle(zodiac_sign, day)
    if language == "zh":
        return _build_zh_prompt(zodiac_sign, gender, day, angle)
    return _build_en_prompt(zodiac_sign, gender, day, angle)


def _build_zh_prompt(zodiac_sign: str, gender: str, day: date, angle: ReadingAngle) -> str:
    banned = "、".join(BANNED_PHRASES_ZH)
    return f"""你是一位写了很多年每日星座专栏的作者，文字短、准、像熟人提醒，不写鸡汤。
为一位{gender}的{zodiac_sign}写{day.isoformat()}的中文运势，作为娱乐内容。

今天这篇只写一个主题（不要面面俱到）：
- 主线：{angle.primary.zh}（可选场景：{angle.primary.zh_hints}；挑一个写具体，或换成同类更具体的场景）
- 副线（一笔自然带过）：{angle.secondary.zh}
- 开头的写作手法：{angle.device.zh}

以上是给你的写作说明，正文要用你自己的话，不要照抄说明里的任何词句，
也不要在正文里提到"主线""副线""重点""半句"这类说明用语。

正文结构：
1. 一句让人"被说中"的观察，用第二人称"你"，可以用"有时""最近"这类留有余地的说法
2. 主线上的一个具体提醒：写出具体场景和具体行为，再写不注意的后果，后果要轻、可挽回
3. 副线半句带过
4. 用一个今天就能做完的小动作收尾，结尾不能是负面的

要求：
- 正文100-150个汉字，短句为主，口语化
- {zodiac_sign}的性格只用来解释"为什么你会这样"，不要单独夸星座特质
- 可以让人有点在意或心虚，但不要吓人：不做医疗诊断、不提疾病名称，不预言事故、分手、失业等具体坏事
- 不要出现这些词：{banned}
- mood 是2-4个字，贴合正文的情绪，不必积极
- compatibility 是另一个星座的中文名，mood 用中文"""


def _build_en_prompt(zodiac_sign: str, gender: str, day: date, angle: ReadingAngle) -> str:
    banned = ", ".join(f'"{phrase}"' for phrase in BANNED_PHRASES_EN)
    return f"""You are a long-running daily horoscope columnist: short, sharp, like a friend who
notices things. No inspirational filler.
Write the reading for a {gender} {zodiac_sign} for {day.isoformat()}, as entertainment.

Cover ONE theme today, not everything:
- Main thread: {angle.primary.en} (scene ideas: {angle.primary.en_hints}; pick one and make it
  specific, or use a similar, more specific scene)
- Side note (pass over it naturally): {angle.secondary.en}
- Opening technique: {angle.device.en}

These are writing notes. Write in your own words; never copy wording from them or mention
"main thread", "side note" or "theme" in the reading.

Structure:
1. One observation that feels uncomfortably accurate, addressed to "you", hedged with
   "at times" or "lately"
2. One concrete warning on the main thread: a specific situation and behavior, then a mild,
   recoverable consequence if it's ignored
3. The side note in half a sentence
4. Close with one small action doable today; never end on a negative note

Requirements:
- 100-150 words, plain conversational sentences
- Use {zodiac_sign} traits only to explain why you'd act this way; no standalone praise
- Slight unease is fine, fear is not: no medical diagnoses or illness names, no predicting
  accidents, breakups, job loss or other specific bad events
- Never use: {banned}
- mood is 1-3 words matching the reading's tone; it need not be upbeat
- Return compatibility (another sign) and mood in English"""
