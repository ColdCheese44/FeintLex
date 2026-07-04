const state = {
  activeLesson: null,
  latestLessons: [],
  vocabulary: [],
  reviewQueue: [],
  reviewIndex: 0,
  reviewRevealed: false,
  progressSummary: null,
  listen: {
    mode: "meaning",
    rate: 0.9,
    item: null,
    picked: null,
    checked: false,
    seen: 0,
    right: 0,
    streak: 0,
  },
  method: {
    plan: null,
    index: 0,
    results: {},
    revealed: false,
    countdown: 0,
    built: [],
    checked: false,
    lastCorrect: null,
    finished: false,
    reported: false,
  },
  tutor: {
    activeTab: "decks",
    selectedDeckId: "contact",
    studyIndex: 0,
    flashFlipped: false,
    mastery: {},
    drillScope: "all",
    drill: null,
    drillPicked: null,
    drillSeen: 0,
    drillRight: 0,
    drillStreak: 0,
    coachMessages: [],
  },
};

const $ = (id) => document.getElementById(id);
const TUTOR_STORAGE_KEY = "feintlex:tutor:mastery";
const TUTOR_MAX_SIGNAL = 5;

const TUTOR_DECKS = [
  {
    id: "contact",
    tag: "01",
    name: "Contact",
    sub: "Greetings and essentials",
    terms: [
      { es: "hola", en: "hello", note: "Basic greeting.", xes: "Hola, como estas?", xen: "Hi, how are you?" },
      { es: "buenos dias", en: "good morning", note: "Used until midday.", xes: "Buenos dias, senor.", xen: "Good morning, sir." },
      { es: "por favor", en: "please", note: "Use with requests.", xes: "Un cafe, por favor.", xen: "A coffee, please." },
      { es: "gracias", en: "thank you", note: "Core courtesy signal.", xes: "Gracias por tu ayuda.", xen: "Thank you for your help." },
      { es: "perdon", en: "excuse me / sorry", note: "Attention or apology.", xes: "Perdon, donde esta el bano?", xen: "Excuse me, where is the bathroom?" },
      { es: "me llamo", en: "my name is", note: "Literal: I call myself.", xes: "Me llamo Brendan.", xen: "My name is Brendan." },
      { es: "mucho gusto", en: "nice to meet you", note: "First contact phrase.", xes: "Mucho gusto, soy Carlos.", xen: "Nice to meet you, I am Carlos." },
      { es: "hasta luego", en: "see you later", note: "Common farewell.", xes: "Hasta luego, amigo.", xen: "See you later, friend." },
    ],
  },
  {
    id: "numbers",
    tag: "02",
    name: "Numerals",
    sub: "Counting and quantities",
    terms: [
      { es: "cero", en: "zero", note: "", xes: "Cero errores.", xen: "Zero errors." },
      { es: "uno", en: "one", note: "Becomes un/una before nouns.", xes: "Tengo un mensaje.", xen: "I have one message." },
      { es: "dos", en: "two", note: "", xes: "Dos cafes, por favor.", xen: "Two coffees, please." },
      { es: "cinco", en: "five", note: "", xes: "Son las cinco.", xen: "It is five o'clock." },
      { es: "diez", en: "ten", note: "", xes: "Diez minutos.", xen: "Ten minutes." },
      { es: "quince", en: "fifteen", note: "", xes: "Quince alertas.", xen: "Fifteen alerts." },
      { es: "treinta", en: "thirty", note: "", xes: "Treinta segundos.", xen: "Thirty seconds." },
      { es: "cien", en: "one hundred", note: "Ciento before smaller numbers.", xes: "Cien por ciento.", xen: "One hundred percent." },
    ],
  },
  {
    id: "sustenance",
    tag: "03",
    name: "Sustenance",
    sub: "Food and ordering",
    terms: [
      { es: "el agua", en: "water", note: "Feminine noun with el.", xes: "Un vaso de agua, por favor.", xen: "A glass of water, please." },
      { es: "el cafe", en: "coffee", note: "", xes: "Quiero un cafe.", xen: "I want a coffee." },
      { es: "el pan", en: "bread", note: "", xes: "El pan esta caliente.", xen: "The bread is warm." },
      { es: "la cuenta", en: "the check / bill", note: "", xes: "La cuenta, por favor.", xen: "The check, please." },
      { es: "tengo hambre", en: "I am hungry", note: "Literal: I have hunger.", xes: "Tengo mucha hambre.", xen: "I am very hungry." },
      { es: "tengo sed", en: "I am thirsty", note: "Literal: I have thirst.", xes: "Tengo sed despues del partido.", xen: "I am thirsty after the game." },
      { es: "que recomienda", en: "what do you recommend", note: "Useful restaurant question.", xes: "Que recomienda?", xen: "What do you recommend?" },
      { es: "sin picante", en: "not spicy", note: "Ordering constraint.", xes: "Sin picante, por favor.", xen: "Not spicy, please." },
    ],
  },
  {
    id: "movement",
    tag: "04",
    name: "Movement",
    sub: "Travel and directions",
    terms: [
      { es: "donde esta", en: "where is", note: "Location question.", xes: "Donde esta la estacion?", xen: "Where is the station?" },
      { es: "izquierda", en: "left", note: "", xes: "A la izquierda.", xen: "To the left." },
      { es: "derecha", en: "right", note: "", xes: "A la derecha.", xen: "To the right." },
      { es: "recto", en: "straight ahead", note: "", xes: "Siga recto.", xen: "Go straight." },
      { es: "cerca", en: "near", note: "", xes: "Esta cerca.", xen: "It is nearby." },
      { es: "lejos", en: "far", note: "", xes: "Esta lejos.", xen: "It is far away." },
      { es: "el mapa", en: "the map", note: "Masculine despite -a.", xes: "Necesito el mapa.", xen: "I need the map." },
      { es: "cuanto cuesta", en: "how much does it cost", note: "Buying tickets or food.", xes: "Cuanto cuesta el billete?", xen: "How much is the ticket?" },
    ],
  },
  {
    id: "timeline",
    tag: "05",
    name: "Timeline",
    sub: "Days and time",
    terms: [
      { es: "hoy", en: "today", note: "", xes: "Hoy trabajo.", xen: "Today I work." },
      { es: "manana", en: "tomorrow / morning", note: "Context decides.", xes: "Hasta manana.", xen: "See you tomorrow." },
      { es: "ayer", en: "yesterday", note: "", xes: "Ayer estudie.", xen: "Yesterday I studied." },
      { es: "ahora", en: "now", note: "", xes: "Ahora no puedo.", xen: "I cannot right now." },
      { es: "la semana", en: "the week", note: "", xes: "Esta semana practico.", xen: "This week I practice." },
      { es: "el dia", en: "the day", note: "Masculine despite -a.", xes: "El dia es largo.", xen: "The day is long." },
      { es: "que hora es", en: "what time is it", note: "", xes: "Que hora es?", xen: "What time is it?" },
      { es: "despues", en: "after / later", note: "Sequence connector.", xes: "Despues, escribo un informe.", xen: "Afterward, I write a report." },
    ],
  },
  {
    id: "verbs",
    tag: "06",
    name: "Core Verbs",
    sub: "Present-tense operating verbs",
    terms: [
      { es: "ser", en: "to be, identity", note: "soy / eres / es", xes: "Soy analista.", xen: "I am an analyst." },
      { es: "estar", en: "to be, state/place", note: "estoy / estas / esta", xes: "Estoy cansado.", xen: "I am tired." },
      { es: "tener", en: "to have", note: "tengo / tienes / tiene", xes: "Tengo tiempo.", xen: "I have time." },
      { es: "hacer", en: "to do / make", note: "hago / haces / hace", xes: "Que haces?", xen: "What are you doing?" },
      { es: "ir", en: "to go", note: "voy / vas / va", xes: "Voy al trabajo.", xen: "I am going to work." },
      { es: "querer", en: "to want", note: "quiero / quieres / quiere", xes: "Quiero aprender.", xen: "I want to learn." },
      { es: "poder", en: "can / to be able", note: "puedo / puedes / puede", xes: "Puedes ayudarme?", xen: "Can you help me?" },
      { es: "entender", en: "to understand", note: "entiendo / entiendes / entiende", xes: "No entiendo.", xen: "I do not understand." },
    ],
  },
  {
    id: "core1",
    tag: "07",
    name: "Core Signal I",
    sub: "Top-frequency verbs and nouns",
    terms: [
      { es: "decir", en: "to say / tell", note: "digo / dices / dice", xes: "El testigo dice la verdad.", xen: "The witness tells the truth." },
      { es: "saber", en: "to know (facts)", note: "sé / sabes / sabe", xes: "No sé la respuesta.", xen: "I do not know the answer." },
      { es: "ver", en: "to see", note: "veo / ves / ve", xes: "Veo el problema.", xen: "I see the problem." },
      { es: "dar", en: "to give", note: "doy / das / da", xes: "Dame un ejemplo.", xen: "Give me an example." },
      { es: "la vida", en: "life", note: "", xes: "La vida es corta.", xen: "Life is short." },
      { es: "el tiempo", en: "time / weather", note: "Context decides.", xes: "No tengo tiempo.", xen: "I do not have time." },
      { es: "la cosa", en: "thing", note: "", xes: "Es una cosa importante.", xen: "It is an important thing." },
      { es: "el mundo", en: "world", note: "", xes: "Todo el mundo lo sabe.", xen: "Everybody knows it." },
      { es: "la gente", en: "people", note: "Singular in Spanish.", xes: "La gente habla mucho.", xen: "People talk a lot." },
      { es: "el trabajo", en: "work / job", note: "", xes: "El trabajo es dificil.", xen: "The work is difficult." },
    ],
  },
  {
    id: "core2",
    tag: "08",
    name: "Core Signal II",
    sub: "High-frequency operating verbs",
    terms: [
      { es: "pensar", en: "to think", note: "pienso / piensas / piensa", xes: "Pienso en el caso.", xen: "I think about the case." },
      { es: "creer", en: "to believe", note: "creo / crees / cree", xes: "Creo que es verdad.", xen: "I believe it is true." },
      { es: "hablar", en: "to speak", note: "hablo / hablas / habla", xes: "Hablamos con el analista.", xen: "We speak with the analyst." },
      { es: "encontrar", en: "to find", note: "encuentro / encuentras", xes: "Encontramos la evidencia.", xen: "We found the evidence." },
      { es: "dejar", en: "to leave / let", note: "", xes: "Deja el archivo aqui.", xen: "Leave the file here." },
      { es: "seguir", en: "to follow / continue", note: "sigo / sigues / sigue", xes: "Sigue la pista.", xen: "Follow the clue." },
      { es: "llevar", en: "to carry / take", note: "", xes: "Llevo el informe.", xen: "I carry the report." },
      { es: "la parte", en: "part", note: "", xes: "Es parte del plan.", xen: "It is part of the plan." },
      { es: "el lugar", en: "place", note: "", xes: "Es un lugar seguro.", xen: "It is a safe place." },
      { es: "la palabra", en: "word", note: "", xes: "Una palabra nueva cada dia.", xen: "One new word every day." },
    ],
  },
  {
    id: "core3",
    tag: "09",
    name: "Core Signal III",
    sub: "Describers and quantity words",
    terms: [
      { es: "nuevo", en: "new", note: "nuevo / nueva", xes: "Hay un mensaje nuevo.", xen: "There is a new message." },
      { es: "grande", en: "big / great", note: "", xes: "Es un riesgo grande.", xen: "It is a big risk." },
      { es: "importante", en: "important", note: "", xes: "La fuente es importante.", xen: "The source is important." },
      { es: "mejor", en: "better / best", note: "", xes: "Es la mejor opcion.", xen: "It is the best option." },
      { es: "siempre", en: "always", note: "", xes: "Siempre revisa los datos.", xen: "Always check the data." },
      { es: "nunca", en: "never", note: "", xes: "Nunca abras ese correo.", xen: "Never open that email." },
      { es: "todo", en: "all / everything", note: "todo / toda / todos", xes: "Todo esta bajo control.", xen: "Everything is under control." },
      { es: "nada", en: "nothing", note: "Double negative is correct.", xes: "No veo nada raro.", xen: "I see nothing strange." },
      { es: "algo", en: "something", note: "", xes: "Algo no funciona.", xen: "Something does not work." },
      { es: "alguien", en: "someone", note: "", xes: "Alguien entro al sistema.", xen: "Someone entered the system." },
    ],
  },
  {
    id: "operators",
    tag: "10",
    name: "Operators",
    sub: "Connectors that reveal sentence logic",
    terms: [
      { es: "porque", en: "because", note: "Cause.", xes: "Fallo porque nadie reviso el codigo.", xen: "It failed because nobody reviewed the code." },
      { es: "pero", en: "but", note: "Contrast.", xes: "Es dificil pero posible.", xen: "It is difficult but possible." },
      { es: "aunque", en: "although", note: "Concession.", xes: "Aunque llueve, jugamos.", xen: "Although it rains, we play." },
      { es: "mientras", en: "while", note: "Time / contrast.", xes: "Mientras leo, tomo notas.", xen: "While I read, I take notes." },
      { es: "sin embargo", en: "however", note: "Formal contrast.", xes: "Sin embargo, el riesgo continua.", xen: "However, the risk continues." },
      { es: "ademas", en: "besides / in addition", note: "Addition.", xes: "Ademas, hay otra alerta.", xen: "In addition, there is another alert." },
      { es: "entonces", en: "then / so", note: "Sequence / result.", xes: "Entonces, cual es el plan?", xen: "So, what is the plan?" },
      { es: "por eso", en: "that's why", note: "Result.", xes: "Por eso estudio cada dia.", xen: "That is why I study every day." },
      { es: "ya que", en: "since / given that", note: "Cause (formal).", xes: "Ya que estas aqui, ayudame.", xen: "Since you are here, help me." },
      { es: "asi que", en: "so / therefore", note: "Result (informal).", xes: "Asi que decidimos esperar.", xen: "So we decided to wait." },
    ],
  },
];

TUTOR_DECKS.forEach((deck) => deck.terms.forEach((term, index) => (term.id = `${deck.id}:${index}`)));
const TUTOR_ALL_TERMS = TUTOR_DECKS.flatMap((deck) => deck.terms.map((term) => ({ ...term, deck: deck.id })));

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Keep the HTTP detail if the response is not JSON.
    }
    throw new Error(detail);
  }
  return response.json();
}

function setStatus(message, isError = false) {
  const node = $("workStatus");
  node.textContent = message;
  node.style.color = isError ? "var(--red)" : "var(--muted)";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getTopicTags() {
  const selected = [...document.querySelectorAll('input[name="topic"]:checked')].map((input) => input.value);
  const extras = $("extraTags")
    .value.split(",")
    .map((tag) => tag.trim().toLowerCase())
    .filter(Boolean);
  return [...new Set([...selected, ...extras])];
}

function renderHealth(payload) {
  $("healthStatus").textContent = payload.app ? "Online" : "Unknown";
  $("healthStatus").classList.toggle("alert", payload.database_status !== "ok");
  $("dbStatus").textContent = `DB ${payload.database_status || "unknown"}`;
  $("envStatus").textContent = payload.environment || "local";
}

function renderLesson(lesson) {
  state.activeLesson = lesson;
  $("exportLessonButton").disabled = !lesson?.id;
  renderWritingPrompt();

  if (!lesson) {
    $("lessonOutput").className = "lesson-output empty-state gloss-zone";
    $("lessonOutput").innerHTML =
      "<h3>No mission brief yet</h3><p>Paste Spanish text into Source Intake — or hit <strong>Sample Intel</strong> for an instant transmission. HQ will build the full brief: summary, vocabulary, grammar, autopsy targets, and a writing prompt.</p>";
    return;
  }

  const vocab = (lesson.key_vocabulary || [])
    .slice(0, 18)
    .map((item) => `<span class="chip"><strong>${escapeHtml(item.term)}</strong> ${escapeHtml(item.frequency)}</span>`)
    .join("");
  const grammar = (lesson.grammar_points || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const questions = (lesson.comprehension_questions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const sentences = (lesson.sentence_breakdown_candidates || [])
    .map(
      (sentence) =>
        `<button class="sentence-button" type="button" data-sentence="${escapeHtml(sentence)}">${escapeHtml(sentence)}</button>`,
    )
    .join("");

  $("lessonOutput").className = "lesson-output gloss-zone";
  $("lessonOutput").innerHTML = `
    <div class="lesson-grid">
      <div class="metric-row">
        <div class="metric"><span>Lesson</span><strong>#${escapeHtml(lesson.id)}</strong></div>
        <div class="metric"><span>Vocabulary</span><strong>${(lesson.key_vocabulary || []).length}</strong></div>
        <div class="metric"><span>Sentences</span><strong>${(lesson.sentence_breakdown_candidates || []).length}</strong></div>
      </div>
      <div class="data-block">
        <h3>${escapeHtml(lesson.title)}</h3>
      </div>
      <div class="data-block">
        <h4>English Summary</h4>
        <p>${escapeHtml(lesson.english_summary)}</p>
      </div>
      <div class="data-block">
        <h4>Spanish Summary</h4>
        <p>${escapeHtml(lesson.spanish_summary)}</p>
      </div>
      <div class="data-block">
        <h4>Vocabulary</h4>
        <div class="chip-field">${vocab || '<p class="list-empty">No vocabulary yet.</p>'}</div>
      </div>
      <div class="data-block">
        <h4>Grammar</h4>
        <ul>${grammar || "<li>No grammar points yet.</li>"}</ul>
      </div>
      <div class="data-block">
        <h4>Autopsy Candidates</h4>
        ${sentences || '<p class="list-empty">No sentence candidates yet.</p>'}
      </div>
      <div class="data-block">
        <h4>Comprehension</h4>
        <ul>${questions || "<li>No comprehension questions yet.</li>"}</ul>
      </div>
      <div class="data-block">
        <h4>Writing Prompt</h4>
        <p>${escapeHtml(lesson.writing_prompt)}</p>
      </div>
    </div>
  `;

  document.querySelectorAll(".sentence-button").forEach((button) => {
    button.addEventListener("click", () => {
      $("autopsyInput").value = button.dataset.sentence;
      $("autopsyInput").focus();
    });
  });
}

function renderLessonList() {
  const list = $("lessonList");
  if (!state.latestLessons.length) {
    list.innerHTML = '<p class="list-empty">No lessons yet.</p>';
    return;
  }
  list.innerHTML = state.latestLessons
    .map(
      (lesson) =>
        `<button class="lesson-button" type="button" data-id="${lesson.id}"><strong>#${lesson.id}</strong> ${escapeHtml(
          lesson.title,
        )}</button>`,
    )
    .join("");

  document.querySelectorAll(".lesson-button").forEach((button) => {
    button.addEventListener("click", async () => {
      await loadLesson(button.dataset.id);
    });
  });
}

function renderVocabulary() {
  const list = $("vocabList");
  if (!state.vocabulary.length) {
    list.innerHTML = '<p class="list-empty">No vocabulary yet.</p>';
    return;
  }
  list.innerHTML = state.vocabulary
    .slice(0, 28)
    .map((item) => `<span class="chip"><strong>${escapeHtml(item.term)}</strong> ${escapeHtml(item.frequency)}</span>`)
    .join("");
}

function renderReviewQueue() {
  const container = $("reviewQueue");
  const remaining = state.reviewQueue.length - state.reviewIndex;
  $("reviewCounter").textContent = `${Math.max(0, remaining)} due`;

  if (remaining <= 0) {
    container.innerHTML = '<p class="list-empty">Queue clear. Generate lessons or run drills to feed it.</p>';
    return;
  }

  const item = state.reviewQueue[state.reviewIndex];
  container.innerHTML = `
    <div class="review-card">
      <span class="review-badge">${escapeHtml(item.kind)} · ${escapeHtml(item.badge || "")}</span>
      <p class="review-prompt">${escapeHtml(item.prompt)}
        ${item.speak ? `<button class="chat-speak" type="button" id="reviewSpeakButton">Say It</button>` : ""}</p>
      ${
        state.reviewRevealed
          ? `<p class="review-answer">${escapeHtml(item.answer)}</p>
             ${item.explanation ? `<p class="review-explanation">${escapeHtml(item.explanation)}</p>` : ""}
             <div class="grade-actions">
               <button id="reviewMissedButton" type="button">Missed</button>
               <button id="reviewGotButton" class="primary-button" type="button">Got It</button>
             </div>`
          : `<button id="reviewRevealButton" class="primary-button" type="button">Show Answer</button>`
      }
    </div>
  `;

  const speakButton = $("reviewSpeakButton");
  if (speakButton) speakButton.addEventListener("click", () => speakSpanish(item.speak));
  const revealButton = $("reviewRevealButton");
  if (revealButton)
    revealButton.addEventListener("click", () => {
      state.reviewRevealed = true;
      renderReviewQueue();
    });
  const gotButton = $("reviewGotButton");
  if (gotButton) gotButton.addEventListener("click", () => gradeReview("got"));
  const missedButton = $("reviewMissedButton");
  if (missedButton) missedButton.addEventListener("click", () => gradeReview("missed"));
}

async function gradeReview(result) {
  const item = state.reviewQueue[state.reviewIndex];
  if (!item) return;
  try {
    await api("/review/complete", {
      method: "POST",
      body: JSON.stringify({ kind: item.kind, id: item.id, result }),
    });
    state.reviewIndex += 1;
    state.reviewRevealed = false;
    renderReviewQueue();
    if (item.kind === "term") {
      // Keep local mastery in step with the backend grade.
      const meta = TUTOR_ALL_TERMS.find((term) => term.es === item.prompt.replace("Translate: ", ""));
      if (meta) {
        const delta = result === "got" ? 1 : -1;
        state.tutor.mastery[meta.id] = Math.max(0, Math.min(TUTOR_MAX_SIGNAL, getTermLevel(meta.id) + delta));
        saveMastery();
        renderTutor();
      }
    }
    setStatus(`Review ${result === "got" ? "cleared" : "rescheduled"}.`);
    if (result === "got") {
      showToast("✅ Cleared from the queue.", "good", 1800);
    } else {
      showToast("↩ Rescheduled — it will come back.", "warn", 1800);
    }
    if (state.reviewIndex >= state.reviewQueue.length) {
      showToast("🧹 Signal Queue clear. Well swept.", "gold", 3200);
    }
    scheduleHqRefresh();
    scheduleProtocolRefresh();
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function refreshReviewQueue() {
  state.reviewQueue = await api("/review/queue?limit=30");
  state.reviewIndex = 0;
  state.reviewRevealed = false;
  renderReviewQueue();
}

// --- Page router ---------------------------------------------------------------

const HQ_PAGES = ["today", "read", "write", "train"];
const MISSION_PAGES = { queue: "today", read: "read", autopsy: "read", write: "write", drill: "train", listen: "train" };

function showPage(name) {
  const page = HQ_PAGES.includes(name) ? name : "today";
  document.querySelectorAll(".page").forEach((node) => {
    node.classList.toggle("active", node.id === `page-${page}`);
  });
  document.querySelectorAll(".hq-nav a").forEach((link) => {
    link.classList.toggle("active", link.dataset.page === page);
  });
  window.scrollTo({ top: 0 });
}

function currentPage() {
  return location.hash.replace("#", "") || "today";
}

function renderProtocol(program) {
  const previous = state.program;
  state.program = program;

  // Celebrate missions that just flipped to done.
  if (previous) {
    const wasDone = new Set(previous.missions.filter((m) => m.done).map((m) => m.id));
    program.missions.forEach((mission) => {
      if (mission.done && !wasDone.has(mission.id)) {
        showToast(`✅ Mission complete: ${mission.title}`, "good", 3200);
      }
    });
  }
  const trackable = program.missions.filter((m) => !m.manual);
  const allDone = trackable.every((m) => m.done);
  if (previous && allDone && !previous.missions.filter((m) => !m.manual).every((m) => m.done)) {
    showToast("🏆 DAILY PROTOCOL COMPLETE — HQ standing by.", "gold", 5000);
  }
  $("hqMissions").textContent = `🎯 ${program.completed}/${program.total}`;
  $("hqMissions").title = `${program.completed} of ${program.total} missions done today`;

  $("protocolPhase").textContent = `Phase ${program.phase}: ${program.name}`;
  const nextLine = program.next_threshold
    ? `${program.known_signals} / ${program.next_threshold} known signals to next phase`
    : `${program.known_signals} known signals — final phase`;
  $("protocolPanel").innerHTML = `
    ${allDone ? '<p class="protocol-banner">🏆 Protocol complete. Outstanding work, agent.</p>' : ""}
    <p class="protocol-focus">${escapeHtml(program.focus)}</p>
    <div class="progress-track"><div class="progress-fill" style="width:${
      program.next_threshold ? Math.min(100, Math.round((program.known_signals / program.next_threshold) * 100)) : 100
    }%"></div></div>
    <p class="protocol-progress">${escapeHtml(nextLine)}</p>
    <ul class="mission-list">
      ${program.missions
        .map(
          (mission) => `
            <li class="mission ${mission.done ? "done" : ""}" data-goto="${escapeHtml(MISSION_PAGES[mission.id] || "today")}" title="Go to the ${escapeHtml(MISSION_PAGES[mission.id] || "today")} page">
              <span class="mission-check">${mission.done ? "✓" : mission.manual ? "·" : "○"}</span>
              <div>
                <strong>${escapeHtml(mission.title)}</strong>
                <span class="mission-detail">${escapeHtml(mission.detail)} — ${escapeHtml(mission.minutes)} min</span>
              </div>
              <span class="mission-go">→</span>
            </li>
          `,
        )
        .join("")}
    </ul>
    <p class="protocol-progress">${program.completed}/${program.total} missions · ${program.protocol_minutes} min protocol · see PROGRAM.md</p>
  `;
}

async function refreshDashboard() {
  const [health, lessons, vocabulary, reviewQueue, program] = await Promise.all([
    api("/health"),
    api("/lessons?limit=12"),
    api("/vocabulary"),
    api("/review/queue?limit=30"),
    api("/program/today"),
  ]);
  renderHealth(health);
  state.latestLessons = lessons;
  state.vocabulary = vocabulary;
  state.reviewQueue = reviewQueue;
  state.reviewIndex = 0;
  state.reviewRevealed = false;
  renderLessonList();
  renderVocabulary();
  renderReviewQueue();
  renderProtocol(program);
  if (!state.activeLesson && lessons.length) {
    await loadLesson(lessons[0].id);
  }
}

async function loadLesson(lessonId) {
  const lesson = await api(`/lessons/${lessonId}`);
  renderLesson(lesson);
  setStatus(`Loaded lesson #${lesson.id}.`);
}

async function importAndGenerate() {
  const text = $("sourceText").value.trim();
  if (!text) {
    setStatus("Paste Spanish source text first.", true);
    return;
  }

  $("generateLessonButton").disabled = true;
  setStatus("Importing source text...");
  try {
    const content = await api("/content/import", {
      method: "POST",
      body: JSON.stringify({
        text,
        source_type: $("sourceType").value,
        topic_tags: getTopicTags(),
      }),
    });
    setStatus(`Generating lesson from content #${content.id}...`);
    const lesson = await api("/lessons/generate", {
      method: "POST",
      body: JSON.stringify({ content_id: content.id }),
    });
    renderLesson(lesson);
    await refreshDashboard();
    setStatus(`Generated lesson #${lesson.id}.`);
    showToast(`📋 Mission brief #${lesson.id} ready — read it through once.`, "good", 3200);
    scheduleHqRefresh();
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    $("generateLessonButton").disabled = false;
  }
}

async function runAutopsy() {
  const sentence = $("autopsyInput").value.trim();
  if (!sentence) {
    setStatus("Paste or select a sentence first.", true);
    return;
  }

  $("runAutopsyButton").disabled = true;
  try {
    const result = await api("/autopsy", {
      method: "POST",
      body: JSON.stringify({
        sentence,
        lesson_id: state.activeLesson?.id || null,
      }),
    });
    $("autopsyOutput").innerHTML = renderAutopsyCard(result);
    setStatus("Sentence autopsy complete.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    $("runAutopsyButton").disabled = false;
  }
}

async function submitWriting() {
  const text = $("writingInput").value.trim();
  if (!text) {
    setStatus("Write a Spanish response first.", true);
    return;
  }

  $("submitWritingButton").disabled = true;
  try {
    const result = await api("/writing/submit", {
      method: "POST",
      body: JSON.stringify({
        text,
        related_lesson_id: state.activeLesson?.id || null,
      }),
    });
    $("writingOutput").innerHTML = renderWritingCard(result);
    setStatus(`Writing submission #${result.id} stored. Detected issues feed the review queue.`);
    const issueCount = (result.issues || []).length;
    showToast(
      issueCount ? `✍️ ${issueCount} correction(s) filed to the queue.` : "✍️ Clean copy — no issues found.",
      issueCount ? "warn" : "good",
      3000,
    );
    await refreshReviewQueue();
    scheduleHqRefresh();
    scheduleProtocolRefresh();
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    $("submitWritingButton").disabled = false;
  }
}

async function exportLesson() {
  if (!state.activeLesson?.id) {
    setStatus("Load a lesson before exporting.", true);
    return;
  }

  $("exportLessonButton").disabled = true;
  try {
    const result = await api(`/exports/lesson/${state.activeLesson.id}`, { method: "POST" });
    setStatus(`Export saved: ${result.path}`);
    showToast("📦 Lesson exported to Markdown.", "good", 2200);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    $("exportLessonButton").disabled = false;
  }
}

function clearIntake() {
  $("sourceText").value = "";
  $("extraTags").value = "";
  document.querySelectorAll('input[name="topic"]').forEach((input) => {
    input.checked = false;
  });
  setStatus("Ready.");
}

function shuffle(items) {
  const copy = items.slice();
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[swap]] = [copy[swap], copy[index]];
  }
  return copy;
}

function getDeck(deckId) {
  return TUTOR_DECKS.find((deck) => deck.id === deckId) || TUTOR_DECKS[0];
}

function getStudyTerm() {
  const deck = getDeck(state.tutor.selectedDeckId);
  return deck.terms[state.tutor.studyIndex] || deck.terms[0];
}

function getTermLevel(termId) {
  return state.tutor.mastery[termId] || 0;
}

function saveMastery() {
  localStorage.setItem(TUTOR_STORAGE_KEY, JSON.stringify(state.tutor.mastery));
}

function loadMastery() {
  try {
    state.tutor.mastery = JSON.parse(localStorage.getItem(TUTOR_STORAGE_KEY) || "{}");
  } catch {
    state.tutor.mastery = {};
  }
}

let masterySyncTimer = null;

async function pushMastery() {
  // Send every deck term so level 0 (including resets) overwrites the server.
  const items = TUTOR_ALL_TERMS.map((term) => ({
    term_id: term.id,
    deck_id: term.deck,
    term: term.es,
    translation: term.en,
    level: getTermLevel(term.id),
    seen: 0,
    correct: 0,
  }));
  (state.captured || []).forEach((item) => {
    items.push({
      term_id: item.id,
      deck_id: "captured",
      term: item.es,
      translation: item.en,
      level: getTermLevel(item.id),
      seen: 0,
      correct: 0,
    });
  });
  try {
    await api("/tutor/mastery", { method: "PUT", body: JSON.stringify({ items }) });
  } catch {
    // Backend sync is a progressive enhancement; localStorage still holds progress.
  }
}

function scheduleMasterySync() {
  clearTimeout(masterySyncTimer);
  masterySyncTimer = setTimeout(pushMastery, 1500);
}

async function pullMastery() {
  try {
    const rows = await api("/tutor/mastery");
    rows.forEach((row) => {
      const local = state.tutor.mastery[row.term_id] || 0;
      state.tutor.mastery[row.term_id] = Math.max(local, row.level);
    });
    state.captured = rows
      .filter((row) => row.deck_id === "captured" && row.term && row.translation)
      .map((row) => ({ id: row.term_id, es: row.term, en: row.translation, deck: "captured" }));
    state.capturedIds = new Set(state.captured.map((item) => item.id));
    saveMastery();
    renderTutor();
  } catch {
    // Offline-tolerant: keep local mastery.
  }
}

function bumpTerm(termId, delta) {
  const previous = getTermLevel(termId);
  const next = Math.max(0, Math.min(TUTOR_MAX_SIGNAL, previous + delta));
  state.tutor.mastery[termId] = next;
  if (next === TUTOR_MAX_SIGNAL && previous < TUTOR_MAX_SIGNAL) {
    const meta = TUTOR_ALL_TERMS.find((term) => term.id === termId);
    showToast(`🔒 SIGNAL LOCKED: ${meta ? meta.es : termId}`, "gold", 3600);
  }
  saveMastery();
  scheduleMasterySync();
  scheduleHqRefresh();
  scheduleProtocolRefresh();
  renderTutor();
}

function deckProgress(deck) {
  const total = deck.terms.length * TUTOR_MAX_SIGNAL;
  const current = deck.terms.reduce((sum, term) => sum + getTermLevel(term.id), 0);
  return total ? current / total : 0;
}

function overallProgress() {
  const total = TUTOR_ALL_TERMS.length * TUTOR_MAX_SIGNAL;
  const current = TUTOR_ALL_TERMS.reduce((sum, term) => sum + getTermLevel(term.id), 0);
  return total ? current / total : 0;
}

function renderSignalBars(node, level) {
  const safeLevel = Math.max(0, Math.min(TUTOR_MAX_SIGNAL, level));
  node.innerHTML = [0, 1, 2, 3, 4]
    .map((bar) => {
      const on = bar < safeLevel;
      const locked = safeLevel >= TUTOR_MAX_SIGNAL;
      return `<span class="signal-bar ${on ? "on" : ""} ${on && locked ? "locked" : ""}" style="height:${9 + bar * 4}px"></span>`;
    })
    .join("");
}

function updateOverallSignal() {
  const progress = overallProgress();
  renderSignalBars($("overallSignalBars"), Math.round(progress * TUTOR_MAX_SIGNAL));
  $("overallSignalPercent").textContent = `${Math.round(progress * 100)}%`;
}

function setTutorTab(tab) {
  state.tutor.activeTab = tab;
  document.querySelectorAll(".tutor-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.tutorTab === tab);
  });
  ["decks", "study", "drill", "listen", "method", "coach", "library", "status"].forEach((name) => {
    $(`tutor${name[0].toUpperCase()}${name.slice(1)}View`).hidden = name !== tab;
  });
  if (tab !== "method") {
    stopMethodCountdown();
  }
  if (tab === "method") {
    renderMethod();
  }
  if (tab === "drill" && !state.tutor.drill) {
    nextDrill();
  }
  if (tab === "listen" && !state.listen.item) {
    nextListen();
  }
  if (tab === "status") {
    refreshProgressSummary();
  }
  renderTutor();
}

function renderDeckGrid() {
  $("deckGrid").innerHTML = TUTOR_DECKS.map((deck) => {
    const progress = deckProgress(deck);
    return `
      <button class="deck-card" type="button" data-deck-id="${deck.id}">
        <span>${deck.tag}</span>
        <strong>${escapeHtml(deck.name)}</strong>
        <span>${escapeHtml(deck.sub)}</span>
        <div class="deck-meta">
          <span>${deck.terms.length} terms</span>
          <div class="signal-bars">${[0, 1, 2, 3, 4]
            .map((bar) => `<span class="signal-bar ${bar < Math.round(progress * TUTOR_MAX_SIGNAL) ? "on" : ""}" style="height:${9 + bar * 4}px"></span>`)
            .join("")}</div>
          <span>${Math.round(progress * 100)}%</span>
        </div>
      </button>
    `;
  }).join("");

  document.querySelectorAll(".deck-card").forEach((button) => {
    button.addEventListener("click", () => {
      state.tutor.selectedDeckId = button.dataset.deckId;
      state.tutor.studyIndex = 0;
      state.tutor.flashFlipped = false;
      setTutorTab("study");
    });
  });
}

function renderStudy() {
  const deck = getDeck(state.tutor.selectedDeckId);
  const term = getStudyTerm();
  $("studyDeckName").textContent = deck.name;
  $("studyCounter").textContent = `${String(state.tutor.studyIndex + 1).padStart(2, "0")} / ${String(deck.terms.length).padStart(2, "0")}`;
  renderSignalBars($("studySignalBars"), getTermLevel(term.id));

  if (state.tutor.flashFlipped) {
    $("flashSide").textContent = "EN";
    $("flashPrimary").textContent = term.en;
    $("flashNote").textContent = term.xen || "Meaning revealed.";
    $("flashExample").textContent = term.xes ? term.xes : "";
  } else {
    $("flashSide").textContent = "ES";
    $("flashPrimary").textContent = term.es;
    $("flashNote").textContent = term.note || "tap to reveal";
    $("flashExample").textContent = term.xes ? term.xes : "";
  }
}

function moveStudy(delta) {
  const deck = getDeck(state.tutor.selectedDeckId);
  state.tutor.studyIndex = (state.tutor.studyIndex + delta + deck.terms.length) % deck.terms.length;
  state.tutor.flashFlipped = false;
  renderStudy();
}

function speakSpanish(text, rate = 0.9) {
  try {
    if (!window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "es-ES";
    utterance.rate = rate;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  } catch {
    // Speech synthesis is a progressive enhancement.
  }
}

function renderDrillScope() {
  const capturedCount = (state.captured || []).length;
  $("drillScope").innerHTML = [
    '<option value="all">All Decks</option>',
    `<option value="captured">🎯 Captured (${capturedCount})</option>`,
    ...TUTOR_DECKS.map((deck) => `<option value="${deck.id}">${escapeHtml(deck.name)}</option>`),
  ].join("");
  $("drillScope").value = state.tutor.drillScope;
}

function drillPool() {
  if (state.tutor.drillScope === "all") {
    return [...TUTOR_ALL_TERMS, ...(state.captured || [])];
  }
  if (state.tutor.drillScope === "captured") {
    return state.captured || [];
  }
  return TUTOR_ALL_TERMS.filter((term) => term.deck === state.tutor.drillScope);
}

function nextDrill() {
  const pool = drillPool();
  if (pool.length < 2) {
    state.tutor.drill = null;
    state.tutor.drillPicked = null;
    $("drillCard").innerHTML =
      '<p class="list-empty">Not enough terms in this scope yet. Hover words while reading and click to capture them — they land here.</p>';
    return;
  }
  const ranked = pool.slice().sort((a, b) => getTermLevel(a.id) - getTermLevel(b.id));
  const weakWindow = ranked.slice(0, Math.max(4, Math.ceil(ranked.length / 3)));
  const target = weakWindow[Math.floor(Math.random() * weakWindow.length)] || pool[0];
  const direction = Math.random() > 0.5 ? "es2en" : "en2es";
  const answerKey = direction === "es2en" ? "en" : "es";
  const prompt = direction === "es2en" ? target.es : target.en;
  const distractors = shuffle(pool.filter((term) => term.id !== target.id && term[answerKey] !== target[answerKey]))
    .slice(0, 3)
    .map((term) => term[answerKey]);
  state.tutor.drill = {
    target,
    direction,
    prompt,
    answer: target[answerKey],
    options: shuffle([target[answerKey], ...distractors]),
  };
  state.tutor.drillPicked = null;
  renderDrill();
}

function renderDrill() {
  const drill = state.tutor.drill;
  $("drillHits").textContent = `Hits ${state.tutor.drillRight}/${state.tutor.drillSeen}`;
  $("drillStreak").textContent = `Streak ${state.tutor.drillStreak}`;
  if (!drill) {
    $("drillCard").innerHTML =
      drillPool().length < 2
        ? '<p class="list-empty">Not enough terms in this scope yet. Hover words while reading and click to capture them — they land here.</p>'
        : '<p class="list-empty">No drill loaded.</p>';
    return;
  }
  const picked = state.tutor.drillPicked;
  $("drillCard").innerHTML = `
    <span class="drill-direction">${drill.direction === "es2en" ? "Translate to English" : "Translate to Spanish"}</span>
    <p class="drill-prompt">${escapeHtml(drill.prompt)}</p>
    <div class="option-grid">
      ${drill.options
        .map((option, index) => {
          const klass = picked ? (option === drill.answer ? "correct" : option === picked ? "wrong" : "") : "";
          return `
            <button class="option-button ${klass}" type="button" data-option="${escapeHtml(option)}" ${picked ? "disabled" : ""}>
              <span class="option-num">${index + 1}</span>
              <span>${escapeHtml(option)}</span>
            </button>
          `;
        })
        .join("")}
    </div>
    ${
      picked
        ? `<div class="drill-feedback">
            <strong>${picked === drill.answer ? "Signal locked" : "Missed signal"}</strong>
            <p>${escapeHtml(drill.target.xes || drill.target.es)} ${escapeHtml(drill.target.xen || "")}</p>
            <button id="nextDrillButton" class="primary-button" type="button">Next Drill</button>
          </div>`
        : ""
    }
  `;

  document.querySelectorAll(".option-button").forEach((button) => {
    button.addEventListener("click", () => chooseDrill(button.dataset.option));
  });
  const nextButton = $("nextDrillButton");
  if (nextButton) nextButton.addEventListener("click", nextDrill);
}

function chooseDrill(option) {
  if (!state.tutor.drill || state.tutor.drillPicked) return;
  state.tutor.drillPicked = option;
  const correct = option === state.tutor.drill.answer;
  state.tutor.drillSeen += 1;
  if (correct) {
    state.tutor.drillRight += 1;
    state.tutor.drillStreak += 1;
    bumpTerm(state.tutor.drill.target.id, 1);
    if (state.tutor.drill.direction === "es2en") speakSpanish(state.tutor.drill.target.es);
    if (state.tutor.drillStreak > 0 && state.tutor.drillStreak % 5 === 0) {
      showToast(`⚡ ${state.tutor.drillStreak}-hit streak!`, "good");
    }
  } else {
    state.tutor.drillStreak = 0;
    bumpTerm(state.tutor.drill.target.id, -1);
  }
  renderDrill();
}

function normalizeSpanish(text) {
  return String(text || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function listenPool() {
  return TUTOR_ALL_TERMS.filter((term) => term.xes && term.xen);
}

function nextListen() {
  const pool = listenPool();
  if (!pool.length) {
    state.listen.item = null;
    renderListen();
    return;
  }
  const ranked = pool.slice().sort((a, b) => getTermLevel(a.id) - getTermLevel(b.id));
  const weakWindow = ranked.slice(0, Math.max(4, Math.ceil(ranked.length / 3)));
  const target = weakWindow[Math.floor(Math.random() * weakWindow.length)];
  const distractors = shuffle(pool.filter((term) => term.id !== target.id && term.xen !== target.xen))
    .slice(0, 3)
    .map((term) => term.xen);
  state.listen.item = {
    target,
    options: shuffle([target.xen, ...distractors]),
  };
  state.listen.picked = null;
  state.listen.checked = false;
  renderListen();
  speakSpanish(target.xes, state.listen.rate);
}

function renderListen() {
  const listen = state.listen;
  $("listenHits").textContent = `Hits ${listen.right}/${listen.seen}`;
  $("listenStreak").textContent = `Streak ${listen.streak}`;
  const card = $("listenCard");
  if (!listen.item) {
    card.innerHTML = '<p class="list-empty">No listening material loaded.</p>';
    return;
  }

  const done = listen.mode === "meaning" ? listen.picked !== null : listen.checked;
  const target = listen.item.target;
  const header = `
    <span class="drill-direction">${listen.mode === "meaning" ? "What does the transmission mean?" : "Type exactly what you hear"}</span>
    <div class="listen-controls">
      <button id="listenPlayButton" class="primary-button" type="button">Play Transmission</button>
      ${done ? "" : '<button id="listenSkipButton" type="button">Reveal (counts as miss)</button>'}
    </div>
  `;

  let body = "";
  if (listen.mode === "meaning") {
    body = `
      <div class="option-grid">
        ${listen.item.options
          .map((option, index) => {
            const klass = listen.picked ? (option === target.xen ? "correct" : option === listen.picked ? "wrong" : "") : "";
            return `
              <button class="option-button listen-option ${klass}" type="button" data-option="${escapeHtml(option)}" ${listen.picked ? "disabled" : ""}>
                <span class="option-num">${index + 1}</span>
                <span>${escapeHtml(option)}</span>
              </button>
            `;
          })
          .join("")}
      </div>
    `;
  } else {
    body = `
      <div class="dictation-row">
        <input id="dictationInput" type="text" spellcheck="false" autocomplete="off"
          placeholder="Escribe lo que escuchas..." ${done ? "disabled" : ""}
          value="${done ? escapeHtml(listen.picked || "") : ""}" />
        ${done ? "" : '<button id="dictationCheckButton" class="primary-button" type="button">Check</button>'}
      </div>
    `;
  }

  const feedback = done
    ? `
      <div class="drill-feedback">
        <strong>${listen.lastCorrect ? "Signal locked" : "Missed signal"}</strong>
        <p><span class="card-label">Heard</span> ${escapeHtml(target.xes)}</p>
        <p><span class="card-label">Meaning</span> ${escapeHtml(target.xen)}</p>
        <button id="nextListenButton" class="primary-button" type="button">Next Transmission</button>
      </div>
    `
    : "";

  card.innerHTML = header + body + feedback;

  $("listenPlayButton").addEventListener("click", () => speakSpanish(target.xes, state.listen.rate));
  const skipButton = $("listenSkipButton");
  if (skipButton) skipButton.addEventListener("click", () => finishListen(false, ""));
  const nextButton = $("nextListenButton");
  if (nextButton) nextButton.addEventListener("click", nextListen);
  document.querySelectorAll(".listen-option").forEach((button) => {
    button.addEventListener("click", () => {
      const correct = button.dataset.option === target.xen;
      finishListen(correct, button.dataset.option);
    });
  });
  const checkButton = $("dictationCheckButton");
  if (checkButton)
    checkButton.addEventListener("click", () => {
      const typed = $("dictationInput").value;
      finishListen(normalizeSpanish(typed) === normalizeSpanish(target.xes), typed);
    });
  const dictationInput = $("dictationInput");
  if (dictationInput && !done) {
    dictationInput.focus();
    dictationInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        finishListen(normalizeSpanish(dictationInput.value) === normalizeSpanish(target.xes), dictationInput.value);
      }
    });
  }
}

function finishListen(correct, picked) {
  const listen = state.listen;
  if (!listen.item) return;
  listen.picked = picked || "(revealed)";
  listen.checked = true;
  listen.lastCorrect = correct;
  listen.seen += 1;
  if (correct) {
    listen.right += 1;
    listen.streak += 1;
    bumpTerm(listen.item.target.id, 1);
    if (listen.streak > 0 && listen.streak % 5 === 0) {
      showToast(`📻 ${listen.streak} clean transmissions in a row!`, "good");
    }
  } else {
    listen.streak = 0;
    bumpTerm(listen.item.target.id, -1);
  }
  renderListen();
}

async function refreshProgressSummary() {
  try {
    state.progressSummary = await api("/progress/summary");
    renderIntelReport();
  } catch {
    // Summary is a progressive enhancement.
  }
}

function renderIntelReport() {
  const summary = state.progressSummary;
  if (!summary) {
    $("intelReport").innerHTML = "";
    return;
  }
  const metrics = [
    ["Lessons", summary.lessons],
    ["Vocab Terms", summary.vocabulary_terms],
    ["Writing Runs", summary.writing_submissions],
    ["Chat Messages", summary.chat_messages],
    ["Mistakes Due", summary.mistakes_due],
    ["Reviews Due", summary.review_items_due],
    ["Signals Tracked", summary.mastery_tracked],
    ["Signals Locked", summary.mastery_locked],
  ];
  $("intelReport").innerHTML = metrics
    .map(
      ([label, value]) => `
        <div class="status-card">
          <strong>${escapeHtml(value)}</strong>
          <p class="list-empty">${escapeHtml(label)}</p>
        </div>
      `,
    )
    .join("");
}

function renderTutorStatus() {
  renderIntelReport();
  $("tutorStatusGrid").innerHTML = TUTOR_DECKS.map((deck) => {
    const progress = deckProgress(deck);
    return `
      <div class="status-card">
        <strong>${deck.tag} ${escapeHtml(deck.name)}</strong>
        <div class="progress-track"><div class="progress-fill" style="width:${Math.round(progress * 100)}%"></div></div>
        <p class="list-empty">${Math.round(progress * 100)}% signal / ${deck.terms.length} terms</p>
      </div>
    `;
  }).join("");

  const distribution = [0, 0, 0, 0, 0, 0];
  TUTOR_ALL_TERMS.forEach((term) => {
    distribution[getTermLevel(term.id)] += 1;
  });
  const max = Math.max(...distribution, 1);
  $("signalDistribution").innerHTML = distribution
    .map((count, level) => `
      <div class="dist-card">
        <div class="dist-bar" style="height:${Math.max(2, Math.round((count / max) * 88))}px"></div>
        <strong>${count}</strong>
        <span>L${level}</span>
      </div>
    `)
    .join("");
}

function renderConjugationCard(card) {
  const tenses = Object.entries(card.tenses || {})
    .map(([tense, rows]) => `
      <div class="conj-tense">
        <h5>${escapeHtml((card.tense_labels || {})[tense] || tense)}</h5>
        <table class="conj-table">
          ${rows.map((row) => `<tr><td>${escapeHtml(row.person)}</td><td><strong>${escapeHtml(row.form)}</strong></td></tr>`).join("")}
        </table>
      </div>
    `)
    .join("");
  return `
    <div class="chat-card">
      <div class="chat-card-head">
        <strong>${escapeHtml(card.verb)}</strong>
        <span>${escapeHtml(card.translation || "")}${card.is_irregular ? " · irregular" : " · regular"}</span>
        <button class="chat-speak" type="button" data-speak="${escapeHtml(card.verb)}">Say It</button>
      </div>
      <div class="conj-grid">${tenses}</div>
    </div>
  `;
}

function renderLookupCard(card) {
  if (card.direction === "en_to_es" && card.matches) {
    const rows = card.matches
      .map((m) => `<li><strong>${escapeHtml(m.es)}</strong> — ${escapeHtml(m.en)} <button class="chat-speak" type="button" data-speak="${escapeHtml(m.es)}">Say It</button></li>`)
      .join("");
    return `<div class="chat-card"><ul class="lookup-list">${rows}</ul><p class="card-next">${escapeHtml(card.next_step || "")}</p></div>`;
  }
  return `
    <div class="chat-card">
      <div class="chat-card-head">
        <strong>${escapeHtml(card.term)}</strong>
        <span>${escapeHtml(card.translation || "not in offline lexicon")}</span>
        <button class="chat-speak" type="button" data-speak="${escapeHtml(card.term)}">Say It</button>
      </div>
      <p class="card-next">${escapeHtml(card.next_step || "")}</p>
    </div>
  `;
}

function renderGrammarCard(card) {
  return `
    <div class="chat-card">
      <h5>${escapeHtml(card.title)}</h5>
      <ul>${(card.points || []).map((point) => `<li>${escapeHtml(point)}</li>`).join("")}</ul>
      ${(card.examples || [])
        .map(
          (example) => `
            <p class="chat-example"><strong>${escapeHtml(example.es)}</strong> ${escapeHtml(example.en)}
              <button class="chat-speak" type="button" data-speak="${escapeHtml(example.es)}">Say It</button></p>
          `,
        )
        .join("")}
      <p class="card-next">Practice: ${escapeHtml(card.practice || "")}</p>
    </div>
  `;
}

function renderQuizCard(card, cardIndex) {
  const questions = (card.questions || [])
    .map(
      (question, questionIndex) => `
        <div class="chat-quiz" data-answer="${escapeHtml(question.answer)}">
          <p class="drill-prompt">${escapeHtml(question.prompt)}
            <button class="chat-speak" type="button" data-speak="${escapeHtml(question.prompt)}">Say It</button></p>
          <div class="option-grid">
            ${question.options
              .map(
                (option) => `
                  <button class="option-button chat-quiz-option" type="button" data-option="${escapeHtml(option)}">
                    <span>${escapeHtml(option)}</span>
                  </button>
                `,
              )
              .join("")}
          </div>
          <p class="quiz-source">${escapeHtml(question.source || "")}</p>
        </div>
      `,
    )
    .join("");
  return `<div class="chat-card">${questions}</div>`;
}

function renderAutopsyCard(card) {
  const connectors = (card.connectors || []).map((item) => `${item.term} (${item.role})`).join(", ");
  return `
    <div class="chat-card">
      <p class="chat-example"><strong>${escapeHtml(card.original)}</strong>
        <button class="chat-speak" type="button" data-speak="${escapeHtml(card.original)}">Say It</button></p>
      <p><span class="card-label">Literal</span> ${escapeHtml(card.literal_translation || "")}</p>
      <p><span class="card-label">Natural</span> ${escapeHtml(card.natural_translation || "")}</p>
      <p><span class="card-label">Verbs</span> ${escapeHtml((card.verbs || []).join(", ") || "none detected")}</p>
      <p><span class="card-label">Connectors</span> ${escapeHtml(connectors || "none detected")}</p>
      <p><span class="card-label">Pattern</span> ${escapeHtml(card.pattern || "")}</p>
      <ul>${(card.grammar_notes || []).map((note) => `<li>${escapeHtml(note)}</li>`).join("")}</ul>
      <p class="card-next">${escapeHtml(card.practice_prompt || "")}</p>
    </div>
  `;
}

function renderWritingCard(card) {
  const issues = (card.issues || [])
    .map(
      (issue) => `
        <li><strong>${escapeHtml(issue.original)}</strong> → <strong class="fix">${escapeHtml(issue.correction)}</strong><br />
        <span>${escapeHtml(issue.explanation)}</span></li>
      `,
    )
    .join("");
  return `
    <div class="chat-card">
      <p><span class="card-label">Corrected</span> ${escapeHtml(card.corrected_version || "")}</p>
      ${issues ? `<ul class="issue-list">${issues}</ul>` : ""}
      <ul>${(card.strengths || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      <p class="card-next">${escapeHtml(card.rewrite_prompt || "")}</p>
    </div>
  `;
}

function renderStudyPlanCard(card) {
  const weak = (card.weak_terms || [])
    .map((item) => `<li><strong>${escapeHtml(item.term)}</strong> ${escapeHtml(item.translation || "")} — L${escapeHtml(item.level)}</li>`)
    .join("");
  return `
    <div class="chat-card">
      <ol>${(card.steps || []).map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ol>
      ${weak ? `<p class="card-label">Weak terms</p><ul>${weak}</ul>` : ""}
    </div>
  `;
}

function renderExplanationCard(card) {
  return `
    <div class="chat-card">
      ${card.literal_gloss ? `<p><span class="card-label">Gloss</span> ${escapeHtml(card.literal_gloss)}</p>` : ""}
      ${(card.vocabulary || []).length
        ? `<div class="chip-field">${card.vocabulary
            .map((item) => `<span class="chip"><strong>${escapeHtml(item.term)}</strong></span>`)
            .join("")}</div>`
        : ""}
      <p class="card-next">${escapeHtml(card.next_step || "")}</p>
    </div>
  `;
}

function renderCardHtml(card, index) {
  switch (card.type) {
    case "conjugation_table":
      return renderConjugationCard(card);
    case "term_lookup":
      return renderLookupCard(card);
    case "grammar_guide":
      return renderGrammarCard(card);
    case "quiz":
      return renderQuizCard(card, index);
    case "autopsy":
      return renderAutopsyCard(card);
    case "writing_feedback":
      return renderWritingCard(card);
    case "study_plan":
      return renderStudyPlanCard(card);
    case "explanation":
      return renderExplanationCard(card);
    default:
      return `<pre>${escapeHtml(JSON.stringify(card, null, 2))}</pre>`;
  }
}

function addCoachMessage(role, body, cards = null, pending = false) {
  state.tutor.coachMessages.push({ role, body, cards, pending });
  renderCoachMessages();
}

function renderCoachMessages() {
  if (!state.tutor.coachMessages.length) {
    $("coachMessages").innerHTML = `
      <div class="coach-message">
        <strong>Tutor</strong>
        <p>Ready. Try: "conjugate tener", "ser vs estar", "quiz me", "what does amenaza mean", or "correct: &lt;tu texto&gt;".</p>
      </div>
    `;
    return;
  }

  $("coachMessages").innerHTML = state.tutor.coachMessages
    .map((message) => `
      <div class="coach-message ${message.role === "user" ? "user" : ""} ${message.pending ? "pending" : ""}">
        <strong>${message.role === "user" ? "You" : "Tutor"}</strong>
        <p>${escapeHtml(message.body)}</p>
        ${(message.cards || []).map((card, index) => renderCardHtml(card, index)).join("")}
      </div>
    `)
    .join("");
  $("coachMessages").scrollTop = $("coachMessages").scrollHeight;
}

function renderCoachSuggestions(suggestions) {
  $("coachSuggestions").innerHTML = (suggestions || [])
    .map((text) => `<button class="suggestion-chip" type="button" data-suggestion="${escapeHtml(text)}">${escapeHtml(text)}</button>`)
    .join("");
}

async function loadCoachHistory() {
  try {
    const history = await api("/tutor/chat/history?limit=40");
    state.tutor.coachMessages = history.map((row) => ({
      role: row.role === "user" ? "user" : "assistant",
      body: row.content,
      cards: row.cards || [],
    }));
    renderCoachMessages();
  } catch {
    // History is a progressive enhancement; offline chat still works.
  }
}

async function clearCoachHistory() {
  try {
    await api("/tutor/chat/history", { method: "DELETE" });
    state.tutor.coachMessages = [];
    renderCoachMessages();
    renderCoachSuggestions([]);
    setStatus("Tutor chat cleared.");
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function sendCoach(overrideMessage = null) {
  const message = (overrideMessage ?? $("coachInput").value).trim();
  if (!message) {
    setStatus("Type a question for the tutor first.", true);
    return;
  }

  addCoachMessage("user", message);
  addCoachMessage("assistant", "…", null, true);
  $("coachInput").value = "";
  $("sendCoachButton").disabled = true;
  try {
    const result = await api("/tutor/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        lesson_id: state.activeLesson?.id || null,
      }),
    });
    state.tutor.coachMessages.pop();
    addCoachMessage("assistant", result.reply, result.cards);
    renderCoachSuggestions(result.suggestions);
    setStatus(`Tutor intent: ${result.intent} (${result.provider}).`);
  } catch (error) {
    state.tutor.coachMessages.pop();
    renderCoachMessages();
    setStatus(error.message, true);
  } finally {
    $("sendCoachButton").disabled = false;
    $("coachInput").focus();
  }
}

function handleCoachClick(event) {
  const speakButton = event.target.closest(".chat-speak");
  if (speakButton) {
    speakSpanish(speakButton.dataset.speak);
    return;
  }
  const optionButton = event.target.closest(".chat-quiz-option");
  if (optionButton && !optionButton.disabled) {
    const quiz = optionButton.closest(".chat-quiz");
    const answer = quiz.dataset.answer;
    quiz.querySelectorAll(".chat-quiz-option").forEach((button) => {
      button.disabled = true;
      if (button.dataset.option === answer) button.classList.add("correct");
      else if (button === optionButton) button.classList.add("wrong");
    });
  }
}

function renderTutor() {
  updateOverallSignal();
  renderDeckGrid();
  renderStudy();
  renderDrillScope();
  renderDrill();
  renderListen();
  renderTutorStatus();
  renderCoachMessages();
}

function initializeTutor() {
  loadMastery();
  renderDrillScope();
  nextDrill();
  setTutorTab("decks");
  pullMastery().then(pushMastery);
  loadCoachHistory();
}

function bindTutorEvents() {
  document.querySelectorAll(".tutor-tab").forEach((button) => {
    button.addEventListener("click", () => setTutorTab(button.dataset.tutorTab));
  });
  $("resetTutorProgressButton").addEventListener("click", () => {
    state.tutor.mastery = {};
    saveMastery();
    pushMastery();
    renderTutor();
    setStatus("Tutor progress reset.");
  });
  $("backToDecksButton").addEventListener("click", () => setTutorTab("decks"));
  $("flashcard").addEventListener("click", () => {
    state.tutor.flashFlipped = !state.tutor.flashFlipped;
    const card = $("flashcard");
    card.classList.remove("flipping");
    void card.offsetWidth; // Restart the animation.
    card.classList.add("flipping");
    renderStudy();
  });
  $("previousTermButton").addEventListener("click", () => moveStudy(-1));
  $("nextTermButton").addEventListener("click", () => moveStudy(1));
  $("speakTermButton").addEventListener("click", () => speakSpanish(getStudyTerm().es));
  $("coachTermButton").addEventListener("click", () => {
    const term = getStudyTerm();
    setTutorTab("coach");
    $("coachInput").value = `Explain ${term.es} and give me 3 usable Spanish examples.`;
  });
  $("missedTermButton").addEventListener("click", () => {
    bumpTerm(getStudyTerm().id, -1);
    moveStudy(1);
  });
  $("gotTermButton").addEventListener("click", () => {
    bumpTerm(getStudyTerm().id, 1);
    moveStudy(1);
  });
  $("drillScope").addEventListener("change", () => {
    state.tutor.drillScope = $("drillScope").value;
    state.tutor.drillSeen = 0;
    state.tutor.drillRight = 0;
    state.tutor.drillStreak = 0;
    nextDrill();
  });
  $("listenMode").addEventListener("change", () => {
    state.listen.mode = $("listenMode").value;
    state.listen.seen = 0;
    state.listen.right = 0;
    state.listen.streak = 0;
    nextListen();
  });
  $("listenRate").addEventListener("change", () => {
    state.listen.rate = parseFloat($("listenRate").value) || 0.9;
  });
  $("startEchoButton").addEventListener("click", () => startMethodSession("echo"));
  $("startConstructorButton").addEventListener("click", () => startMethodSession("constructor"));
  $("methodPlayer").addEventListener("click", handleMethodClick);
  $("methodPlayer").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && event.target.id === "methodInput") {
      event.preventDefault();
      const step = currentMethodStep();
      if (step && !state.method.checked) checkMethodAnswer(step, event.target.value);
    }
  });
  $("librarySearch").addEventListener("input", renderLibrary);
  $("libraryCategory").addEventListener("change", renderLibrary);
  $("libraryList").addEventListener("click", (event) => {
    const speakButton = event.target.closest(".chat-speak");
    if (speakButton) speakSpanish(speakButton.dataset.speak);
  });
  $("sendCoachButton").addEventListener("click", () => sendCoach());
  $("clearCoachButton").addEventListener("click", clearCoachHistory);
  $("coachInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendCoach();
    }
  });
  $("coachMessages").addEventListener("click", handleCoachClick);
  $("coachSuggestions").addEventListener("click", (event) => {
    const chip = event.target.closest(".suggestion-chip");
    if (chip) sendCoach(chip.dataset.suggestion);
  });
  document.querySelectorAll("[data-coach-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const prompts = {
        explain: "Explain the most useful grammar pattern in my active lesson.",
        quiz: "Quiz me on my weakest terms.",
        autopsy: `Autopsy: ${$("coachInput").value.trim() || "El equipo analiza la amenaza porque el sistema detecta actividad sospechosa."}`,
        writing: $("coachInput").value.trim() ? `Correct: ${$("coachInput").value.trim()}` : "Give me a writing prompt about my active lesson.",
        conjugate: `Conjugate ${$("coachInput").value.trim() || "tener"}`,
        plan: "What should I study today?",
      };
      sendCoach(prompts[button.dataset.coachAction] || button.dataset.coachAction);
    });
  });
}

// --- Method sessions (Echo / Constructor) -------------------------------------

let methodCountdownTimer = null;

function stopMethodCountdown() {
  clearInterval(methodCountdownTimer);
  methodCountdownTimer = null;
}

function resetMethodStep() {
  stopMethodCountdown();
  state.method.revealed = false;
  state.method.countdown = 0;
  state.method.built = [];
  state.method.checked = false;
  state.method.lastCorrect = null;
}

async function startMethodSession(kind) {
  try {
    const plan = await api(`/methods/session?method=${kind}${kind === "echo" ? "&size=6" : ""}`);
    state.method.plan = plan;
    state.method.index = 0;
    state.method.results = {};
    state.method.finished = false;
    state.method.reported = false;
    resetMethodStep();
    renderMethod();
    showToast(kind === "echo" ? "🔁 Echo Session started — say everything aloud." : "🧱 Constructor Session started — build, don't memorize.", "info", 3000);
  } catch (error) {
    setStatus(error.message, true);
  }
}

function methodSteps() {
  const plan = state.method.plan;
  if (!plan) return [];
  return plan.prompts || plan.steps || [];
}

function currentMethodStep() {
  return methodSteps()[state.method.index] || null;
}

function recordMethodResult(step, correct) {
  state.method.results[step.term_id] = {
    term_id: step.term_id,
    es: step.es || step.answer_es || "",
    en: step.en || step.prompt_en || "",
    correct,
  };
}

async function finishMethodSession() {
  stopMethodCountdown();
  state.method.finished = true;
  renderMethod();
  if (state.method.reported) return;
  const results = Object.values(state.method.results);
  if (!results.length) return;
  state.method.reported = true;
  try {
    const summary = await api("/methods/complete", {
      method: "POST",
      body: JSON.stringify({ method: state.method.plan.method, results }),
    });
    showToast(`🎧 Session logged: ${summary.correct}/${summary.recorded} signals locked.`, "gold", 3600);
    scheduleHqRefresh();
    scheduleProtocolRefresh();
  } catch (error) {
    setStatus(error.message, true);
  }
}

function methodAdvance() {
  resetMethodStep();
  state.method.index += 1;
  if (state.method.index >= methodSteps().length) {
    finishMethodSession();
    return;
  }
  renderMethod();
}

function startRecallCountdown() {
  state.method.countdown = 4;
  methodCountdownTimer = setInterval(() => {
    state.method.countdown -= 1;
    const node = $("methodCountdown");
    if (node) node.textContent = state.method.countdown;
    if (state.method.countdown <= 0) {
      revealMethodStep();
    }
  }, 1000);
}

function revealMethodStep() {
  stopMethodCountdown();
  if (state.method.revealed) return;
  state.method.revealed = true;
  const step = currentMethodStep();
  if (step && step.es) speakSpanish(step.es);
  renderMethod();
}

function checkMethodAnswer(step, typed) {
  const correct = normalizeSpanish(typed) === normalizeSpanish(step.answer_es);
  state.method.checked = true;
  state.method.lastCorrect = correct;
  recordMethodResult(step, correct);
  speakSpanish(step.answer_es);
  renderMethod();
}

function chunksHtml(chunks) {
  return `
    <div class="buildup">
      ${chunks
        .map(
          (chunk) => `
            <button class="buildup-chunk" type="button" data-speak="${escapeHtml(chunk)}">
              ${escapeHtml(chunk)} <span>🔊</span>
            </button>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderMethod() {
  const picker = $("methodPicker");
  const player = $("methodPlayer");
  const plan = state.method.plan;

  if (!plan) {
    picker.hidden = false;
    player.hidden = true;
    return;
  }
  picker.hidden = true;
  player.hidden = false;

  if (state.method.finished) {
    const results = Object.values(state.method.results);
    const correct = results.filter((r) => r.correct).length;
    player.innerHTML = `
      <div class="drill-card method-summary">
        <span class="drill-direction">Session complete</span>
        <p class="drill-prompt">${correct}/${results.length} signals locked</p>
        <p class="list-empty">${escapeHtml(plan.title)}. Results feed your mastery, queue, and XP.</p>
        <div class="listen-controls">
          <button id="methodAgainButton" class="primary-button" type="button">Run Another</button>
          <button id="methodExitButton" type="button">Back to Methods</button>
        </div>
      </div>
    `;
    return;
  }

  const steps = methodSteps();
  const step = currentMethodStep();
  if (!step) return;
  const progress = `${state.method.index + 1} / ${steps.length}`;
  const header = `
    <div class="method-head">
      <span class="review-badge">${escapeHtml(plan.method === "echo" ? "echo" : "constructor")} · ${progress}</span>
      <button id="methodQuitButton" type="button" title="Abandon session">✕</button>
    </div>
  `;

  let body = "";
  const type = step.mode || step.type;

  if (type === "introduce") {
    body = `
      <span class="drill-direction">New signal — listen, then say it aloud twice</span>
      <p class="drill-prompt">${escapeHtml(step.es)}
        <button class="chat-speak" type="button" data-speak="${escapeHtml(step.es)}">🔊</button></p>
      <p class="method-en">${escapeHtml(step.en)}</p>
      ${step.chunks.length > 1 ? `<p class="card-label">Build it from the tail</p>${chunksHtml(step.chunks)}` : ""}
      <button id="methodContinueButton" class="primary-button" type="button">Got it — continue</button>
    `;
  } else if (type === "recall") {
    if (!state.method.revealed) {
      body = `
        <span class="drill-direction">Recall ${step.recall_index}/${step.recall_total} — say it in Spanish NOW</span>
        <p class="drill-prompt">${escapeHtml(step.en)}</p>
        <div class="countdown-ring"><span id="methodCountdown">${state.method.countdown || 4}</span></div>
        <button id="methodRevealButton" type="button">I said it — reveal</button>
      `;
    } else {
      body = `
        <span class="drill-direction">Did you produce it?</span>
        <p class="drill-prompt">${escapeHtml(step.es)}
          <button class="chat-speak" type="button" data-speak="${escapeHtml(step.es)}">🔊</button></p>
        <p class="method-en">${escapeHtml(step.en)}</p>
        ${step.chunks.length > 1 ? chunksHtml(step.chunks) : ""}
        <div class="grade-actions">
          <button id="methodMissedButton" type="button">Missed</button>
          <button id="methodGotButton" class="primary-button" type="button">Got It</button>
        </div>
      `;
    }
  } else if (type === "teach") {
    body = `
      <span class="drill-direction">Building block</span>
      <h3 class="method-title">${escapeHtml(step.title)}</h3>
      <ul>${step.points.map((point) => `<li>${escapeHtml(point)}</li>`).join("")}</ul>
      ${(step.examples || [])
        .map(
          (example) => `<p class="chat-example"><strong>${escapeHtml(example.es)}</strong> ${escapeHtml(example.en)}
            <button class="chat-speak" type="button" data-speak="${escapeHtml(example.es)}">🔊</button></p>`,
        )
        .join("")}
      <button id="methodContinueButton" class="primary-button" type="button">Ready — test me</button>
    `;
  } else if (type === "convert" || type === "produce") {
    const label = type === "convert" ? "Convert it to Spanish" : "Say it, then type it";
    if (!state.method.checked) {
      body = `
        <span class="drill-direction">${label}</span>
        <p class="drill-prompt">${escapeHtml(step.prompt_en)}</p>
        ${step.hint ? `<p class="method-hint">💡 ${escapeHtml(step.hint)}</p>` : ""}
        <div class="dictation-row">
          <input id="methodInput" type="text" spellcheck="false" autocomplete="off" placeholder="Escribe en espanol... (accents optional)" />
          <button id="methodCheckButton" class="primary-button" type="button">Check</button>
        </div>
      `;
    } else {
      body = `
        <span class="drill-direction">${state.method.lastCorrect ? "Constructed. That's the method." : "Close — study the pattern"}</span>
        <p class="drill-prompt">${escapeHtml(step.answer_es)}
          <button class="chat-speak" type="button" data-speak="${escapeHtml(step.answer_es)}">🔊</button></p>
        <p class="method-en">${escapeHtml(step.prompt_en)}</p>
        <button id="methodContinueButton" class="primary-button" type="button">Next</button>
      `;
    }
  } else if (type === "build") {
    const remaining = step.tiles.filter((tile, index) => !state.method.built.includes(index));
    if (!state.method.checked) {
      body = `
        <span class="drill-direction">Build the sentence from tiles</span>
        <p class="drill-prompt">${escapeHtml(step.prompt_en)}</p>
        <div class="built-row">${
          state.method.built.length
            ? state.method.built
                .map((tileIndex, position) => `<button class="tile built" type="button" data-unbuild="${position}">${escapeHtml(step.tiles[tileIndex])}</button>`)
                .join("")
            : '<span class="list-empty">Tap tiles below in order...</span>'
        }</div>
        <div class="tile-row">${step.tiles
          .map((tile, tileIndex) =>
            state.method.built.includes(tileIndex)
              ? ""
              : `<button class="tile" type="button" data-build="${tileIndex}">${escapeHtml(tile)}</button>`,
          )
          .join("")}</div>
        <button id="methodCheckButton" class="primary-button" type="button" ${remaining.length ? "disabled" : ""}>Check</button>
      `;
    } else {
      body = `
        <span class="drill-direction">${state.method.lastCorrect ? "Constructed. That's the method." : "Close — study the order"}</span>
        <p class="drill-prompt">${escapeHtml(step.answer_es)}
          <button class="chat-speak" type="button" data-speak="${escapeHtml(step.answer_es)}">🔊</button></p>
        <p class="method-en">${escapeHtml(step.prompt_en)}</p>
        <button id="methodContinueButton" class="primary-button" type="button">Next</button>
      `;
    }
  }

  player.innerHTML = `${header}<div class="drill-card">${body}</div>`;

  // Fresh recall prompts start their anticipation countdown.
  if (type === "recall" && !state.method.revealed && !methodCountdownTimer) {
    startRecallCountdown();
  }
  const input = $("methodInput");
  if (input) input.focus();
}

function handleMethodClick(event) {
  const speak = event.target.closest("[data-speak]");
  if (speak) {
    speakSpanish(speak.dataset.speak);
    return;
  }
  const step = currentMethodStep();
  if (event.target.closest("#methodQuitButton")) {
    stopMethodCountdown();
    state.method.plan = null;
    renderMethod();
    return;
  }
  if (event.target.closest("#methodAgainButton")) {
    startMethodSession(state.method.plan.method);
    return;
  }
  if (event.target.closest("#methodExitButton")) {
    state.method.plan = null;
    renderMethod();
    return;
  }
  if (!step) return;
  if (event.target.closest("#methodContinueButton")) {
    methodAdvance();
    return;
  }
  if (event.target.closest("#methodRevealButton")) {
    revealMethodStep();
    return;
  }
  if (event.target.closest("#methodGotButton")) {
    recordMethodResult(step, true);
    methodAdvance();
    return;
  }
  if (event.target.closest("#methodMissedButton")) {
    recordMethodResult(step, false);
    methodAdvance();
    return;
  }
  if (event.target.closest("#methodCheckButton")) {
    if ((step.type || step.mode) === "build") {
      const attempt = state.method.built.map((tileIndex) => step.tiles[tileIndex]).join(" ");
      checkMethodAnswer(step, attempt);
    } else {
      checkMethodAnswer(step, $("methodInput") ? $("methodInput").value : "");
    }
    return;
  }
  const buildTile = event.target.closest("[data-build]");
  if (buildTile) {
    state.method.built.push(Number(buildTile.dataset.build));
    renderMethod();
    return;
  }
  const unbuildTile = event.target.closest("[data-unbuild]");
  if (unbuildTile) {
    state.method.built.splice(Number(unbuildTile.dataset.unbuild), 1);
    renderMethod();
  }
}

// --- HQ status bar and toasts ------------------------------------------------

let hqRefreshTimer = null;

async function loadHq() {
  try {
    const hq = await api("/progress/hq");
    const previousRank = state.hqRank;
    state.hqRank = hq.rank;
    $("hqRankName").textContent = hq.rank;
    $("hqXpLine").textContent = `${hq.xp} XP`;
    $("hqXpFill").style.width = `${Math.round(hq.rank_progress * 100)}%`;
    $("hqNextRank").textContent = hq.next_rank
      ? `Next: ${hq.next_rank} at ${hq.next_rank_xp} XP`
      : "Top of the ladder";
    $("hqStreak").textContent = `🔥 ${hq.streak_days}`;
    $("hqStreak").title = hq.active_today
      ? `${hq.streak_days}-day streak — today is logged`
      : `${hq.streak_days}-day streak — train today to keep it`;
    $("hqStreak").classList.toggle("hot", hq.streak_days >= 3);
    if (previousRank && previousRank !== hq.rank) {
      showToast(`🎖️ PROMOTION: ${hq.rank}`, "gold", 4200);
    }
  } catch {
    // HQ bar is a progressive enhancement.
  }
}

function scheduleHqRefresh() {
  clearTimeout(hqRefreshTimer);
  hqRefreshTimer = setTimeout(loadHq, 1800);
}

let protocolRefreshTimer = null;

function scheduleProtocolRefresh() {
  clearTimeout(protocolRefreshTimer);
  protocolRefreshTimer = setTimeout(async () => {
    try {
      renderProtocol(await api("/program/today"));
    } catch {
      // Protocol panel refresh is best-effort.
    }
  }, 2000);
}

function showToast(message, tone = "info", duration = 2600) {
  const holder = $("toastHolder");
  const node = document.createElement("div");
  node.className = `toast ${tone}`;
  node.textContent = message;
  holder.appendChild(node);
  while (holder.children.length > 4) holder.removeChild(holder.firstChild);
  requestAnimationFrame(() => node.classList.add("show"));
  setTimeout(() => {
    node.classList.remove("show");
    setTimeout(() => node.remove(), 350);
  }, duration);
}

// --- Hover gloss dictionary --------------------------------------------------

const hoverLexicon = { terms: {}, phrases: {}, derived: {}, categories: {}, stats: null, loaded: false };
const WORD_CHAR = /[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]/;

const CATEGORY_LABELS = {
  function_words: "Function Words",
  pronouns: "Pronouns",
  verbs: "Verbs",
  verb_forms: "Verb Forms",
  people_family: "People & Family",
  home_objects: "Home & Objects",
  city_travel: "City & Travel",
  food_drink: "Food & Drink",
  body_health: "Body & Health",
  work_school: "Work & School",
  technology_cyber: "Technology & Cyber",
  soccer_sports: "Soccer & Sports",
  news_politics: "News & Politics",
  crime_investigation: "Crime & Investigation",
  nature_weather: "Nature & Weather",
  time_calendar: "Time & Calendar",
  numbers: "Numbers",
  adjectives: "Adjectives",
  adverbs_quantity: "Adverbs & Quantity",
  conversation: "Conversation",
  abstract: "Abstract & Culture",
  phrases: "Phrases & Idioms",
};

async function loadLexicon() {
  try {
    const payload = await api("/lexicon");
    hoverLexicon.terms = payload.terms || {};
    hoverLexicon.phrases = payload.phrases || {};
    hoverLexicon.derived = payload.derived || {};
    hoverLexicon.categories = payload.categories || {};
    hoverLexicon.stats = payload.stats || null;
    // Deck terms join the dictionary: multi-word entries act as phrases.
    TUTOR_ALL_TERMS.forEach((term) => {
      const normalized = normalizeSpanish(term.es);
      if (!normalized) return;
      const bucket = normalized.includes(" ") ? hoverLexicon.phrases : hoverLexicon.terms;
      if (!bucket[normalized]) bucket[normalized] = term.en;
      // "el agua" should also gloss when hovering just "agua".
      const stripped = normalized.replace(/^(el|la|los|las) /, "");
      if (stripped !== normalized && !stripped.includes(" ") && !hoverLexicon.terms[stripped]) {
        hoverLexicon.terms[stripped] = term.en;
      }
    });
    hoverLexicon.loaded = true;
    buildLibraryIndex();
    renderLibraryCategories();
    renderLibrary();
  } catch {
    // Hover gloss is a progressive enhancement.
  }
}

function wordAtPoint(x, y) {
  let node = null;
  let offset = 0;
  if (document.caretPositionFromPoint) {
    const position = document.caretPositionFromPoint(x, y);
    if (!position) return null;
    node = position.offsetNode;
    offset = position.offset;
  } else if (document.caretRangeFromPoint) {
    const range = document.caretRangeFromPoint(x, y);
    if (!range) return null;
    node = range.startContainer;
    offset = range.startOffset;
  }
  if (!node || node.nodeType !== Node.TEXT_NODE) return null;

  const text = node.textContent;
  let index = offset;
  if (index >= text.length || !WORD_CHAR.test(text[index])) {
    if (index > 0 && WORD_CHAR.test(text[index - 1])) index -= 1;
    else return null;
  }
  let start = index;
  let end = index + 1;
  while (start > 0 && WORD_CHAR.test(text[start - 1])) start -= 1;
  while (end < text.length && WORD_CHAR.test(text[end])) end += 1;

  // Confirm the pointer is actually over the word, not empty line space.
  const wordRange = document.createRange();
  wordRange.setStart(node, start);
  wordRange.setEnd(node, end);
  const rect = wordRange.getBoundingClientRect();
  if (x < rect.left - 2 || x > rect.right + 2 || y < rect.top - 2 || y > rect.bottom + 2) return null;

  const before = text.slice(0, start).match(/([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]*$/);
  const after = text.slice(end).match(/^[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)/);
  return {
    word: text.slice(start, end),
    prev: before ? before[1] : null,
    next: after ? after[1] : null,
  };
}

function lookupWord(word) {
  // Mirrors the server fallback chain: exact -> plural -> feminine -> derived.
  const terms = hoverLexicon.terms;
  if (terms[word]) return terms[word];
  if (word.length > 4 && word.endsWith("es") && terms[word.slice(0, -2)]) return terms[word.slice(0, -2)];
  if (word.length > 3 && word.endsWith("s") && terms[word.slice(0, -1)]) return terms[word.slice(0, -1)];
  if (word.length > 3 && word.endsWith("a") && terms[`${word.slice(0, -1)}o`]) return terms[`${word.slice(0, -1)}o`];
  if (word.length > 4 && word.endsWith("as") && terms[`${word.slice(0, -2)}o`]) return terms[`${word.slice(0, -2)}o`];
  const derived = hoverLexicon.derived;
  if (derived[word]) return derived[word];
  if (word.length > 3 && word.endsWith("s") && derived[word.slice(0, -1)]) return derived[word.slice(0, -1)];
  return null;
}

function glossFor(hit) {
  const word = normalizeSpanish(hit.word);
  if (!word) return null;
  const prev = hit.prev ? normalizeSpanish(hit.prev) : null;
  const next = hit.next ? normalizeSpanish(hit.next) : null;
  // Phrases outrank single words: "por favor", "sin embargo", "el agua".
  if (next && hoverLexicon.phrases[`${word} ${next}`]) {
    return { term: `${hit.word} ${hit.next}`, gloss: hoverLexicon.phrases[`${word} ${next}`] };
  }
  if (prev && hoverLexicon.phrases[`${prev} ${word}`]) {
    return { term: `${hit.prev} ${hit.word}`, gloss: hoverLexicon.phrases[`${prev} ${word}`] };
  }
  const gloss = lookupWord(word);
  return gloss ? { term: hit.word, gloss } : null;
}

// --- Library tab ---------------------------------------------------------

const libraryIndex = [];

function buildLibraryIndex() {
  libraryIndex.length = 0;
  const seen = new Set();
  Object.entries(hoverLexicon.categories).forEach(([category, terms]) => {
    terms.forEach((term) => {
      const gloss = hoverLexicon.terms[term];
      if (!gloss || seen.has(term)) return;
      seen.add(term);
      libraryIndex.push({ term, gloss, category });
    });
  });
  Object.entries(hoverLexicon.phrases).forEach(([term, gloss]) => {
    if (seen.has(term)) return;
    seen.add(term);
    libraryIndex.push({ term, gloss, category: "phrases" });
  });
  libraryIndex.sort((a, b) => a.term.localeCompare(b.term));
}

function renderLibraryCategories() {
  const select = $("libraryCategory");
  const options = ['<option value="all">All Categories</option>'];
  Object.keys(hoverLexicon.categories).forEach((category) => {
    options.push(`<option value="${escapeHtml(category)}">${escapeHtml(CATEGORY_LABELS[category] || category)}</option>`);
  });
  options.push('<option value="phrases">Phrases & Idioms</option>');
  select.innerHTML = options.join("");
}

function renderLibrary() {
  const query = normalizeSpanish($("librarySearch").value);
  const category = $("libraryCategory").value;
  const matches = libraryIndex.filter((entry) => {
    if (category !== "all" && entry.category !== category) return false;
    if (!query) return true;
    return entry.term.includes(query) || entry.gloss.toLowerCase().includes(query);
  });

  const shown = matches.slice(0, 200);
  const stats = hoverLexicon.stats;
  const statsLine = stats
    ? ` · Library holds ${stats.terms} terms, ${stats.phrases} phrases, and ${stats.derived_forms} conjugated forms`
    : "";
  $("libraryCount").textContent = `${matches.length} match(es), showing ${shown.length}${statsLine}.`;

  $("libraryList").innerHTML = shown
    .map(
      (entry) => `
        <div class="library-row">
          <button class="chat-speak" type="button" data-speak="${escapeHtml(entry.term)}">🔊</button>
          <strong>${escapeHtml(entry.term)}</strong>
          <span>${escapeHtml(entry.gloss)}</span>
          <em>${escapeHtml(CATEGORY_LABELS[entry.category] || entry.category)}</em>
        </div>
      `,
    )
    .join("") || '<p class="list-empty">No matches. Try a shorter search.</p>';
}

let activeGlossHit = null;

function hideHoverGloss() {
  activeGlossHit = null;
  const tip = $("hoverGloss");
  if (!tip.hidden) tip.hidden = true;
}

async function captureActiveGloss(event) {
  // Click a hover-glossed word to mine it into the Captured deck.
  if (!activeGlossHit) return;
  const zone = event.target.closest(".gloss-zone");
  if (!zone || event.target.closest("button, a, input, select, textarea")) return;
  const hit = activeGlossHit;
  try {
    const result = await api("/tutor/capture", {
      method: "POST",
      body: JSON.stringify({
        term: hit.term.toLowerCase(),
        translation: hit.gloss,
        context: hit.context || "",
      }),
    });
    if (result.already_captured) {
      showToast(`🎯 Already tracking: ${result.term}`, "info", 1800);
    } else {
      showToast(`🎯 Captured: ${result.term} — it will start appearing in drills.`, "good", 2600);
      await pullMastery();
      scheduleHqRefresh();
    }
  } catch (error) {
    setStatus(error.message, true);
  }
}

function handleGlossHover(event) {
  if (!hoverLexicon.loaded) return;
  const zone = event.target.closest(".gloss-zone");
  // Never gloss quiz/drill answer options — that would leak answers.
  if (!zone || event.target.closest(".option-button")) {
    hideHoverGloss();
    return;
  }
  const hit = wordAtPoint(event.clientX, event.clientY);
  const found = hit ? glossFor(hit) : null;
  if (!found) {
    hideHoverGloss();
    return;
  }
  activeGlossHit = found;

  const captured = !!state.capturedIds && state.capturedIds.has(`captured:${normalizeSpanish(found.term)}`);
  const tip = $("hoverGloss");
  tip.innerHTML = `<strong>${escapeHtml(found.term.toLowerCase())}</strong> ${escapeHtml(found.gloss)}<span class="gloss-hint">${captured ? "🎯 tracked" : "click to capture"}</span>`;
  tip.hidden = false;
  const pad = 14;
  const width = tip.offsetWidth;
  const height = tip.offsetHeight;
  let left = event.clientX + pad;
  let top = event.clientY + pad + 4;
  if (left + width > window.innerWidth - 8) left = event.clientX - width - pad;
  if (top + height > window.innerHeight - 8) top = event.clientY - height - pad;
  tip.style.left = `${Math.max(4, left)}px`;
  tip.style.top = `${Math.max(4, top)}px`;
}

const SAMPLE_INTEL = [
  "El equipo de seguridad detecta actividad sospechosa en la red porque un usuario abre un correo con un archivo peligroso. El analista revisa las alertas y escribe un informe claro. Después, el equipo cierra el acceso y protege el sistema. La investigación sigue porque hay más pistas en los datos.",
  "El equipo gana el partido porque el delantero marca dos goles en la segunda parte. El portero hace una parada importante cuando el rival avanza. Después del partido, el entrenador explica el plan y los jugadores celebran con la gente. La temporada sigue la próxima semana.",
  "El periodista investiga el caso porque una fuente habla de un acuerdo secreto. La policía busca evidencia en la oficina y encuentra documentos importantes. El gobierno responde con una declaración corta. Sin embargo, hay más preguntas que respuestas y la investigación continúa.",
];

function loadTextFile(file) {
  const reader = new FileReader();
  reader.onload = () => {
    $("sourceText").value = String(reader.result || "");
    const isSubtitle = /\.(srt|vtt)$/i.test(file.name);
    if (isSubtitle) $("sourceType").value = "subtitle";
    setStatus(`Loaded ${file.name} (${Math.round(file.size / 1024)} KB). Hit Import + Generate.`);
    showToast(
      isSubtitle ? "📄 Subtitles loaded — timestamps get stripped on import." : `📄 ${file.name} loaded.`,
      "info",
      2600,
    );
  };
  reader.onerror = () => setStatus(`Could not read ${file.name}.`, true);
  reader.readAsText(file);
}

const WRITING_PROMPTS = [
  (title) => `SUMMARY: In 5 sentences, summarize "${title}". Use past tenses and at least one connector.`,
  (title) => `OPINION: Do you agree with what happens in "${title}"? Write "creo que..." / "no creo que..." and explain porque.`,
  (title) => `INTERROGATION: Write 5 questions you would ask the main actor of "${title}". Use dónde, por qué, quién, cuándo, cómo.`,
  (title) => `PREDICTION: What happens next after "${title}"? Use "va a + infinitive" or the future tense.`,
  (title) => `RETELLING: Retell "${title}" from another actor's point of view. Watch your verb persons.`,
  () => "FREE WRITE: Write about anything — but use 3 terms from your weak-signal list and one connector.",
];

function renderWritingPrompt(advance = false) {
  if (advance) {
    state.writingPromptIndex = ((state.writingPromptIndex ?? new Date().getDay() % WRITING_PROMPTS.length) + 1) % WRITING_PROMPTS.length;
  } else if (state.writingPromptIndex === undefined) {
    state.writingPromptIndex = new Date().getDay() % WRITING_PROMPTS.length;
  }
  const title = state.activeLesson?.title || "your latest reading";
  $("writingPromptText").textContent = WRITING_PROMPTS[state.writingPromptIndex](title);
}

async function exportAnki() {
  $("exportAnkiButton").disabled = true;
  try {
    const result = await api("/exports/anki", { method: "POST" });
    showToast(`🃏 ${result.cards} Anki cards exported.`, "good", 3200);
    setStatus(`Anki TSV saved: ${result.path}`);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    $("exportAnkiButton").disabled = false;
  }
}

function loadSampleIntel() {
  const sample = SAMPLE_INTEL[Math.floor(Math.random() * SAMPLE_INTEL.length)];
  $("sourceText").value = sample;
  const topics = ["cybersecurity", "soccer", "investigation"][SAMPLE_INTEL.indexOf(sample)];
  document.querySelectorAll('input[name="topic"]').forEach((input) => {
    input.checked = input.value === topics;
  });
  setStatus("Sample intel loaded. Hit Import + Generate to build the mission brief.");
  showToast("📡 Sample transmission received.", "info", 2200);
}

function bindEvents() {
  $("generateLessonButton").addEventListener("click", importAndGenerate);
  $("sampleTextButton").addEventListener("click", loadSampleIntel);
  $("clearButton").addEventListener("click", clearIntake);
  $("refreshButton").addEventListener("click", async () => {
    setStatus("Refreshing dashboard...");
    try {
      await refreshDashboard();
      setStatus("Dashboard refreshed.");
    } catch (error) {
      setStatus(error.message, true);
    }
  });
  $("runAutopsyButton").addEventListener("click", runAutopsy);
  $("submitWritingButton").addEventListener("click", submitWriting);
  $("autopsyOutput").addEventListener("click", handleCoachClick);
  $("writingOutput").addEventListener("click", handleCoachClick);
  document.addEventListener("mousemove", handleGlossHover);
  document.addEventListener("scroll", hideHoverGloss, true);
  document.addEventListener("mouseleave", hideHoverGloss);
  document.addEventListener("click", captureActiveGloss);
  $("loadFileButton").addEventListener("click", () => $("fileInput").click());
  $("fileInput").addEventListener("change", () => {
    const file = $("fileInput").files[0];
    if (file) loadTextFile(file);
    $("fileInput").value = "";
  });
  $("newWritingPromptButton").addEventListener("click", () => renderWritingPrompt(true));
  $("exportAnkiButton").addEventListener("click", exportAnki);
  window.addEventListener("hashchange", () => showPage(currentPage()));
  $("protocolPanel").addEventListener("click", (event) => {
    const mission = event.target.closest(".mission[data-goto]");
    if (mission) location.hash = mission.dataset.goto;
  });
  $("exportLessonButton").addEventListener("click", exportLesson);
  bindTutorEvents();
}

bindEvents();
initializeTutor();
loadLexicon();
loadHq();
renderWritingPrompt();
showPage(currentPage());
refreshDashboard().catch((error) => setStatus(error.message, true));
