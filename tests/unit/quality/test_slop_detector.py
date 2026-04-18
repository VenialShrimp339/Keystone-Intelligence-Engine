"""Unit tests for the deterministic slop detector.

Structure mirrors the detector's public surface: one class per category
plus classes for clean(), severity filtering, and integration on a
consulting paragraph.
"""

from __future__ import annotations

import pytest

from keystone.quality import (
    DEFAULT_PATTERNS,
    Category,
    Severity,
    SlopDetector,
    SlopPattern,
    SlopReport,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _detector() -> SlopDetector:
    return SlopDetector()


def _matched_phrases(report: SlopReport) -> list[str]:
    return [match.phrase for match in report.matches]


# ---------------------------------------------------------------------------
# Pattern database shape
# ---------------------------------------------------------------------------


class TestPatternDatabase:
    def test_has_at_least_two_hundred_patterns(self) -> None:
        assert len(DEFAULT_PATTERNS) >= 200

    def test_every_category_has_patterns(self) -> None:
        cats = {pattern.category for pattern in DEFAULT_PATTERNS}
        # Every category we defined should be represented.
        assert cats == set(Category)

    def test_every_severity_appears(self) -> None:
        sevs = {pattern.severity for pattern in DEFAULT_PATTERNS}
        assert sevs == set(Severity)

    def test_no_duplicate_regexes(self) -> None:
        regexes = [pattern.regex for pattern in DEFAULT_PATTERNS]
        assert len(regexes) == len(set(regexes))

    def test_replacements_exist_for_most_high_severity(self) -> None:
        high = [pattern for pattern in DEFAULT_PATTERNS if pattern.severity == Severity.HIGH]
        with_replacement = [pattern for pattern in high if pattern.replacement is not None]
        # Plenty of HIGH patterns are "flag only" because no single word
        # substitutes for e.g. "tapestry"; still want a meaningful share
        # of HIGH patterns to be auto-fixable.
        assert len(with_replacement) >= 40


# ---------------------------------------------------------------------------
# FILLER category
# ---------------------------------------------------------------------------


class TestFillerCategory:
    @pytest.mark.parametrize(
        "text",
        [
            "It is important to note that the market is small.",
            "It's important to note that pricing matters.",
            "It should be noted that the trend is flat.",
            "As previously mentioned, revenue fell.",
            "It goes without saying that costs matter.",
        ],
    )
    def test_filler_matches(self, text: str) -> None:
        report = _detector().detect(text)
        assert any(match.category == Category.FILLER for match in report.matches), text

    def test_filler_matches_are_high_severity(self) -> None:
        report = _detector().detect("It is important to note that revenue doubled.")
        filler = [match for match in report.matches if match.category == Category.FILLER]
        assert filler
        assert all(match.severity == Severity.HIGH for match in filler)


# ---------------------------------------------------------------------------
# BUZZWORD category
# ---------------------------------------------------------------------------


class TestBuzzwordCategory:
    @pytest.mark.parametrize(
        ("text", "expected_phrase"),
        [
            ("We leverage data.", "leverage"),
            ("We leveraged partnerships.", "leveraged"),
            ("Leveraging synergies across teams.", "leveraging"),
            ("We utilize the platform.", "utilize"),
            ("A plethora of features.", "a plethora of"),
            ("A wide range of products exist.", "a wide range of"),
            ("Our cutting-edge stack.", "cutting-edge"),
            ("A game-changing insight.", "game-changing"),
        ],
    )
    def test_buzzword_matches(self, text: str, expected_phrase: str) -> None:
        report = _detector().detect(text)
        assert expected_phrase in _matched_phrases(report), text

    def test_synergy_matches_even_at_end_of_sentence(self) -> None:
        report = _detector().detect("Expect significant synergies.")
        assert "synergies" in _matched_phrases(report)


# ---------------------------------------------------------------------------
# HEDGING category
# ---------------------------------------------------------------------------


class TestHedgingCategory:
    @pytest.mark.parametrize(
        "text",
        [
            "It could potentially be argued that revenue grew.",
            "One could argue that demand is soft.",
            "There is a possibility that supply tightens.",
            "It might be the case that rates rise.",
        ],
    )
    def test_hedging_matches(self, text: str) -> None:
        report = _detector().detect(text)
        assert any(match.category == Category.HEDGING for match in report.matches), text


# ---------------------------------------------------------------------------
# FALSE_TRANSITION category
# ---------------------------------------------------------------------------


class TestFalseTransitionCategory:
    @pytest.mark.parametrize(
        "text",
        [
            "Revenue grew. Furthermore, margin expanded.",
            "Margins widened. Moreover, costs fell.",
            "In conclusion, the strategy is sound.",
            "In today's fast-paced world, speed matters.",
        ],
    )
    def test_false_transition_matches(self, text: str) -> None:
        report = _detector().detect(text)
        assert any(match.category == Category.FALSE_TRANSITION for match in report.matches), text


# ---------------------------------------------------------------------------
# SUPERLATIVE category
# ---------------------------------------------------------------------------


class TestSuperlativeCategory:
    @pytest.mark.parametrize(
        "text",
        [
            "The product is incredibly fast.",
            "The team absolutely delivered.",
            "A remarkably elegant solution.",
            "An unparalleled opportunity.",
        ],
    )
    def test_superlative_matches(self, text: str) -> None:
        report = _detector().detect(text)
        assert any(match.category == Category.SUPERLATIVE for match in report.matches), text


# ---------------------------------------------------------------------------
# AI_TELL category
# ---------------------------------------------------------------------------


class TestAITellCategory:
    @pytest.mark.parametrize(
        "text",
        [
            "As a language model, I cannot guarantee accuracy.",
            "Based on my training data, revenue grew.",
            "I don't have access to real-time prices.",
            "My knowledge has a cutoff in 2024.",
        ],
    )
    def test_ai_tell_matches_and_is_high(self, text: str) -> None:
        report = _detector().detect(text)
        ai_matches = [match for match in report.matches if match.category == Category.AI_TELL]
        assert ai_matches, text
        assert all(match.severity == Severity.HIGH for match in ai_matches)


# ---------------------------------------------------------------------------
# LLM_TIC category
# ---------------------------------------------------------------------------


class TestLLMTicCategory:
    @pytest.mark.parametrize(
        "text",
        [
            "The report delves into revenue drivers.",
            "A tapestry of interconnected risks.",
            "In the realm of enterprise software, margins compress.",
            "This stands as a testament to execution.",
            "Let's dive into the data.",
            "An ever-evolving landscape of competition.",
            "The company showcases its new product.",
        ],
    )
    def test_llm_tic_matches(self, text: str) -> None:
        report = _detector().detect(text)
        assert any(match.category == Category.LLM_TIC for match in report.matches), text


# ---------------------------------------------------------------------------
# CORPORATE_FILLER category
# ---------------------------------------------------------------------------


class TestCorporateFillerCategory:
    @pytest.mark.parametrize(
        "text",
        [
            "We need to move the needle on retention.",
            "Start with the low-hanging fruit.",
            "Let's circle back next week.",
            "Drive value across the portfolio.",
        ],
    )
    def test_corporate_filler_matches(self, text: str) -> None:
        report = _detector().detect(text)
        assert any(match.category == Category.CORPORATE_FILLER for match in report.matches), text


# ---------------------------------------------------------------------------
# WEAK_OPENER category
# ---------------------------------------------------------------------------


class TestWeakOpenerCategory:
    @pytest.mark.parametrize(
        "text",
        [
            "When it comes to pricing, data is mixed.",
            "In terms of margin, growth is steady.",
            "Notably, cash conversion improved.",
            "Interestingly, churn fell.",
        ],
    )
    def test_weak_opener_matches(self, text: str) -> None:
        report = _detector().detect(text)
        assert any(match.category == Category.WEAK_OPENER for match in report.matches), text


# ---------------------------------------------------------------------------
# Word-boundary correctness
# ---------------------------------------------------------------------------


class TestWordBoundaries:
    @pytest.mark.parametrize(
        "text",
        [
            "The paradigmatic example of this pattern.",  # contains 'paradigm' but not pattern
            "A developer wrote this.",  # contains 'develop' family, unrelated
            "The developed market.",  # 'develop' inside 'developed'
            "Leveragers of capital.",  # 'leverag' + 'ers'
            "Showcasing.",  # 'showcasing' should match; this asserts no crash on edge
            "Landscaper.",  # 'landscape' family inside 'landscaper' should not match "landscape of"
            "Mistakenly.",  # no match for anything
        ],
    )
    def test_no_false_positives_inside_longer_words(self, text: str) -> None:
        report = _detector().detect(text)
        # If any match fires, its matched_text span must equal a whole word
        # (not a subword). We check that the text immediately adjacent to
        # the match is not a word character.
        for match in report.matches:
            before = text[match.start - 1] if match.start > 0 else " "
            after = text[match.end] if match.end < len(text) else " "
            assert not before.isalnum(), f"false positive boundary: {text!r} / {match!r}"
            assert not after.isalnum(), f"false positive boundary: {text!r} / {match!r}"

    def test_paradigm_does_not_fire_inside_paradigmatic(self) -> None:
        report = _detector().detect("A paradigmatic analysis.")
        phrases = _matched_phrases(report)
        # Neither "paradigm shift" nor any form containing the bare word
        # should match. (The database does not list "paradigm" alone.)
        assert all("paradigm" not in phrase for phrase in phrases)

    def test_delve_into_wins_over_delve(self) -> None:
        report = _detector().detect("The report delves into details.")
        # Overlap resolution keeps the longer phrase.
        phrases = _matched_phrases(report)
        assert "delves into" in phrases
        assert "delves" not in phrases


# ---------------------------------------------------------------------------
# clean()
# ---------------------------------------------------------------------------


class TestClean:
    def test_clean_deletes_high_filler_and_capitalizes(self) -> None:
        original = "It is important to note that the market is flat."
        assert _detector().clean(original) == "The market is flat."

    def test_clean_substitutes_buzzwords_for_replacements(self) -> None:
        assert _detector().clean("We leverage data.") == "We use data."

    def test_clean_preserves_medium_without_replacement(self) -> None:
        # "Furthermore" is MEDIUM with no replacement — left in place.
        text = "Revenue grew. Furthermore, margins expanded."
        assert _detector().clean(text) == text

    def test_clean_substitutes_plethora(self) -> None:
        assert _detector().clean("A plethora of options exist.") == "Many options exist."

    def test_clean_is_noop_on_empty_input(self) -> None:
        assert _detector().clean("") == ""

    def test_clean_is_noop_when_no_matches(self) -> None:
        text = "Revenue grew 12% year over year in 2026."
        assert _detector().clean(text) == text

    def test_clean_handles_all_slop_paragraph(self) -> None:
        raw = (
            "It is important to note that we leverage cutting-edge solutions "
            "to unlock the potential of a plethora of use cases."
        )
        cleaned = _detector().clean(raw)
        assert "important to note" not in cleaned.lower()
        assert "leverage" not in cleaned.lower()
        assert "plethora" not in cleaned.lower()

    def test_clean_preserves_markdown_list_markers(self) -> None:
        raw = "- It is important to note that revenue grew."
        cleaned = _detector().clean(raw)
        assert cleaned == "- Revenue grew."

    def test_clean_preserves_trailing_newline(self) -> None:
        cleaned = _detector().clean("Revenue grew.\n")
        assert cleaned.endswith("\n")

    def test_clean_is_idempotent(self) -> None:
        raw = "It is important to note that we leverage data."
        detector = _detector()
        once = detector.clean(raw)
        twice = detector.clean(once)
        assert once == twice

    def test_clean_leaves_low_severity_even_with_replacement(self) -> None:
        # Construct a custom detector where a LOW pattern has a replacement
        # to prove clean() refuses to auto-edit LOW matches.
        custom = SlopPattern(
            phrase="foobarbaz",
            regex=r"\bfoobarbaz\b",
            category=Category.WEAK_OPENER,
            severity=Severity.LOW,
            replacement="XXX",
        )
        detector = SlopDetector([custom])
        assert detector.clean("alpha foobarbaz beta.") == "alpha foobarbaz beta."


# ---------------------------------------------------------------------------
# Severity filtering
# ---------------------------------------------------------------------------


class TestSeverityFiltering:
    def test_min_severity_high_excludes_low_and_medium(self) -> None:
        text = "Notably, we leverage synergies. Furthermore, we delve."
        report = _detector().detect(text, min_severity=Severity.HIGH)
        assert all(match.severity == Severity.HIGH for match in report.matches)
        assert any(match.phrase == "leverage" for match in report.matches)
        assert not any(match.phrase == "furthermore" for match in report.matches)

    def test_min_severity_medium_excludes_low(self) -> None:
        text = "Notably, we leverage data. Furthermore, costs rose."
        report = _detector().detect(text, min_severity=Severity.MEDIUM)
        assert all(match.severity != Severity.LOW for match in report.matches)

    def test_at_or_above_helper(self) -> None:
        text = "Notably, we leverage synergies."
        report = _detector().detect(text)
        high_only = report.at_or_above(Severity.HIGH)
        assert all(match.severity == Severity.HIGH for match in high_only)


# ---------------------------------------------------------------------------
# Report shape
# ---------------------------------------------------------------------------


class TestReportShape:
    def test_empty_input_returns_empty_report(self) -> None:
        report = _detector().detect("")
        assert report.total == 0
        assert report.matches == ()
        assert report.counts_by_severity == {}
        assert report.counts_by_category == {}

    def test_no_matches_returns_empty_report(self) -> None:
        report = _detector().detect("Revenue grew 12% in 2026.")
        assert report.total == 0
        assert report.matches == ()

    def test_counts_match_matches(self) -> None:
        text = "It is important to note that we leverage a plethora of ideas."
        report = _detector().detect(text)
        assert report.total == sum(report.counts_by_severity.values())
        assert report.total == sum(report.counts_by_category.values())

    def test_matches_carry_line_and_col(self) -> None:
        text = "\nalpha beta.\nIt is important to note that growth slowed."
        report = _detector().detect(text)
        filler = next(match for match in report.matches if match.category == Category.FILLER)
        assert filler.line == 3
        assert filler.col == 1

    def test_matches_are_ordered_by_start_offset(self) -> None:
        text = (
            "It is important to note that we leverage synergies "
            "to unlock the potential of the ecosystem."
        )
        report = _detector().detect(text)
        starts = [match.start for match in report.matches]
        assert starts == sorted(starts)


# ---------------------------------------------------------------------------
# Consulting-text integration
# ---------------------------------------------------------------------------


class TestConsultingIntegration:
    SAMPLE = (
        "# Market Sizing: AV Sensor TAM\n"
        "\n"
        "It is important to note that the automotive sensor market is "
        "incredibly competitive. We leverage cutting-edge voice-of-customer "
        "research to delve into buyer preferences.\n"
        "\n"
        "Furthermore, a plethora of suppliers are entering the market, "
        "which creates a tapestry of pricing pressure. In today's fast-paced "
        "world, navigating the landscape of tier-one OEM relationships "
        "requires us to unlock the potential of data-driven decision-making.\n"
        "\n"
        "- It is important to note that unit economics vary by region.\n"
        "- We utilize the latest forecasting techniques.\n"
    )

    def test_detects_multiple_categories(self) -> None:
        report = _detector().detect(self.SAMPLE)
        cats = {match.category for match in report.matches}
        assert {
            Category.FILLER,
            Category.BUZZWORD,
            Category.LLM_TIC,
            Category.SUPERLATIVE,
        }.issubset(cats)

    def test_clean_drops_high_severity_phrases(self) -> None:
        cleaned = _detector().clean(self.SAMPLE)
        # Deleted filler.
        assert "It is important to note that" not in cleaned
        # Substituted buzzwords.
        assert "leverage" not in cleaned.lower()
        assert "utilize" not in cleaned.lower()
        assert "a plethora of" not in cleaned.lower()
        # Substituted LLM tic.
        assert "delve into" not in cleaned.lower()

    def test_clean_preserves_headers(self) -> None:
        cleaned = _detector().clean(self.SAMPLE)
        assert cleaned.startswith("# Market Sizing: AV Sensor TAM")

    def test_clean_preserves_list_markers_and_capitalizes(self) -> None:
        cleaned = _detector().clean(self.SAMPLE)
        assert "- Unit economics vary by region." in cleaned
