const state = {
  activeLesson: null,
  latestLessons: [],
  vocabulary: [],
  reviewDue: { mistakes: [], review_items: [] },
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

  if (!lesson) {
    $("lessonOutput").className = "lesson-output empty-state";
    $("lessonOutput").innerHTML = "<h3>No lesson loaded</h3><p>Paste Spanish source text to generate the first drill.</p>";
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

  $("lessonOutput").className = "lesson-output";
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

function renderReviewDue() {
  const list = $("reviewList");
  const reviews = state.reviewDue.review_items || [];
  const mistakes = state.reviewDue.mistakes || [];
  const items = [
    ...reviews.map((item) => `[${item.item_type}] ${item.prompt}`),
    ...mistakes.map((item) => `[mistake] ${item.original_input} -> ${item.correction}`),
  ];

  if (!items.length) {
    list.innerHTML = '<p class="list-empty">Nothing due.</p>';
    return;
  }
  list.innerHTML = `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

async function refreshDashboard() {
  const [health, lessons, vocabulary, reviewDue] = await Promise.all([
    api("/health"),
    api("/lessons?limit=12"),
    api("/vocabulary"),
    api("/review/due"),
  ]);
  renderHealth(health);
  state.latestLessons = lessons;
  state.vocabulary = vocabulary;
  state.reviewDue = reviewDue;
  renderLessonList();
  renderVocabulary();
  renderReviewDue();
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
    $("autopsyOutput").innerHTML = `<pre>${escapeHtml(JSON.stringify(result, null, 2))}</pre>`;
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
    $("writingOutput").innerHTML = `<pre>${escapeHtml(JSON.stringify(result, null, 2))}</pre>`;
    setStatus(`Writing submission #${result.id} stored.`);
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
    saveMastery();
    renderTutor();
  } catch {
    // Offline-tolerant: keep local mastery.
  }
}

function bumpTerm(termId, delta) {
  const next = Math.max(0, Math.min(TUTOR_MAX_SIGNAL, getTermLevel(termId) + delta));
  state.tutor.mastery[termId] = next;
  saveMastery();
  scheduleMasterySync();
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
  ["decks", "study", "drill", "coach", "status"].forEach((name) => {
    $(`tutor${name[0].toUpperCase()}${name.slice(1)}View`).hidden = name !== tab;
  });
  if (tab === "drill" && !state.tutor.drill) {
    nextDrill();
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

function speakSpanish(text) {
  try {
    if (!window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "es-ES";
    utterance.rate = 0.9;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  } catch {
    // Speech synthesis is a progressive enhancement.
  }
}

function renderDrillScope() {
  $("drillScope").innerHTML = [
    '<option value="all">All Decks</option>',
    ...TUTOR_DECKS.map((deck) => `<option value="${deck.id}">${escapeHtml(deck.name)}</option>`),
  ].join("");
  $("drillScope").value = state.tutor.drillScope;
}

function drillPool() {
  if (state.tutor.drillScope === "all") return TUTOR_ALL_TERMS;
  return TUTOR_ALL_TERMS.filter((term) => term.deck === state.tutor.drillScope);
}

function nextDrill() {
  const pool = drillPool();
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
    $("drillCard").innerHTML = '<p class="list-empty">No drill loaded.</p>';
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
  } else {
    state.tutor.drillStreak = 0;
    bumpTerm(state.tutor.drill.target.id, -1);
  }
  renderDrill();
}

function renderTutorStatus() {
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

function bindEvents() {
  $("generateLessonButton").addEventListener("click", importAndGenerate);
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
  $("exportLessonButton").addEventListener("click", exportLesson);
  bindTutorEvents();
}

bindEvents();
initializeTutor();
refreshDashboard().catch((error) => setStatus(error.message, true));
