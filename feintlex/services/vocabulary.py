from __future__ import annotations

import re
import unicodedata
from collections import Counter

from sqlmodel import Session, select

from feintlex.models import VocabularyEntry, utc_now


SPANISH_STOPWORDS = {
    "a",
    "al",
    "algo",
    "ante",
    "antes",
    "aquel",
    "aquella",
    "aquellas",
    "aquello",
    "aquellos",
    "aqui",
    "aun",
    "aunque",
    "cada",
    "como",
    "con",
    "contra",
    "cual",
    "cuando",
    "de",
    "del",
    "desde",
    "donde",
    "dos",
    "el",
    "ella",
    "ellas",
    "ellos",
    "en",
    "entre",
    "era",
    "eran",
    "eres",
    "es",
    "esa",
    "esas",
    "ese",
    "eso",
    "esos",
    "esta",
    "estan",
    "estar",
    "este",
    "esto",
    "estos",
    "fue",
    "han",
    "hasta",
    "hay",
    "la",
    "las",
    "le",
    "les",
    "lo",
    "los",
    "mas",
    "me",
    "mi",
    "muy",
    "no",
    "nos",
    "o",
    "para",
    "pero",
    "por",
    "porque",
    "que",
    "se",
    "ser",
    "si",
    "sin",
    "sobre",
    "son",
    "su",
    "sus",
    "tambien",
    "te",
    "tiene",
    "tienen",
    "un",
    "una",
    "uno",
    "unos",
    "y",
    "ya",
}

WORD_PATTERN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", re.UNICODE)


def normalize_term(term: str) -> str:
    normalized = unicodedata.normalize("NFKD", term.strip().lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def tokenize(text: str) -> list[str]:
    return WORD_PATTERN.findall(text)


def extract_vocabulary(text: str, *, min_length: int = 3, limit: int = 30) -> list[dict[str, int | str]]:
    counts: Counter[str] = Counter()
    display_terms: dict[str, str] = {}
    for word in tokenize(text):
        normalized = normalize_term(word)
        if len(normalized) < min_length or normalized in SPANISH_STOPWORDS:
            continue
        counts[normalized] += 1
        display_terms.setdefault(normalized, word.lower())
    return [
        {"term": display_terms[normalized], "normalized_term": normalized, "frequency": count}
        for normalized, count in counts.most_common(limit)
    ]


def upsert_vocabulary_entries(
    session: Session,
    vocabulary: list[dict[str, int | str]],
    *,
    lesson_id: int | None,
    topic_tags: list[str] | None = None,
) -> list[VocabularyEntry]:
    entries: list[VocabularyEntry] = []
    topic_tags = topic_tags or []
    for item in vocabulary:
        normalized = str(item["normalized_term"])
        statement = select(VocabularyEntry).where(
            VocabularyEntry.normalized_term == normalized,
            VocabularyEntry.source_lesson_id == lesson_id,
        )
        entry = session.exec(statement).first()
        if entry is None:
            entry = VocabularyEntry(
                term=str(item["term"]),
                normalized_term=normalized,
                source_lesson_id=lesson_id,
                frequency=int(item["frequency"]),
                topic_tags=topic_tags,
            )
            session.add(entry)
        else:
            entry.frequency += int(item["frequency"])
            entry.topic_tags = sorted(set(entry.topic_tags + topic_tags))
            entry.last_seen_at = utc_now()
            session.add(entry)
        entries.append(entry)
    session.commit()
    for entry in entries:
        session.refresh(entry)
    return entries
