from __future__ import annotations

"""Offline Spanish->English lexicon.

This is the vocabulary backbone for the offline tutor: word lookups,
literal sentence glosses for autopsy, and reverse (EN->ES) searches.
Keys are stored accent-free lowercase; use lookup()/gloss functions
instead of touching LEXICON directly.
"""

from feintlex.services.vocabulary import normalize_term, tokenize


LEXICON: dict[str, str] = {
    # Articles, pronouns, and function words
    "el": "the", "la": "the", "los": "the", "las": "the",
    "un": "a/an", "una": "a/an", "unos": "some", "unas": "some",
    "yo": "I", "tu": "you / your", "usted": "you (formal)", "nosotros": "we",
    "ella": "she", "ellos": "they", "ellas": "they (f.)", "vosotros": "you all",
    "me": "me / myself", "te": "you / yourself", "se": "oneself / itself",
    "mi": "my", "su": "his/her/your/their", "nuestro": "our",
    "este": "this", "esta": "this", "ese": "that", "esa": "that",
    "esto": "this (neutral)", "eso": "that (neutral)", "aqui": "here", "alli": "there",
    "que": "that / what", "quien": "who", "como": "how / like", "cuando": "when",
    "donde": "where", "cual": "which", "cuanto": "how much",
    "y": "and", "o": "or", "pero": "but", "porque": "because", "si": "if / yes",
    "no": "no / not", "muy": "very", "mas": "more", "menos": "less",
    "tambien": "also", "aunque": "although", "mientras": "while",
    "despues": "after", "antes": "before", "ahora": "now", "luego": "later",
    "siempre": "always", "nunca": "never", "todavia": "still / yet", "ya": "already",
    "con": "with", "sin": "without", "para": "for / in order to", "por": "for / by / through",
    "de": "of / from", "en": "in / on", "a": "to / at", "entre": "between",
    "sobre": "about / on top of", "hasta": "until", "desde": "since / from",
    "contra": "against", "durante": "during", "hacia": "toward",
    "todo": "all / everything", "nada": "nothing", "algo": "something",
    "alguien": "someone", "nadie": "nobody", "cada": "each", "otro": "other",
    "mucho": "a lot", "poco": "little / few", "bien": "well", "mal": "badly",
    # Core verbs (infinitives)
    "ser": "to be (identity)", "estar": "to be (state/place)", "tener": "to have",
    "hacer": "to do / make", "ir": "to go", "querer": "to want", "poder": "can / to be able",
    "decir": "to say", "venir": "to come", "saber": "to know (facts)",
    "conocer": "to know (people/places)", "ver": "to see", "dar": "to give",
    "hablar": "to speak", "comer": "to eat", "beber": "to drink", "vivir": "to live",
    "trabajar": "to work", "estudiar": "to study", "aprender": "to learn",
    "entender": "to understand", "escribir": "to write", "leer": "to read",
    "escuchar": "to listen", "mirar": "to look at", "buscar": "to search for",
    "encontrar": "to find", "pensar": "to think", "creer": "to believe",
    "necesitar": "to need", "usar": "to use", "ayudar": "to help",
    "empezar": "to begin", "terminar": "to finish", "llegar": "to arrive",
    "salir": "to leave / go out", "volver": "to return", "poner": "to put",
    "jugar": "to play", "ganar": "to win / earn", "perder": "to lose",
    "pagar": "to pay", "comprar": "to buy", "vender": "to sell",
    "abrir": "to open", "cerrar": "to close", "seguir": "to follow / continue",
    "dejar": "to leave / let", "llamar": "to call", "llevar": "to carry / wear",
    "pasar": "to pass / happen", "deber": "must / to owe", "parecer": "to seem",
    "analizar": "to analyze", "revisar": "to review / check", "detectar": "to detect",
    "investigar": "to investigate", "responder": "to respond", "informar": "to report",
    "proteger": "to protect", "atacar": "to attack", "defender": "to defend",
    "controlar": "to control", "mejorar": "to improve", "practicar": "to practice",
    "explicar": "to explain", "preguntar": "to ask", "contestar": "to answer",
    "recordar": "to remember", "olvidar": "to forget", "intentar": "to try",
    # Common conjugated forms (high-frequency)
    "es": "is", "son": "are", "soy": "I am", "eres": "you are", "somos": "we are",
    "esta": "is (state) / this", "estan": "are (state)", "estoy": "I am (state)",
    "fue": "was / went", "era": "was (descr.)", "eran": "were (descr.)",
    "hay": "there is / there are", "tiene": "has", "tienen": "have", "tengo": "I have",
    "hace": "does / makes / ago", "hizo": "did / made", "va": "goes", "van": "they go",
    "voy": "I go", "puede": "can", "pueden": "they can", "puedo": "I can",
    "quiere": "wants", "quiero": "I want", "dice": "says", "dijo": "said",
    "sabe": "knows", "veo": "I see", "vio": "saw",
    # People and identity
    "hombre": "man", "mujer": "woman", "nino": "boy / child", "nina": "girl",
    "amigo": "friend", "amiga": "friend (f.)", "familia": "family",
    "gente": "people", "persona": "person", "nombre": "name",
    "senor": "sir / mister", "senora": "madam / missus",
    "equipo": "team", "jugador": "player", "entrenador": "coach",
    "analista": "analyst", "policia": "police", "testigo": "witness",
    "sospechoso": "suspect", "victima": "victim", "periodista": "journalist",
    # Places and things
    "casa": "house", "ciudad": "city", "pais": "country", "mundo": "world",
    "calle": "street", "trabajo": "work / job", "oficina": "office",
    "escuela": "school", "tienda": "store", "estacion": "station",
    "aeropuerto": "airport", "hotel": "hotel", "bano": "bathroom",
    "puerta": "door", "mesa": "table", "libro": "book", "telefono": "telephone",
    "computadora": "computer", "coche": "car", "tren": "train", "avion": "airplane",
    "dinero": "money", "cosa": "thing", "parte": "part", "lugar": "place",
    "agua": "water", "cafe": "coffee", "pan": "bread", "comida": "food",
    "cuenta": "bill / account", "cerveza": "beer", "vino": "wine", "leche": "milk",
    # Time
    "dia": "day", "noche": "night", "manana": "tomorrow / morning", "tarde": "afternoon / late",
    "hoy": "today", "ayer": "yesterday", "semana": "week", "mes": "month",
    "ano": "year", "hora": "hour / time", "minuto": "minute", "tiempo": "time / weather",
    "momento": "moment", "vez": "time (instance)", "veces": "times",
    # Numbers
    "cero": "zero", "uno": "one", "dos": "two", "tres": "three", "cuatro": "four",
    "cinco": "five", "seis": "six", "siete": "seven", "ocho": "eight",
    "nueve": "nine", "diez": "ten", "quince": "fifteen", "veinte": "twenty",
    "treinta": "thirty", "cincuenta": "fifty", "cien": "one hundred", "mil": "one thousand",
    # Adjectives
    "bueno": "good", "malo": "bad", "grande": "big", "pequeno": "small",
    "nuevo": "new", "viejo": "old", "primero": "first", "ultimo": "last",
    "importante": "important", "dificil": "difficult", "facil": "easy",
    "rapido": "fast", "lento": "slow", "caliente": "hot", "frio": "cold",
    "cansado": "tired", "contento": "happy", "triste": "sad", "seguro": "safe / sure",
    "peligroso": "dangerous", "claro": "clear / of course", "largo": "long",
    "izquierda": "left", "derecha": "right", "recto": "straight", "cerca": "near",
    "lejos": "far", "mejor": "better / best", "peor": "worse / worst",
    # Soccer domain
    "futbol": "soccer", "partido": "match / game", "gol": "goal", "pelota": "ball",
    "porteria": "goalposts", "portero": "goalkeeper", "defensa": "defense",
    "delantero": "forward / striker", "arbitro": "referee", "falta": "foul",
    "penalti": "penalty", "campo": "field", "liga": "league", "temporada": "season",
    "campeon": "champion", "rival": "rival", "marcador": "scoreboard",
    "presiona": "presses", "avanza": "advances",
    # Cybersecurity / investigation domain
    "seguridad": "security", "alerta": "alert", "alertas": "alerts",
    "amenaza": "threat", "ataque": "attack", "riesgo": "risk",
    "contrasena": "password", "clave": "key / password", "red": "network",
    "sistema": "system", "servidor": "server", "datos": "data",
    "archivo": "file", "correo": "email", "mensaje": "message",
    "usuario": "user", "acceso": "access", "codigo": "code",
    "error": "error", "fallo": "failure", "prueba": "test / proof",
    "evidencia": "evidence", "caso": "case", "pista": "clue / track",
    "informe": "report", "fuente": "source", "actividad": "activity",
    "sospechosa": "suspicious (f.)", "investigacion": "investigation",
    # News domain
    "noticia": "news item", "noticias": "news", "gobierno": "government",
    "presidente": "president", "eleccion": "election", "ley": "law",
    "economia": "economy", "empresa": "company", "mercado": "market",
    "guerra": "war", "paz": "peace", "crisis": "crisis", "acuerdo": "agreement",
    # Courtesy and conversation
    "hola": "hello", "adios": "goodbye", "gracias": "thank you",
    "perdon": "excuse me / sorry", "favor": "favor", "ayuda": "help",
    "verdad": "truth / right?", "ejemplo": "example", "pregunta": "question",
    "respuesta": "answer", "palabra": "word", "frase": "phrase / sentence",
    "idioma": "language", "espanol": "Spanish", "ingles": "English",
}

# Multi-word phrases checked before single-word lookup.
PHRASES: dict[str, str] = {
    "por favor": "please",
    "buenos dias": "good morning",
    "buenas tardes": "good afternoon",
    "buenas noches": "good evening / night",
    "me llamo": "my name is",
    "mucho gusto": "nice to meet you",
    "hasta luego": "see you later",
    "tengo hambre": "I am hungry",
    "tengo sed": "I am thirsty",
    "donde esta": "where is",
    "cuanto cuesta": "how much does it cost",
    "que hora es": "what time is it",
    "de nada": "you're welcome",
    "lo siento": "I'm sorry",
    "por supuesto": "of course",
    "sin embargo": "however",
    "por eso": "that's why",
    "a veces": "sometimes",
    "tener que": "to have to",
    "hay que": "one must",
    "por que": "why",
}


def lookup(term: str) -> str | None:
    """Return the English gloss for a Spanish term or phrase, if known."""
    cleaned = " ".join(term.strip().split())
    if not cleaned:
        return None
    normalized_phrase = " ".join(normalize_term(token) for token in tokenize(cleaned))
    if normalized_phrase in PHRASES:
        return PHRASES[normalized_phrase]
    return LEXICON.get(normalized_phrase) or LEXICON.get(normalize_term(cleaned))


def reverse_lookup(english: str, *, limit: int = 5) -> list[dict[str, str]]:
    """Find Spanish terms whose gloss mentions the English word."""
    needle = english.strip().lower()
    if not needle:
        return []
    matches: list[dict[str, str]] = []
    for source in (PHRASES, LEXICON):
        for spanish, gloss in source.items():
            gloss_words = gloss.lower().replace("/", " ").replace("(", " ").replace(")", " ").split()
            if needle in gloss_words or needle == gloss.lower():
                matches.append({"es": spanish, "en": gloss})
                if len(matches) >= limit:
                    return matches
    return matches


def gloss_tokens(sentence: str) -> list[dict[str, str]]:
    """Word-by-word gloss of a Spanish sentence for literal translations."""
    glosses: list[dict[str, str]] = []
    for token in tokenize(sentence):
        gloss = LEXICON.get(normalize_term(token))
        glosses.append({"es": token.lower(), "en": gloss or "?"})
    return glosses


def literal_gloss(sentence: str) -> str:
    """Human-readable literal translation line, e.g. 'the | team | analyzes'."""
    glosses = gloss_tokens(sentence)
    if not glosses:
        return ""
    return " | ".join(item["en"] if item["en"] != "?" else f"[{item['es']}]" for item in glosses)


def coverage(sentence: str) -> float:
    """Fraction of tokens the lexicon can gloss (0.0-1.0)."""
    glosses = gloss_tokens(sentence)
    if not glosses:
        return 0.0
    known = sum(1 for item in glosses if item["en"] != "?")
    return known / len(glosses)
