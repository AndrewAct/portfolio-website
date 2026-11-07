"""Offline eval: how homogeneous / on-spec are horoscopes per provider+model+prompt?

Calls real provider APIs (costs a few cents). Run from backend/:

    uv run python scripts/eval_horoscope_prompt.py --days 2 \
        --candidate google:gemini-3.1-flash-lite:legacy \
        --candidate google:gemini-3.1-flash-lite \
        --candidate openai:gpt-5.4-mini

Candidate format is provider:model[:legacy]; ":legacy" uses the pre-rotation prompt as a
baseline. Prints one row per (candidate, language) and writes every sample to --out.
"""

from __future__ import annotations

import argparse
import asyncio
import itertools
import json
import re
import statistics
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from difflib import SequenceMatcher
from pathlib import Path

from apps.config import get_settings
from apps.services.horoscope.ai_provider import build_provider
from apps.services.horoscope.prompting import (
    BANNED_PHRASES_EN,
    BANNED_PHRASES_ZH,
    ZODIAC_EN,
    ZODIAC_ZH,
    build_prompt,
)
from apps.services.horoscope.service import GeneratedHoroscope, HoroscopeService

GENDERS = {"zh": ("女性", "男性"), "en": ("female", "male")}
REASONING_EFFORT = ""
CJK = re.compile(r"[一-鿿]")


def legacy_prompt(language: str, sign: str, gender: str, day: date) -> str:
    """The production prompt before the rotation rewrite, kept only as an eval baseline."""
    if language == "zh":
        return f"""为一位{gender}的{sign}生成{day.isoformat()}的中文星座运势，作为轻松的娱乐内容。

要求：
1. 使用温暖、自然、有人情味的语气，避免通用模板和重复表述
2. 结合{sign}的性格特点，写出具体且可行动的建议
3. 保持积极但不要断言未来，也不要夸张或制造焦虑
4. 运势正文控制在100-150个汉字
5. compatibility 和 mood 必须使用中文"""
    return f"""Write an English horoscope-style reading for {day.isoformat()} for a {gender} {sign}. Treat it as light entertainment.

Requirements:
1. Sound warm, natural, and human; avoid generic templates and repeated phrases
2. Connect a recognizable {sign} trait to one concrete, actionable suggestion
3. Stay encouraging without claiming certainty, exaggerating, or creating anxiety
4. Keep the reading between 100 and 150 words
5. Return compatibility and mood in English"""  # noqa: E501


@dataclass
class Sample:
    candidate: str
    language: str
    sign: str
    day: str
    seconds: float
    prompt: str = ""
    text: str = ""
    mood: str = ""
    error: str = ""


@dataclass
class Candidate:
    provider: str
    model: str
    legacy: bool = False
    samples: list[Sample] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.provider}:{self.model}" + (":legacy" if self.legacy else "")


def parse_candidate(spec: str) -> Candidate:
    parts = spec.split(":")
    if len(parts) not in (2, 3) or (len(parts) == 3 and parts[2] != "legacy"):
        raise argparse.ArgumentTypeError(f"bad candidate {spec!r}")
    return Candidate(parts[0], parts[1], legacy=len(parts) == 3)


def make_provider(candidate: Candidate):
    settings = get_settings()
    overrides: dict[str, str] = {}
    if candidate.provider == "google":
        overrides["gemini_model"] = candidate.model
        overrides["gemini_thinking_level"] = "minimal" if "flash-lite" in candidate.model else ""
    elif candidate.provider == "openai":
        overrides["openai_model"] = candidate.model
        overrides["openai_reasoning_effort"] = REASONING_EFFORT
    else:
        overrides[f"{candidate.provider}_model"] = candidate.model
        overrides[f"{candidate.provider}_reasoning_effort"] = REASONING_EFFORT
    return build_provider(candidate.provider, settings.model_copy(update=overrides))


async def run_candidate(candidate: Candidate, days: list[date], languages: list[str]) -> None:
    provider = make_provider(candidate)
    semaphore = asyncio.Semaphore(6)

    async def one(language: str, index: int, day: date) -> Sample:
        sign = (ZODIAC_ZH if language == "zh" else ZODIAC_EN)[index]
        gender = GENDERS[language][(index + day.day) % 2]
        prompt_fn = legacy_prompt if candidate.legacy else build_prompt
        prompt = prompt_fn(language, sign, gender, day)
        started = time.perf_counter()
        sample = Sample(candidate.label, language, sign, day.isoformat(), 0.0, prompt)
        async with semaphore:
            try:
                response = await provider.generate_structured(
                    prompt=prompt, response_schema=GeneratedHoroscope
                )
                parsed = HoroscopeService._parse_generated_horoscope(response)
                sample.text, sample.mood = parsed.daily_horoscope, parsed.mood
            except Exception as exc:  # noqa: BLE001 - eval records every failure kind
                sample.error = f"{type(exc).__name__}: {str(exc)[:200]}"
        sample.seconds = time.perf_counter() - started
        return sample

    jobs = [
        one(language, index, day)
        for language in languages
        for day in days
        for index in range(len(ZODIAC_EN))
    ]
    candidate.samples = await asyncio.gather(*jobs)
    await provider.close()


def text_length(language: str, text: str) -> int:
    return len(CJK.findall(text)) if language == "zh" else len(text.split())


def ngrams(text: str, n: int = 3) -> set[str]:
    compact = re.sub(r"\s+", " ", text.lower())
    return {compact[i : i + n] for i in range(len(compact) - n + 1)}


def copies_prompt(sample: Sample) -> bool:
    """True when the reading pastes a long run of the prompt's own instruction text."""
    matcher = SequenceMatcher(None, sample.prompt, sample.text, autojunk=False)
    match = matcher.find_longest_match(0, len(sample.prompt), 0, len(sample.text))
    return match.size >= (10 if sample.language == "zh" else 35)


def mean_pairwise_jaccard(texts: list[str]) -> float:
    grams = [ngrams(text) for text in texts]
    scores = [len(a & b) / len(a | b) for a, b in itertools.combinations(grams, 2) if a | b]
    return statistics.mean(scores) if scores else 0.0


def summarize(candidate: Candidate, language: str) -> dict[str, object]:
    samples = [s for s in candidate.samples if s.language == language]
    ok = [s for s in samples if not s.error]
    banned = BANNED_PHRASES_ZH if language == "zh" else BANNED_PHRASES_EN
    lengths = [text_length(language, s.text) for s in ok]
    return {
        "candidate": candidate.label,
        "lang": language,
        "ok": f"{len(ok)}/{len(samples)}",
        "len_in_100_150": f"{sum(100 <= n <= 150 for n in lengths)}/{len(ok)}",
        "len_median": statistics.median(lengths) if lengths else 0,
        "banned_hit": f"{sum(any(p in s.text.lower() for p in banned) for s in ok)}/{len(ok)}",
        "prompt_copy": f"{sum(copies_prompt(s) for s in ok)}/{len(ok)}",
        "similarity": round(mean_pairwise_jaccard([s.text for s in ok]), 3),
        "distinct_mood": f"{len({s.mood for s in ok})}/{len(ok)}",
        "p50_s": round(statistics.median(s.seconds for s in samples), 2) if samples else 0,
        "first_error": next((s.error for s in samples if s.error), ""),
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", action="append", type=parse_candidate, required=True)
    parser.add_argument("--days", type=int, default=2)
    parser.add_argument("--start", type=date.fromisoformat, default=date.today())
    parser.add_argument("--languages", default="zh,en")
    parser.add_argument("--reasoning-effort", default="")
    parser.add_argument("--out", type=Path, default=Path("horoscope_eval_samples.jsonl"))
    args = parser.parse_args()

    global REASONING_EFFORT
    REASONING_EFFORT = args.reasoning_effort
    days = [args.start + timedelta(days=offset) for offset in range(args.days)]
    languages = args.languages.split(",")
    await asyncio.gather(*(run_candidate(c, days, languages) for c in args.candidate))

    with args.out.open("w", encoding="utf-8") as handle:
        for candidate in args.candidate:
            for sample in candidate.samples:
                handle.write(json.dumps(sample.__dict__, ensure_ascii=False) + "\n")
    for candidate in args.candidate:
        for language in languages:
            print(json.dumps(summarize(candidate, language), ensure_ascii=False))
    print(f"samples -> {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
