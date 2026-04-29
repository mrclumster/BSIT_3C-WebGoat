"""
WebGoat-style SQL Injection lesson backend.

This module deliberately implements a VULNERABLE login function for educational
purposes. It operates on its own in-memory demo dataset and CANNOT touch the
real users table. The student's task is to exploit it with a SQL injection
payload; if successful, the lesson is marked complete.

DO NOT copy this pattern into real authentication code. Every query in
models.py uses parameterized statements — see the contrast.
"""
import sqlite3

# Seeded demo accounts. The student does NOT need to guess these passwords —
# the lesson is to bypass the check entirely with SQL injection.
DEMO_USERS = [
    ("admin",  "supersecret123"),
    ("alice",  "alicepass"),
    ("bob",    "bobpass"),
]


def _build_demo_db() -> sqlite3.Connection:
    """Build a fresh in-memory SQLite DB seeded with DEMO_USERS each call."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        "CREATE TABLE demo_users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)"
    )
    con.executemany(
        "INSERT INTO demo_users (username, password) VALUES (?, ?)", DEMO_USERS
    )
    con.commit()
    return con


def vulnerable_login(username: str, password: str) -> dict:
    """
    Intentionally insecure login: builds the SQL string by concatenation.
    Returns a dict with the executed query, the row found (if any), and the
    list of all rows the query matched (so the student can see the impact).
    """
    con = _build_demo_db()
    # !!! VULNERABLE ON PURPOSE !!! Do not do this in real code.
    query = (
        "SELECT id, username FROM demo_users "
        f"WHERE username = '{username}' AND password = '{password}'"
    )
    try:
        rows = con.execute(query).fetchall()
        rows_list = [dict(r) for r in rows]
        return {
            "query": query,
            "success": len(rows_list) > 0,
            "rows": rows_list,
            "error": None,
        }
    except sqlite3.Error as e:
        return {"query": query, "success": False, "rows": [], "error": str(e)}
    finally:
        con.close()


def secure_login(username: str, password: str) -> dict:
    """
    Same operation, done safely with a parameterized query — for side-by-side
    comparison. The injection payload that bypasses vulnerable_login() will
    fail here because the input is bound as a value, not parsed as SQL.
    """
    con = _build_demo_db()
    query_template = (
        "SELECT id, username FROM demo_users WHERE username = ? AND password = ?"
    )
    try:
        rows = con.execute(query_template, (username, password)).fetchall()
        rows_list = [dict(r) for r in rows]
        return {
            "query": query_template,
            "params": (username, password),
            "success": len(rows_list) > 0,
            "rows": rows_list,
            "error": None,
        }
    finally:
        con.close()


def is_injection_payload(username: str, password: str) -> bool:
    """
    Heuristic to confirm the student actually used injection (not just guessed
    a password). Triggers if the input contains classic SQLi indicators.
    """
    indicators = ["'", "--", " or ", " OR ", "/*", "*/", "#"]
    blob = f"{username} {password}"
    return any(ind in blob for ind in indicators)
