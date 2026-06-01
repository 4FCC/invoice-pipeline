import sqlite3

conn = sqlite3.connect("invoice-pipeline.db")

conn = conn.cursor()

print("Connected successfully")
