# Olist Store Ops Automation

AI-powered operations automation for an e-commerce store, built on **100k real orders** from the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

Three n8n workflows run on top of a Postgres (Supabase) database and handle work an ops team usually does by hand: spotting late deliveries, triaging angry customer reviews, and writing a daily summary for the manager.

## What it does

| Workflow | What it automates | Schedule |
| --- | --- | --- |
| **1. Late Delivery Monitor** | Finds orders delivered after the promised date, flags them so nothing is reported twice, emails a summary table | Hourly |
| **2. AI Review Triage** | Takes 1 to 2 star reviews (written in Portuguese), uses Gemini to translate, categorise the complaint and draft a reply, saves results to the database | Daily, 8 AM |
| **3. Daily Ops Report** | Counts what the other workflows did in the last 24 hours, asks AI for a 3-sentence summary, emails the manager | Daily, 9 AM |

## Architecture

```
Kaggle CSVs ──► Python ETL (load_data.py) ──► Supabase Postgres
                                                   │
                       ┌───────────────────────────┼───────────────────────────┐
                       ▼                           ▼                           ▼
              Late Delivery Monitor        AI Review Triage            Daily Ops Report
              SQL → flag → email       SQL → Gemini → save         SQL stats → Gemini → email
```

## Tech stack

- **Python + pandas**: ETL, cleaning and batched upserts of ~447k rows into 6 tables
- **PostgreSQL (Supabase)**: storage, with Row Level Security on
- **n8n**: workflow orchestration and scheduling
- **Google Gemini**: translation, classification and summary writing
- **Gmail SMTP**: alert and report emails

## Results

- 160+ late orders flagged and reported automatically
- Portuguese reviews translated and sorted into categories (`late_delivery`, `wrong_item`, `damaged_product`, ...) with a ready-to-send reply draft
- A daily manager email that also caught a pipeline problem on its own: it flagged "0 reviews triaged" as needing attention

## Design decisions

- **Idempotent runs**: a `late_flagged` / `triaged_at` column means each record is processed once, so re-runs never duplicate alerts.
- **Safe SQL**: updates use query parameters (`$1`) rather than string building, to prevent SQL injection.
- **Rate-limit aware**: AI calls are batched and scheduled to stay inside the Gemini free tier; retries are capped so a refusal cannot snowball.
- **UTC timestamps**: all times are stored in UTC so 24-hour windows are correct whatever timezone n8n runs in.
- **Secrets stay out of code**: keys live in `.env` (git-ignored); exported workflows contain no credentials.

## Project structure

```
olist-ops-automation/
├── schema.sql             # table definitions
├── automation/
│   └── load_data.py       # ETL: CSV → Supabase
├── workflows/             # n8n workflow exports (import into any n8n)
│   ├── 1-late-delivery-monitor.json
│   ├── 2-ai-review-triage.json
│   └── 3-daily-ops-report.json
├── .env.example
└── .gitignore
```

## Run it yourself

1. Download the dataset from Kaggle into `data/archive/`.
2. Create a Supabase project and run `schema.sql` in the SQL Editor.
3. Copy `.env.example` to `.env` and add your Supabase URL and service key.
4. `pip install pandas supabase python-dotenv` then `python automation/load_data.py`
5. Start n8n (`npx n8n`), import the files in `workflows/`, and add your own Postgres, SMTP and Gemini credentials.

---

Built by Ayan Haider: automation and data workflows for marketing, sales and operations teams.
