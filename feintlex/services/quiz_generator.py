from __future__ import annotations


def generate_quiz(
    *,
    title: str,
    sentence_candidates: list[str],
    key_vocabulary: list[dict[str, object]],
) -> dict[str, object]:
    first_sentence = sentence_candidates[0] if sentence_candidates else title
    vocab_terms = [str(item["term"]) for item in key_vocabulary[:4]]
    return {
        "multiple_choice": [
            {
                "question": "What is the main idea of this text?",
                "choices": [
                    "Identify the central event or argument.",
                    "Ignore the verbs and focus only on nouns.",
                    "Translate every word without context.",
                    "Assume the topic from the title only.",
                ],
                "answer": "Identify the central event or argument.",
            }
        ],
        "short_answer": [
            {
                "question": "Write a 1-2 sentence English summary of the Spanish content.",
                "answer_hint": "Mention who/what is involved and what changed or happened.",
            }
        ],
        "vocabulary_recall": [
            {"term": term, "prompt": f"Define '{term}' in context, then use it in a new sentence."}
            for term in vocab_terms
        ],
        "sentence_reconstruction": {
            "prompt": "Rebuild this sentence from memory, then compare word order and connectors.",
            "sentence": first_sentence,
        },
    }
