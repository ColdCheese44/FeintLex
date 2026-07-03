from __future__ import annotations

from fastapi.testclient import TestClient

from feintlex.app import create_app
from feintlex.db import clear_engine_cache
from feintlex.services.conjugator import conjugate, find_infinitive
from feintlex.services.lexicon import literal_gloss, lookup, reverse_lookup
from feintlex.services.tutor_chat import detect_intent, respond_chat
from feintlex.services.writing_coach import analyze_writing


# --- Lexicon ----------------------------------------------------------------

def test_lexicon_lookup_handles_accents_and_phrases():
    assert lookup("amenaza") == "threat"
    assert lookup("Amenaza") == "threat"
    assert lookup("por favor") == "please"
    assert lookup("palabrainventada") is None


def test_library_scale_and_categories():
    from feintlex.services.lexicon import CATEGORIES, LEXICON, PHRASES, library_stats

    assert len(LEXICON) >= 1000, "the library should hold 1000+ curated terms"
    assert len(PHRASES) >= 120, "the library should hold 120+ phrases"
    assert len(CATEGORIES) >= 15
    stats = library_stats()
    assert stats["derived_forms"] >= 3000, "derived conjugations should cover thousands of forms"


def test_derived_verb_form_lookup():
    assert "to analyze" in lookup("analizaron")
    assert "preterite" in lookup("analizaron")
    assert "to speak" in lookup("hablaremos")
    assert "future" in lookup("hablaremos")


def test_stem_changing_verbs_conjugate_correctly():
    from feintlex.services.conjugator import conjugate

    cerrar = conjugate("cerrar")
    forms = [row["form"] for row in cerrar["tenses"]["present"]]
    assert forms[0] == "cierro"
    assert forms[3] == "cerramos", "nosotros keeps the unstressed stem"
    # Stem-changed forms resolve through the derived-forms hover chain.
    assert "to close" in lookup("cierra")
    assert "to cost" in lookup("cuesta")
    assert "to ask for" in lookup("pide")


def test_contractions_and_domain_words_gloss():
    assert "de+el" in lookup("del")
    assert "a+el" in lookup("al")
    assert lookup("analista") == "analyst"
    assert lookup("actividad") == "activity"


def test_sample_texts_have_full_gloss_coverage():
    from feintlex.services.lexicon import coverage

    text = (
        "El equipo de seguridad detecta actividad sospechosa en la red porque un usuario "
        "abre un correo con un archivo peligroso. El analista revisa las alertas y escribe "
        "un informe claro. Despues, el equipo cierra el acceso y protege el sistema."
    )
    assert coverage(text) == 1.0, "bundled sample texts must gloss end to end"


def test_fallback_chain_prefers_curated_over_derived():
    # 'amenazas' is both a plural noun and a verb form; the noun wins.
    assert lookup("amenazas") == "threat"
    # Feminine adjective falls back to the masculine entry.
    assert lookup("nueva") == "new"
    assert lookup("cansadas") == "tired"
    # Plural of a curated noun.
    assert lookup("ciudades") == "city"


def test_lexicon_reverse_lookup_finds_spanish():
    matches = reverse_lookup("threat")
    assert any(item["es"] == "amenaza" for item in matches)


def test_literal_gloss_marks_unknown_words():
    gloss = literal_gloss("El equipo zzzxx")
    assert "the" in gloss
    assert "[zzzxx]" in gloss


# --- Conjugator ---------------------------------------------------------------

def test_conjugate_regular_ar_verb():
    result = conjugate("hablar")
    present = {row["person"]: row["form"] for row in result["tenses"]["present"]}
    assert present["yo"] == "hablo"
    assert present["nosotros"] == "hablamos"
    preterite = {row["person"]: row["form"] for row in result["tenses"]["preterite"]}
    assert preterite["él/ella/usted"] == "habló"


def test_conjugate_irregular_verbs():
    ser = conjugate("ser")
    assert ser["is_irregular"]
    assert ser["tenses"]["present"][0]["form"] == "soy"
    assert ser["tenses"]["imperfect"][0]["form"] == "era"

    tener = conjugate("tener")
    assert tener["tenses"]["present"][0]["form"] == "tengo"
    assert tener["tenses"]["future"][0]["form"] == "tendré"

    ir = conjugate("ir")
    assert ir["tenses"]["present"][0]["form"] == "voy"
    assert ir["tenses"]["future"][0]["form"] == "iré"


def test_conjugate_rejects_non_infinitives():
    assert conjugate("casa") is None


def test_find_infinitive_prefers_known_verbs():
    assert find_infinitive("please conjugate tener for me") == "tener"
    assert find_infinitive("conjugate analizar") == "analizar"


# --- Writing coach -------------------------------------------------------------

def test_writing_analysis_detects_and_fixes_issues():
    analysis = analyze_writing("donde esta el problema? la sistema falla.")
    types = {issue["type"] for issue in analysis["issues"]}
    assert "punctuation" in types
    assert "capitalization" in types
    assert "gender_agreement" in types
    assert "el sistema" in analysis["corrected_version"].lower()
    assert "dónde" in analysis["corrected_version"].lower()
    assert analysis["corrected_version"].count("¿") == 1


def test_writing_analysis_praises_clean_text():
    analysis = analyze_writing("El equipo gana porque practica cada semana. Los jugadores corren mucho. El entrenador explica el plan.")
    assert not analysis["issues"]
    assert any("connector" in item.lower() for item in analysis["strengths"])


# --- Chat intents ---------------------------------------------------------------

def test_detect_intent_routing():
    assert detect_intent("hola") == "greeting"
    assert detect_intent("conjugate tener") == "conjugate"
    assert detect_intent("what does amenaza mean?") == "meaning"
    assert detect_intent("how do you say threat?") == "say"
    assert detect_intent("ser vs estar") == "grammar"
    assert detect_intent("quiz me") == "quiz"
    assert detect_intent("autopsy: El equipo gana.") == "autopsy"
    assert detect_intent("correct: yo tengo hambre") == "writing"
    assert detect_intent("what should I study?") == "study_plan"
    assert detect_intent("El sistema detecta la amenaza") == "explain"


def test_chat_conjugation_flow(isolated_session):
    result = respond_chat(isolated_session, "conjugate tener")
    assert result["intent"] == "conjugate"
    assert result["provider"] == "offline_rule_based"
    card = result["cards"][0]
    assert card["type"] == "conjugation_table"
    assert card["verb"] == "tener"


def test_chat_meaning_flow(isolated_session):
    result = respond_chat(isolated_session, "what does amenaza mean?")
    assert result["intent"] == "meaning"
    assert "threat" in result["reply"]


def test_chat_persists_history(isolated_session):
    respond_chat(isolated_session, "hola", session_key="t1")
    respond_chat(isolated_session, "conjugate ser", session_key="t1")

    from feintlex.services.tutor_chat import clear_history, get_history

    history = get_history(isolated_session, session_key="t1")
    assert len(history) == 4  # 2 user + 2 tutor
    assert history[0].role == "user"
    assert history[1].role == "tutor"

    deleted = clear_history(isolated_session, session_key="t1")
    assert deleted == 4
    assert get_history(isolated_session, session_key="t1") == []


def test_chat_quiz_uses_weak_mastery_terms(isolated_session):
    from feintlex.services.tutor_chat import sync_mastery

    sync_mastery(
        isolated_session,
        [
            {"term_id": "contact:0", "deck_id": "contact", "term": "hola", "translation": "hello", "level": 1},
            {"term_id": "contact:1", "deck_id": "contact", "term": "gracias", "translation": "thank you", "level": 0},
            {"term_id": "verbs:0", "deck_id": "verbs", "term": "ser", "translation": "to be, identity", "level": 2},
        ],
    )
    result = respond_chat(isolated_session, "quiz me")
    assert result["intent"] == "quiz"
    assert result["cards"], "quiz should build questions from weak mastery terms"
    questions = result["cards"][0]["questions"]
    assert questions
    for question in questions:
        assert question["answer"] in question["options"]


# --- Routes ------------------------------------------------------------------

def _client(tmp_path, monkeypatch, name):
    monkeypatch.setenv("FEINTLEX_DB_PATH", str(tmp_path / f"{name}.db"))
    monkeypatch.setenv("FEINTLEX_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("FEINTLEX_ENV", "test")
    clear_engine_cache()
    return TestClient(create_app())


def test_lexicon_route_serves_hover_dictionary(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch, "lexicon-route") as client:
        payload = client.get("/lexicon").json()
        assert payload["terms"]["amenaza"] == "threat"
        assert payload["phrases"]["por favor"] == "please"
        # Keys must be normalized (lowercase, accent-free) for frontend lookup.
        assert all(key == key.lower() for key in payload["terms"])
        # Library payload: derived forms, categories, and stats.
        assert "to analyze" in payload["derived"]["analizaron"]
        assert "verbs" in payload["categories"]
        assert "amenaza" in payload["categories"]["technology_cyber"]
        assert payload["stats"]["terms"] >= 1000
    clear_engine_cache()


def test_chat_route_round_trip(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch, "chat-route") as client:
        response = client.post("/tutor/chat", json={"message": "conjugate hablar"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["intent"] == "conjugate"
        assert payload["cards"][0]["verb"] == "hablar"

        history = client.get("/tutor/chat/history").json()
        assert len(history) == 2

        cleared = client.delete("/tutor/chat/history").json()
        assert cleared["deleted"] == 2
    clear_engine_cache()


def test_chat_route_rejects_missing_lesson(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch, "chat-missing") as client:
        response = client.post("/tutor/chat", json={"message": "hola", "lesson_id": 999})
        assert response.status_code == 404
    clear_engine_cache()


def test_mastery_sync_route(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch, "mastery") as client:
        items = [
            {"term_id": "contact:0", "deck_id": "contact", "term": "hola", "translation": "hello", "level": 3},
            {"term_id": "contact:1", "deck_id": "contact", "term": "gracias", "translation": "thank you", "level": 5},
        ]
        put_response = client.put("/tutor/mastery", json={"items": items})
        assert put_response.status_code == 200
        rows = {row["term_id"]: row for row in put_response.json()}
        assert rows["contact:0"]["level"] == 3
        assert rows["contact:1"]["level"] == 5

        # Last-write-wins on level so dashboard resets propagate.
        client.put("/tutor/mastery", json={"items": [{"term_id": "contact:1", "level": 0}]})
        rows = {row["term_id"]: row for row in client.get("/tutor/mastery").json()}
        assert rows["contact:1"]["level"] == 0
        assert rows["contact:1"]["term"] == "gracias"
    clear_engine_cache()
