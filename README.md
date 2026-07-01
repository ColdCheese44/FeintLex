# FeintLex

FeintLex is a local-first FeintAI language intelligence trainer. The MVP focuses on Spanish reading, grammar mapping, sentence autopsy, writing correction scaffolds, vocabulary extraction, review scheduling, and Markdown exports.

Core loop:

```text
Immersion -> Sentence Autopsy -> Practice -> Correction -> Reinforcement
```

This first pass is intentionally boring and stable: SQLite, deterministic rule-based fallbacks, human-readable exports, structured logs, and no required paid AI APIs.

## MVP Goal

As Brendan, you can paste Spanish content and receive:

- A structured reading lesson
- English and Spanish summaries
- Key vocabulary
- Grammar notes
- Sentence autopsy candidates
- Comprehension questions
- Writing prompt
- Review items
- Markdown export
- Interactive scenario decks, drills, and local tutor coaching

## Architecture

```text
feintlex/
  app.py                  FastAPI app factory
  cli.py                  Typer CLI
  config.py               Environment-driven settings
  db.py                   SQLite engine/session/init
  models.py               SQLModel tables
  routes/                 API routes
  services/               Rule-based MVP services
  prompts/                Future AI prompt templates
  integrations/           Optional FeintCommand, FeintVault, Discord placeholders
data/                     SQLite database lives here by default
exports/                  Markdown lesson exports
logs/                     Structured JSON logs
scripts/                  Windows PowerShell helpers
tests/                    Offline pytest coverage
```

## Setup

Use Python 3.11 or newer.

```powershell
cd D:\Windows\FeintLex
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Copy `.env.example` to `.env` only if you need local overrides. Do not put real secrets in docs, commits, logs, or screenshots.

## Run The API

```powershell
.\scripts\run_api.ps1
```

Default URL:

```text
http://127.0.0.1:8044
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8044/health
```

## Run The Dashboard

```powershell
.\scripts\launch_dashboard.ps1
```

The launcher starts the local FastAPI server if needed, then opens the dashboard in a full-screen Brave window by default:

```text
http://127.0.0.1:8044/dashboard
```

If Brave is unavailable, FeintLex falls back to the default system browser and prints a warning.

Create or refresh the Windows Desktop shortcut:

```powershell
.\scripts\create_desktop_shortcut.ps1
```

Browser overrides:

```powershell
$env:FEINT_BROWSER_MODE="fullscreen" # fullscreen, maximized, normal, kiosk
$env:FEINT_BROWSER_PATH="C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
```

`FEINT_BROWSER` defaults to `brave`. Set `FEINT_BROWSER=default` only when you intentionally want the system browser fallback.

The dashboard now includes a Signal Tutor workspace inspired by the Senal Spanish kit:

- Scenario decks for contact, numbers, food, movement, time, and core verbs
- Flashcard study with local signal-strength mastery
- Multiple-choice drills weighted toward weak terms
- Spanish speech synthesis where the browser supports it
- Tutor coach panel for explanations, quizzes, sentence autopsy, and writing prompts
- Local progress persistence in browser storage

The tutor is AI-ready but does not require a paid API. Quick actions still use the offline rule-based endpoint at `/tutor/respond`, and the Coach tab now runs on the full chat engine below.

## AI Tutor Chat

The Coach tab is a real conversational tutor that runs fully offline:

- **Verb conjugation engine**: regular -ar/-er/-ir verbs plus common irregulars (ser, estar, ir, tener, hacer, poder, querer, decir, venir, saber, ver, dar, ...) across present, preterite, imperfect, future, and conditional. Try `conjugate tener`.
- **Offline lexicon**: word and phrase lookups in both directions. Try `what does amenaza mean` or `how do you say threat`.
- **Grammar guides**: ser vs estar, por vs para, preterite vs imperfect, gender/articles, questions, negation, and connectors. Try `ser vs estar`.
- **Targeted quizzes**: multiple-choice drills built from your weakest tracked terms and active-lesson vocabulary. Try `quiz me`.
- **Sentence autopsy in chat**: `autopsy: El equipo detecta la amenaza.`
- **Writing correction**: `correct: donde esta el problema?` returns fixes for inverted punctuation, capitalization, interrogative accents, and article-noun gender agreement, and files each issue into the mistake bank for spaced review.
- **Study plans**: `what should I study?` blends weak terms, due mistakes, and the active lesson.
- **Persistent chat history** per session key in SQLite (`/tutor/chat/history`).
- **Persistent mastery**: flashcard/drill signal strength syncs to the backend (`/tutor/mastery`) so progress survives browser resets.

Chat API:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8044/tutor/chat -Body '{"message":"conjugate tener"}' -ContentType "application/json"
```

Terminal chat:

```powershell
.\scripts\run_cli.ps1 chat                        # interactive REPL
.\scripts\run_cli.ps1 chat -m "ser vs estar"      # one-shot
```

### Optional local AI enrichment (free, no cloud)

Conversational replies can be enriched by a local [Ollama](https://ollama.com) model. This is strictly optional and fallback-first: if Ollama is not installed, not running, or errors, the rule-based tutor answers instead. Structured tools (conjugation, quizzes, autopsy) always stay deterministic.

```powershell
$env:FEINTLEX_AI_PROVIDER="ollama"
$env:FEINTLEX_OLLAMA_MODEL="llama3.2"   # any local model you have pulled
```

## API Examples

Import pasted Spanish text:

```powershell
$body = @{
  text = "El analista revisa alertas porque el equipo detecta actividad sospechosa."
  source_type = "pasted_text"
  topic_tags = @("cybersecurity")
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8044/content/import -Body $body -ContentType "application/json"
```

Generate a lesson:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8044/lessons/generate -Body '{"content_id":1}' -ContentType "application/json"
```

Run sentence autopsy:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8044/autopsy -Body '{"sentence":"El equipo analiza el partido porque necesita mejorar."}' -ContentType "application/json"
```

Ask the tutor for local coaching:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8044/tutor/respond -Body '{"message":"El equipo analiza alertas porque necesita responder.","action":"autopsy"}' -ContentType "application/json"
```

Export a lesson:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8044/exports/lesson/1
```

## CLI Usage

```powershell
.\scripts\run_cli.ps1 health
.\scripts\run_cli.ps1 import-text --file "El equipo analiza el partido porque necesita mejorar." --topic-tag soccer
.\scripts\run_cli.ps1 make-lesson --content-id 1
.\scripts\run_cli.ps1 autopsy --sentence "El equipo analiza el partido porque necesita mejorar."
.\scripts\run_cli.ps1 export-lesson --lesson-id 1
.\scripts\run_cli.ps1 review-due
```

If `--file` points to an existing text file, FeintLex reads the file. Otherwise it treats the argument as direct pasted text.

## Environment Variables

| Variable | Purpose | Required |
| --- | --- | --- |
| `FEINTLEX_ENV` | Runtime environment label | No |
| `FEINTLEX_DB_PATH` | SQLite path, default `data/feintlex.db` | No |
| `FEINTLEX_LOG_LEVEL` | Python log level | No |
| `FEINTLEX_EXPORT_DIR` | Markdown export directory | No |
| `FEINTLEX_AI_PROVIDER` | Tutor AI provider: `none` (default, offline rules) or `ollama` (local, free) | No |
| `FEINTLEX_OLLAMA_URL` | Local Ollama server URL, default `http://127.0.0.1:11434` | No |
| `FEINTLEX_OLLAMA_MODEL` | Local Ollama model name, default `llama3.2` | No |
| `FEINT_BROWSER` | Browser preference for local launchers, default `brave` | No |
| `FEINT_BROWSER_MODE` | Browser window mode: `fullscreen`, `maximized`, `normal`, `kiosk` | No |
| `FEINT_BROWSER_PATH` | Optional explicit Brave executable path | No |
| `OPENAI_API_KEY` | Optional future AI key | No |
| `ANTHROPIC_API_KEY` | Optional future AI key | No |
| `DISCORD_WEBHOOK_URL` | Optional future notifier | No |
| `FEINTCOMMAND_ENDPOINT` | Optional future FeintCommand endpoint | No |
| `FEINTVAULT_ENDPOINT` | Optional future FeintVault endpoint | No |

## Tests

```powershell
.\scripts\run_tests.ps1
```

Tests use temporary SQLite/export paths and do not require external API keys or network access.

## Data And Logs

- SQLite database: `data/feintlex.db`
- Markdown exports: `exports/`
- Structured JSON logs: `logs/feintlex.log`

Logs should never include API key values, webhook values, or `.env` contents.

## Roadmap

- Add provider-backed lesson generation while preserving rule-based fallbacks.
- Improve Spanish tense and grammar detection.
- Add article/subtitle/transcript import adapters after safe infrastructure exists.
- Add a tactical dashboard without turning FeintLex into a bloated SaaS shell.
- Wire optional FeintCommand heartbeat/events.
- Wire optional FeintVault archival for exports, vocab packs, and reports.
- Wire optional Discord notifications for daily lessons and reviews.
- Expand topics for soccer, cybersecurity, SOC analysis, investigations, news, and TV/subtitles.

## Safety Notes

- Local-first by default.
- No paid API required for MVP behavior.
- Do not print `.env` contents.
- Do not log secrets.
- Do not overwrite exports on filename collisions.
- Do not make optional integrations required for core learning.
