"""Curated slop-pattern database for consulting-brief prose.

Each pattern is a single deterministic regex. Categories group related
phenomena; severity ranks how confident we are that the phrase is slop in
every reasonable context:

- ``HIGH``   — always slop in a consulting brief. ``clean()`` applies any
  configured replacement (often deletion).
- ``MEDIUM`` — usually slop. ``clean()`` applies a replacement when one is
  configured; otherwise flags without editing.
- ``LOW``    — contextually questionable. Flagged only, never auto-edited.

Patterns are curated for a senior-partner ear. Each one is something a
consultant would wince at. They are NOT a general English style guide; they
are specifically the phrases that make AI output sound like AI output.

The list is intentionally hand-picked (~220 entries) rather than exhaustive.
Every pattern has been checked against the three-way trade-off: (a) high
frequency in LLM output, (b) rarely appropriate in a consulting brief, and
(c) does not produce obvious false positives in finance / strategy text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    """How confident we are that a match is slop."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(StrEnum):
    """Pattern family. Used for grouped reports and targeted tests."""

    FILLER = "filler"
    BUZZWORD = "buzzword"
    HEDGING = "hedging"
    FALSE_TRANSITION = "false_transition"
    SUPERLATIVE = "superlative"
    AI_TELL = "ai_tell"
    LLM_TIC = "llm_tic"
    CORPORATE_FILLER = "corporate_filler"
    WEAK_OPENER = "weak_opener"


@dataclass(frozen=True)
class SlopPattern:
    """A single slop pattern.

    Attributes:
        phrase: Canonical human-readable form shown in reports.
        regex: Case-insensitive regex. Callers compile with ``re.IGNORECASE``.
        category: Family this pattern belongs to.
        severity: HIGH / MEDIUM / LOW.
        replacement: Text to substitute when cleaning. ``None`` means
            "report only, never auto-edit". ``""`` means "delete the match".
        note: Optional one-line diagnostic explaining why the phrase is slop.
    """

    phrase: str
    regex: str
    category: Category
    severity: Severity
    replacement: str | None = None
    note: str | None = None


def phrase_regex(phrase: str) -> str:
    """Build a word-boundary regex with flexible inter-word whitespace.

    Escapes regex metacharacters in the phrase, splits on whitespace, and
    joins with ``\\s+`` so double spaces or wrapped lines still match.
    """
    parts = re.split(r"\s+", phrase.strip())
    escaped = [re.escape(p) for p in parts if p]
    return r"\b" + r"\s+".join(escaped) + r"\b"


def _p(
    phrase: str,
    category: Category,
    severity: Severity,
    replacement: str | None = None,
    note: str | None = None,
    *,
    regex: str | None = None,
) -> SlopPattern:
    return SlopPattern(
        phrase=phrase,
        regex=regex if regex is not None else phrase_regex(phrase),
        category=category,
        severity=severity,
        replacement=replacement,
        note=note,
    )


# ---------------------------------------------------------------------------
# FILLER — empty meta-commentary. HIGH / delete.
# ---------------------------------------------------------------------------


def _filler_patterns() -> list[SlopPattern]:
    phrases = [
        "it is important to note that",
        "it's important to note that",
        "it is important to mention that",
        "it's important to mention that",
        "it is worth noting that",
        "it's worth noting that",
        "it is worth mentioning that",
        "it's worth mentioning that",
        "it is worth pointing out that",
        "it's worth pointing out that",
        "it should be noted that",
        "it must be noted that",
        "it must be mentioned that",
        "it goes without saying that",
        "it is important to understand that",
        "it's important to understand that",
        "it is crucial to note that",
        "it's crucial to note that",
        "it is crucial to understand that",
        "it's crucial to understand that",
        "it is essential to note that",
        "it's essential to note that",
        "it is essential to understand that",
        "it's essential to understand that",
        "it is important to consider that",
        "it's important to consider that",
        "it is important to recognize that",
        "it's important to recognize that",
        "it is interesting to note that",
        "it's interesting to note that",
        "one important thing to note is that",
        "one thing to keep in mind is that",
        "as previously mentioned",
        "as mentioned previously",
        "as mentioned earlier",
        "as mentioned above",
        "as stated above",
        "as stated earlier",
        "as has been shown",
        "as has been demonstrated",
        "at the end of the day",
        "needless to say",
    ]
    out = [_p(phrase, Category.FILLER, Severity.HIGH, "") for phrase in phrases]
    out.append(
        _p(
            "it goes without saying",
            Category.FILLER,
            Severity.HIGH,
            "",
            note="Deletable preamble; the claim that follows should stand alone.",
        )
    )
    return out


# ---------------------------------------------------------------------------
# BUZZWORDS — corporate-speak words.
# ---------------------------------------------------------------------------


def _buzzword_patterns() -> list[SlopPattern]:
    out: list[SlopPattern] = []
    # Conjugated verbs where a per-form replacement actually reads well.
    out.extend(
        [
            _p(
                "leverage",
                Category.BUZZWORD,
                Severity.HIGH,
                "use",
                note="Prefer 'use' unless the financial/engineering sense is intended.",
            ),
            _p("leverages", Category.BUZZWORD, Severity.HIGH, "uses"),
            _p("leveraged", Category.BUZZWORD, Severity.HIGH, "used"),
            _p("leveraging", Category.BUZZWORD, Severity.HIGH, "using"),
            _p("utilize", Category.BUZZWORD, Severity.HIGH, "use"),
            _p("utilizes", Category.BUZZWORD, Severity.HIGH, "uses"),
            _p("utilized", Category.BUZZWORD, Severity.HIGH, "used"),
            _p("utilizing", Category.BUZZWORD, Severity.HIGH, "using"),
            _p("utilization", Category.BUZZWORD, Severity.MEDIUM, "use"),
        ]
    )
    # Buzzword adjectives and nouns — flag, no auto-replace.
    flag_only = [
        "synergy",
        "synergies",
        "synergistic",
        "synergize",
        "paradigm shift",
        "paradigm-shifting",
        "cutting-edge",
        "cutting edge",
        "state-of-the-art",
        "state of the art",
        "best-in-class",
        "best in class",
        "world-class",
        "world class",
        "next-generation",
        "next generation",
        "bleeding-edge",
        "bleeding edge",
        "mission-critical",
        "mission critical",
        "turnkey",
        "end-to-end solution",
        "end to end solution",
        "holistic approach",
        "holistic view",
        "holistically",
        "seamlessly",
        "seamless integration",
        "seamless experience",
        "scalable solution",
        "game-changing",
        "game changing",
        "game-changer",
        "game changer",
        "groundbreaking",
        "revolutionary",
        "disruptive innovation",
        "thought leadership",
        "thought leader",
        "value-add",
        "value add",
        "value-added",
        "value added",
    ]
    out.extend(
        _p(phrase, Category.BUZZWORD, Severity.HIGH, note="Corporate buzzword.")
        for phrase in flag_only
    )
    # "Empower" family — MEDIUM because it sometimes has legitimate uses.
    out.extend(
        [
            _p("empower", Category.BUZZWORD, Severity.MEDIUM),
            _p("empowers", Category.BUZZWORD, Severity.MEDIUM),
            _p("empowered", Category.BUZZWORD, Severity.MEDIUM),
            _p("empowering", Category.BUZZWORD, Severity.MEDIUM),
            _p("empowerment", Category.BUZZWORD, Severity.MEDIUM),
        ]
    )
    # Quantifier inflation.
    out.extend(
        [
            _p("a plethora of", Category.BUZZWORD, Severity.HIGH, "many"),
            _p("plethora of", Category.BUZZWORD, Severity.HIGH, "many"),
            _p("a myriad of", Category.BUZZWORD, Severity.HIGH, "many"),
            _p("myriad of", Category.BUZZWORD, Severity.HIGH, "many"),
            _p("a multitude of", Category.BUZZWORD, Severity.HIGH, "many"),
            _p("multitude of", Category.BUZZWORD, Severity.HIGH, "many"),
            _p("a wide range of", Category.BUZZWORD, Severity.MEDIUM),
            _p("a wide variety of", Category.BUZZWORD, Severity.MEDIUM),
            _p("a vast array of", Category.BUZZWORD, Severity.MEDIUM),
            _p("a vast number of", Category.BUZZWORD, Severity.MEDIUM),
            _p("a broad spectrum of", Category.BUZZWORD, Severity.MEDIUM),
        ]
    )
    return out


# ---------------------------------------------------------------------------
# HEDGING — verbose hedges. Usually collapsible to a direct statement.
# ---------------------------------------------------------------------------


def _hedging_patterns() -> list[SlopPattern]:
    phrases_medium = [
        "it could potentially be argued that",
        "it could be argued that",
        "one could argue that",
        "one might argue that",
        "it might be suggested that",
        "it might be argued that",
        "there is a possibility that",
        "there exists a possibility that",
        "there is a chance that",
        "it may be the case that",
        "it might be the case that",
        "in some sense",
        "in a manner of speaking",
        "more or less",
    ]
    out = [_p(phrase, Category.HEDGING, Severity.MEDIUM) for phrase in phrases_medium]
    # "Arguably" as a standalone hedge opener is LOW — sometimes useful.
    out.append(_p("arguably", Category.HEDGING, Severity.LOW))
    return out


# ---------------------------------------------------------------------------
# FALSE_TRANSITION — meaningless connectives.
# ---------------------------------------------------------------------------


def _false_transition_patterns() -> list[SlopPattern]:
    medium = [
        "furthermore",
        "moreover",
        "in conclusion",
        "in summary",
        "to summarize",
        "to conclude",
        "in today's world",
        "in today's fast-paced world",
        "in today's fast paced world",
        "in today's digital age",
        "in today's modern era",
        "in the modern era",
        "in modern times",
        "in this day and age",
        "when all is said and done",
        "at the end of the day",
    ]
    out = [_p(phrase, Category.FALSE_TRANSITION, Severity.MEDIUM) for phrase in medium]
    out.extend(
        [
            _p(
                "in today's",
                Category.FALSE_TRANSITION,
                Severity.LOW,
                note="Vague time-marker; specify the year or period.",
                regex=r"\bin\s+today'?s\b",
            ),
            _p("nowadays", Category.FALSE_TRANSITION, Severity.LOW),
        ]
    )
    return out


# ---------------------------------------------------------------------------
# SUPERLATIVE — inflated adverbs/adjectives.
# ---------------------------------------------------------------------------


def _superlative_patterns() -> list[SlopPattern]:
    phrases = [
        "incredibly",
        "absolutely",
        "truly",
        "extraordinarily",
        "remarkably",
        "remarkable",
        "exceptionally",
        "exceptional",
        "immensely",
        "tremendously",
        "profoundly",
        "unparalleled",
        "unrivaled",
        "unrivalled",
        "awe-inspiring",
        "mind-blowing",
        "mind blowing",
        "jaw-dropping",
        "jaw dropping",
        "breathtaking",
        "utterly",
    ]
    out = [_p(phrase, Category.SUPERLATIVE, Severity.MEDIUM) for phrase in phrases]
    # "Very" — LOW because sometimes legitimately used; in consulting
    # prefer specific quantification.
    out.append(_p("very", Category.SUPERLATIVE, Severity.LOW, note="Prefer a specific quantifier."))
    return out


# ---------------------------------------------------------------------------
# AI_TELL — phrases that should not appear in any consulting brief.
# ---------------------------------------------------------------------------


def _ai_tell_patterns() -> list[SlopPattern]:
    phrases = [
        "as a language model",
        "as an ai language model",
        "as an ai assistant",
        "i am an ai",
        "i'm an ai",
        "i am just an ai",
        "i'm just an ai",
        "i don't have access to",
        "i do not have access to",
        "i don't have the ability to",
        "i do not have the ability to",
        "i cannot browse the internet",
        "i can't browse the internet",
        "based on my training data",
        "based on my training",
        "my knowledge has a cutoff",
        "my training data has a cutoff",
        "i cannot predict future events",
        "i cannot predict the future",
    ]
    return [
        _p(
            phrase,
            Category.AI_TELL,
            Severity.HIGH,
            note="AI self-reference never belongs in a consulting brief.",
        )
        for phrase in phrases
    ]


# ---------------------------------------------------------------------------
# LLM_TIC — the "delve / tapestry / realm" family.
# ---------------------------------------------------------------------------


def _llm_tic_patterns() -> list[SlopPattern]:
    out: list[SlopPattern] = []
    # Delve family — "delve" is intransitive with "into", so the grammatical
    # replacement needs to consume "into" as well. Standalone forms are
    # flagged without a replacement so the writer picks a specific verb.
    out.extend(
        [
            _p("delve into", Category.LLM_TIC, Severity.HIGH, "examine"),
            _p("delves into", Category.LLM_TIC, Severity.HIGH, "examines"),
            _p("delved into", Category.LLM_TIC, Severity.HIGH, "examined"),
            _p("delving into", Category.LLM_TIC, Severity.HIGH, "examining"),
            _p(
                "delve",
                Category.LLM_TIC,
                Severity.HIGH,
                note="Classic LLM tic. Pick a specific verb.",
            ),
            _p(
                "delves",
                Category.LLM_TIC,
                Severity.HIGH,
                note="Classic LLM tic. Pick a specific verb.",
            ),
            _p(
                "delved",
                Category.LLM_TIC,
                Severity.HIGH,
                note="Classic LLM tic. Pick a specific verb.",
            ),
            _p(
                "delving",
                Category.LLM_TIC,
                Severity.HIGH,
                note="Classic LLM tic. Pick a specific verb.",
            ),
        ]
    )
    # Other LLM tics — flagged, no auto-replace (the writer needs to
    # pick a specific word).
    flag_only = [
        "tapestry",
        "tapestries",
        "in the realm of",
        "the realm of",
        "realm of possibility",
        "the landscape of",
        "landscape of",
        "navigate the landscape",
        "navigate the complexities",
        "navigate the complex",
        "navigate the intricacies",
        "the intricacies of",
        "a testament to",
        "stands as a testament",
        "stand as a testament",
        "testament to",
        "embark on a journey",
        "embark upon",
        "embark on",
        "unleash the power",
        "harness the power",
        "unlock the potential",
        "unlock the power",
        "dive deep into",
        "dive deep",
        "take a deep dive",
        "a deep dive into",
        "let's explore",
        "let's dive into",
        "let's dive in",
        "let's take a look at",
        "let's examine",
        "let us explore",
        "at its essence",
        "at the crossroads of",
        "at the intersection of",
        "at the heart of",
        "weaving together",
        "interwoven",
        "intertwined",
        "meticulously",
        "meticulous",
        "showcase",
        "showcases",
        "showcased",
        "showcasing",
        "game-changing",
        "elevate your",
        "elevates your",
        "transformative",
        "unwavering",
        "ever-evolving",
        "ever evolving",
        "ever-changing",
        "ever changing",
        "in the tapestry of",
        "the ever-evolving landscape",
    ]
    out.extend(
        _p(phrase, Category.LLM_TIC, Severity.HIGH, note="High-frequency LLM verbal tic.")
        for phrase in flag_only
    )
    return out


# ---------------------------------------------------------------------------
# CORPORATE_FILLER — business-speak clichés.
# ---------------------------------------------------------------------------


def _corporate_filler_patterns() -> list[SlopPattern]:
    phrases = [
        "move the needle",
        "low-hanging fruit",
        "low hanging fruit",
        "boil the ocean",
        "circle back",
        "circle-back",
        "touch base",
        "take this offline",
        "think outside the box",
        "outside the box",
        "drill down into",
        "drill down",
        "drive value",
        "drive success",
        "drive growth",
        "drive results",
        "driving value",
        "driving success",
        "foster a culture",
        "foster collaboration",
        "foster innovation",
        "fostering a culture",
        "game plan",
        "deep dive",
        "deep-dive",
        "win-win",
        "win win",
        "bandwidth",
        "at scale",
        "rightsize",
        "right-size",
        "operationalize",
        "ideate",
        "ideation",
        "incentivize",
    ]
    return [_p(phrase, Category.CORPORATE_FILLER, Severity.MEDIUM) for phrase in phrases]


# ---------------------------------------------------------------------------
# WEAK_OPENER — weak sentence starts.
# ---------------------------------------------------------------------------


def _weak_opener_patterns() -> list[SlopPattern]:
    phrases_medium = [
        "when it comes to",
        "in terms of",
        "with regards to",
        "with regard to",
        "in regards to",
        "in regard to",
        "in the context of",
        "in a world where",
        "at the forefront of",
    ]
    out = [_p(phrase, Category.WEAK_OPENER, Severity.MEDIUM) for phrase in phrases_medium]
    phrases_low = [
        "notably",
        "specifically",
        "particularly",
        "interestingly",
        "essentially",
        "basically",
        "ultimately",
        "fundamentally",
    ]
    out.extend(_p(phrase, Category.WEAK_OPENER, Severity.LOW) for phrase in phrases_low)
    return out


# ---------------------------------------------------------------------------
# Exported, flat, ordered tuple.
# ---------------------------------------------------------------------------


def _build_default_patterns() -> tuple[SlopPattern, ...]:
    patterns = (
        _filler_patterns()
        + _buzzword_patterns()
        + _hedging_patterns()
        + _false_transition_patterns()
        + _superlative_patterns()
        + _ai_tell_patterns()
        + _llm_tic_patterns()
        + _corporate_filler_patterns()
        + _weak_opener_patterns()
    )
    # Dedupe while preserving order. A phrase can legitimately appear in
    # two lists (e.g. "at the end of the day" in both FILLER and
    # FALSE_TRANSITION); the earlier category wins so reports stay stable.
    seen: set[str] = set()
    deduped: list[SlopPattern] = []
    for pattern in patterns:
        key = pattern.regex.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(pattern)
    return tuple(deduped)


DEFAULT_PATTERNS: tuple[SlopPattern, ...] = _build_default_patterns()
"""Immutable tuple of curated patterns. Safe to share across detectors."""
