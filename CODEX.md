# FeintLex Assistant Instructions

Preserve the FeintAI architecture and local-first operating style.

- Do not print secrets, `.env` contents, API keys, webhook URLs, or token values.
- Prefer small, tested changes over broad rewrites.
- Keep the Spanish MVP focus unless Brendan explicitly expands scope.
- Build deterministic rule-based fallbacks before adding AI-provider enhancements.
- Keep FeintCommand, FeintVault, and Discord integrations optional.
- Use SQLite first and keep exports Markdown-friendly.
- Keep commands Windows-friendly.
- Keep logs structured and human-readable.
- Do not add web scraping until safe import infrastructure exists.
- Run tests before final summaries whenever code changes.
- Maintain the core loop: Immersion -> Sentence Autopsy -> Practice -> Correction -> Reinforcement.
- Avoid generic flashcard-app drift and bloated SaaS scaffolding.
