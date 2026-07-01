from __future__ import annotations

from dataclasses import dataclass

from feintlex.models import Lesson
from feintlex.services.sentence_autopsy import autopsy_sentence
from feintlex.services.vocabulary import extract_vocabulary


QUICK_ACTIONS = {
    "explain": "Explain the grammar and reusable pattern.",
    "quiz": "Generate a short comprehension and vocabulary drill.",
    "autopsy": "Break the sentence into verbs, connectors, vocabulary, and practice.",
    "writing": "Create a writing prompt and correction checklist.",
}


@dataclass(frozen=True)
class TutorContext:
    lesson: Lesson | None = None
    selected_term: str | None = None
    selected_deck: str | None = None


def infer_action(message: str, requested_action: str | None = None) -> str:
    if requested_action in QUICK_ACTIONS:
        return requested_action
    lowered = message.lower()
    if any(word in lowered for word in ("quiz", "test", "drill", "practice")):
        return "quiz"
    if any(word in lowered for word in ("autopsy", "break down", "sentence", "verbs", "connectors")):
        return "autopsy"
    if any(word in lowered for word in ("write", "writing", "correct", "rewrite")):
        return "writing"
    return "explain"


def _source_text(message: str, context: TutorContext) -> str:
    if message.strip():
        return message.strip()
    if context.lesson:
        return " ".join(context.lesson.sentence_breakdown_candidates[:2]) or context.lesson.spanish_summary
    if context.selected_term:
        return context.selected_term
    return "Necesito practicar espanol con frases claras."


def _lesson_brief(context: TutorContext) -> str:
    if not context.lesson:
        return "No active lesson is attached, so I am coaching from your prompt and the local field decks."
    return f"Active lesson: {context.lesson.title}. Focus summary: {context.lesson.english_summary}"


def _term_brief(context: TutorContext) -> str | None:
    if not context.selected_term:
        return None
    deck = f" from {context.selected_deck}" if context.selected_deck else ""
    return f"Selected term{deck}: {context.selected_term}"


def _quiz_cards(text: str, vocab: list[dict[str, object]]) -> list[dict[str, object]]:
    terms = [str(item["term"]) for item in vocab[:4]]
    cards: list[dict[str, object]] = [
        {
            "type": "short_answer",
            "prompt": "Summarize the Spanish in one plain English sentence.",
            "answer_hint": "Name the actor, action, and reason or result.",
        },
        {
            "type": "sentence_rebuild",
            "prompt": "Rebuild the most important Spanish sentence from memory.",
            "answer_hint": text,
        },
    ]
    if terms:
        cards.append(
            {
                "type": "vocabulary_recall",
                "prompt": "Define these terms in context, then write one new Spanish sentence.",
                "terms": terms,
            }
        )
    return cards


def generate_tutor_response(
    message: str,
    *,
    action: str | None = None,
    context: TutorContext | None = None,
) -> dict[str, object]:
    context = context or TutorContext()
    resolved_action = infer_action(message, action)
    text = _source_text(message, context)
    vocab = extract_vocabulary(text, limit=8)
    autopsy = autopsy_sentence(text) if resolved_action == "autopsy" else None
    term_brief = _term_brief(context)

    if resolved_action == "quiz":
        reply = (
            "Drill mode: answer from memory first, then check the hint. "
            "I am weighting this toward comprehension, vocabulary recall, and sentence reconstruction."
        )
        cards = _quiz_cards(text, vocab)
    elif resolved_action == "autopsy":
        reply = (
            "Sentence autopsy mode: isolate the action, connector, and reusable pattern. "
            "Use the practice prompt to create three variants."
        )
        cards = [autopsy] if autopsy else []
    elif resolved_action == "writing":
        reply = (
            "Writing coach mode: produce a short answer, mark your verbs, and use one connector. "
            "Then rewrite it once for clarity."
        )
        cards = [
            {
                "type": "writing_prompt",
                "prompt": f"Write 5 Spanish sentences responding to: {text}",
                "checklist": [
                    "Use one clear connector such as porque, pero, cuando, or aunque.",
                    "Mark every conjugated verb.",
                    "Rewrite one sentence with simpler word order.",
                ],
            }
        ]
    else:
        reply = (
            "Tutor mode: treat this like codebreaking. First identify the useful phrase, "
            "then map the grammar, then create a reusable sentence pattern."
        )
        cards = [
            {
                "type": "explanation",
                "focus": term_brief or text,
                "lesson_context": _lesson_brief(context),
                "vocabulary": vocab,
                "next_step": "Say it aloud, write one variation, then run sentence autopsy on the variation.",
            }
        ]

    suggestions = [
        "Explain the grammar pattern",
        "Quiz me on weak terms",
        "Break down this sentence",
        "Give me a writing prompt",
    ]

    return {
        "action": resolved_action,
        "reply": reply,
        "lesson_context": _lesson_brief(context),
        "selected_term": context.selected_term,
        "cards": cards,
        "suggestions": suggestions,
        "ai_provider": "offline_rule_based",
    }
