from __future__ import annotations

"""Rule-based Spanish writing correction.

Offline heuristics that catch high-confidence beginner mistakes:
inverted punctuation, capitalization, interrogative accents, and
article-noun gender agreement. Detected issues feed the mistake bank
so they resurface in spaced review.
"""

import logging
import re

from sqlmodel import Session

from feintlex.models import WritingSubmission
from feintlex.services.mistake_bank import create_mistake
from feintlex.services.sentence_autopsy import detect_connectors, detect_verbs
from feintlex.services.vocabulary import normalize_term


LOGGER = logging.getLogger("feintlex.writing")

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Nouns ending in -a that take el, and -o that take la.
MASCULINE_A_NOUNS = {
    "dia", "mapa", "problema", "programa", "sistema", "tema",
    "idioma", "clima", "planeta", "sofa", "drama",
}
FEMININE_O_NOUNS = {"mano", "foto", "moto", "radio"}
# Feminine nouns that take el for pronunciation (stressed initial a-).
STRESSED_A_FEMININES = {"agua", "alma", "area", "hambre", "aguila", "arma", "aula"}

INTERROGATIVES = {
    "que": "qué", "como": "cómo", "donde": "dónde", "cuando": "cuándo",
    "quien": "quién", "cuanto": "cuánto", "cual": "cuál",
}

ARTICLE_PATTERN = re.compile(r"\b(el|la)\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)", re.IGNORECASE)


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in SENTENCE_SPLIT.split(text.strip()) if part.strip()]


def _check_inverted_punctuation(sentences: list[str]) -> list[dict[str, str]]:
    issues = []
    for sentence in sentences:
        if sentence.endswith("?") and not sentence.startswith("¿"):
            issues.append(
                {
                    "type": "punctuation",
                    "original": sentence,
                    "correction": f"¿{sentence}",
                    "explanation": "Spanish questions open with an inverted question mark: ¿...?",
                }
            )
        if sentence.endswith("!") and not sentence.startswith("¡"):
            issues.append(
                {
                    "type": "punctuation",
                    "original": sentence,
                    "correction": f"¡{sentence}",
                    "explanation": "Spanish exclamations open with an inverted exclamation mark: ¡...!",
                }
            )
    return issues


def _check_capitalization(sentences: list[str]) -> list[dict[str, str]]:
    issues = []
    for sentence in sentences:
        stripped = sentence.lstrip("¿¡")
        if stripped and stripped[0].isalpha() and stripped[0].islower():
            fixed = sentence.replace(stripped, stripped[0].upper() + stripped[1:], 1)
            issues.append(
                {
                    "type": "capitalization",
                    "original": sentence,
                    "correction": fixed,
                    "explanation": "Sentences start with a capital letter.",
                }
            )
    return issues


def _check_interrogative_accents(sentences: list[str]) -> list[dict[str, str]]:
    issues = []
    for sentence in sentences:
        if not (sentence.endswith("?") or sentence.startswith("¿")):
            continue
        lead = sentence.lstrip("¿ ").split()
        if not lead:
            continue
        first = lead[0].rstrip("?,.!").lower()
        if first in INTERROGATIVES and first == normalize_term(first):
            accented = INTERROGATIVES[first]
            if first != accented and accented not in sentence.lower():
                issues.append(
                    {
                        "type": "accent",
                        "original": sentence,
                        "correction": sentence.replace(lead[0], accented.capitalize() if lead[0][0].isupper() else accented, 1),
                        "explanation": f"Question words carry an accent: '{first}' becomes '{accented}' in questions.",
                    }
                )
    return issues


def _check_gender_agreement(text: str) -> list[dict[str, str]]:
    issues = []
    for match in ARTICLE_PATTERN.finditer(text):
        article = match.group(1).lower()
        noun = match.group(2)
        normalized = normalize_term(noun)
        if article == "la" and (normalized in MASCULINE_A_NOUNS or normalized in STRESSED_A_FEMININES):
            issues.append(
                {
                    "type": "gender_agreement",
                    "original": match.group(0),
                    "correction": f"el {noun}",
                    "explanation": f"'{noun}' takes el: it is a common exception (el {noun}).",
                }
            )
        elif article == "el" and normalized in FEMININE_O_NOUNS:
            issues.append(
                {
                    "type": "gender_agreement",
                    "original": match.group(0),
                    "correction": f"la {noun}",
                    "explanation": f"'{noun}' is feminine despite ending in -o: la {noun}.",
                }
            )
        elif article == "el" and normalized.endswith("a"):
            if normalized in MASCULINE_A_NOUNS or normalized in STRESSED_A_FEMININES:
                continue
            issues.append(
                {
                    "type": "gender_agreement",
                    "original": match.group(0),
                    "correction": f"la {noun}",
                    "explanation": f"'{noun}' ends in -a and is likely feminine: la {noun}.",
                }
            )
        elif article == "la" and normalized.endswith("o") and normalized not in FEMININE_O_NOUNS:
            issues.append(
                {
                    "type": "gender_agreement",
                    "original": match.group(0),
                    "correction": f"el {noun}",
                    "explanation": f"'{noun}' ends in -o and is likely masculine: el {noun}.",
                }
            )
    return issues


def _apply_corrections(text: str, issues: list[dict[str, str]]) -> str:
    corrected = text
    for issue in issues:
        corrected = corrected.replace(issue["original"], issue["correction"], 1)
    return corrected


def _collect_strengths(text: str, sentences: list[str]) -> list[str]:
    strengths = []
    connectors = detect_connectors(text)
    if connectors:
        used = ", ".join(sorted({item["term"] for item in connectors}))
        strengths.append(f"Good connector use: {used}.")
    verbs = detect_verbs(text)
    if len(set(verbs)) >= 3:
        strengths.append(f"Verb variety detected ({len(set(verbs))} distinct verb forms).")
    if len(sentences) >= 3:
        strengths.append(f"Solid volume: {len(sentences)} sentences submitted.")
    if not strengths:
        strengths.append("Submission captured; keep sentences short and verb-focused.")
    return strengths


def analyze_writing(text: str) -> dict[str, object]:
    """Pure analysis used by both the writing endpoint and tutor chat."""
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Submitted text cannot be empty.")

    # Fixes are applied in stages so earlier rewrites cannot break later
    # matches: word-level fixes first, then punctuation, then capitalization
    # recomputed against the current text.
    corrected = cleaned
    word_issues = [
        *_check_gender_agreement(corrected),
        *_check_interrogative_accents(_split_sentences(corrected)),
    ]
    corrected = _apply_corrections(corrected, word_issues)

    punctuation_issues = _check_inverted_punctuation(_split_sentences(corrected))
    corrected = _apply_corrections(corrected, punctuation_issues)

    capitalization_issues = _check_capitalization(_split_sentences(corrected))
    corrected = _apply_corrections(corrected, capitalization_issues)

    sentences = _split_sentences(cleaned)
    issues = [*word_issues, *punctuation_issues, *capitalization_issues]
    grammar_notes = sorted({issue["explanation"] for issue in issues})
    if not grammar_notes:
        grammar_notes = ["Rule-based scan found no high-confidence issues. Read it aloud and check verb endings."]

    return {
        "submitted_text": cleaned,
        "corrected_version": corrected,
        "strengths": _collect_strengths(cleaned, sentences),
        "issues": issues,
        "grammar_notes": grammar_notes,
        "rewrite_prompt": "Rewrite the text once using one connector and one clearly marked verb tense.",
    }


def submit_writing(
    session: Session,
    submitted_text: str,
    *,
    related_lesson_id: int | None = None,
) -> WritingSubmission:
    analysis = analyze_writing(submitted_text)

    feedback = WritingSubmission(
        submitted_text=analysis["submitted_text"],
        corrected_version=analysis["corrected_version"],
        strengths=analysis["strengths"],
        issues=[f"{issue['original']} -> {issue['correction']} ({issue['explanation']})" for issue in analysis["issues"]],
        grammar_notes=analysis["grammar_notes"],
        rewrite_prompt=analysis["rewrite_prompt"],
        related_lesson_id=related_lesson_id,
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)

    for issue in analysis["issues"]:
        create_mistake(
            session,
            mistake_type=issue["type"],
            original_input=issue["original"],
            correction=issue["correction"],
            explanation=issue["explanation"],
            related_lesson_id=related_lesson_id,
        )

    LOGGER.info(
        "writing_submitted",
        extra={"writing_submission_id": feedback.id, "issue_count": len(analysis["issues"])},
    )
    return feedback
