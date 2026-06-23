from __future__ import annotations

import logging
import re

from sqlmodel import Session

from feintlex.models import ContentItem, Lesson, ReviewItem
from feintlex.services.quiz_generator import generate_quiz
from feintlex.services.vocabulary import extract_vocabulary, upsert_vocabulary_entries


LOGGER = logging.getLogger("feintlex.lessons")
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")


def segment_sentences(text: str) -> list[str]:
    sentences = [" ".join(part.split()) for part in SENTENCE_PATTERN.split(text.strip())]
    return [sentence for sentence in sentences if sentence]


def make_title(content: ContentItem, sentences: list[str]) -> str:
    if content.topic_tags:
        topic = " / ".join(tag.title() for tag in content.topic_tags[:2])
        return f"{topic} Reading Drill"
    first = sentences[0] if sentences else "Spanish Reading Drill"
    words = first.split()
    return " ".join(words[:8]).rstrip(".,;:") or "Spanish Reading Drill"


def summarize_english(sentences: list[str]) -> str:
    if not sentences:
        return "Rule-based summary unavailable because no sentence was detected."
    return (
        "Rule-based MVP summary: review the opening sentence, identify the main actors, "
        "and confirm the core action before refining with AI."
    )


def summarize_spanish(sentences: list[str]) -> str:
    if not sentences:
        return "Resumen no disponible."
    return sentences[0]


def detect_grammar_points(text: str) -> list[str]:
    lowered = text.lower()
    points = []
    if any(marker in lowered for marker in ("porque", "aunque", "pero", "mientras")):
        points.append("Connectors for cause, contrast, or time appear in the text.")
    if any(marker in lowered for marker in ("ha ", "han ", "he ", "hemos ")):
        points.append("Possible present perfect structure detected: haber + participle.")
    if any(word.endswith(("aba", "aban", "ia", "ian")) for word in re.findall(r"\w+", lowered)):
        points.append("Possible imperfect tense markers appear; verify in sentence autopsy.")
    if not points:
        points.append("MVP grammar scan: identify verbs, connectors, and noun-adjective agreement manually.")
    points.append("TODO: enrich grammar mapping with LLM-assisted explanations.")
    return points


def build_review_items(vocabulary: list[dict[str, object]], sentence_candidates: list[str]) -> list[dict[str, str]]:
    review_items = [
        {"type": "vocabulary", "prompt": f"Recall and use '{item['term']}' in a new sentence."}
        for item in vocabulary[:5]
    ]
    for sentence in sentence_candidates[:2]:
        review_items.append({"type": "sentence", "prompt": f"Reconstruct and explain: {sentence}"})
    return review_items


def generate_lesson(session: Session, content_id: int) -> Lesson:
    content = session.get(ContentItem, content_id)
    if content is None:
        raise ValueError(f"Content item {content_id} was not found.")

    sentences = segment_sentences(content.text)
    vocabulary = extract_vocabulary(content.text)
    sentence_candidates = sorted(sentences, key=len, reverse=True)[:5]
    title = make_title(content, sentences)
    quiz = generate_quiz(title=title, sentence_candidates=sentence_candidates, key_vocabulary=vocabulary)
    review_items = build_review_items(vocabulary, sentence_candidates)

    lesson = Lesson(
        content_id=content.id,
        title=title,
        english_summary=summarize_english(sentences),
        spanish_summary=summarize_spanish(sentences),
        key_vocabulary=vocabulary,
        grammar_points=detect_grammar_points(content.text),
        sentence_breakdown_candidates=sentence_candidates,
        comprehension_questions=[
            "Who or what is the main subject?",
            "What changed, happened, or was argued?",
            "Which connectors explain cause, contrast, or sequence?",
        ],
        writing_prompt="Write 5 Spanish sentences responding to the text, then mark the verbs and connectors.",
        review_items=review_items,
        quiz=quiz,
    )
    session.add(lesson)
    session.commit()
    session.refresh(lesson)

    upsert_vocabulary_entries(session, vocabulary, lesson_id=lesson.id, topic_tags=content.topic_tags)
    for item in review_items:
        session.add(
            ReviewItem(
                item_type=item["type"],
                prompt=item["prompt"],
                answer="Self-check against the lesson and source text.",
                related_lesson_id=lesson.id,
            )
        )
    session.commit()
    LOGGER.info("lesson_generated", extra={"lesson_id": lesson.id, "content_id": content_id})
    return lesson
