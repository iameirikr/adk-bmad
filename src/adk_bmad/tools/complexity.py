"""Story complexity scoring — ported from upstream `bmad-story-automator`'s
`complexity-rules.json` / `complexity-scoring.md` (regex pattern matching over
story text, plus a structural bonus for AC count / story length). This is a
scoring *algorithm*, not domain instruction prose, so unlike `skills.py` it's
reimplemented directly in Python rather than loaded from the skill files at
runtime — a compact subset of upstream's ~40 rules, not a byte-for-byte port.

The score feeds `agents/dev_story.py`'s `before_model_callback`, which escalates
a complex story's dev-story pass from the cheap default model to the heavier
configured tier — real dynamic per-story model routing, not just a config knob.
"""

from __future__ import annotations

import re

# (label, regex, score) — each match adds `score` to the story's complexity total.
_RULES: tuple[tuple[str, re.Pattern[str], int], ...] = tuple(
    (label, re.compile(pattern, re.IGNORECASE), score)
    for label, pattern, score in (
        (
            "external_api",
            r"\b(stripe|twilio|whatsapp|aws sdk|third-party api|external api|webhook)\b",
            2,
        ),
        ("async_processing", r"\b(message queue|pub/?sub|background job|event-driven)\b", 2),
        ("realtime", r"\b(websocket|server-sent events?|sse|push notification|long poll)\b", 2),
        ("db_schema", r"\b(migration|new table|foreign key|schema change)\b", 1),
        (
            "db_complex",
            r"\b(complex quer(y|ies)|join|subquery|aggregate|stored procedure|transaction)\b",
            2,
        ),
        ("etl", r"\b(data pipeline|bulk import|bulk export|csv parsing|data sync|etl)\b", 2),
        ("caching", r"\b(redis|memcache|cdn|cache invalidation)\b", 1),
        ("search_index", r"\b(elasticsearch|algolia|full-text search|vector search)\b", 2),
        ("file_storage", r"\b(s3|blob storage|presigned url|pdf generation)\b", 1),
        ("auth", r"\b(login flow|jwt|password reset|sso|2fa|mfa|social login)\b", 2),
        ("authorization", r"\b(rbac|acl|row-level security|multi-tenant|route guard)\b", 2),
        ("crypto", r"\b(encryption|hashing|csrf|xss|cors|security header)\b", 1),
        ("cross_story_dependency", r"\bdepends on (story|epic) \d", 1),
    )
)

_AC_HEADER_RE = re.compile(r"^##\s*Acceptance Criteria", re.MULTILINE | re.IGNORECASE)


def score_story_text(text: str) -> int:
    """Sum of matched-rule scores plus a structural bonus for AC count and length."""
    score = sum(weight for _, pattern, weight in _RULES if pattern.search(text))

    ac_count = len(re.findall(r"^\d+\.\s", text, re.MULTILINE))
    if ac_count > 10:
        score += 2
    elif ac_count > 6:
        score += 1

    word_count = len(text.split())
    if word_count > 400:
        score += 1

    return score


def tier_for_score(score: int, *, threshold: int = 4) -> str:
    """"heavy" once `score` clears `threshold` (upstream's own default cutoff), else "standard"."""
    return "heavy" if score >= threshold else "standard"


def matched_rules(text: str) -> list[str]:
    """Which rule labels matched — surfaced in the story's Dev Agent Record for transparency."""
    return [label for label, pattern, _ in _RULES if pattern.search(text)]
