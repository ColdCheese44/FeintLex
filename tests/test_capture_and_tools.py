from __future__ import annotations

import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from feintlex.app import create_app
from feintlex.db import clear_engine_cache
from feintlex.models import TutorMastery
from feintlex.services.content_importer import clean_subtitles, import_content, looks_like_subtitles
from feintlex.services.mistake_bank import create_mistake
from feintlex.services.review_queue import build_review_queue
from feintlex.services.tutor_chat import capture_term


SRT_SAMPLE = """1
00:00:01,000 --> 00:00:03,500
<i>El equipo detecta la amenaza.</i>

2
00:00:04,000 --> 00:00:06,000
- ¿Donde esta la evidencia?
- No lo se.

3
00:00:06,500 --> 00:00:08,000
No lo se.
"""


# --- Capture -------------------------------------------------------------------

def test_capture_term_files_into_captured_deck(isolated_session):
    result = capture_term(isolated_session, term="Amenaza", translation="threat")
    assert result["term_id"] == "captured:amenaza"
    assert result["already_captured"] is False

    again = capture_term(isolated_session, term="amenaza")
    assert again["already_captured"] is True

    rows = isolated_session.exec(
        __import__("sqlmodel").select(TutorMastery).where(TutorMastery.deck_id == "captured")
    ).all()
    assert len(rows) == 1
    assert rows[0].term == "amenaza"


def test_capture_falls_back_to_lexicon_gloss(isolated_session):
    result = capture_term(isolated_session, term="evidencia")
    assert result["translation"] == "evidence"


def test_capture_rejects_unknown_word_without_translation(isolated_session):
    try:
        capture_term(isolated_session, term="zzzpalabrafalsa")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_captured_terms_enter_the_review_queue(isolated_session):
    capture_term(isolated_session, term="amenaza", translation="threat")
    queue = build_review_queue(isolated_session)
    prompts = [entry["prompt"] for entry in queue]
    assert any("amenaza" in prompt for prompt in prompts)


# --- Subtitle import -------------------------------------------------------------

def test_subtitle_detection_and_cleaning():
    assert looks_like_subtitles(SRT_SAMPLE)
    assert not looks_like_subtitles("El equipo gana el partido.")
    cleaned = clean_subtitles(SRT_SAMPLE)
    lines = cleaned.splitlines()
    assert lines[0] == "El equipo detecta la amenaza."
    assert "-->" not in cleaned
    assert "<i>" not in cleaned
    assert not any(line.isdigit() for line in lines)
    # Consecutive duplicate collapses.
    assert cleaned.count("No lo se.") == 1


def test_import_content_auto_cleans_srt(isolated_session):
    item = import_content(isolated_session, SRT_SAMPLE, source_type="pasted_text")
    assert item.source_type == "subtitle"
    assert "-->" not in item.text
    assert "El equipo detecta la amenaza." in item.text


# --- Interleaved queue -----------------------------------------------------------

def test_review_queue_interleaves_kinds(isolated_session):
    create_mistake(
        isolated_session,
        mistake_type="accent",
        original_input="donde",
        correction="dónde",
        explanation="Question words carry accents.",
    )
    create_mistake(
        isolated_session,
        mistake_type="gender_agreement",
        original_input="la sistema",
        correction="el sistema",
        explanation="Sistema is masculine.",
    )
    isolated_session.add(TutorMastery(term_id="a:0", term="hola", translation="hello", level=1))
    isolated_session.add(TutorMastery(term_id="a:1", term="gracias", translation="thank you", level=1))
    isolated_session.commit()

    queue = build_review_queue(isolated_session)
    kinds = [entry["kind"] for entry in queue]
    assert kinds[0] == "mistake"
    assert kinds[1] == "term", f"expected interleaving, got {kinds}"
    assert kinds[2] == "mistake"
    assert kinds[3] == "term"


# --- Anki export + backup + routes -----------------------------------------------

def test_anki_export_and_backup_routes(tmp_path, monkeypatch):
    monkeypatch.setenv("FEINTLEX_DB_PATH", str(tmp_path / "tools.db"))
    monkeypatch.setenv("FEINTLEX_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("FEINTLEX_ENV", "test")
    clear_engine_cache()

    with TestClient(create_app()) as client:
        # Empty database refuses politely.
        empty = client.post("/exports/anki")
        assert empty.status_code == 400

        client.post("/tutor/capture", json={"term": "amenaza", "translation": "threat"})
        client.post("/writing/submit", json={"text": "donde esta el problema?"})

        exported = client.post("/exports/anki")
        assert exported.status_code == 200
        payload = exported.json()
        assert payload["cards"] >= 2
        content = Path(payload["path"]).read_text(encoding="utf-8")
        assert "amenaza\tthreat" in content
        assert "Fix:" in content

        captured = client.get("/tutor/captured").json()
        assert captured[0]["term"] == "amenaza"

    from feintlex.config import get_settings
    from feintlex.services.backup import create_backup

    result = create_backup(settings=get_settings(), dest_dir=tmp_path / "backups")
    archive = Path(result["path"])
    assert archive.exists()
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        assert any(name.startswith("data/") for name in names)
        assert any(name.startswith("exports/") for name in names)
    clear_engine_cache()
