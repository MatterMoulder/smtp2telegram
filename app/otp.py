from __future__ import annotations

import re


OTP_PATTERNS = [
    re.compile(r"\b(?:code|код|otp|verification code|security code)\D{0,40}(\d{4,10})\b", re.I),
    re.compile(r"\b(\d{6})\b"),
    re.compile(r"\b(\d{4})\b"),
]


def extract_otp(text: str) -> str | None:
    for pattern in OTP_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)

    return None