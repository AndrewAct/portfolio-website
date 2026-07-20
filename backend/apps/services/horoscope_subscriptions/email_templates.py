"""Email HTML/text builders — plain f-strings, no templating engine, matching the rest
of this codebase's style (see horoscope/service.py's prompt generation). Kept deliberately
simple/inline-styled/table-based rather than mirroring the web app's glassmorphism, since
email clients strip backdrop-filter and most modern CSS; the warm gold accent color is
reused for brand continuity where it *does* render.
"""

import html as html_lib
from typing import Any

_GOLD_GRADIENT = "linear-gradient(90deg, #c9a96e, #e8c99a, #c9a96e)"


def _wrap_html(title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html>
  <body style="margin:0;padding:32px 16px;background:#f3f1ec;font-family:Georgia,'Times New Roman',serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr><td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0"
               style="background:#fffdf8;border:1px solid #e8e2d8;border-radius:12px;overflow:hidden;">
          <tr><td style="height:4px;background:{_GOLD_GRADIENT};font-size:0;line-height:0;">&nbsp;</td></tr>
          <tr><td style="padding:32px 32px 24px;">
            <h1 style="margin:0 0 16px;font-size:22px;color:#1a1612;">{html_lib.escape(title)}</h1>
            {body_html}
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>"""


def build_confirmation_email(*, confirm_url: str) -> tuple[str, str, str]:
    """Returns (subject, html, text)."""
    subject = "Confirm your daily horoscope subscription"
    body_html = f"""
    <p style="color:#3d3228;font-size:15px;line-height:1.6;margin:0 0 24px;">
      Click below to confirm your subscription and start receiving your daily horoscope.
    </p>
    <p style="text-align:center;margin:0 0 24px;">
      <a href="{confirm_url}" style="display:inline-block;padding:12px 28px;background:#1a1612;
         color:#fffdf8;text-decoration:none;border-radius:8px;font-size:15px;">Confirm subscription</a>
    </p>
    <p style="color:#8a7a68;font-size:13px;margin:0;">
      If you didn't request this, you can safely ignore this email.
    </p>
    """
    html_body = _wrap_html("Confirm your subscription", body_html)
    text = (
        f"Confirm your daily horoscope subscription: {confirm_url}\n\n"
        "If you didn't request this, you can safely ignore this email."
    )
    return subject, html_body, text


def build_daily_horoscope_email(
    *, horoscope: dict[str, Any], preferences_url: str, unsubscribe_url: str
) -> tuple[str, str, str]:
    """Returns (subject, html, text)."""
    zodiac = str(horoscope["zodiac_sign"])
    zodiac_chinese = horoscope.get("zodiac_sign_chinese")
    zodiac_display = f"{zodiac} ({zodiac_chinese})" if zodiac_chinese else zodiac
    daily_text = str(horoscope["daily_horoscope"])
    subject = f"Your {zodiac} horoscope for today"

    detail_pairs = [
        ("Lucky number", horoscope.get("lucky_number")),
        ("Compatibility", horoscope.get("compatibility")),
        ("Mood", horoscope.get("mood")),
    ]
    detail_pairs = [(label, value) for label, value in detail_pairs if value]

    heading = html_lib.escape(zodiac)
    if zodiac_chinese:
        heading += f" · {html_lib.escape(str(zodiac_chinese))}"

    details_html = "".join(
        f'<p style="margin:0 0 4px;color:#8a7a68;font-size:13px;">'
        f"{html_lib.escape(label)}: {html_lib.escape(str(value))}</p>"
        for label, value in detail_pairs
    )

    body_html = f"""
    <p style="color:#8a7a68;font-size:12px;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 4px;">
      {heading}
    </p>
    <p style="color:#3d3228;font-size:15px;line-height:1.7;margin:0 0 20px;">
      {html_lib.escape(daily_text)}
    </p>
    {details_html}
    <p style="margin:28px 0 0;font-size:12px;color:#b0a090;">
      <a href="{preferences_url}" style="color:#8a7a68;">Change delivery time or email</a>
      &nbsp;&middot;&nbsp;
      <a href="{unsubscribe_url}" style="color:#8a7a68;">Unsubscribe</a>
    </p>
    """
    html_body = _wrap_html(f"Your {zodiac} horoscope", body_html)

    text_lines = [f"Your {zodiac_display} horoscope for today", "", daily_text]
    if detail_pairs:
        text_lines += ["", *(f"{label}: {value}" for label, value in detail_pairs)]
    text_lines += ["", f"Change preferences: {preferences_url}", f"Unsubscribe: {unsubscribe_url}"]
    text = "\n".join(text_lines)

    return subject, html_body, text
