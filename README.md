# Pinhal Junior Site

Minimal Django shell for `pinhaljunior.com.br` with an audit-ready diagnostics app.

## Features
- Project scaffold created with Django 6.0 and a diagnostics app that tracks every request/response cycle.
- `DiagnosticLog` persists structured entries (request data, metadata, response status, external services).
- `DatabaseLogHandler` writes anything routed through Django logging directly into the diagnostics table.
- Middleware automatically annotates request metadata, and helper services (`diagnostics.services.log_external_api_call`)
  allow third-party API interactions to be logged with the same schema.
- Endpoints under `/health/` and `/logs/` report availability and surface the latest diagnostics records.
- `/cadastro/` exibe um formulário completo com cabeçalho ilustrado, layout em cards para responsável e aventureiros, validação inline, seletores de dia/mês/ano e upload obrigatório apenas dos aventureiros com pré-visualização 3x4.
- Após login (a rota `/dashboard/`), o usuário vê um painel com menu contextual (“Inicial” e “Meus aventureiros”), que mostra os cartões de cada aventureiro e disponibiliza os dados para edição no futuro com base nos próximos perfis (responsável vs diretoria).
- O backend agora cria um `User` + `Responsible` e grava cada `Adventurer` com foto, contato de emergência e data de nascimento convertida a partir do trio dia/mês/ano.
- Landing screen now opens on a vibrant Clube de Aventureiros Pinhal Junior login com paleta azul bem clara, selo circular iluminado e inputs/CTA harmonizados para um visual lúdico e elegante.

## Getting started
1. Create/activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run migrations: `python manage.py migrate`.
4. Start the dev server: `python manage.py runserver`.

## Diagnostics
- All log records go through `diagnostics.logging.DatabaseLogHandler`, so nothing is lost regardless of log level.
- `DiagnosticLoggingMiddleware` (enabled in `settings.MIDDLEWARE`) records HTTP method, path, response status, and duration.
- The helper `log_external_api_call` is available to instrument integrations that talk to external services.

## Tests
- `python manage.py test` runs `diagnostics.tests` to ensure the health endpoint and middleware log path stay healthy.

## Next steps
1. Add API serializers/views for long-term log analysis (filters, pagination, protected dashboard).
2. Wire the site front-end (`pinhaljunior.com.br`) behind an async task queue or React/Vue SPA that consumes the diagnostics data.
3. Harden logging for production (dedicated database table per subsystem, log rotation/export to analytics).

## Activity log
- Record every user instruction and action in `SYSTEM_ACTIVITY.md` so the history of changes is self-documenting.
- Use `python scripts/log_activity.py --request "<user text>" --actions "<what you did>"` to append entries with the correct timestamp and structure.
# sitepinhaljuniornovo
