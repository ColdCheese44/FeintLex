from __future__ import annotations

"""Offline Spanish->English lexicon — the FeintLex library.

The vocabulary backbone for the offline tutor: hover glosses, word
lookups, literal sentence translations, reverse (EN->ES) search, and the
browsable Library tab.

Structure:
- CATEGORIES: ~1,300 hand-curated entries grouped by theme
- LEXICON: the merged flat map (normalized accent-free keys)
- PHRASES: multi-word expressions checked before single-word lookup
- derived_forms(): conjugated verb forms auto-generated from every verb
  in the lexicon, so hovering "analizaron" resolves to "to analyze"

Lookup fallback chain: phrase -> exact word -> derived verb form ->
plural stripped -> feminine -o swap.
"""

from feintlex.services.vocabulary import normalize_term, tokenize


CATEGORIES: dict[str, dict[str, str]] = {
    "function_words": {
        "el": "the", "la": "the", "los": "the", "las": "the",
        "del": "of the / from the (de+el)", "al": "to the (a+el)",
        "un": "a/an", "una": "a/an", "unos": "some", "unas": "some",
        "de": "of / from", "en": "in / on", "a": "to / at", "con": "with",
        "sin": "without", "por": "for / by / through", "para": "for / in order to",
        "embargo": "embargo (sin embargo = however)",
        "sobre": "about / on top of", "entre": "between / among", "hasta": "until / up to",
        "desde": "since / from", "contra": "against", "durante": "during",
        "hacia": "toward", "segun": "according to", "tras": "after / behind",
        "ante": "before / faced with", "bajo": "under", "mediante": "by means of",
        "y": "and", "e": "and (before i-)", "o": "or", "u": "or (before o-)",
        "ni": "nor / neither", "pero": "but", "sino": "but rather",
        "porque": "because", "aunque": "although", "si": "if / yes",
        "cuando": "when", "mientras": "while", "como": "how / like / as",
        "que": "that / what / which", "quien": "who", "quienes": "who (plural)",
        "donde": "where", "cual": "which", "cuales": "which (plural)",
        "cuanto": "how much", "cuantos": "how many", "cuya": "whose (f.)", "cuyo": "whose",
        "este": "this", "esta": "this / is (state)", "estos": "these", "estas": "these",
        "ese": "that", "esa": "that", "esos": "those", "esas": "those",
        "aquel": "that (far)", "aquella": "that (far, f.)", "esto": "this (neutral)",
        "eso": "that (neutral)", "aquello": "that (neutral, far)",
        "cada": "each / every", "otro": "other / another", "otra": "other (f.)",
        "mismo": "same / self", "misma": "same (f.)", "tal": "such",
        "cualquier": "any", "ambos": "both", "varios": "several", "varias": "several (f.)",
        "todo": "all / everything", "toda": "all (f.)", "todos": "everyone / all",
        "todas": "all (f. pl.)", "nada": "nothing", "nadie": "nobody",
        "algo": "something", "alguien": "someone", "alguno": "some / any",
        "ninguno": "none / no one", "ninguna": "none (f.)", "demasiado": "too much",
    },
    "pronouns": {
        "yo": "I", "tu": "you / your", "usted": "you (formal)", "ustedes": "you all (formal)",
        "el": "the / he", "ella": "she", "ellos": "they", "ellas": "they (f.)",
        "nosotros": "we", "nosotras": "we (f.)", "vosotros": "you all", "vosotras": "you all (f.)",
        "me": "me / myself", "te": "you / yourself", "se": "oneself / itself",
        "nos": "us / ourselves", "os": "you all (object)", "le": "to him/her/you",
        "les": "to them/you all", "lo": "it / him / the (neutral)", "los": "them / the",
        "mi": "my", "mis": "my (plural)", "su": "his/her/your/their", "sus": "their (plural)",
        "nuestro": "our", "nuestra": "our (f.)", "tus": "your (plural)",
        "mio": "mine", "mia": "mine (f.)", "tuyo": "yours", "suyo": "his/hers/theirs",
        "conmigo": "with me", "contigo": "with you", "consigo": "with oneself",
        "quien": "who", "alguien": "someone",
    },
    "verbs": {
        "ser": "to be (identity)", "estar": "to be (state/place)", "haber": "to have (auxiliary)",
        "tener": "to have", "hacer": "to do / make", "ir": "to go", "venir": "to come",
        "decir": "to say / tell", "hablar": "to speak", "querer": "to want / love",
        "poder": "to be able / can", "deber": "to must / owe", "saber": "to know (facts)",
        "conocer": "to know (people/places)", "ver": "to see", "mirar": "to look at",
        "dar": "to give", "poner": "to put", "salir": "to leave / go out",
        "llegar": "to arrive", "pasar": "to pass / happen", "volver": "to return",
        "quedar": "to remain / meet up", "creer": "to believe", "pensar": "to think",
        "sentir": "to feel", "dejar": "to leave / let", "seguir": "to follow / continue",
        "encontrar": "to find", "llamar": "to call", "llevar": "to carry / wear",
        "traer": "to bring", "buscar": "to search for", "existir": "to exist",
        "entrar": "to enter", "trabajar": "to work", "escribir": "to write",
        "leer": "to read", "escuchar": "to listen", "oir": "to hear",
        "comer": "to eat", "beber": "to drink", "vivir": "to live",
        "morir": "to die", "nacer": "to be born", "estudiar": "to study",
        "aprender": "to learn", "ensenar": "to teach / show", "entender": "to understand",
        "comprender": "to comprehend", "explicar": "to explain", "preguntar": "to ask",
        "contestar": "to answer", "responder": "to respond", "pedir": "to ask for / order",
        "recibir": "to receive", "enviar": "to send", "mandar": "to send / order",
        "abrir": "to open", "cerrar": "to close", "empezar": "to begin",
        "comenzar": "to commence", "terminar": "to finish", "acabar": "to end / just did",
        "ganar": "to win / earn", "perder": "to lose", "jugar": "to play",
        "correr": "to run", "caminar": "to walk", "andar": "to walk / go about",
        "subir": "to go up / upload", "bajar": "to go down / download",
        "caer": "to fall", "levantar": "to lift / raise", "sentar": "to seat",
        "dormir": "to sleep", "despertar": "to wake", "descansar": "to rest",
        "necesitar": "to need", "usar": "to use", "ayudar": "to help",
        "intentar": "to try / attempt", "tratar": "to try / treat", "lograr": "to achieve",
        "conseguir": "to obtain / manage to", "permitir": "to allow", "prohibir": "to forbid",
        "evitar": "to avoid", "recordar": "to remember", "olvidar": "to forget",
        "cambiar": "to change", "mejorar": "to improve", "empeorar": "to worsen",
        "avanzar": "to advance", "celebrar": "to celebrate", "continuar": "to continue",
        "crear": "to create", "construir": "to build", "romper": "to break",
        "arreglar": "to fix", "reparar": "to repair", "limpiar": "to clean",
        "lavar": "to wash", "cocinar": "to cook", "preparar": "to prepare",
        "comprar": "to buy", "vender": "to sell", "pagar": "to pay",
        "costar": "to cost", "gastar": "to spend", "ahorrar": "to save (money)",
        "prestar": "to lend", "devolver": "to return (something)",
        "viajar": "to travel", "conducir": "to drive", "manejar": "to drive / manage",
        "parar": "to stop", "esperar": "to wait / hope", "tardar": "to take time",
        "empujar": "to push", "tirar": "to throw / pull", "lanzar": "to launch / throw",
        "tocar": "to touch / play (music)", "cantar": "to sing", "bailar": "to dance",
        "reir": "to laugh", "llorar": "to cry", "sonreir": "to smile",
        "gritar": "to shout", "susurrar": "to whisper", "contar": "to count / tell",
        "mostrar": "to show", "demostrar": "to demonstrate", "indicar": "to indicate",
        "senalar": "to point out / signal", "significar": "to mean", "traducir": "to translate",
        "repetir": "to repeat", "practicar": "to practice",
        "analizar": "to analyze", "investigar": "to investigate", "revisar": "to review / check",
        "verificar": "to verify", "comprobar": "to check / confirm", "confirmar": "to confirm",
        "detectar": "to detect", "descubrir": "to discover", "revelar": "to reveal",
        "ocultar": "to hide", "esconder": "to hide (something)", "proteger": "to protect",
        "defender": "to defend", "atacar": "to attack", "amenazar": "to threaten",
        "robar": "to steal", "matar": "to kill", "herir": "to wound",
        "escapar": "to escape", "huir": "to flee", "perseguir": "to chase / pursue",
        "capturar": "to capture", "detener": "to detain / stop", "arrestar": "to arrest",
        "acusar": "to accuse", "culpar": "to blame", "mentir": "to lie",
        "enganar": "to deceive", "sospechar": "to suspect", "vigilar": "to watch / monitor",
        "controlar": "to control", "informar": "to report / inform", "avisar": "to warn / notify",
        "advertir": "to warn", "anunciar": "to announce", "publicar": "to publish",
        "declarar": "to declare", "negar": "to deny", "admitir": "to admit",
        "aceptar": "to accept", "rechazar": "to reject", "decidir": "to decide",
        "elegir": "to choose / elect", "votar": "to vote", "apoyar": "to support",
        "oponer": "to oppose", "discutir": "to argue / discuss", "debatir": "to debate",
        "acordar": "to agree", "prometer": "to promise", "cumplir": "to fulfill / turn (age)",
        "fallar": "to fail", "funcionar": "to function / work", "servir": "to serve",
        "producir": "to produce", "desarrollar": "to develop", "programar": "to program",
        "instalar": "to install", "configurar": "to configure", "conectar": "to connect",
        "desconectar": "to disconnect", "actualizar": "to update", "guardar": "to save / keep",
        "borrar": "to erase / delete", "eliminar": "to eliminate / delete", "copiar": "to copy",
        "pegar": "to paste / hit", "cortar": "to cut", "imprimir": "to print",
        "descargar": "to download", "cargar": "to load / charge", "compartir": "to share",
        "acceder": "to access", "bloquear": "to block", "hackear": "to hack",
        "cifrar": "to encrypt", "descifrar": "to decrypt / decipher", "filtrar": "to filter / leak",
        "marcar": "to mark / score / dial", "entrenar": "to train", "competir": "to compete",
        "empatar": "to tie (score)", "lesionar": "to injure", "sustituir": "to substitute",
        "abandonar": "to abandon", "regresar": "to go back", "quedarse": "to stay",
        "convertir": "to convert / turn into", "aparecer": "to appear", "desaparecer": "to disappear",
        "ocurrir": "to occur", "suceder": "to happen", "resultar": "to turn out",
        "parecer": "to seem", "imaginar": "to imagine", "sonar": "to dream / sound",
        "preferir": "to prefer", "gustar": "to be pleasing (like)", "encantar": "to delight (love)",
        "molestar": "to bother", "preocupar": "to worry", "asustar": "to scare",
        "sorprender": "to surprise", "interesar": "to interest", "importar": "to matter / import",
        "faltar": "to be missing / lack", "sobrar": "to be left over", "alcanzar": "to reach",
        "aumentar": "to increase", "reducir": "to reduce", "crecer": "to grow",
        "disminuir": "to decrease", "medir": "to measure", "pesar": "to weigh",
        "comparar": "to compare", "incluir": "to include", "excluir": "to exclude",
        "organizar": "to organize", "planear": "to plan", "dirigir": "to direct / lead",
        "liderar": "to lead", "gobernar": "to govern", "administrar": "to manage",
        "resolver": "to solve", "solucionar": "to solve / fix", "causar": "to cause",
        "provocar": "to provoke / cause", "afectar": "to affect", "depender": "to depend",
        "pertenecer": "to belong", "merecer": "to deserve", "sufrir": "to suffer",
        "soportar": "to endure / support", "aguantar": "to put up with",
    },
    "verb_forms": {
        "es": "is", "son": "are", "soy": "I am", "eres": "you are", "somos": "we are",
        "esta": "is (state) / this", "estan": "are (state)", "estoy": "I am (state)",
        "estamos": "we are (state)", "fue": "was / went", "fueron": "were / went",
        "era": "was (descr.)", "eran": "were (descr.)", "sido": "been",
        "hay": "there is / there are", "habia": "there was / were", "habra": "there will be",
        "ha": "has (aux.)", "han": "have (aux.)", "he": "I have (aux.)", "hemos": "we have (aux.)",
        "tiene": "has", "tienen": "have", "tengo": "I have", "tenemos": "we have",
        "tuvo": "had", "tenia": "had (ongoing)", "hace": "does / makes / ago",
        "hizo": "did / made", "hecho": "done / made / fact", "haciendo": "doing",
        "va": "goes", "van": "they go", "voy": "I go", "vamos": "we go / let's go",
        "iba": "was going", "ido": "gone", "yendo": "going",
        "puede": "can", "pueden": "they can", "puedo": "I can", "podemos": "we can",
        "pudo": "could / managed to", "podria": "could / would be able",
        "quiere": "wants", "quiero": "I want", "quieren": "they want", "quiso": "wanted",
        "dice": "says", "dicen": "they say", "digo": "I say", "dijo": "said",
        "dijeron": "they said", "dicho": "said (participle)", "diciendo": "saying",
        "sabe": "knows", "se": "I know / oneself", "sabemos": "we know", "supo": "found out",
        "veo": "I see", "ve": "sees", "ven": "they see / come", "vio": "saw",
        "visto": "seen", "viendo": "seeing", "da": "gives", "dio": "gave", "dado": "given",
        "viene": "comes", "vino": "came / wine", "puesto": "put / position",
        "sigue": "continues / follows", "siguio": "followed", "siendo": "being",
        "debe": "must / owes", "deben": "they must", "deberia": "should",
        "parece": "seems", "parecia": "seemed", "gusta": "is pleasing (like)",
        "gustan": "are pleasing", "encanta": "delights (love it)",
    },
    "people_family": {
        "hombre": "man", "mujer": "woman", "nino": "boy / child", "nina": "girl",
        "chico": "boy / guy", "chica": "girl", "joven": "young person", "adulto": "adult",
        "anciano": "elderly man", "bebe": "baby", "persona": "person", "gente": "people",
        "familia": "family", "padre": "father", "madre": "mother", "padres": "parents",
        "hijo": "son", "hija": "daughter", "hijos": "children / sons",
        "hermano": "brother", "hermana": "sister", "abuelo": "grandfather",
        "abuela": "grandmother", "tio": "uncle", "tia": "aunt", "primo": "cousin",
        "prima": "cousin (f.)", "sobrino": "nephew", "sobrina": "niece",
        "esposo": "husband", "esposa": "wife", "marido": "husband", "pareja": "partner / couple",
        "novio": "boyfriend", "novia": "girlfriend", "amigo": "friend", "amiga": "friend (f.)",
        "companero": "companion / coworker", "vecino": "neighbor", "vecina": "neighbor (f.)",
        "jefe": "boss", "jefa": "boss (f.)", "cliente": "client / customer",
        "analista": "analyst", "experto": "expert", "experta": "expert (f.)",
        "ingeniero": "engineer", "tecnico": "technician / technical",
        "trabajador": "worker / hard-working", "abogado": "lawyer",
        "duena": "owner (f.)", "dueno": "owner", "invitado": "guest",
        "extranjero": "foreigner / abroad", "ciudadano": "citizen", "senor": "sir / mister",
        "senora": "madam / missus", "senorita": "miss", "don": "sir (title)",
        "nombre": "name", "apellido": "last name", "edad": "age",
        "cumpleanos": "birthday", "boda": "wedding", "muerte": "death", "vida": "life",
    },
    "home_objects": {
        "casa": "house", "hogar": "home", "apartamento": "apartment", "piso": "flat / floor",
        "habitacion": "room / bedroom", "cuarto": "room / fourth", "sala": "living room",
        "cocina": "kitchen", "bano": "bathroom", "dormitorio": "bedroom",
        "puerta": "door", "ventana": "window", "pared": "wall", "techo": "roof / ceiling",
        "suelo": "floor / ground", "escalera": "stairs / ladder", "llave": "key",
        "mesa": "table", "silla": "chair", "sillon": "armchair", "sofa": "sofa",
        "cama": "bed", "almohada": "pillow", "manta": "blanket", "espejo": "mirror",
        "lampara": "lamp", "luz": "light", "reloj": "clock / watch",
        "televisor": "television set", "television": "television", "radio": "radio",
        "telefono": "telephone", "movil": "cell phone", "celular": "cell phone",
        "computadora": "computer", "ordenador": "computer (Spain)", "libro": "book",
        "revista": "magazine", "periodico": "newspaper", "papel": "paper",
        "boligrafo": "pen", "lapiz": "pencil", "cuaderno": "notebook",
        "mochila": "backpack", "bolsa": "bag", "bolsillo": "pocket", "cartera": "wallet",
        "ropa": "clothes", "camisa": "shirt", "camiseta": "t-shirt", "pantalon": "pants",
        "zapato": "shoe", "zapatos": "shoes", "abrigo": "coat", "chaqueta": "jacket",
        "vestido": "dress", "sombrero": "hat", "gafas": "glasses", "guante": "glove",
        "basura": "trash", "regalo": "gift", "juguete": "toy", "cosa": "thing",
        "objeto": "object", "herramienta": "tool", "maquina": "machine",
    },
    "city_travel": {
        "ciudad": "city", "pueblo": "town / people", "pais": "country", "mundo": "world",
        "calle": "street", "avenida": "avenue", "camino": "road / way", "carretera": "highway",
        "plaza": "square / plaza", "parque": "park", "edificio": "building",
        "oficina": "office", "tienda": "store", "mercado": "market",
        "supermercado": "supermarket", "banco": "bank / bench", "hospital": "hospital",
        "farmacia": "pharmacy", "iglesia": "church", "museo": "museum",
        "biblioteca": "library", "escuela": "school", "universidad": "university",
        "restaurante": "restaurant", "hotel": "hotel", "cine": "cinema",
        "teatro": "theater", "estadio": "stadium", "aeropuerto": "airport",
        "estacion": "station / season", "puerto": "port", "frontera": "border",
        "tren": "train", "autobus": "bus", "coche": "car", "carro": "car (LatAm)",
        "auto": "car", "taxi": "taxi", "metro": "subway", "avion": "airplane",
        "barco": "boat / ship", "bicicleta": "bicycle", "moto": "motorcycle",
        "viaje": "trip / journey", "maleta": "suitcase", "equipaje": "luggage",
        "pasaporte": "passport", "billete": "ticket / bill", "boleto": "ticket (LatAm)",
        "mapa": "map", "direccion": "address / direction", "esquina": "corner",
        "izquierda": "left", "derecha": "right", "recto": "straight ahead",
        "cerca": "near", "lejos": "far", "norte": "north", "sur": "south",
        "este": "east / this", "oeste": "west", "centro": "center / downtown",
        "lugar": "place", "sitio": "site / place", "zona": "zone / area",
    },
    "food_drink": {
        "comida": "food / meal", "desayuno": "breakfast", "almuerzo": "lunch",
        "cena": "dinner", "agua": "water", "cafe": "coffee", "te": "tea / you",
        "leche": "milk", "jugo": "juice", "zumo": "juice (Spain)", "cerveza": "beer",
        "vino": "wine / came", "refresco": "soft drink", "hielo": "ice",
        "pan": "bread", "queso": "cheese", "huevo": "egg", "mantequilla": "butter",
        "carne": "meat", "pollo": "chicken", "pescado": "fish (food)", "cerdo": "pork / pig",
        "arroz": "rice", "pasta": "pasta", "sopa": "soup", "ensalada": "salad",
        "verdura": "vegetable", "fruta": "fruit", "manzana": "apple", "naranja": "orange",
        "platano": "banana", "limon": "lemon", "tomate": "tomato", "papa": "potato / pope",
        "patata": "potato (Spain)", "cebolla": "onion", "ajo": "garlic",
        "sal": "salt", "azucar": "sugar", "aceite": "oil", "pimienta": "pepper",
        "salsa": "sauce", "postre": "dessert", "pastel": "cake", "helado": "ice cream",
        "chocolate": "chocolate", "galleta": "cookie", "cuchillo": "knife",
        "tenedor": "fork", "cuchara": "spoon", "plato": "plate / dish", "vaso": "glass (drinking)",
        "taza": "cup / mug", "botella": "bottle", "cuenta": "bill / account",
        "propina": "tip", "camarero": "waiter", "menu": "menu", "receta": "recipe / prescription",
        "sabor": "flavor", "hambre": "hunger", "sed": "thirst",
    },
    "body_health": {
        "cuerpo": "body", "cabeza": "head", "cara": "face", "ojo": "eye", "ojos": "eyes",
        "oreja": "ear", "oido": "ear (inner) / hearing", "nariz": "nose", "boca": "mouth",
        "diente": "tooth", "lengua": "tongue / language", "cuello": "neck",
        "hombro": "shoulder", "brazo": "arm", "mano": "hand", "dedo": "finger",
        "pecho": "chest", "espalda": "back", "estomago": "stomach", "pierna": "leg",
        "rodilla": "knee", "pie": "foot", "piel": "skin", "pelo": "hair",
        "cabello": "hair", "corazon": "heart", "sangre": "blood", "hueso": "bone",
        "cerebro": "brain", "voz": "voice", "salud": "health", "enfermedad": "illness",
        "enfermo": "sick", "sano": "healthy", "dolor": "pain", "fiebre": "fever",
        "gripe": "flu", "resfriado": "cold (illness)", "tos": "cough", "herida": "wound",
        "medico": "doctor", "doctora": "doctor (f.)", "enfermera": "nurse",
        "paciente": "patient", "medicina": "medicine", "pastilla": "pill",
        "vacuna": "vaccine", "cita": "appointment / date", "emergencia": "emergency",
        "ambulancia": "ambulance", "cansado": "tired", "fuerte": "strong", "debil": "weak",
    },
    "work_school": {
        "trabajo": "work / job", "empleo": "employment", "empresa": "company",
        "negocio": "business", "oficio": "trade / craft", "carrera": "career / race",
        "sueldo": "salary", "salario": "salary", "dinero": "money", "moneda": "coin / currency",
        "precio": "price", "costo": "cost", "coste": "cost (Spain)", "pago": "payment",
        "impuesto": "tax", "deuda": "debt", "cuenta": "account / bill",
        "reunion": "meeting", "proyecto": "project", "informe": "report",
        "documento": "document", "firma": "signature / firm", "contrato": "contract",
        "entrevista": "interview", "curriculum": "resume", "experiencia": "experience",
        "habilidad": "skill", "conocimiento": "knowledge", "escuela": "school",
        "colegio": "school (primary)", "instituto": "high school", "clase": "class",
        "curso": "course", "leccion": "lesson", "tarea": "homework / task",
        "examen": "exam", "prueba": "test / proof", "nota": "grade / note",
        "maestro": "teacher", "maestra": "teacher (f.)", "profesor": "professor",
        "profesora": "professor (f.)", "estudiante": "student", "alumno": "pupil",
        "idioma": "language", "palabra": "word", "frase": "phrase / sentence",
        "oracion": "sentence / prayer", "letra": "letter (alphabet) / lyrics",
        "pregunta": "question", "respuesta": "answer", "ejemplo": "example",
        "significado": "meaning", "traduccion": "translation", "gramatica": "grammar",
        "vocabulario": "vocabulary", "ejercicio": "exercise", "practica": "practice",
        "error": "error / mistake", "acierto": "correct answer / good call",
    },
    "technology_cyber": {
        "tecnologia": "technology", "sistema": "system", "red": "network / net",
        "internet": "internet", "sitio web": "website", "pagina": "page",
        "servidor": "server", "base de datos": "database", "datos": "data",
        "informacion": "information", "archivo": "file", "carpeta": "folder",
        "programa": "program", "aplicacion": "application / app", "software": "software",
        "hardware": "hardware", "codigo": "code", "contrasena": "password",
        "clave": "key / password", "usuario": "user", "cuenta": "account",
        "correo": "mail / email", "mensaje": "message", "pantalla": "screen",
        "teclado": "keyboard", "raton": "mouse (computer/animal)", "disco": "disk",
        "memoria": "memory", "seguridad": "security", "privacidad": "privacy",
        "amenaza": "threat", "ataque": "attack", "riesgo": "risk",
        "vulnerabilidad": "vulnerability", "virus": "virus", "malware": "malware",
        "phishing": "phishing", "estafa": "scam", "fraude": "fraud",
        "hacker": "hacker", "pirata": "pirate / hacker", "brecha": "breach / gap",
        "fuga": "leak / escape", "filtracion": "leak (of data)", "acceso": "access",
        "permiso": "permission", "alerta": "alert", "alertas": "alerts",
        "actividad": "activity", "incidente": "incident",
        "aviso": "notice / warning", "advertencia": "warning", "registro": "log / record / registry",
        "respaldo": "backup", "copia": "copy", "cifrado": "encryption / encrypted",
        "cortafuegos": "firewall", "herramienta": "tool", "fallo": "failure / bug",
        "error": "error", "actualizacion": "update", "version": "version",
        "dispositivo": "device", "equipo": "team / equipment", "maquina": "machine",
        "robot": "robot", "inteligencia": "intelligence", "artificial": "artificial",
    },
    "soccer_sports": {
        "futbol": "soccer", "deporte": "sport", "partido": "match / game / party (political)",
        "juego": "game", "equipo": "team", "jugador": "player", "jugadora": "player (f.)",
        "entrenador": "coach", "arbitro": "referee", "aficion": "fans / hobby",
        "aficionado": "fan", "hincha": "fan (LatAm)", "estadio": "stadium",
        "campo": "field / countryside", "cancha": "court / pitch (LatAm)",
        "pelota": "ball", "balon": "ball (large)", "gol": "goal (score)",
        "porteria": "goalposts", "portero": "goalkeeper / doorman", "arquero": "goalkeeper (LatAm)",
        "defensa": "defense / defender", "defensor": "defender", "delantero": "forward / striker",
        "centrocampista": "midfielder", "mediocampo": "midfield", "capitan": "captain",
        "suplente": "substitute", "banquillo": "bench", "falta": "foul / lack",
        "penalti": "penalty", "penal": "penalty (LatAm)", "tarjeta": "card",
        "amarilla": "yellow (card)", "roja": "red (card)", "fuera de juego": "offside",
        "saque": "kickoff / serve", "corner": "corner kick", "tiro": "shot",
        "pase": "pass", "remate": "finish / strike", "jugada": "play (move)",
        "marcador": "scoreboard / score", "resultado": "result / score",
        "parada": "save (goalkeeper) / stop",
        "victoria": "victory", "derrota": "defeat", "empate": "tie / draw",
        "liga": "league", "torneo": "tournament", "copa": "cup", "campeonato": "championship",
        "campeon": "champion", "temporada": "season (sports)", "clasificacion": "standings / qualification",
        "ascenso": "promotion", "descenso": "relegation", "rival": "rival / opponent",
        "lesion": "injury", "entrenamiento": "training", "vestuario": "locker room",
    },
    "news_politics": {
        "noticia": "news item", "noticias": "news", "prensa": "press",
        "medio": "medium / media outlet / half", "periodista": "journalist",
        "reportero": "reporter", "entrevista": "interview", "articulo": "article",
        "titular": "headline", "portada": "front page / cover", "fuente": "source / fountain",
        "declaracion": "statement", "rueda de prensa": "press conference",
        "gobierno": "government", "estado": "state", "nacion": "nation",
        "presidente": "president", "presidenta": "president (f.)", "ministro": "minister",
        "alcalde": "mayor", "senador": "senator", "diputado": "representative",
        "politico": "politician / political", "politica": "politics / policy",
        "eleccion": "election", "elecciones": "elections", "campana": "campaign / bell",
        "voto": "vote", "votante": "voter", "partido": "party (political) / match",
        "ley": "law", "derecho": "right / law (field)", "justicia": "justice",
        "tribunal": "court", "juez": "judge", "juicio": "trial / judgment",
        "congreso": "congress", "senado": "senate", "constitucion": "constitution",
        "reforma": "reform", "protesta": "protest", "manifestacion": "demonstration",
        "huelga": "strike (labor)", "crisis": "crisis", "escandalo": "scandal",
        "corrupcion": "corruption", "economia": "economy", "mercado": "market",
        "empleo": "employment", "desempleo": "unemployment", "inflacion": "inflation",
        "pobreza": "poverty", "riqueza": "wealth", "guerra": "war", "paz": "peace",
        "acuerdo": "agreement", "tratado": "treaty", "frontera": "border",
        "inmigracion": "immigration", "refugiado": "refugee", "sociedad": "society",
        "poblacion": "population", "comunidad": "community", "opinion": "opinion",
        "encuesta": "poll / survey", "debate": "debate", "discurso": "speech",
    },
    "crime_investigation": {
        "investigacion": "investigation", "caso": "case", "crimen": "crime",
        "delito": "offense / crime", "robo": "robbery / theft", "asesinato": "murder",
        "secuestro": "kidnapping", "amenaza": "threat", "victima": "victim",
        "sospechoso": "suspect", "sospechosa": "suspicious (f.) / suspect (f.)",
        "culpable": "guilty", "inocente": "innocent", "testigo": "witness",
        "testimonio": "testimony", "coartada": "alibi", "motivo": "motive / reason",
        "evidencia": "evidence", "prueba": "proof / test", "pista": "clue / track / runway",
        "huella": "fingerprint / footprint", "rastro": "trail / trace",
        "escena": "scene", "arma": "weapon", "pistola": "pistol", "cuchillo": "knife",
        "bala": "bullet", "policia": "police / police officer", "detective": "detective",
        "investigador": "investigator", "agente": "agent / officer", "espia": "spy",
        "informante": "informant", "comisaria": "police station", "carcel": "jail / prison",
        "prision": "prison", "celda": "cell", "condena": "sentence (legal)",
        "castigo": "punishment", "multa": "fine (penalty)", "fianza": "bail",
        "interrogatorio": "interrogation", "detencion": "arrest / detention",
        "busqueda": "search", "operacion": "operation", "mision": "mission",
        "objetivo": "objective / target", "plan": "plan", "estrategia": "strategy",
        "secreto": "secret", "misterio": "mystery", "peligro": "danger",
        "riesgo": "risk", "trampa": "trap", "engano": "deception",
        "mentira": "lie", "verdad": "truth", "silencio": "silence",
        "sombra": "shadow", "senal": "signal / sign", "codigo": "code",
    },
    "nature_weather": {
        "naturaleza": "nature", "tierra": "earth / land", "cielo": "sky / heaven",
        "sol": "sun", "luna": "moon", "estrella": "star", "nube": "cloud",
        "lluvia": "rain", "nieve": "snow", "viento": "wind", "tormenta": "storm",
        "trueno": "thunder", "relampago": "lightning", "niebla": "fog",
        "calor": "heat", "frio": "cold", "temperatura": "temperature",
        "clima": "climate / weather", "tiempo": "time / weather", "grado": "degree",
        "mar": "sea", "oceano": "ocean", "rio": "river", "lago": "lake",
        "playa": "beach", "isla": "island", "montana": "mountain", "colina": "hill",
        "valle": "valley", "bosque": "forest", "selva": "jungle", "desierto": "desert",
        "arbol": "tree", "flor": "flower", "planta": "plant / floor (building)",
        "hierba": "grass / herb", "hoja": "leaf / sheet", "piedra": "stone",
        "arena": "sand / arena", "fuego": "fire", "humo": "smoke", "aire": "air",
        "animal": "animal", "perro": "dog", "gato": "cat", "caballo": "horse",
        "vaca": "cow", "pajaro": "bird", "pez": "fish (live)", "insecto": "insect",
    },
    "time_calendar": {
        "tiempo": "time / weather", "momento": "moment", "instante": "instant",
        "hora": "hour / time", "minuto": "minute", "segundo": "second",
        "dia": "day", "noche": "night", "manana": "tomorrow / morning",
        "tarde": "afternoon / late", "mediodia": "noon", "medianoche": "midnight",
        "semana": "week", "mes": "month", "ano": "year", "siglo": "century",
        "fecha": "date (calendar)", "epoca": "era / period", "pasado": "past",
        "presente": "present", "futuro": "future", "hoy": "today", "ayer": "yesterday",
        "anoche": "last night", "lunes": "Monday", "martes": "Tuesday",
        "miercoles": "Wednesday", "jueves": "Thursday", "viernes": "Friday",
        "sabado": "Saturday", "domingo": "Sunday", "enero": "January",
        "febrero": "February", "marzo": "March", "abril": "April", "mayo": "May",
        "junio": "June", "julio": "July", "agosto": "August", "septiembre": "September",
        "octubre": "October", "noviembre": "November", "diciembre": "December",
        "primavera": "spring", "verano": "summer", "otono": "autumn", "invierno": "winter",
        "vez": "time (instance)", "veces": "times", "principio": "beginning / principle",
        "final": "end / final", "fin": "end", "inicio": "start",
    },
    "numbers": {
        "cero": "zero", "uno": "one", "dos": "two", "tres": "three", "cuatro": "four",
        "cinco": "five", "seis": "six", "siete": "seven", "ocho": "eight", "nueve": "nine",
        "diez": "ten", "once": "eleven", "doce": "twelve", "trece": "thirteen",
        "catorce": "fourteen", "quince": "fifteen", "veinte": "twenty",
        "treinta": "thirty", "cuarenta": "forty", "cincuenta": "fifty",
        "sesenta": "sixty", "setenta": "seventy", "ochenta": "eighty",
        "noventa": "ninety", "cien": "one hundred", "ciento": "hundred (compound)",
        "doscientos": "two hundred", "quinientos": "five hundred", "mil": "one thousand",
        "millon": "million", "mitad": "half", "doble": "double", "par": "pair / even",
        "primero": "first", "segundo": "second (ordinal/time)", "tercero": "third",
        "ultimo": "last", "numero": "number", "cifra": "figure / digit",
    },
    "adjectives": {
        "bueno": "good", "malo": "bad", "grande": "big / great", "pequeno": "small",
        "alto": "tall / high", "bajo": "short / low / under", "largo": "long",
        "corto": "short (length)", "ancho": "wide", "estrecho": "narrow",
        "nuevo": "new", "viejo": "old", "joven": "young", "antiguo": "ancient / former",
        "moderno": "modern", "rapido": "fast", "lento": "slow", "facil": "easy",
        "dificil": "difficult", "simple": "simple", "complicado": "complicated",
        "importante": "important", "necesario": "necessary", "posible": "possible",
        "imposible": "impossible", "seguro": "safe / sure", "peligroso": "dangerous",
        "cierto": "true / certain", "falso": "false", "verdadero": "true / real",
        "real": "real / royal", "claro": "clear / of course", "oscuro": "dark",
        "limpio": "clean", "sucio": "dirty", "lleno": "full", "vacio": "empty",
        "abierto": "open", "cerrado": "closed", "libre": "free", "ocupado": "busy / occupied",
        "caro": "expensive", "barato": "cheap", "rico": "rich / tasty", "pobre": "poor",
        "feliz": "happy", "triste": "sad", "contento": "glad", "enojado": "angry",
        "enfadado": "angry (Spain)", "nervioso": "nervous", "tranquilo": "calm",
        "preocupado": "worried", "asustado": "scared", "sorprendido": "surprised",
        "cansado": "tired", "aburrido": "boring / bored", "divertido": "fun",
        "interesante": "interesting", "extrano": "strange", "raro": "rare / weird",
        "normal": "normal", "comun": "common", "especial": "special",
        "diferente": "different", "igual": "equal / same", "similar": "similar",
        "propio": "own", "ajeno": "someone else's", "publico": "public",
        "privado": "private", "nacional": "national", "internacional": "international",
        "local": "local", "mundial": "world (adj.) / World Cup", "oficial": "official",
        "legal": "legal", "ilegal": "illegal", "justo": "fair / just", "injusto": "unfair",
        "fuerte": "strong", "debil": "weak", "duro": "hard / tough", "blando": "soft",
        "pesado": "heavy / annoying", "ligero": "light (weight)", "caliente": "hot",
        "frio": "cold", "templado": "mild / lukewarm", "mojado": "wet", "seco": "dry",
        "dulce": "sweet", "amargo": "bitter", "salado": "salty", "picante": "spicy",
        "hermoso": "beautiful", "bello": "beautiful", "bonito": "pretty", "guapo": "handsome",
        "feo": "ugly", "perfecto": "perfect", "terrible": "terrible", "horrible": "horrible",
        "increible": "incredible", "excelente": "excellent", "grave": "serious / grave",
        "serio": "serious", "urgente": "urgent", "principal": "main", "unico": "only / unique",
        "proximo": "next", "anterior": "previous", "siguiente": "following / next",
        "listo": "ready / clever", "capaz": "capable", "responsable": "responsible",
        "culpable": "guilty", "disponible": "available", "gratis": "free (cost)",
        "medio": "half / average", "entero": "whole", "completo": "complete",
        "mejor": "better / best", "peor": "worse / worst", "mayor": "older / bigger",
        "menor": "younger / smaller",
    },
    "adverbs_quantity": {
        "muy": "very", "mucho": "a lot / much", "poco": "little / few", "mas": "more",
        "menos": "less", "tanto": "so much", "tan": "so / as", "bastante": "quite / enough",
        "demasiado": "too much", "casi": "almost", "apenas": "barely / hardly",
        "solo": "only / alone", "solamente": "only", "bien": "well", "mal": "badly",
        "mejor": "better", "peor": "worse", "asi": "like this / so",
        "siempre": "always", "nunca": "never", "jamas": "never (emphatic)",
        "todavia": "still / yet", "aun": "still / even", "ya": "already / now",
        "ahora": "now", "luego": "later / then", "despues": "after / later",
        "antes": "before", "pronto": "soon", "tarde": "late", "temprano": "early",
        "hoy": "today", "ayer": "yesterday", "aqui": "here", "aca": "here (LatAm)",
        "alli": "there", "alla": "over there", "ahi": "there (near you)",
        "cerca": "nearby", "lejos": "far away", "dentro": "inside", "fuera": "outside",
        "adentro": "inside (LatAm)", "afuera": "outside (LatAm)", "arriba": "up / upstairs",
        "abajo": "down / downstairs", "adelante": "forward", "atras": "behind / back",
        "encima": "on top", "debajo": "underneath", "delante": "in front",
        "detras": "behind", "alrededor": "around", "enfrente": "across / facing",
        "quizas": "maybe", "quiza": "maybe", "tal vez": "perhaps",
        "seguramente": "surely", "probablemente": "probably", "realmente": "really",
        "verdaderamente": "truly", "exactamente": "exactly", "claramente": "clearly",
        "rapidamente": "quickly", "lentamente": "slowly", "facilmente": "easily",
        "finalmente": "finally", "generalmente": "generally", "normalmente": "normally",
        "especialmente": "especially", "principalmente": "mainly", "inmediatamente": "immediately",
        "actualmente": "currently (NOT actually)", "entonces": "then / so",
        "tambien": "also", "tampoco": "neither / not either", "incluso": "even / including",
        "ademas": "besides / in addition", "sobre todo": "above all",
    },
    "conversation": {
        "hola": "hello", "adios": "goodbye", "gracias": "thank you",
        "perdon": "excuse me / sorry", "disculpe": "excuse me (formal)",
        "favor": "favor", "ayuda": "help", "socorro": "help! (emergency)",
        "bienvenido": "welcome", "salud": "health / cheers / bless you",
        "suerte": "luck", "cuidado": "care / watch out", "atencion": "attention",
        "vale": "okay (Spain)", "bueno": "good / well...", "claro": "of course",
        "verdad": "truth / right?", "mentira": "lie / no way", "genial": "great",
        "estupendo": "wonderful", "perfecto": "perfect", "exacto": "exactly",
        "correcto": "correct", "incorrecto": "incorrect", "depende": "it depends",
        "nada": "nothing / you're welcome (de nada)", "mucho gusto": "nice to meet you",
        "encantado": "delighted (to meet you)", "igualmente": "likewise",
        "saludos": "greetings / regards", "abrazo": "hug", "beso": "kiss",
        "felicidades": "congratulations", "enhorabuena": "congratulations (Spain)",
        "ojala": "hopefully / I wish", "dios": "god", "hombre": "man / dude (interjection)",
        "oye": "hey / listen", "mira": "look", "vaya": "wow / well",
        "anda": "come on / no way", "venga": "come on (Spain)", "dale": "go ahead (LatAm)",
    },
    "abstract": {
        "idea": "idea", "pensamiento": "thought", "razon": "reason / right",
        "causa": "cause", "efecto": "effect", "consecuencia": "consequence",
        "resultado": "result", "problema": "problem", "solucion": "solution",
        "cuestion": "issue / matter", "asunto": "matter / affair", "tema": "topic / theme",
        "detalle": "detail", "aspecto": "aspect", "punto": "point / dot",
        "parte": "part", "resto": "rest / remainder", "conjunto": "set / whole",
        "grupo": "group", "tipo": "type / guy", "clase": "kind / class",
        "forma": "form / way / shape", "manera": "way / manner", "modo": "way / mode",
        "nivel": "level", "grado": "degree / grade", "cantidad": "quantity",
        "calidad": "quality", "valor": "value / courage", "importancia": "importance",
        "interes": "interest", "sentido": "sense / meaning / direction",
        "proposito": "purpose", "intencion": "intention", "meta": "goal (aim)",
        "exito": "success (NOT exit)", "fracaso": "failure", "logro": "achievement",
        "esfuerzo": "effort", "intento": "attempt", "oportunidad": "opportunity",
        "posibilidad": "possibility", "opcion": "option", "eleccion": "choice / election",
        "decision": "decision", "cambio": "change", "diferencia": "difference",
        "ventaja": "advantage", "desventaja": "disadvantage", "beneficio": "benefit",
        "dano": "damage / harm", "perdida": "loss", "ganancia": "gain / profit",
        "aumento": "increase", "reduccion": "reduction", "desarrollo": "development",
        "crecimiento": "growth", "progreso": "progress", "avance": "advance",
        "historia": "history / story", "cuento": "short story / tale", "memoria": "memory",
        "recuerdo": "memory (a) / souvenir", "sueno": "dream / sleep", "esperanza": "hope",
        "miedo": "fear", "amor": "love", "odio": "hate", "alegria": "joy",
        "tristeza": "sadness", "sorpresa": "surprise", "confianza": "trust / confidence",
        "duda": "doubt", "certeza": "certainty", "libertad": "freedom",
        "poder": "power / to be able", "fuerza": "force / strength", "energia": "energy",
        "paciencia": "patience", "cultura": "culture", "arte": "art",
        "musica": "music", "cancion": "song", "pelicula": "movie", "serie": "series",
        "personaje": "character (fiction)", "actor": "actor", "actriz": "actress",
        "escena": "scene", "capitulo": "chapter / episode", "subtitulo": "subtitle",
    },
}

# The merged flat dictionary. Later categories do not overwrite earlier
# entries, so put the most useful gloss first when a word repeats.
LEXICON: dict[str, str] = {}
for _category_terms in CATEGORIES.values():
    for _term, _gloss in _category_terms.items():
        LEXICON.setdefault(_term, _gloss)

# Multi-word phrases checked before single-word lookup.
PHRASES: dict[str, str] = {
    # Courtesy and conversation
    "por favor": "please",
    "buenos dias": "good morning",
    "buenas tardes": "good afternoon",
    "buenas noches": "good evening / night",
    "me llamo": "my name is",
    "como te llamas": "what is your name",
    "mucho gusto": "nice to meet you",
    "encantado de conocerte": "pleased to meet you",
    "hasta luego": "see you later",
    "hasta manana": "see you tomorrow",
    "hasta pronto": "see you soon",
    "nos vemos": "see you",
    "de nada": "you're welcome",
    "no hay de que": "don't mention it",
    "lo siento": "I'm sorry",
    "con permiso": "excuse me (passing)",
    "que tal": "how's it going",
    "como estas": "how are you",
    "como esta usted": "how are you (formal)",
    "muy bien": "very well",
    "mas o menos": "more or less / so-so",
    "que pasa": "what's happening",
    "que hora es": "what time is it",
    "no entiendo": "I don't understand",
    "no lo se": "I don't know",
    "puede repetir": "can you repeat",
    "mas despacio": "more slowly",
    "que significa": "what does it mean",
    "como se dice": "how do you say",
    "tengo hambre": "I am hungry",
    "tengo sed": "I am thirsty",
    "tengo prisa": "I am in a hurry",
    "tengo miedo": "I am afraid",
    "tengo razon": "I am right",
    "tengo suerte": "I am lucky",
    "tener ganas de": "to feel like (doing)",
    "tener que": "to have to",
    "hay que": "one must / you have to",
    "acabar de": "to have just (done)",
    "estar a punto de": "to be about to",
    "ir a": "to be going to",
    "volver a": "to do again",
    "dejar de": "to stop (doing)",
    "tratar de": "to try to",
    "darse cuenta": "to realize",
    "llevar a cabo": "to carry out",
    "echar de menos": "to miss (someone)",
    "hacer falta": "to be needed",
    "valer la pena": "to be worth it",
    "tomar el pelo": "to pull someone's leg",
    "meter la pata": "to put your foot in it",
    "estar de acuerdo": "to agree",
    "ponerse de acuerdo": "to come to an agreement",
    # Location and direction
    "donde esta": "where is",
    "cuanto cuesta": "how much does it cost",
    "a la izquierda": "to the left",
    "a la derecha": "to the right",
    "todo recto": "straight ahead",
    "al lado de": "next to",
    "cerca de": "near to",
    "lejos de": "far from",
    "delante de": "in front of",
    "detras de": "behind",
    "encima de": "on top of",
    "debajo de": "underneath",
    "dentro de": "inside / within",
    "fuera de": "outside of",
    "en frente de": "across from",
    "alrededor de": "around",
    "a traves de": "through / across",
    "junto a": "next to",
    # Connectors and discourse
    "sin embargo": "however",
    "no obstante": "nevertheless",
    "por eso": "that's why",
    "por lo tanto": "therefore",
    "asi que": "so / therefore",
    "ya que": "since / given that",
    "puesto que": "given that",
    "debido a": "due to",
    "gracias a": "thanks to",
    "a causa de": "because of",
    "a pesar de": "despite",
    "en cambio": "on the other hand",
    "por otro lado": "on the other hand",
    "por un lado": "on one hand",
    "en primer lugar": "in the first place",
    "por ultimo": "lastly",
    "por fin": "finally / at last",
    "al final": "in the end",
    "al principio": "at the beginning",
    "de repente": "suddenly",
    "de pronto": "suddenly",
    "poco a poco": "little by little",
    "paso a paso": "step by step",
    "de vez en cuando": "from time to time",
    "a veces": "sometimes",
    "a menudo": "often",
    "casi nunca": "almost never",
    "todos los dias": "every day",
    "cada vez": "each time",
    "cada vez mas": "more and more",
    "una vez": "once",
    "otra vez": "again",
    "de nuevo": "again",
    "en seguida": "right away",
    "ahora mismo": "right now",
    "hoy en dia": "nowadays",
    "hace poco": "a little while ago",
    "dentro de poco": "shortly",
    "a tiempo": "on time",
    "a la vez": "at the same time",
    "mientras tanto": "meanwhile",
    "en cuanto": "as soon as",
    "tan pronto como": "as soon as",
    "por supuesto": "of course",
    "desde luego": "of course",
    "claro que si": "of course",
    "en realidad": "actually",
    "de verdad": "really / truly",
    "de hecho": "in fact",
    "por ejemplo": "for example",
    "es decir": "that is to say",
    "o sea": "in other words",
    "en general": "in general",
    "sobre todo": "above all",
    "por lo menos": "at least",
    "al menos": "at least",
    "como minimo": "at minimum",
    "mas bien": "rather",
    "en vez de": "instead of",
    "en lugar de": "instead of",
    "ademas de": "in addition to",
    "aparte de": "apart from",
    "acerca de": "about / regarding",
    "en cuanto a": "as for / regarding",
    "segun parece": "apparently",
    "por si acaso": "just in case",
    "de todos modos": "anyway",
    "de todas formas": "in any case",
    "en serio": "seriously",
    "en broma": "jokingly",
    "por que": "why",
    "porque si": "just because",
    "que va": "no way",
    "ni hablar": "no way / out of the question",
    "vale la pena": "it's worth it",
    "no importa": "it doesn't matter",
    "da igual": "it makes no difference",
    "menos mal": "thank goodness",
    "ojo con": "watch out for",
    # Domain phrases
    "sitio web": "website",
    "base de datos": "database",
    "correo electronico": "email",
    "red social": "social network",
    "copia de seguridad": "backup",
    "fuga de datos": "data leak",
    "fuerza bruta": "brute force",
    "doble factor": "two-factor",
    "fuera de juego": "offside",
    "tiro libre": "free kick",
    "saque de esquina": "corner kick",
    "tiempo extra": "extra time",
    "medio tiempo": "halftime",
    "rueda de prensa": "press conference",
    "opinion publica": "public opinion",
    "derechos humanos": "human rights",
    "estado de derecho": "rule of law",
    "toma de decisiones": "decision-making",
    "punto de vista": "point of view",
    "obra de teatro": "play (theater)",
    "fin de semana": "weekend",
    "hora punta": "rush hour",
    "sala de espera": "waiting room",
    "primeros auxilios": "first aid",
    "seguro medico": "health insurance",
}

# Conjugated verb forms derived from the lexicon at first use.
_DERIVED: dict[str, str] = {}
_DERIVED_BUILT = False


def derived_forms() -> dict[str, str]:
    """Conjugation glosses for every verb in the lexicon (built lazily).

    Hovering 'analizaron' resolves to 'to analyze [analizar · preterite]'.
    Imported inside the function to avoid a circular import with the
    conjugator, which uses lookup() for translations.
    """
    global _DERIVED_BUILT
    if _DERIVED_BUILT:
        return _DERIVED

    from feintlex.services.conjugator import conjugate, is_infinitive

    for term, gloss in LEXICON.items():
        if " " in term or not gloss.startswith("to ") or not is_infinitive(term):
            continue
        table = conjugate(term)
        if not table:
            continue
        for tense, rows in table["tenses"].items():
            for row in rows:
                form = normalize_term(row["form"])
                if not form or form in LEXICON or form in PHRASES or form in _DERIVED:
                    continue
                _DERIVED[form] = f"{gloss} [{term} · {tense}]"
    _DERIVED_BUILT = True
    return _DERIVED


def _lookup_word(normalized: str) -> str | None:
    """Single-word lookup with the full fallback chain.

    Order matters: hand-curated entries (including their plural and
    feminine variants) outrank auto-derived verb forms, so 'amenazas'
    resolves to the noun 'threat' rather than the tú-form of amenazar.
    """
    if not normalized:
        return None
    if normalized in LEXICON:
        return LEXICON[normalized]
    # Plural fallback: alertas -> alerta, ciudades -> ciudad.
    if normalized.endswith("es") and len(normalized) > 4 and normalized[:-2] in LEXICON:
        return LEXICON[normalized[:-2]]
    if normalized.endswith("s") and len(normalized) > 3 and normalized[:-1] in LEXICON:
        return LEXICON[normalized[:-1]]
    # Feminine adjective fallback: nueva -> nuevo, cansadas -> cansado.
    if normalized.endswith("a") and len(normalized) > 3 and normalized[:-1] + "o" in LEXICON:
        return LEXICON[normalized[:-1] + "o"]
    if normalized.endswith("as") and len(normalized) > 4 and normalized[:-2] + "o" in LEXICON:
        return LEXICON[normalized[:-2] + "o"]
    # Auto-derived conjugated verb forms.
    derived = derived_forms()
    if normalized in derived:
        return derived[normalized]
    if normalized.endswith("s") and len(normalized) > 3 and normalized[:-1] in derived:
        return derived[normalized[:-1]]
    return None


def lookup(term: str) -> str | None:
    """Return the English gloss for a Spanish term or phrase, if known."""
    cleaned = " ".join(term.strip().split())
    if not cleaned:
        return None
    normalized_phrase = " ".join(normalize_term(token) for token in tokenize(cleaned))
    if normalized_phrase in PHRASES:
        return PHRASES[normalized_phrase]
    return _lookup_word(normalized_phrase) or _lookup_word(normalize_term(cleaned))


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
        gloss = _lookup_word(normalize_term(token))
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


def library_stats() -> dict[str, int]:
    return {
        "terms": len(LEXICON),
        "phrases": len(PHRASES),
        "derived_forms": len(derived_forms()),
        "categories": len(CATEGORIES),
    }
