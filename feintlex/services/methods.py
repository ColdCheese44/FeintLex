from __future__ import annotations

"""Audio-lingual training sessions inspired by classic methods.

Echo Sessions (Pimsleur-style):
- graduated interval recall INSIDE the session: each line is introduced,
  then recalled at expanding gaps (+1, +3, +7, +14 prompts)
- anticipation: the player shows English first and pauses before the
  reveal so you produce the Spanish from memory
- backward buildup: long phrases rebuild from the tail ("...responder"
  -> "necesita responder" -> "el equipo necesita responder")

Constructor Sessions (Michel Thomas-style):
- cognate rules that convert thousands of English words instantly
- verb "handles": one verb scaffolded from single word to full question
- progressive sentence construction from word tiles — the session leads,
  nothing is memorized up front

Both feed TutorMastery, so method work counts toward signals, XP, and
the review queue. Fully offline.
"""

import logging
import random
from collections import defaultdict

from sqlmodel import Session, select

from feintlex.models import TutorMastery, utc_now
from feintlex.services.vocabulary import normalize_term


LOGGER = logging.getLogger("feintlex.methods")

RECALL_GAPS = [1, 3, 7, 14]

# Curated practical lines for Echo Sessions: (spanish, english).
ECHO_LINES: list[tuple[str, str]] = [
    ("Quiero un cafe, por favor", "I want a coffee, please"),
    ("No entiendo la pregunta", "I don't understand the question"),
    ("¿Puedes hablar mas despacio?", "Can you speak more slowly?"),
    ("Necesito mas tiempo", "I need more time"),
    ("¿Donde esta la estacion?", "Where is the station?"),
    ("No tengo dinero ahora", "I don't have money right now"),
    ("Quiero aprender espanol", "I want to learn Spanish"),
    ("¿Que significa esta palabra?", "What does this word mean?"),
    ("El equipo necesita responder", "The team needs to respond"),
    ("No puedo hablar ahora", "I can't talk right now"),
    ("¿Cuanto cuesta el billete?", "How much does the ticket cost?"),
    ("Tengo una pregunta importante", "I have an important question"),
    ("El sistema no funciona hoy", "The system isn't working today"),
    ("¿Por que no vienes con nosotros?", "Why don't you come with us?"),
    ("Voy a trabajar manana", "I'm going to work tomorrow"),
    ("Quiero ver el informe", "I want to see the report"),
    ("La reunion empieza a las diez", "The meeting starts at ten"),
    ("¿Puedes ayudarme con esto?", "Can you help me with this?"),
    ("No se donde esta mi telefono", "I don't know where my phone is"),
    ("Necesitamos hablar del proyecto", "We need to talk about the project"),
    ("El partido empieza en una hora", "The match starts in an hour"),
    ("Creo que tienes razon", "I think you're right"),
    ("No estoy seguro de la respuesta", "I'm not sure of the answer"),
    ("¿A que hora sale el tren?", "What time does the train leave?"),
    ("Quiero practicar todos los dias", "I want to practice every day"),
    ("El analista revisa las alertas", "The analyst reviews the alerts"),
    ("Hay actividad sospechosa en la red", "There is suspicious activity on the network"),
    ("Tenemos que proteger los datos", "We have to protect the data"),
    ("La policia investiga el caso", "The police are investigating the case"),
    ("El testigo dice la verdad", "The witness is telling the truth"),
    ("No quiero perder el tiempo", "I don't want to waste time"),
    ("¿Puedo pagar con tarjeta?", "Can I pay by card?"),
    ("Es mas dificil de lo que parece", "It's harder than it seems"),
    ("Todavia estoy aprendiendo", "I'm still learning"),
    ("Lo siento, no puedo ir", "I'm sorry, I can't go"),
    ("¿Me puedes dar un ejemplo?", "Can you give me an example?"),
    ("Eso no es un problema", "That's not a problem"),
    ("Nos vemos la proxima semana", "See you next week"),
    ("El gobierno anuncia una reforma", "The government announces a reform"),
    ("Segun la fuente, hay mas pistas", "According to the source, there are more clues"),
]


def backward_buildup(sentence: str) -> list[str]:
    """Pimsleur-style tail-first chunks: end of the phrase, then grow."""
    words = sentence.split()
    if len(words) <= 3:
        return [sentence]
    starts = {len(words) - 2}
    if len(words) > 5:
        starts.add(len(words) - 4)
    starts.add(0)
    chunks: list[str] = []
    for start in sorted(starts, reverse=True):
        chunk = " ".join(words[start:])
        if chunk not in chunks:
            chunks.append(chunk)
    return chunks


def _echo_term_id(spanish: str) -> str:
    return f"echo:{normalize_term(spanish)[:60]}"


def build_echo_session(session: Session, *, size: int = 6) -> dict[str, object]:
    """Graduated-interval prompt queue mixing new and weak lines."""
    size = max(3, min(size, 10))
    mastery = {
        row.term_id: row
        for row in session.exec(select(TutorMastery).where(TutorMastery.deck_id == "echo")).all()
    }

    def level_of(line: tuple[str, str]) -> int:
        row = mastery.get(_echo_term_id(line[0]))
        return row.level if row else 0

    # Weakest lines first (new lines have level 0), light shuffle inside bands.
    pool = ECHO_LINES[:]
    random.shuffle(pool)
    pool.sort(key=level_of)
    chosen = pool[:size]

    timeline: dict[int, list[dict[str, object]]] = defaultdict(list)
    slot = 0
    for spanish, english in chosen:
        item = {
            "term_id": _echo_term_id(spanish),
            "es": spanish,
            "en": english,
            "chunks": backward_buildup(spanish),
            "level": level_of((spanish, english)),
        }
        timeline[slot].append({"mode": "introduce", **item})
        for index, gap in enumerate(RECALL_GAPS, start=1):
            timeline[slot + gap].append(
                {"mode": "recall", "recall_index": index, "recall_total": len(RECALL_GAPS), **item}
            )
        slot += 2

    prompts: list[dict[str, object]] = []
    for key in sorted(timeline):
        prompts.extend(timeline[key])

    return {
        "method": "echo",
        "title": "Echo Session — graduated interval recall",
        "instructions": (
            "Say every line ALOUD. On recalls, produce the Spanish during the "
            "countdown before the reveal — the anticipation is the workout."
        ),
        "items": len(chosen),
        "prompts": prompts,
    }


# --- Constructor Sessions (Michel Thomas-style) -------------------------------

COGNATE_RULES: list[dict[str, object]] = [
    {
        "id": "cion",
        "title": "The -tion rule",
        "points": [
            "English -tion becomes Spanish -ción — and the word is always feminine (la).",
            "You already own thousands of Spanish words: nation -> nación, action -> acción.",
        ],
        "examples": [
            {"es": "la nacion", "en": "the nation"},
            {"es": "la informacion", "en": "the information"},
            {"es": "la situacion", "en": "the situation"},
            {"es": "la investigacion", "en": "the investigation"},
        ],
        "conversions": [
            {"en": "operation", "es": "operacion"},
            {"en": "condition", "es": "condicion"},
            {"en": "conversation", "es": "conversacion"},
        ],
    },
    {
        "id": "dad",
        "title": "The -ty rule",
        "points": [
            "English -ty becomes Spanish -dad — also always feminine (la).",
            "possibility -> posibilidad, reality -> realidad, security -> seguridad.",
        ],
        "examples": [
            {"es": "la posibilidad", "en": "the possibility"},
            {"es": "la universidad", "en": "the university"},
            {"es": "la seguridad", "en": "the security"},
            {"es": "la actividad", "en": "the activity"},
        ],
        "conversions": [
            {"en": "reality", "es": "realidad"},
            {"en": "opportunity", "es": "oportunidad"},
            {"en": "identity", "es": "identidad"},
        ],
    },
    {
        "id": "mente",
        "title": "The -ly rule",
        "points": [
            "English -ly becomes Spanish -mente, attached to the feminine adjective.",
            "exact -> exactamente, probable -> probablemente, normal -> normalmente.",
        ],
        "examples": [
            {"es": "exactamente", "en": "exactly"},
            {"es": "probablemente", "en": "probably"},
            {"es": "normalmente", "en": "normally"},
            {"es": "finalmente", "en": "finally"},
        ],
        "conversions": [
            {"en": "immediately (from inmediata)", "es": "inmediatamente"},
            {"en": "clearly (from clara)", "es": "claramente"},
            {"en": "generally (from general)", "es": "generalmente"},
        ],
    },
    {
        "id": "ble",
        "title": "The -ble rule",
        "points": [
            "Words ending in -ble are usually identical in both languages.",
            "possible -> posible, terrible -> terrible, probable -> probable.",
        ],
        "examples": [
            {"es": "posible", "en": "possible"},
            {"es": "terrible", "en": "terrible"},
            {"es": "responsable", "en": "responsible"},
            {"es": "increible", "en": "incredible"},
        ],
        "conversions": [
            {"en": "impossible", "es": "imposible"},
            {"en": "probable", "es": "probable"},
            {"en": "flexible", "es": "flexible"},
        ],
    },
    {
        "id": "ario",
        "title": "The -ary rule",
        "points": [
            "English -ary becomes Spanish -ario.",
            "necessary -> necesario, ordinary -> ordinario, vocabulary -> vocabulario.",
        ],
        "examples": [
            {"es": "necesario", "en": "necessary"},
            {"es": "ordinario", "en": "ordinary"},
            {"es": "el vocabulario", "en": "the vocabulary"},
            {"es": "el salario", "en": "the salary"},
        ],
        "conversions": [
            {"en": "secretary", "es": "secretario"},
            {"en": "anniversary", "es": "aniversario"},
            {"en": "extraordinary", "es": "extraordinario"},
        ],
    },
]

VERB_SCAFFOLDS: list[dict[str, object]] = [
    {
        "verb": "querer",
        "title": "QUERER — your first handle",
        "points": [
            "quiero = I want · quieres = you want · quiere = he/she wants.",
            "Add ANY infinitive after it: quiero hablar = I want to speak.",
            "Negate by putting 'no' before the verb: no quiero = I don't want.",
        ],
        "steps": [
            {"type": "produce", "prompt_en": "I want", "answer_es": "quiero", "hint": "One word."},
            {"type": "produce", "prompt_en": "I want to speak", "answer_es": "quiero hablar", "hint": "quiero + infinitive"},
            {"type": "produce", "prompt_en": "I don't want to speak", "answer_es": "no quiero hablar", "hint": "'no' goes before the verb"},
            {"type": "produce", "prompt_en": "you want to see", "answer_es": "quieres ver", "hint": "-es ending for 'you'"},
            {"type": "build", "prompt_en": "I don't want to see it now", "answer_es": "no quiero verlo ahora", "tiles": ["ahora", "no", "verlo", "quiero"]},
            {"type": "produce", "prompt_en": "why don't you want to speak?", "answer_es": "por que no quieres hablar", "hint": "por qué + no + quieres + infinitive"},
        ],
    },
    {
        "verb": "poder",
        "title": "PODER — can / to be able",
        "points": [
            "puedo = I can · puedes = you can · puede = he/she can.",
            "Same trick: puedo + infinitive. no puedo = I can't.",
            "¿puedes...? at the start makes a request: can you...?",
        ],
        "steps": [
            {"type": "produce", "prompt_en": "I can", "answer_es": "puedo", "hint": "One word."},
            {"type": "produce", "prompt_en": "I can't go", "answer_es": "no puedo ir", "hint": "no + puedo + ir"},
            {"type": "produce", "prompt_en": "can you help me?", "answer_es": "puedes ayudarme", "hint": "ayudar + me stuck on the end"},
            {"type": "build", "prompt_en": "I can't talk right now", "answer_es": "no puedo hablar ahora", "tiles": ["hablar", "no", "ahora", "puedo"]},
            {"type": "produce", "prompt_en": "we can wait", "answer_es": "podemos esperar", "hint": "-emos ending for 'we'"},
        ],
    },
    {
        "verb": "tener",
        "title": "TENER — to have (and to be, sometimes)",
        "points": [
            "tengo = I have · tienes = you have · tiene = he/she has.",
            "tengo que + infinitive = I have to: tengo que trabajar.",
            "Spanish HAS hunger and fear: tengo hambre, tengo miedo.",
        ],
        "steps": [
            {"type": "produce", "prompt_en": "I have", "answer_es": "tengo", "hint": "One word."},
            {"type": "produce", "prompt_en": "I have to work", "answer_es": "tengo que trabajar", "hint": "tengo que + infinitive"},
            {"type": "produce", "prompt_en": "I am hungry (I have hunger)", "answer_es": "tengo hambre", "hint": "have, not am"},
            {"type": "build", "prompt_en": "I don't have time today", "answer_es": "no tengo tiempo hoy", "tiles": ["tiempo", "no", "hoy", "tengo"]},
            {"type": "produce", "prompt_en": "do you have a question?", "answer_es": "tienes una pregunta", "hint": "tienes + una + ..."},
        ],
    },
    {
        "verb": "ir",
        "title": "IR — to go (and the instant future)",
        "points": [
            "voy = I go · vas = you go · va = he/she goes · vamos = we go / let's go.",
            "voy a + infinitive = I'm going to: instant future tense for free.",
            "voy a trabajar = I'm going to work.",
        ],
        "steps": [
            {"type": "produce", "prompt_en": "I go / I'm going", "answer_es": "voy", "hint": "One word."},
            {"type": "produce", "prompt_en": "I'm going to work tomorrow", "answer_es": "voy a trabajar manana", "hint": "voy a + infinitive + mañana"},
            {"type": "produce", "prompt_en": "we are going to win", "answer_es": "vamos a ganar", "hint": "vamos a + infinitive"},
            {"type": "build", "prompt_en": "why aren't you going to the match?", "answer_es": "por que no vas al partido", "tiles": ["no", "al", "por", "vas", "que", "partido"]},
            {"type": "produce", "prompt_en": "let's see", "answer_es": "vamos a ver", "hint": "vamos a + ver"},
        ],
    },
]

CONSTRUCTOR_BUILDS: list[dict[str, object]] = [
    {"prompt_en": "I want a coffee, please", "answer_es": "quiero un cafe por favor", "tiles": ["por", "un", "quiero", "favor", "cafe"]},
    {"prompt_en": "it's not possible right now", "answer_es": "no es posible ahora", "tiles": ["posible", "no", "ahora", "es"]},
    {"prompt_en": "the situation is complicated", "answer_es": "la situacion es complicada", "tiles": ["es", "la", "complicada", "situacion"]},
    {"prompt_en": "I need more information", "answer_es": "necesito mas informacion", "tiles": ["informacion", "necesito", "mas"]},
    {"prompt_en": "we have to protect the data", "answer_es": "tenemos que proteger los datos", "tiles": ["los", "proteger", "tenemos", "datos", "que"]},
    {"prompt_en": "the team is going to respond", "answer_es": "el equipo va a responder", "tiles": ["va", "el", "responder", "a", "equipo"]},
]


def build_constructor_session(session: Session) -> dict[str, object]:
    """One cognate rule + one verb scaffold + construction drills."""
    mastery_ids = {
        row.term_id
        for row in session.exec(
            select(TutorMastery).where(TutorMastery.deck_id == "constructor").where(TutorMastery.level >= 3)
        ).all()
    }

    def unseen_first(entries: list[dict[str, object]], key_fn) -> list[dict[str, object]]:
        pool = entries[:]
        random.shuffle(pool)
        pool.sort(key=lambda entry: key_fn(entry) in mastery_ids)
        return pool

    rule = unseen_first(COGNATE_RULES, lambda r: f"constructor:rule:{r['id']}")[0]
    scaffold = unseen_first(VERB_SCAFFOLDS, lambda s: f"constructor:verb:{s['verb']}")[0]
    builds = random.sample(CONSTRUCTOR_BUILDS, k=2)

    steps: list[dict[str, object]] = [
        {
            "type": "teach",
            "term_id": f"constructor:rule:{rule['id']}",
            "title": rule["title"],
            "points": rule["points"],
            "examples": rule["examples"],
        }
    ]
    for conversion in rule["conversions"]:
        steps.append(
            {
                "type": "convert",
                "term_id": f"constructor:rule:{rule['id']}",
                "prompt_en": conversion["en"],
                "answer_es": conversion["es"],
                "hint": rule["title"],
            }
        )
    steps.append(
        {
            "type": "teach",
            "term_id": f"constructor:verb:{scaffold['verb']}",
            "title": scaffold["title"],
            "points": scaffold["points"],
            "examples": [],
        }
    )
    for step in scaffold["steps"]:
        entry = dict(step)
        entry["term_id"] = f"constructor:verb:{scaffold['verb']}"
        if entry["type"] == "build":
            tiles = entry["tiles"][:]
            random.shuffle(tiles)
            entry["tiles"] = tiles
        steps.append(entry)
    for build in builds:
        tiles = build["tiles"][:]
        random.shuffle(tiles)
        steps.append(
            {
                "type": "build",
                "term_id": f"constructor:build:{normalize_term(build['answer_es'])[:40]}",
                "prompt_en": build["prompt_en"],
                "answer_es": build["answer_es"],
                "tiles": tiles,
            }
        )

    return {
        "method": "constructor",
        "title": f"Constructor Session — {rule['title']} + {scaffold['verb'].upper()}",
        "instructions": (
            "Never memorize — construct. Answer out loud first, then type or "
            "assemble. Accents are optional; the structure is what counts."
        ),
        "items": len([step for step in steps if step["type"] != "teach"]),
        "steps": steps,
    }


def record_method_results(
    session: Session,
    *,
    method: str,
    results: list[dict[str, object]],
) -> dict[str, object]:
    """Feed session results into TutorMastery so methods earn signals/XP."""
    deck_id = "echo" if method == "echo" else "constructor"
    correct_count = 0
    for result in results:
        term_id = str(result.get("term_id", "")).strip()
        if not term_id:
            continue
        correct = bool(result.get("correct"))
        if correct:
            correct_count += 1
        row = session.exec(select(TutorMastery).where(TutorMastery.term_id == term_id)).first()
        if row is None:
            row = TutorMastery(
                term_id=term_id,
                deck_id=deck_id,
                term=str(result.get("es", ""))[:120],
                translation=str(result.get("en", ""))[:120],
            )
        row.level = max(0, min(5, row.level + (1 if correct else -1)))
        row.seen += 1
        if correct:
            row.correct += 1
        row.updated_at = utc_now()
        session.add(row)
    session.commit()
    LOGGER.info("method_session_recorded", extra={"method": method, "results": len(results), "correct": correct_count})
    return {"method": method, "recorded": len(results), "correct": correct_count}
