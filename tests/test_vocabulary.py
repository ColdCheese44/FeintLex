from __future__ import annotations

from feintlex.services.vocabulary import extract_vocabulary, normalize_term


def test_vocabulary_extraction_removes_stopwords_and_counts_repeats():
    vocab = extract_vocabulary("El analista analiza alertas y analiza registros del sistema.")
    by_term = {item["normalized_term"]: item for item in vocab}

    assert "el" not in by_term
    assert by_term["analiza"]["frequency"] == 2
    assert by_term["alertas"]["frequency"] == 1


def test_normalize_term_removes_accents_for_matching():
    assert normalize_term("investigación") == "investigacion"
