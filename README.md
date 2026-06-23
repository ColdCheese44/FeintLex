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

The launcher starts the local FastAPI server if needed, then opens:

```text
http://127.0.0.1:8044/dashboard
```

Create or refresh the Windows Desktop shortcut:

```powershell
.\scripts\create_desktop_shortcut.ps1
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
| `FEINTLEX_AI_PROVIDER` | Future provider selector, default `none` | No |
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
