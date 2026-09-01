# Citi-mazon

A repo to demonstrate an implementation of Amazon's department dynamic filter system based on user search.

## Setup

```bash
uv sync --group dev
cp .env.example .env   # SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_SERVICE_ROLE_KEY, SECRET_KEY
npm install
```

## Run

```bash
uv run python app.py
```

Portals: `/user` (search), `/vendor` (list items), `/site` (manage departments).

## Test

```bash
uv run pytest -v
```

## Supabase schema

```bash
npx supabase link --project-ref <project-ref>
npx supabase db push
```

Migrations live in `supabase/migrations/`.

## Seed data

After schema is applied, load Citi themed demo data:

```bash
uv run python scripts/seed_data.py
```

## Deploy

Render: build `pip install -r requirements.txt`, start `gunicorn app:app --bind 0.0.0.0:$PORT`. Set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SECRET_KEY`. Auto-deploy after CI passes on `main`.
