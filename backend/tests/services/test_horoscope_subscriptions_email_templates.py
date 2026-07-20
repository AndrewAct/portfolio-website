from apps.services.horoscope_subscriptions.email_templates import (
    build_confirmation_email,
    build_daily_horoscope_email,
)

FULL_HOROSCOPE = {
    "zodiac_sign": "Aries",
    "zodiac_sign_chinese": "白羊座",
    "daily_horoscope": "A focused day.",
    "lucky_number": 7,
    "compatibility": "Leo",
    "mood": "Calm",
}


def test_confirmation_email_contains_link_in_html_and_text():
    subject, html_body, text = build_confirmation_email(
        confirm_url="https://andrewcee.io/horoscope/confirm?token=abc"
    )

    assert "confirm" in subject.lower()
    assert "https://andrewcee.io/horoscope/confirm?token=abc" in html_body
    assert "https://andrewcee.io/horoscope/confirm?token=abc" in text


def test_daily_horoscope_email_includes_all_detail_fields():
    subject, html_body, text = build_daily_horoscope_email(
        horoscope=FULL_HOROSCOPE,
        preferences_url="https://andrewcee.io/horoscope/preferences?token=p",
        unsubscribe_url="https://andrewcee.io/horoscope/unsubscribe?token=u",
    )

    assert "Aries" in subject
    for expected in (
        "Aries",
        "白羊座",
        "A focused day.",
        "Lucky number: 7",
        "Compatibility: Leo",
        "Mood: Calm",
    ):
        assert expected in html_body
        assert expected in text
    assert "preferences?token=p" in html_body
    assert "unsubscribe?token=u" in html_body


def test_daily_horoscope_email_omits_missing_detail_fields():
    sparse = {"zodiac_sign": "Leo", "daily_horoscope": "Stay bold."}

    _, html_body, text = build_daily_horoscope_email(
        horoscope=sparse, preferences_url="https://x/p", unsubscribe_url="https://x/u"
    )

    assert "Lucky number" not in html_body
    assert "Lucky number" not in text
    assert "白羊座" not in html_body  # no zodiac_sign_chinese key present


def test_daily_horoscope_email_escapes_html_special_characters():
    unsafe = {
        "zodiac_sign": "Aries",
        "daily_horoscope": "<script>alert('x')</script> & <b>bold</b>",
    }

    _, html_body, _ = build_daily_horoscope_email(
        horoscope=unsafe, preferences_url="https://x/p", unsubscribe_url="https://x/u"
    )

    assert "<script>" not in html_body
    assert "&lt;script&gt;" in html_body
