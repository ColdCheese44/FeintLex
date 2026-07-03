from __future__ import annotations

"""Offline Spanish verb conjugation engine.

Handles regular -ar/-er/-ir verbs across five tenses plus the most
common irregular verbs. Pure rules, no network, no models.
"""

from feintlex.services.lexicon import lookup
from feintlex.services.vocabulary import normalize_term


PERSONS = ["yo", "tú", "él/ella/usted", "nosotros", "vosotros", "ellos/ustedes"]

TENSES = ["present", "preterite", "imperfect", "future", "conditional"]

TENSE_LABELS = {
    "present": "Present",
    "preterite": "Preterite (completed past)",
    "imperfect": "Imperfect (ongoing past)",
    "future": "Future",
    "conditional": "Conditional",
}

_REGULAR_ENDINGS: dict[str, dict[str, list[str]]] = {
    "present": {
        "ar": ["o", "as", "a", "amos", "áis", "an"],
        "er": ["o", "es", "e", "emos", "éis", "en"],
        "ir": ["o", "es", "e", "imos", "ís", "en"],
    },
    "preterite": {
        "ar": ["é", "aste", "ó", "amos", "asteis", "aron"],
        "er": ["í", "iste", "ió", "imos", "isteis", "ieron"],
        "ir": ["í", "iste", "ió", "imos", "isteis", "ieron"],
    },
    "imperfect": {
        "ar": ["aba", "abas", "aba", "ábamos", "abais", "aban"],
        "er": ["ía", "ías", "ía", "íamos", "íais", "ían"],
        "ir": ["ía", "ías", "ía", "íamos", "íais", "ían"],
    },
}

# Future and conditional endings attach to the full infinitive (or irregular stem).
_FUTURE_ENDINGS = ["é", "ás", "á", "emos", "éis", "án"]
_CONDITIONAL_ENDINGS = ["ía", "ías", "ía", "íamos", "íais", "ían"]

_IRREGULAR_FUTURE_STEMS = {
    "tener": "tendr", "hacer": "har", "poder": "podr", "querer": "querr",
    "decir": "dir", "venir": "vendr", "saber": "sabr", "poner": "pondr",
    "salir": "saldr", "haber": "habr", "caber": "cabr", "valer": "valdr",
}

# Fully or partially irregular verbs. Missing tenses fall back to regular rules.
_IRREGULARS: dict[str, dict[str, list[str]]] = {
    "ser": {
        "present": ["soy", "eres", "es", "somos", "sois", "son"],
        "preterite": ["fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"],
        "imperfect": ["era", "eras", "era", "éramos", "erais", "eran"],
    },
    "estar": {
        "present": ["estoy", "estás", "está", "estamos", "estáis", "están"],
        "preterite": ["estuve", "estuviste", "estuvo", "estuvimos", "estuvisteis", "estuvieron"],
    },
    "ir": {
        "present": ["voy", "vas", "va", "vamos", "vais", "van"],
        "preterite": ["fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"],
        "imperfect": ["iba", "ibas", "iba", "íbamos", "ibais", "iban"],
    },
    "tener": {
        "present": ["tengo", "tienes", "tiene", "tenemos", "tenéis", "tienen"],
        "preterite": ["tuve", "tuviste", "tuvo", "tuvimos", "tuvisteis", "tuvieron"],
    },
    "hacer": {
        "present": ["hago", "haces", "hace", "hacemos", "hacéis", "hacen"],
        "preterite": ["hice", "hiciste", "hizo", "hicimos", "hicisteis", "hicieron"],
    },
    "poder": {
        "present": ["puedo", "puedes", "puede", "podemos", "podéis", "pueden"],
        "preterite": ["pude", "pudiste", "pudo", "pudimos", "pudisteis", "pudieron"],
    },
    "querer": {
        "present": ["quiero", "quieres", "quiere", "queremos", "queréis", "quieren"],
        "preterite": ["quise", "quisiste", "quiso", "quisimos", "quisisteis", "quisieron"],
    },
    "decir": {
        "present": ["digo", "dices", "dice", "decimos", "decís", "dicen"],
        "preterite": ["dije", "dijiste", "dijo", "dijimos", "dijisteis", "dijeron"],
    },
    "venir": {
        "present": ["vengo", "vienes", "viene", "venimos", "venís", "vienen"],
        "preterite": ["vine", "viniste", "vino", "vinimos", "vinisteis", "vinieron"],
    },
    "saber": {
        "present": ["sé", "sabes", "sabe", "sabemos", "sabéis", "saben"],
        "preterite": ["supe", "supiste", "supo", "supimos", "supisteis", "supieron"],
    },
    "ver": {
        "present": ["veo", "ves", "ve", "vemos", "veis", "ven"],
        "preterite": ["vi", "viste", "vio", "vimos", "visteis", "vieron"],
        "imperfect": ["veía", "veías", "veía", "veíamos", "veíais", "veían"],
    },
    "dar": {
        "present": ["doy", "das", "da", "damos", "dais", "dan"],
        "preterite": ["di", "diste", "dio", "dimos", "disteis", "dieron"],
    },
    "poner": {
        "present": ["pongo", "pones", "pone", "ponemos", "ponéis", "ponen"],
        "preterite": ["puse", "pusiste", "puso", "pusimos", "pusisteis", "pusieron"],
    },
    "salir": {
        "present": ["salgo", "sales", "sale", "salimos", "salís", "salen"],
    },
    "conocer": {
        "present": ["conozco", "conoces", "conoce", "conocemos", "conocéis", "conocen"],
    },
    "jugar": {
        "present": ["juego", "juegas", "juega", "jugamos", "jugáis", "juegan"],
        "preterite": ["jugué", "jugaste", "jugó", "jugamos", "jugasteis", "jugaron"],
    },
    "pensar": {
        "present": ["pienso", "piensas", "piensa", "pensamos", "pensáis", "piensan"],
    },
    "encontrar": {
        "present": ["encuentro", "encuentras", "encuentra", "encontramos", "encontráis", "encuentran"],
    },
    "volver": {
        "present": ["vuelvo", "vuelves", "vuelve", "volvemos", "volvéis", "vuelven"],
    },
    "empezar": {
        "present": ["empiezo", "empiezas", "empieza", "empezamos", "empezáis", "empiezan"],
        "preterite": ["empecé", "empezaste", "empezó", "empezamos", "empezasteis", "empezaron"],
    },
    "seguir": {
        "present": ["sigo", "sigues", "sigue", "seguimos", "seguís", "siguen"],
    },
    "entender": {
        "present": ["entiendo", "entiendes", "entiende", "entendemos", "entendéis", "entienden"],
    },
    "perder": {
        "present": ["pierdo", "pierdes", "pierde", "perdemos", "perdéis", "pierden"],
    },
    "buscar": {
        "preterite": ["busqué", "buscaste", "buscó", "buscamos", "buscasteis", "buscaron"],
    },
    "llegar": {
        "preterite": ["llegué", "llegaste", "llegó", "llegamos", "llegasteis", "llegaron"],
    },
    "leer": {
        "preterite": ["leí", "leíste", "leyó", "leímos", "leísteis", "leyeron"],
    },
    # High-frequency stem-changers (present tense boot pattern).
    "cerrar": {
        "present": ["cierro", "cierras", "cierra", "cerramos", "cerráis", "cierran"],
    },
    "comenzar": {
        "present": ["comienzo", "comienzas", "comienza", "comenzamos", "comenzáis", "comienzan"],
        "preterite": ["comencé", "comenzaste", "comenzó", "comenzamos", "comenzasteis", "comenzaron"],
    },
    "sentir": {
        "present": ["siento", "sientes", "siente", "sentimos", "sentís", "sienten"],
        "preterite": ["sentí", "sentiste", "sintió", "sentimos", "sentisteis", "sintieron"],
    },
    "dormir": {
        "present": ["duermo", "duermes", "duerme", "dormimos", "dormís", "duermen"],
        "preterite": ["dormí", "dormiste", "durmió", "dormimos", "dormisteis", "durmieron"],
    },
    "recordar": {
        "present": ["recuerdo", "recuerdas", "recuerda", "recordamos", "recordáis", "recuerdan"],
    },
    "contar": {
        "present": ["cuento", "cuentas", "cuenta", "contamos", "contáis", "cuentan"],
    },
    "mostrar": {
        "present": ["muestro", "muestras", "muestra", "mostramos", "mostráis", "muestran"],
    },
    "costar": {
        "present": ["cuesto", "cuestas", "cuesta", "costamos", "costáis", "cuestan"],
    },
    "morir": {
        "present": ["muero", "mueres", "muere", "morimos", "morís", "mueren"],
        "preterite": ["morí", "moriste", "murió", "morimos", "moristeis", "murieron"],
    },
    "servir": {
        "present": ["sirvo", "sirves", "sirve", "servimos", "servís", "sirven"],
        "preterite": ["serví", "serviste", "sirvió", "servimos", "servisteis", "sirvieron"],
    },
    "repetir": {
        "present": ["repito", "repites", "repite", "repetimos", "repetís", "repiten"],
        "preterite": ["repetí", "repetiste", "repitió", "repetimos", "repetisteis", "repitieron"],
    },
    "preferir": {
        "present": ["prefiero", "prefieres", "prefiere", "preferimos", "preferís", "prefieren"],
    },
    "devolver": {
        "present": ["devuelvo", "devuelves", "devuelve", "devolvemos", "devolvéis", "devuelven"],
    },
    "pedir": {
        "present": ["pido", "pides", "pide", "pedimos", "pedís", "piden"],
        "preterite": ["pedí", "pediste", "pidió", "pedimos", "pedisteis", "pidieron"],
    },
    "conseguir": {
        "present": ["consigo", "consigues", "consigue", "conseguimos", "conseguís", "consiguen"],
    },
    "traer": {
        "present": ["traigo", "traes", "trae", "traemos", "traéis", "traen"],
        "preterite": ["traje", "trajiste", "trajo", "trajimos", "trajisteis", "trajeron"],
    },
    "oir": {
        "present": ["oigo", "oyes", "oye", "oímos", "oís", "oyen"],
        "preterite": ["oí", "oíste", "oyó", "oímos", "oísteis", "oyeron"],
    },
    "caer": {
        "present": ["caigo", "caes", "cae", "caemos", "caéis", "caen"],
        "preterite": ["caí", "caíste", "cayó", "caímos", "caísteis", "cayeron"],
    },
    "construir": {
        "present": ["construyo", "construyes", "construye", "construimos", "construís", "construyen"],
    },
    "conducir": {
        "present": ["conduzco", "conduces", "conduce", "conducimos", "conducís", "conducen"],
        "preterite": ["conduje", "condujiste", "condujo", "condujimos", "condujisteis", "condujeron"],
    },
}


def is_infinitive(word: str) -> bool:
    normalized = normalize_term(word)
    if normalized == "ir":
        return True
    return len(normalized) > 2 and normalized.endswith(("ar", "er", "ir"))


def _regular_forms(verb: str, tense: str) -> list[str]:
    ending = verb[-2:]
    stem = verb[:-2]
    if tense == "future":
        base = _IRREGULAR_FUTURE_STEMS.get(verb, verb)
        return [base + suffix for suffix in _FUTURE_ENDINGS]
    if tense == "conditional":
        base = _IRREGULAR_FUTURE_STEMS.get(verb, verb)
        return [base + suffix for suffix in _CONDITIONAL_ENDINGS]
    endings = _REGULAR_ENDINGS[tense][ending]
    return [stem + suffix for suffix in endings]


def conjugate(verb: str, *, tenses: list[str] | None = None) -> dict[str, object] | None:
    """Conjugate a Spanish infinitive. Returns None if not conjugatable."""
    normalized = normalize_term(verb)
    if not is_infinitive(normalized):
        return None

    wanted = [tense for tense in (tenses or TENSES) if tense in TENSES]
    irregular = _IRREGULARS.get(normalized, {})
    table: dict[str, list[dict[str, str]]] = {}
    for tense in wanted:
        forms = irregular.get(tense) or _regular_forms(normalized, tense)
        table[tense] = [
            {"person": person, "form": form} for person, form in zip(PERSONS, forms)
        ]

    return {
        "verb": normalized,
        "translation": lookup(normalized) or "",
        "is_irregular": normalized in _IRREGULARS or normalized in _IRREGULAR_FUTURE_STEMS,
        "tenses": table,
        "tense_labels": {tense: TENSE_LABELS[tense] for tense in wanted},
    }


def find_infinitive(text: str) -> str | None:
    """Pick the most likely infinitive mentioned in a chat message."""
    from feintlex.services.vocabulary import SPANISH_STOPWORDS, tokenize

    candidates: list[str] = []
    for token in tokenize(text):
        normalized = normalize_term(token)
        if normalized in _IRREGULARS or normalized in _IRREGULAR_FUTURE_STEMS:
            return normalized
        if is_infinitive(normalized) and normalized not in SPANISH_STOPWORDS:
            candidates.append(normalized)
    # Prefer verbs the lexicon knows; otherwise take the first candidate.
    for candidate in candidates:
        gloss = lookup(candidate)
        if gloss and gloss.startswith(("to ", "can ", "must")):
            return candidate
    return candidates[0] if candidates else None
