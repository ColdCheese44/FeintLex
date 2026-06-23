const state = {
  activeLesson: null,
  latestLessons: [],
  vocabulary: [],
  reviewDue: { mistakes: [], review_items: [] },
};

const $ = (id) => document.getElementById(id);

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
}

bindEvents();
refreshDashboard().catch((error) => setStatus(error.message, true));
