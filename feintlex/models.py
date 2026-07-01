from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


JsonList = list[Any]
JsonDict = dict[str, Any]


class ContentItem(SQLModel, table=True):
    __tablename__ = "content_items"

    id: int | None = Field(default=None, primary_key=True)
    text: str
    source_type: str = Field(default="pasted_text", index=True)
    topic_tags: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now, index=True)


class Lesson(SQLModel, table=True):
    __tablename__ = "lessons"

    id: int | None = Field(default=None, primary_key=True)
    content_id: int = Field(foreign_key="content_items.id", index=True)
    title: str
    source_language: str = "Spanish"
    target_language: str = "English"
    english_summary: str
    spanish_summary: str
    key_vocabulary: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    grammar_points: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    sentence_breakdown_candidates: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    comprehension_questions: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    writing_prompt: str
    review_items: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    quiz: JsonDict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now, index=True)


class SentenceAutopsy(SQLModel, table=True):
    __tablename__ = "sentence_autopsies"

    id: int | None = Field(default=None, primary_key=True)
    lesson_id: int | None = Field(default=None, foreign_key="lessons.id", index=True)
    original: str
    literal_translation: str
    natural_translation: str
    grammar_notes: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    verbs: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    connectors: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    vocabulary: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    pattern: str
    practice_prompt: str
    created_at: datetime = Field(default_factory=utc_now, index=True)


class VocabularyEntry(SQLModel, table=True):
    __tablename__ = "vocabulary_entries"

    id: int | None = Field(default=None, primary_key=True)
    term: str
    normalized_term: str = Field(index=True)
    language: str = Field(default="Spanish", index=True)
    source_lesson_id: int | None = Field(default=None, foreign_key="lessons.id", index=True)
    frequency: int = 1
    topic_tags: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    status: str = Field(default="new", index=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)
    last_seen_at: datetime = Field(default_factory=utc_now, index=True)


class WritingSubmission(SQLModel, table=True):
    __tablename__ = "writing_submissions"

    id: int | None = Field(default=None, primary_key=True)
    submitted_text: str
    corrected_version: str
    strengths: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    issues: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    grammar_notes: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    rewrite_prompt: str
    related_lesson_id: int | None = Field(default=None, foreign_key="lessons.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)


class Mistake(SQLModel, table=True):
    __tablename__ = "mistakes"

    id: int | None = Field(default=None, primary_key=True)
    mistake_type: str = Field(index=True)
    original_input: str
    correction: str
    explanation: str
    related_lesson_id: int | None = Field(default=None, foreign_key="lessons.id", index=True)
    review_due_at: datetime = Field(default_factory=utc_now, index=True)
    status: str = Field(default="new", index=True)
    review_count: int = 0
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now, index=True)


class ReviewItem(SQLModel, table=True):
    __tablename__ = "review_items"

    id: int | None = Field(default=None, primary_key=True)
    item_type: str = Field(index=True)
    prompt: str
    answer: str
    related_lesson_id: int | None = Field(default=None, foreign_key="lessons.id", index=True)
    due_at: datetime = Field(default_factory=utc_now, index=True)
    status: str = Field(default="due", index=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)


class ExportRecord(SQLModel, table=True):
    __tablename__ = "exports"

    id: int | None = Field(default=None, primary_key=True)
    lesson_id: int = Field(foreign_key="lessons.id", index=True)
    path: str
    format: str = "markdown"
    created_at: datetime = Field(default_factory=utc_now, index=True)


class TutorChatMessage(SQLModel, table=True):
    __tablename__ = "tutor_chat_messages"

    id: int | None = Field(default=None, primary_key=True)
    session_key: str = Field(default="default", index=True)
    role: str = Field(index=True)  # "user" or "tutor"
    content: str
    intent: str | None = Field(default=None, index=True)
    cards: JsonList = Field(default_factory=list, sa_column=Column(JSON))
    provider: str = Field(default="offline_rule_based")
    created_at: datetime = Field(default_factory=utc_now, index=True)


class TutorMastery(SQLModel, table=True):
    __tablename__ = "tutor_mastery"

    id: int | None = Field(default=None, primary_key=True)
    term_id: str = Field(index=True, unique=True)
    deck_id: str = Field(default="", index=True)
    term: str = ""
    translation: str = ""
    level: int = 0
    seen: int = 0
    correct: int = 0
    updated_at: datetime = Field(default_factory=utc_now, index=True)
