# Citi-mazon

A repo to demonstrate an implementation of Amazon's department dynamic filter system based on user search.

## Setup

```bash
uv sync --group dev
cp .env.example .env   # SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY
npm install
```

## Run

```bash
uv run python app.py
```

## Test

```bash
uv run pytest -v
```

## Supabase schema

```bash
npx supabase init
npx supabase login
npx supabase link --project-ref <project-ref>
npx supabase db push
```

Migrations live in `supabase/migrations/`.

## Deploy

Render: build `pip install -r requirements.txt`, start `gunicorn app:app --bind 0.0.0.0:$PORT`. Set `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`. Auto-deploy after CI passes on `main`.
