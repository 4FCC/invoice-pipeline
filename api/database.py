import sqlite3

DB_PATH = "invoice-pipeline.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
