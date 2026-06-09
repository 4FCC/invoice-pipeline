from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date, datetime
from database import get_conn

app = FastAPI(title="Invoice Pipeline API")


class OverdueLog(BaseModel):
    invoice_id: int
    reminder_number: int
    email_body: str


class PendingLog(BaseModel):
    invoice_id: int
    days_until_due: int
    email_body: str


# -- overdue invoices --------------------
@app.get("/invoices/overdue")
def get_due_today():
    conn = get_conn()
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT
            invoice.invoice_id,
            client.name,
            client.email,
            client.company,
            invoice.amount,
            invoice.due_date,
            CAST(julianday('now') - julianday(invoice.due_date) AS INTEGER) AS days_overdue,
            COALESCE((
                SELECT COUNT(*)
                FROM reminder_log
                WHERE reminder_log.invoice_id = invoice.invoice_id
            ), 0) + 1 AS reminder_number
        FROM invoice
        JOIN client ON client.client_id = invoice.client_id
        WHERE invoice.status = 'overdue'
          AND CAST(julianday('now') - julianday(invoice.due_date) AS INTEGER) IN (3, 7, 15)
    """).fetchall()

    conn.close()
    return [dict(row) for row in rows]


# -- pending invoices --------------------
@app.get("/invoices/pending")
def get_due_soon():
    conn = get_conn()
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT
            invoice.invoice_id,
            client.name,
            client.email,
            client.company,
            invoice.amount,
            invoice.due_date,
            CAST(julianday(invoice.due_date) - julianday(date('now', '+6 hours')) AS INTEGER) AS days_until_due
        FROM invoice
        JOIN client ON client.client_id = invoice.client_id
        WHERE invoice.status = 'pending'
          AND CAST(julianday(invoice.due_date) - julianday(date('now', '+6 hours')) AS INTEGER) IN (2, 6, 14)
    """).fetchall()

    conn.close()
    return [dict(row) for row in rows]


# -- log overdue reminder --------------------
@app.post("/reminders/log-overdue")
def log_reminder(data: OverdueLog):
    conn = get_conn()
    cursor = conn.cursor()

    invoice = cursor.execute(
        "SELECT invoice_id FROM invoice WHERE invoice_id = ?", (data.invoice_id,)
    ).fetchone()

    if not invoice:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")

    cursor.execute("""
        INSERT INTO reminder_log (sent_at, reminder_number, email_body, invoice_id)
        VALUES (?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.reminder_number,
        data.email_body,
        data.invoice_id
    ))

    conn.commit()
    conn.close()
    return {"status": "logged", "invoice_id": data.invoice_id}


# -- log pending reminder --------------------
@app.post("/reminders/log-pending")
def log_pending(data: PendingLog):
    conn = get_conn()
    cursor = conn.cursor()

    invoice = cursor.execute(
        "SELECT invoice_id FROM invoice WHERE invoice_id = ?", (data.invoice_id,)
    ).fetchone()

    if not invoice:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")

    cursor.execute("""
        INSERT INTO reminder_log (sent_at, reminder_number, email_body, invoice_id)
        VALUES (?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        0,
        data.email_body,
        data.invoice_id
    ))

    conn.commit()
    conn.close()
    return {"status": "logged", "invoice_id": data.invoice_id}


# -- weekly report --------------------
@app.get("/report/weekly")
def weekly_report():
    conn = get_conn()
    cursor = conn.cursor()

    overdue = cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(amount), 0)
        FROM invoice
        WHERE status = 'overdue'
    """).fetchone()

    pending = cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(amount), 0)
        FROM invoice
        WHERE status = 'pending'
    """).fetchone()

    paid_week = cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(amount), 0)
        FROM invoice
        WHERE status = 'paid'
          AND created_at >= date('now', '-7 days')
    """).fetchone()

    reminders_sent = cursor.execute("""
        SELECT COUNT(*)
        FROM reminder_log
        WHERE sent_at >= date('now', '-7 days')
    """).fetchone()[0]

    overdue_reminders = cursor.execute("""
        SELECT COUNT(*)
        FROM reminder_log
        WHERE sent_at >= date('now', '-7 days')
          AND reminder_number > 0
    """).fetchone()[0]

    pending_reminders = cursor.execute("""
        SELECT COUNT(*)
        FROM reminder_log
        WHERE sent_at >= date('now', '-7 days')
          AND reminder_number = 0
    """).fetchone()[0]

    conn.close()
    return {
        "week": str(date.today()),
        "overdue": {
            "total_invoices": overdue[0],
            "total_amount": overdue[1]
        },
        "pending": {
            "total_invoices": pending[0],
            "total_amount": pending[1]
        },
        "paid_this_week": {
            "total_invoices": paid_week[0],
            "total_amount": paid_week[1]
        },
        "reminders_this_week": {
            "total": reminders_sent,
            "overdue": overdue_reminders,
            "pending": pending_reminders
        }
    }
