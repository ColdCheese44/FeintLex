from __future__ import annotations

import re

from sqlmodel import Session

from feintlex.models import SentenceAutopsy
from feintlex.services.lexicon import coverage, gloss_tokens, literal_gloss
from feintlex.services.vocabulary import SPANISH_STOPWORDS, extract_vocabulary, normalize_term, tokenize


CONNECTORS = {
    "ademas": "addition",
    "aunque": "contrast/concession",
    "cuando": "time",
    "despues": "sequence",
    "entonces": "sequence/result",
    "mientras": "time/contrast",
    "pero": "contrast",
    "porque": "cause",
    "que": "clause connector",
    "si": "condition",
    "sin": "absence/contrast",
    "tambien": "addition",
    "y": "addition",
}

COMMON_VERBS = {
    "analiza",
    "aprende",
    "busca",
    "controla",
    "crea",
    "debe",
    "deben",
    "detecta",
    "dice",
    "dijo",
    "entra",
    "escribe",
    "es",
    "esta",
    "estan",
    "estaba",
    "explica",
    "fue",
    "hay",
    "hace",
    "hizo",
    "mejora",
    "necesita",
    "puede",
    "pueden",
    "quiere",
    "revisa",
    "son",
    "tiene",
    "tienen",
    "usa",
    "va",
    "van",
}

VERB_ENDING_PATTERN = re.compile(
    r"(ar|er|ir|ando|iendo|aba|aban|ia|ian|aste|aron|ieron|aremos|eran)$"
)


def detect_connectors(sentence: str) -> list[dict[str, str]]:
    found = []
    for token in tokenize(sentence):
        normalized = normalize_term(token)
        if normalized in CONNECTORS:
            found.append({"term": token.lower(), "role": CONNECTORS[normalized]})
    return found


def detect_verbs(sentence: str) -> list[str]:
    verbs: list[str] = []
    for token in tokenize(sentence):
        raw = token.lower()
        normalized = normalize_term(token)
        if len(normalized) < 2 or normalized in SPANISH_STOPWORDS:
            continue
        if normalized in COMMON_VERBS or VERB_ENDING_PATTERN.search(normalized) or raw.endswith(("ó", "ió")):
            verbs.append(token.lower())
    return list(dict.fromkeys(verbs))


def detect_tense_notes(sentence: str, verbs: list[str]) -> list[str]:
    normalized_sentence = normalize_term(sentence)
    notes: list[str] = []
    if re.search(r"\b(estoy|estas|esta|estamos|estan)\b.*(ando|iendo)\b", normalized_sentence):
        notes.append("Likely present progressive structure: estar + -ando/-iendo.")
    if any(re.search(r"(o|aste|aron|io|ieron)$", normalize_term(verb)) for verb in verbs):
        notes.append("Some verbs may be preterite or present forms; confirm with context.")
    if any(re.search(r"(aba|aban|ia|ian)$", normalize_term(verb)) for verb in verbs):
        notes.append("Possible imperfect tense marker detected.")
    if any(re.search(r"(are|era|eran|ara|aran)$", normalize_term(verb)) for verb in verbs):
        notes.append("Possible future or subjunctive marker detected.")
    if not notes:
        notes.append("Rule-based grammar scan found no strong tense marker.")
    return notes


def _natural_gloss(sentence: str) -> str:
    """Best-effort natural reading assembled from the offline lexicon."""
    glosses = gloss_tokens(sentence)
    known = coverage(sentence)
    words = []
    for item in glosses:
        english = item["en"]
        if english == "?":
            words.append(f"[{item['es']}]")
        else:
            # Take the first alternative when the gloss lists several.
            words.append(english.split("/")[0].split("(")[0].strip())
    reading = " ".join(words)
    confidence = "high" if known >= 0.8 else "partial" if known >= 0.5 else "low"
    return f"{reading} (offline gloss, {confidence} confidence — unknown words in brackets)"


def autopsy_sentence(sentence: str) -> dict[str, object]:
    cleaned = " ".join(sentence.strip().split())
    if not cleaned:
        raise ValueError("Sentence cannot be empty.")

    verbs = detect_verbs(cleaned)
    connectors = detect_connectors(cleaned)
    vocabulary = extract_vocabulary(cleaned, limit=12)
    grammar_notes = detect_tense_notes(cleaned, verbs)
    connector_terms = ", ".join(item["term"] for item in connectors) or "no major connector"
    verb_terms = ", ".join(verbs) or "main action"

    return {
        "original": cleaned,
        "literal_translation": literal_gloss(cleaned),
        "natural_translation": _natural_gloss(cleaned),
        "grammar_notes": grammar_notes,
        "verbs": verbs,
        "connectors": connectors,
        "vocabulary": vocabulary,
        "pattern": f"Sentence built around {verb_terms} with {connector_terms}.",
        "practice_prompt": "Write 3 similar Spanish sentences using this structure.",
    }


def persist_autopsy(session: Session, sentence: str, *, lesson_id: int | None = None) -> SentenceAutopsy:
    result = autopsy_sentence(sentence)
    autopsy = SentenceAutopsy(lesson_id=lesson_id, **result)
    session.add(autopsy)
    session.commit()
    session.refresh(autopsy)
    return autopsy
