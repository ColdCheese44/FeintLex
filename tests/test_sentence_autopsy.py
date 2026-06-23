from __future__ import annotations

from feintlex.services.sentence_autopsy import autopsy_sentence, persist_autopsy


def test_sentence_autopsy_returns_signature_shape():
    result = autopsy_sentence("El equipo analiza el partido porque necesita mejorar.")

    assert result["original"] == "El equipo analiza el partido porque necesita mejorar."
    assert result["literal_translation"]
    assert result["natural_translation"]
    assert "analiza" in result["verbs"]
    assert "equipo" not in result["verbs"]
    assert "partido" not in result["verbs"]
    assert {"term": "porque", "role": "cause"} in result["connectors"]
    assert result["vocabulary"]
    assert result["practice_prompt"].startswith("Write 3")


def test_sentence_autopsy_can_be_persisted(isolated_session):
    autopsy = persist_autopsy(isolated_session, "La defensa presiona cuando el rival avanza.")
    assert autopsy.id is not None
    assert autopsy.original.startswith("La defensa")
