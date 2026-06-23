from __future__ import annotations

from sqlalchemy import inspect

from feintlex.config import get_settings
from feintlex.db import get_engine


def test_db_init_creates_expected_tables(isolated_session):
    inspector = inspect(get_engine(get_settings()))
    assert {
        "content_items",
        "lessons",
        "sentence_autopsies",
        "vocabulary_entries",
        "writing_submissions",
        "mistakes",
        "review_items",
        "exports",
    }.issubset(set(inspector.get_table_names()))
