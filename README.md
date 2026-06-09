# invoice-pipeline

Automated invoice reminder system that notifies clients about overdue and upcoming payments — built with FastAPI, n8n, SQLite, and Docker.

---

## Problem it solves

Small businesses lose an average of 14% of revenue to late payments — not because clients refuse to pay, but because nobody follows up consistently. This system automates the entire reminder cycle: it detects which invoices need attention each day, sends personalized emails to the right people, and logs every action taken.

---

## How it works

```
n8n (daily 9am)
    │
    ├── GET /invoices/overdue    → emails clients who are 3, 7, or 15 days late
    │       └── POST /reminders/log-overdue
    │
    ├── GET /invoices/pending    → emails clients whose payment is due in 3, 7, or 15 days
    │       └── POST /reminders/log-pending
    │
    └── GET /report/weekly       → sends weekly summary to business owner (Mondays)
```

FastAPI handles all business logic and data. n8n handles scheduling, email sending, and orchestration. Neither knows too much about the other.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Automation | n8n |
| Backend | FastAPI + Python |
| Database | SQLite |
| Containerization | Docker Compose |

---

## Quick start

**Requirements:** Docker and Docker Compose installed.

```bash
# 1. Clone the repo
git clone https://github.com/4FCC/invoice-pipeline.git
cd invoice-pipeline

# 2. Start all services
docker compose up -d

# 3. Verify both services are running
curl http://localhost:8000/invoices/overdue
curl http://localhost:5678
```

**Import the workflow:**
1. Open `http://localhost:5678`
2. Create an account
3. Go to **Workflows** → **Import from file**
4. Select `n8n/workflows/invoice-pipeline-workflow.json`
5. Update the HTTP Request node URLs from `192.168.x.x:8000` to `api:8000`
6. Add your email credentials and activate the workflow

---

## API reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/invoices/overdue` | Returns invoices overdue by exactly 3, 7, or 15 days |
| `GET` | `/invoices/pending` | Returns invoices due in exactly 3, 7, or 15 days |
| `POST` | `/reminders/log-overdue` | Logs a sent overdue reminder |
| `POST` | `/reminders/log-pending` | Logs a sent pending reminder |
| `GET` | `/report/weekly` | Returns weekly summary: overdue, pending, paid, reminders sent |

Full interactive docs available at `http://localhost:8000/docs`

---

## Project structure

```
invoice-pipeline/
├── api/
│   ├── main.py              # FastAPI endpoints
│   ├── database.py          # SQLite connection
│   ├── models.py            # Pydantic models
│   ├── requirements.txt
│   └── Dockerfile
├── n8n/
│   └── workflows/
│       └── invoice-pipeline-workflow.json
├── docker-compose.yml
└── README.md
```

---

## Database schema

```sql
client        — id, name, email, company
invoice       — id, amount, due_date, status, client_id, created_at
reminder_log  — id, sent_at, reminder_number, email_body, invoice_id
```

Invoices have three possible statuses: `pending`, `overdue`, `paid`.

Reminder numbers are calculated dynamically — FastAPI counts existing logs per invoice and returns the next number. No manual tracking needed.

---

## Reminder logic

**Overdue reminders** fire on days 3, 7, and 15 after the due date. The tone escalates with each reminder.

**Pending reminders** fire on days 15, 7, and 3 before the due date. The tone is friendly and informational.

**Weekly report** runs every Monday at 8:00 AM and sends the business owner a summary of all activity from the past 7 days.

---

## Extending this project

- **Real email provider:** swap n8n's mock email node for Gmail, SMTP, or SendGrid credentials
- **Slack notifications:** add a Slack node to notify your sales channel on new overdue invoices
- **Mark as paid:** add a `PATCH /invoices/{id}/status` endpoint and wire it to a payment webhook
- **PostgreSQL:** replace SQLite with PostgreSQL for production — only `database.py` needs to change
- **Ollama integration:** add a generate-reminder endpoint that uses a local LLM to personalize each email body

---

## License

MIT
