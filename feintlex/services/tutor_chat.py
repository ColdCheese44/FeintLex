from __future__ import annotations

"""FeintLex AI tutor chat engine.

A conversational Spanish tutor that runs fully offline:
- intent detection (conjugation, word lookups, quizzes, autopsy,
  writing review, grammar guides, study planning, conversation)
- context pulled from the local database (active lesson, weak terms,
  due mistakes) so coaching targets real gaps
- persistent chat history per session key
- optional local-LLM enrichment (Ollama) with strict rule-based fallback

No network calls unless FEINTLEX_AI_PROVIDER=ollama is explicitly set.
"""

import logging
import random
import re

from sqlmodel import Session, select

from feintlex.config import Settings, get_settings
from feintlex.models import Lesson, Mistake, TutorChatMessage, TutorMastery, utc_now
from feintlex.services.ai_providers import generate_ai_reply, provider_enabled
from feintlex.services.conjugator import TENSE_LABELS, conjugate, find_infinitive
from feintlex.services.lexicon import literal_gloss, lookup, reverse_lookup
from feintlex.services.sentence_autopsy import autopsy_sentence
from feintlex.services.vocabulary import extract_vocabulary, tokenize
from feintlex.services.writing_coach import analyze_writing


LOGGER = logging.getLogger("feintlex.tutor_chat")

OFFLINE_PROVIDER = "offline_rule_based"

GRAMMAR_GUIDES: dict[str, dict[str, object]] = {
    "ser_estar": {
        "keywords": ["ser vs estar", "ser or estar", "ser y estar", "when to use ser", "when to use estar", "difference between ser and estar"],
        "title": "Ser vs Estar",
        "points": [
            "SER = identity, origin, profession, time, permanent traits. Think DOCTOR: Description, Occupation, Characteristic, Time, Origin, Relationship.",
            "ESTAR = location, feelings, temporary states, ongoing actions. Think PLACE: Position, Location, Action, Condition, Emotion.",
            "Same adjective, different meaning: 'es aburrido' = he is boring, 'está aburrido' = he is bored.",
        ],
        "examples": [
            {"es": "Soy analista de seguridad.", "en": "I am a security analyst. (identity -> ser)"},
            {"es": "Estoy cansado hoy.", "en": "I am tired today. (temporary state -> estar)"},
            {"es": "El servidor está en Madrid.", "en": "The server is in Madrid. (location -> estar)"},
        ],
        "practice": "Write 3 sentences about yourself: one with ser, one with estar for feeling, one with estar for location.",
    },
    "por_para": {
        "keywords": ["por vs para", "por or para", "por y para", "when to use por", "when to use para", "difference between por and para"],
        "title": "Por vs Para",
        "points": [
            "PARA = destination, purpose, deadline, recipient. Points forward at a goal.",
            "POR = cause, exchange, duration, movement through, 'per'. Explains the reason behind.",
            "Test: 'in order to' fits -> para. 'because of' fits -> por.",
        ],
        "examples": [
            {"es": "Estudio para entender las noticias.", "en": "I study in order to understand the news. (purpose -> para)"},
            {"es": "Gracias por tu ayuda.", "en": "Thanks for (because of) your help. (cause -> por)"},
            {"es": "Caminamos por el centro.", "en": "We walked through downtown. (movement through -> por)"},
        ],
        "practice": "Write one sentence with para (goal) and one with por (reason) about your work.",
    },
    "past_tenses": {
        "keywords": ["preterite vs imperfect", "preterite or imperfect", "past tense", "pasado", "preterito", "imperfecto", "imperfect"],
        "title": "Preterite vs Imperfect",
        "points": [
            "PRETERITE = completed, one-time events with clear boundaries. The plot of the story.",
            "IMPERFECT = background, habits, descriptions, ongoing past. The scenery of the story.",
            "Signal words: ayer/una vez/de repente -> preterite. siempre/cada dia/mientras -> imperfect.",
        ],
        "examples": [
            {"es": "El equipo ganó el partido ayer.", "en": "The team won the match yesterday. (completed -> preterite)"},
            {"es": "Cuando era niño, jugaba fútbol.", "en": "When I was a kid, I used to play soccer. (habit -> imperfect)"},
            {"es": "Analizaba los datos cuando llegó la alerta.", "en": "I was analyzing the data when the alert arrived. (both)"},
        ],
        "practice": "Describe yesterday in 3 sentences: one completed action, one background description, one interrupted action.",
    },
    "gender_articles": {
        "keywords": ["gender", "el la", "articles", "masculine", "feminine", "genero"],
        "title": "Gender and Articles",
        "points": [
            "-o endings are usually masculine (el), -a endings usually feminine (la).",
            "Key exceptions: el día, el mapa, el problema, el sistema, el idioma / la mano, la foto, la radio.",
            "Feminine nouns starting with stressed a- take el in singular: el agua, el alma — but stay feminine: el agua fría.",
        ],
        "examples": [
            {"es": "El sistema detecta la amenaza.", "en": "The system detects the threat."},
            {"es": "El agua está fría.", "en": "The water is cold. (el + feminine adjective)"},
        ],
        "practice": "Pick 5 nouns from your active lesson and write them with the correct article.",
    },
    "questions": {
        "keywords": ["ask questions", "question words", "interrogative", "how to ask", "hacer preguntas"],
        "title": "Building Questions",
        "points": [
            "Wrap questions in ¿...? and put the accented question word first: qué, cómo, dónde, cuándo, quién, cuánto, cuál, por qué.",
            "Word order flips: statement 'El equipo juega hoy' -> question '¿Juega el equipo hoy?'",
            "Accents matter: 'que' (that) vs 'qué' (what), 'como' (like) vs 'cómo' (how).",
        ],
        "examples": [
            {"es": "¿Dónde está la evidencia?", "en": "Where is the evidence?"},
            {"es": "¿Por qué falló el sistema?", "en": "Why did the system fail?"},
        ],
        "practice": "Write 3 investigation questions using dónde, por qué, and quién.",
    },
    "negation": {
        "keywords": ["negation", "negative", "how to say no", "nunca", "nadie", "double negative"],
        "title": "Negation",
        "points": [
            "Put 'no' directly before the verb: No entiendo. No hay alertas.",
            "Double negatives are correct Spanish: 'No veo nada' = I don't see anything.",
            "Common negatives: nada (nothing), nadie (nobody), nunca (never), ninguno (none), tampoco (neither).",
        ],
        "examples": [
            {"es": "El analista no encontró nada sospechoso.", "en": "The analyst found nothing suspicious."},
            {"es": "Nunca abras ese archivo.", "en": "Never open that file."},
        ],
        "practice": "Rewrite 3 affirmative sentences from your lesson as negatives.",
    },
    "connectors": {
        "keywords": ["connectors", "conectores", "linking words", "transition words"],
        "title": "Connectors — the codebreaker's toolkit",
        "points": [
            "Cause: porque (because), por eso (that's why), ya que (since).",
            "Contrast: pero (but), aunque (although), sin embargo (however).",
            "Sequence: primero, después, luego, entonces, finalmente.",
            "Connectors are the highest-value signal in real texts: they reveal the logic of the sentence.",
        ],
        "examples": [
            {"es": "El ataque falló porque el equipo detectó la actividad.", "en": "The attack failed because the team detected the activity."},
            {"es": "Sin embargo, el riesgo continúa.", "en": "However, the risk continues."},
        ],
        "practice": "Write one sentence each with porque, aunque, and después about the same event.",
    },
}

_MEANING_PATTERNS = [
    re.compile(r"(?:what\s+does|what's|whats)\s+[\"']?(?P<term>[\w\sáéíóúüñÁÉÍÓÚÜÑ]+?)[\"']?\s+mean", re.IGNORECASE),
    re.compile(r"(?:que|qué)\s+significa\s+[\"']?(?P<term>[\w\sáéíóúüñÁÉÍÓÚÜÑ]+?)[\"']?\s*[?.!]*$", re.IGNORECASE),
    re.compile(r"meaning\s+of\s+[\"']?(?P<term>[\w\sáéíóúüñÁÉÍÓÚÜÑ]+?)[\"']?\s*[?.!]*$", re.IGNORECASE),
    re.compile(r"translate\s+[\"']?(?P<term>[\w\sáéíóúüñÁÉÍÓÚÜÑ]+?)[\"']?\s*[?.!]*$", re.IGNORECASE),
    re.compile(r"define\s+[\"']?(?P<term>[\w\sáéíóúüñÁÉÍÓÚÜÑ]+?)[\"']?\s*[?.!]*$", re.IGNORECASE),
]

_SAY_PATTERNS = [
    re.compile(r"how\s+do\s+(?:i|you)\s+say\s+[\"']?(?P<term>[\w\s]+?)[\"']?(?:\s+in\s+spanish)?\s*[?.!]*$", re.IGNORECASE),
    re.compile(r"(?:como|cómo)\s+se\s+dice\s+[\"']?(?P<term>[\w\s]+?)[\"']?\s*[?.!]*$", re.IGNORECASE),
    re.compile(r"spanish\s+(?:word\s+)?for\s+[\"']?(?P<term>[\w\s]+?)[\"']?\s*[?.!]*$", re.IGNORECASE),
]

_GREETINGS = {"hola", "hello", "hi", "hey", "buenos dias", "buenas", "help", "ayuda", "start", "?"}


def detect_intent(message: str) -> str:
    lowered = " ".join(message.lower().split())
    if not lowered or lowered in _GREETINGS or lowered.rstrip("!.") in _GREETINGS:
        return "greeting"
    for pattern in _SAY_PATTERNS:
        if pattern.search(lowered):
            return "say"
    for pattern in _MEANING_PATTERNS:
        if pattern.search(lowered):
            return "meaning"
    if re.search(r"\bconjugat|\bconjuga\b|\bconjugue\b", lowered):
        return "conjugate"
    for guide in GRAMMAR_GUIDES.values():
        if any(keyword in lowered for keyword in guide["keywords"]):
            return "grammar"
    if any(word in lowered for word in ("quiz", "test me", "drill", "practice", "examen")):
        return "quiz"
    if any(word in lowered for word in ("autopsy", "break down", "breakdown", "analyze this", "analiza esta")):
        return "autopsy"
    if any(word in lowered for word in ("correct", "check my writing", "revisa", "review my", "corrige", "fix my")):
        return "writing"
    if any(word in lowered for word in ("weak", "study plan", "what should i study", "progress", "mastery")):
        return "study_plan"
    return "explain"


def _extract_target_text(message: str) -> str:
    """Pull the payload out of messages like 'correct: <text>' or quoted text."""
    if ":" in message:
        _, _, tail = message.partition(":")
        if tail.strip():
            return tail.strip()
    quoted = re.search(r"[\"'“”](.+?)[\"'“”]", message)
    if quoted:
        return quoted.group(1).strip()
    return message.strip()


def _weak_terms(session: Session, *, limit: int = 6) -> list[TutorMastery]:
    statement = (
        select(TutorMastery)
        .where(TutorMastery.level <= 2)
        .order_by(TutorMastery.level, TutorMastery.updated_at)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def _due_mistakes_count(session: Session) -> int:
    statement = select(Mistake).where(Mistake.review_due_at <= utc_now()).where(Mistake.status != "mastered")
    return len(list(session.exec(statement).all()))


def _resolve_lesson(session: Session, lesson_id: int | None) -> Lesson | None:
    if lesson_id is not None:
        return session.get(Lesson, lesson_id)
    statement = select(Lesson).order_by(Lesson.created_at.desc()).limit(1)
    return session.exec(statement).first()


def _context_summary(lesson: Lesson | None, weak: list[TutorMastery], due_mistakes: int) -> str:
    parts = []
    if lesson:
        parts.append(f"Active lesson: {lesson.title}")
    if weak:
        terms = ", ".join(item.term for item in weak[:4] if item.term)
        if terms:
            parts.append(f"Weak signals: {terms}")
    if due_mistakes:
        parts.append(f"{due_mistakes} mistake(s) due for review")
    return ". ".join(parts) if parts else "No lesson, mastery, or mistake data yet — import a text or run some drills."


# --- Intent handlers -------------------------------------------------------

def _handle_greeting(context_line: str) -> tuple[str, list[dict[str, object]]]:
    reply = (
        "FeintLex tutor online. I work fully offline and I know your training data. "
        f"{context_line} "
        "I can: conjugate any verb ('conjugate tener'), define words ('what does amenaza mean'), "
        "translate back ('how do you say threat'), explain grammar ('ser vs estar'), "
        "quiz your weakest terms ('quiz me'), break down sentences ('autopsy: <frase>'), "
        "and correct your writing ('correct: <texto>')."
    )
    return reply, []


def _handle_conjugate(message: str) -> tuple[str, list[dict[str, object]]]:
    verb = find_infinitive(message)
    if not verb:
        return (
            "Give me an infinitive to conjugate, like 'conjugate tener' or 'conjuga analizar'. "
            "I cover present, preterite, imperfect, future, and conditional.",
            [],
        )
    table = conjugate(verb)
    if not table:
        return (f"I could not conjugate '{verb}'. Try a standard infinitive ending in -ar, -er, or -ir.", [])
    translation = f" ({table['translation']})" if table["translation"] else ""
    irregular_note = " It has irregular forms — worth drilling." if table["is_irregular"] else " It follows regular patterns."
    reply = f"Conjugation table for {verb}{translation}.{irregular_note} Say one row aloud, then write one sentence per tense."
    return reply, [{"type": "conjugation_table", **table}]


def _handle_meaning(message: str) -> tuple[str, list[dict[str, object]]]:
    term = None
    for pattern in _MEANING_PATTERNS:
        match = pattern.search(message)
        if match:
            term = match.group("term").strip()
            break
    if not term:
        term = _extract_target_text(message)
    gloss = lookup(term)
    if gloss:
        card = {
            "type": "term_lookup",
            "direction": "es_to_en",
            "term": term.lower(),
            "translation": gloss,
            "next_step": f"Use '{term.lower()}' in one new Spanish sentence and run autopsy on it.",
        }
        return f"'{term.lower()}' means: {gloss}.", [card]
    # Unknown word: still be useful with structure analysis.
    guess = []
    if term.strip().lower().endswith(("ar", "er", "ir")):
        guess.append("It looks like a verb infinitive — try 'conjugate " + term.strip().lower() + "'.")
    if term.strip().lower().endswith("mente"):
        guess.append("The -mente ending usually marks an adverb (like English -ly).")
    if term.strip().lower().endswith(("cion", "ción", "sión", "sion")):
        guess.append("The -ción/-sión ending usually maps to English -tion/-sion and is feminine (la).")
    hint = " ".join(guess) if guess else "Add it to a lesson import so it enters your vocabulary pipeline."
    return (
        f"'{term}' is not in my offline lexicon yet. {hint}",
        [{"type": "term_lookup", "direction": "es_to_en", "term": term, "translation": None, "next_step": hint}],
    )


def _handle_say(message: str) -> tuple[str, list[dict[str, object]]]:
    term = None
    for pattern in _SAY_PATTERNS:
        match = pattern.search(message)
        if match:
            term = match.group("term").strip()
            break
    if not term:
        return ("Tell me the English word, like 'how do you say threat'.", [])
    matches = reverse_lookup(term)
    if matches:
        best = matches[0]
        reply = f"'{term}' in Spanish: {best['es']}" + (
            f". Also related: {', '.join(m['es'] for m in matches[1:3])}." if len(matches) > 1 else "."
        )
        return reply, [
            {
                "type": "term_lookup",
                "direction": "en_to_es",
                "term": term,
                "matches": matches,
                "next_step": f"Say '{best['es']}' aloud, then build a sentence around it.",
            }
        ]
    return (
        f"I do not have '{term}' in the offline lexicon. Try a simpler synonym, or import a text that uses it.",
        [],
    )


def _handle_grammar(message: str) -> tuple[str, list[dict[str, object]]]:
    lowered = message.lower()
    for guide in GRAMMAR_GUIDES.values():
        if any(keyword in lowered for keyword in guide["keywords"]):
            card = {
                "type": "grammar_guide",
                "title": guide["title"],
                "points": guide["points"],
                "examples": guide["examples"],
                "practice": guide["practice"],
            }
            return f"{guide['title']} — decoded. Read the pattern, check the examples, then run the practice task.", [card]
    return _handle_greeting("")


def _handle_quiz(
    session: Session,
    lesson: Lesson | None,
    weak: list[TutorMastery],
) -> tuple[str, list[dict[str, object]]]:
    pool: list[dict[str, str]] = []
    for item in weak:
        if item.term and item.translation:
            pool.append({"es": item.term, "en": item.translation, "source": "weak deck term"})
    if lesson:
        for vocab in (lesson.key_vocabulary or [])[:8]:
            term = str(vocab.get("term", "")) if isinstance(vocab, dict) else str(vocab)
            gloss = lookup(term)
            if term and gloss:
                pool.append({"es": term, "en": gloss, "source": f"lesson: {lesson.title}"})

    # Deduplicate on the Spanish side.
    seen: set[str] = set()
    pool = [item for item in pool if not (item["es"] in seen or seen.add(item["es"]))]

    if len(pool) < 2:
        return (
            "Not enough tracked vocabulary to build a targeted quiz yet. "
            "Run some flashcard drills or generate a lesson first, then ask me again.",
            [],
        )

    random.shuffle(pool)
    questions = []
    for target in pool[:4]:
        distractors = [item["en"] for item in pool if item["en"] != target["en"]][:3]
        if len(distractors) < 2:
            continue
        options = [target["en"], *distractors]
        random.shuffle(options)
        questions.append(
            {
                "prompt": target["es"],
                "direction": "es_to_en",
                "options": options,
                "answer": target["en"],
                "source": target["source"],
            }
        )
    if not questions:
        return ("Quiz pool came up empty — drill a few flashcards first.", [])
    reply = (
        f"Targeted drill: {len(questions)} question(s) weighted toward your weakest signals. "
        "Answer from memory before you click."
    )
    return reply, [{"type": "quiz", "questions": questions}]


def _handle_autopsy(message: str) -> tuple[str, list[dict[str, object]]]:
    sentence = _extract_target_text(message)
    # Strip command words when the user typed 'autopsy este texto...'.
    sentence = re.sub(r"^(autopsy|break\s*down|analyze\s*this|analiza\s*esta?)\s*", "", sentence, flags=re.IGNORECASE).strip()
    if not sentence or len(tokenize(sentence)) < 2:
        return ("Give me a full Spanish sentence, like 'autopsy: El equipo detecta la amenaza.'", [])
    result = autopsy_sentence(sentence)
    reply = (
        "Sentence autopsy complete. Pattern isolated — check the verbs and connectors, "
        "then write three variants using the same structure."
    )
    return reply, [{"type": "autopsy", **result}]


def _handle_writing(session: Session, message: str, lesson: Lesson | None) -> tuple[str, list[dict[str, object]]]:
    text = _extract_target_text(message)
    text = re.sub(r"^(correct|check\s+my\s+writing|revisa|corrige|review|fix\s+my)\s*", "", text, flags=re.IGNORECASE).strip()
    if not text or len(tokenize(text)) < 2:
        return ("Paste the Spanish you want reviewed, like 'correct: Yo tengo veinte anos.'", [])
    analysis = analyze_writing(text)
    issue_count = len(analysis["issues"])
    if issue_count:
        reply = f"Found {issue_count} correction(s). Compare line by line, then rewrite once from memory."
    else:
        reply = "No high-confidence issues found by the offline scan. Read it aloud and verify verb endings."
    card = {
        "type": "writing_feedback",
        "submitted_text": analysis["submitted_text"],
        "corrected_version": analysis["corrected_version"],
        "issues": analysis["issues"],
        "strengths": analysis["strengths"],
        "grammar_notes": analysis["grammar_notes"],
        "rewrite_prompt": analysis["rewrite_prompt"],
    }
    return reply, [card]


def _handle_study_plan(
    lesson: Lesson | None,
    weak: list[TutorMastery],
    due_mistakes: int,
) -> tuple[str, list[dict[str, object]]]:
    steps: list[str] = []
    if weak:
        terms = ", ".join(item.term for item in weak[:5] if item.term)
        steps.append(f"Drill these weak signals first: {terms}.")
    if due_mistakes:
        steps.append(f"Clear the {due_mistakes} mistake(s) due for review in the Review panel.")
    if lesson:
        steps.append(f"Run sentence autopsy on one candidate from '{lesson.title}', then answer its writing prompt.")
    if not steps:
        steps.append("Import a Spanish text (news, subtitles, match report) to generate your first lesson.")
        steps.append("Then run 10 flashcard drills so I can map your weak signals.")
    steps.append("Finish with 5 written sentences using one new connector.")
    card = {
        "type": "study_plan",
        "steps": steps,
        "weak_terms": [
            {"term": item.term, "translation": item.translation, "level": item.level}
            for item in weak
            if item.term
        ],
        "due_mistakes": due_mistakes,
    }
    return "Here is today's signal plan — ordered by intelligence value.", [card]


def _handle_explain(message: str, lesson: Lesson | None, context_line: str) -> tuple[str, list[dict[str, object]]]:
    text = _extract_target_text(message)
    vocab = extract_vocabulary(text, limit=6)
    gloss = literal_gloss(text) if len(tokenize(text)) > 1 else None
    focus_bits = []
    if gloss:
        focus_bits.append(f"Literal gloss: {gloss}")
    reply = (
        "Treat this like codebreaking: isolate the useful phrase, map the grammar, then build a reusable pattern. "
        + (f"{focus_bits[0]}. " if focus_bits else "")
        + "Ask me to 'autopsy' it for the full breakdown, or 'quiz me' to lock it in."
    )
    card = {
        "type": "explanation",
        "focus": text,
        "literal_gloss": gloss,
        "vocabulary": vocab,
        "lesson_context": context_line,
        "next_step": "Say it aloud, write one variation, then run sentence autopsy on the variation.",
    }
    return reply, [card]


# --- Public API -------------------------------------------------------------

def _suggestions_for(intent: str) -> list[str]:
    base = {
        "greeting": ["Conjugate tener", "Ser vs estar", "Quiz me", "What should I study?"],
        "conjugate": ["Quiz me", "Conjugate ser", "Preterite vs imperfect", "Autopsy: Voy al trabajo porque tengo tiempo."],
        "meaning": ["Quiz me", "Conjugate this verb", "How do you say threat?", "Break down a sentence"],
        "say": ["What does amenaza mean?", "Quiz me", "Connectors", "Give me a study plan"],
        "grammar": ["Quiz me", "Conjugate estar", "Correct: yo estar cansado", "What should I study?"],
        "quiz": ["Quiz me again", "What should I study?", "Ser vs estar", "Conjugate poder"],
        "autopsy": ["Explain the connectors", "Quiz me", "Correct: <your rewrite>", "Conjugate the main verb"],
        "writing": ["Quiz me", "Preterite vs imperfect", "Autopsy my corrected sentence", "What should I study?"],
        "study_plan": ["Quiz me", "Ser vs estar", "Conjugate querer", "Break down a sentence"],
        "explain": ["Autopsy this sentence", "Quiz me", "Conjugate the verb", "How do you say evidence?"],
    }
    return base.get(intent, base["greeting"])


def _save_message(
    session: Session,
    *,
    session_key: str,
    role: str,
    content: str,
    intent: str | None = None,
    cards: list[dict[str, object]] | None = None,
    provider: str = OFFLINE_PROVIDER,
) -> TutorChatMessage:
    record = TutorChatMessage(
        session_key=session_key,
        role=role,
        content=content,
        intent=intent,
        cards=cards or [],
        provider=provider,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_history(session: Session, *, session_key: str = "default", limit: int = 50) -> list[TutorChatMessage]:
    statement = (
        select(TutorChatMessage)
        .where(TutorChatMessage.session_key == session_key)
        .order_by(TutorChatMessage.created_at.desc(), TutorChatMessage.id.desc())
        .limit(limit)
    )
    rows = list(session.exec(statement).all())
    rows.reverse()
    return rows


def clear_history(session: Session, *, session_key: str = "default") -> int:
    rows = list(
        session.exec(select(TutorChatMessage).where(TutorChatMessage.session_key == session_key)).all()
    )
    for row in rows:
        session.delete(row)
    session.commit()
    return len(rows)


def _try_ai_enrichment(
    message: str,
    intent: str,
    context_line: str,
    history: list[TutorChatMessage],
    settings: Settings,
) -> tuple[str, str] | None:
    """Ask the optional local LLM for a better conversational reply."""
    if not provider_enabled(settings):
        return None
    recent = history[-6:]
    transcript = "\n".join(f"{row.role}: {row.content}" for row in recent)
    prompt = (
        f"Student context: {context_line}\n"
        f"Detected intent: {intent}\n"
        f"Recent conversation:\n{transcript}\n"
        f"Student says: {message}\n"
        "Reply as the tutor."
    )
    return generate_ai_reply(prompt, settings)


def respond_chat(
    session: Session,
    message: str,
    *,
    session_key: str = "default",
    lesson_id: int | None = None,
    settings: Settings | None = None,
) -> dict[str, object]:
    """Main chat entry point: detect intent, build reply + cards, persist history."""
    settings = settings or get_settings()
    cleaned = " ".join(message.split()) if message else ""
    intent = detect_intent(cleaned)

    lesson = _resolve_lesson(session, lesson_id)
    weak = _weak_terms(session)
    due_mistakes = _due_mistakes_count(session)
    context_line = _context_summary(lesson, weak, due_mistakes)

    history = get_history(session, session_key=session_key, limit=12)
    if cleaned:
        _save_message(session, session_key=session_key, role="user", content=cleaned, intent=intent)

    if intent == "greeting":
        reply, cards = _handle_greeting(context_line)
    elif intent == "conjugate":
        reply, cards = _handle_conjugate(cleaned)
    elif intent == "meaning":
        reply, cards = _handle_meaning(cleaned)
    elif intent == "say":
        reply, cards = _handle_say(cleaned)
    elif intent == "grammar":
        reply, cards = _handle_grammar(cleaned)
    elif intent == "quiz":
        reply, cards = _handle_quiz(session, lesson, weak)
    elif intent == "autopsy":
        reply, cards = _handle_autopsy(cleaned)
    elif intent == "writing":
        reply, cards = _handle_writing(session, cleaned, lesson)
    elif intent == "study_plan":
        reply, cards = _handle_study_plan(lesson, weak, due_mistakes)
    else:
        reply, cards = _handle_explain(cleaned, lesson, context_line)

    provider = OFFLINE_PROVIDER
    # Conversational intents benefit most from the optional local model;
    # structured tools (conjugation, quiz, autopsy) stay deterministic.
    if intent in {"explain", "greeting", "grammar"}:
        enriched = _try_ai_enrichment(cleaned, intent, context_line, history, settings)
        if enriched:
            reply, provider = enriched

    _save_message(
        session,
        session_key=session_key,
        role="tutor",
        content=reply,
        intent=intent,
        cards=cards,
        provider=provider,
    )

    LOGGER.info("tutor_chat", extra={"intent": intent, "provider": provider, "session_key": session_key})
    return {
        "reply": reply,
        "intent": intent,
        "cards": cards,
        "suggestions": _suggestions_for(intent),
        "context": context_line,
        "provider": provider,
        "session_key": session_key,
    }


# --- Mastery sync ------------------------------------------------------------

def sync_mastery(session: Session, items: list[dict[str, object]]) -> list[TutorMastery]:
    """Upsert mastery rows sent by the dashboard. Level merges take the max."""
    for item in items:
        term_id = str(item.get("term_id", "")).strip()
        if not term_id:
            continue
        row = session.exec(select(TutorMastery).where(TutorMastery.term_id == term_id)).first()
        level = max(0, min(5, int(item.get("level", 0))))
        seen = max(0, int(item.get("seen", 0)))
        correct = max(0, int(item.get("correct", 0)))
        if row is None:
            row = TutorMastery(
                term_id=term_id,
                deck_id=str(item.get("deck_id", "")),
                term=str(item.get("term", "")),
                translation=str(item.get("translation", "")),
                level=level,
                seen=seen,
                correct=correct,
            )
        else:
            row.level = max(row.level, level) if bool(item.get("merge", False)) else level
            row.seen = max(row.seen, seen)
            row.correct = max(row.correct, correct)
            if item.get("term"):
                row.term = str(item["term"])
            if item.get("translation"):
                row.translation = str(item["translation"])
            row.updated_at = utc_now()
        session.add(row)
    session.commit()
    return get_all_mastery(session)


def get_all_mastery(session: Session) -> list[TutorMastery]:
    return list(session.exec(select(TutorMastery).order_by(TutorMastery.term_id)).all())
