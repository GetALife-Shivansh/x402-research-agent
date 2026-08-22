import sqlite3
import json

def init_db():
    conn = sqlite3.connect("research_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS researches (
            task_id TEXT PRIMARY KEY,
            query TEXT,
            report_markdown TEXT,
            plan TEXT,
            payments TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_research(task_id, query, report_markdown, plan, payments):
    conn = sqlite3.connect("research_history.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO researches (task_id, query, report_markdown, plan, payments) VALUES (?, ?, ?, ?, ?)",
        (task_id, query, report_markdown, json.dumps(plan), json.dumps(payments))
    )
    conn.commit()
    conn.close()

def get_all_researches():
    conn = sqlite3.connect("research_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM researches")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"task_id": r[0], "query": r[1], "report_markdown": r[2], "plan": json.loads(r[3]), "payments": json.loads(r[4])}
        for r in rows
    ]