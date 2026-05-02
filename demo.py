"""
WebGoat-style SQL Injection lesson backend.

Three stages, each with:
- A challenge target the student must hit (e.g. log in as 'admin').
- A demo target used by the worked-example sandbox (e.g. log in as 'guest').
- A failure classifier that turns a wrong attempt into a teaching message.
"""
import sqlite3

DEMO_USERS = [
    ("admin",  "supersecret123"),
    ("alice",  "alicepass"),
    ("bob",    "bobpass"),
    ("guest",  "guestpass"),
]

DEMO_PRODUCTS = [
    (1, "Hardware Token", 39.95),
    (2, "VPN Subscription", 9.00),
    (3, "Password Manager", 4.50),
    (4, "Encrypted USB", 24.00),
]

SECRET_API_KEY        = "wg_live_8c3a91d7f4e2b6a5"   # production — challenge target
STAGING_API_KEY       = "wg_test_aaaa1111"           # staging — worked-example target
DEMO_SECRETS = [
    (1, SECRET_API_KEY, "production"),
    (2, STAGING_API_KEY, "staging"),
]

ADMIN_RECOVERY_TOKEN  = "Qz9kP4mN2vL7sX1c"           # 16 chars — challenge S3 target
ALICE_TOKEN_DEMO      = "irrelevant1234567"          # 17 chars — worked-example S3 (visible)
DEMO_TOKENS = [
    ("admin", ADMIN_RECOVERY_TOKEN),
    ("alice", ALICE_TOKEN_DEMO),
]

STAGE1_BLACKLIST = ["UNION", "SELECT", "OR ", " OR", "DROP", "INSERT", "DELETE"]

# Worked-example payloads (used by the sandbox endpoint).
WORKED_S1_USERNAME = "guest' oR '1'='1"
WORKED_S1_PASSWORD = "anything"
WORKED_S2_TERM     = "' UnIoN SeLeCt api_key, env FROM secrets --"
WORKED_S3_PROBE    = "alice' AND SUBSTR((SELECT token FROM tokens WHERE user='alice'),1,1)='i' --"


def _build_db() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE demo_users   (id INTEGER PRIMARY KEY, username TEXT, password TEXT);
        CREATE TABLE products     (id INTEGER PRIMARY KEY, name TEXT, price REAL);
        CREATE TABLE secrets      (id INTEGER PRIMARY KEY, api_key TEXT, env TEXT);
        CREATE TABLE tokens       (user TEXT PRIMARY KEY, token TEXT);
        """
    )
    con.executemany("INSERT INTO demo_users (username, password) VALUES (?, ?)", DEMO_USERS)
    con.executemany("INSERT INTO products (id, name, price) VALUES (?, ?, ?)", DEMO_PRODUCTS)
    con.executemany("INSERT INTO secrets (id, api_key, env) VALUES (?, ?, ?)", DEMO_SECRETS)
    con.executemany("INSERT INTO tokens (user, token) VALUES (?, ?)", DEMO_TOKENS)
    con.commit()
    return con


# ----- Stage 1 ------------------------------------------------------------- #
def stage1_login(username: str, password: str) -> dict:
    blocked = next((kw for kw in STAGE1_BLACKLIST if kw in username or kw in password), None)
    if blocked:
        return {"blocked": True, "blocked_keyword": blocked, "query": None,
                "rows": [], "success": False, "logged_in_as": None, "error": None}
    con = _build_db()
    query = (
        "SELECT id, username FROM demo_users "
        f"WHERE username = '{username}' AND password = '{password}'"
    )
    try:
        rows = [dict(r) for r in con.execute(query).fetchall()]
        return {"blocked": False, "blocked_keyword": None, "query": query, "rows": rows,
                "success": bool(rows),
                "logged_in_as": rows[0]["username"] if rows else None,
                "error": None}
    except sqlite3.Error as e:
        return {"blocked": False, "blocked_keyword": None, "query": query, "rows": [],
                "success": False, "logged_in_as": None, "error": str(e)}
    finally:
        con.close()


def stage1_solved(result: dict) -> bool:
    """Challenge: solved iff logged in as 'admin'."""
    return bool(result.get("success") and result.get("logged_in_as") == "admin")


def stage1_classify_failure(username: str, password: str, result: dict) -> str | None:
    if result.get("blocked"):
        return (f"Your input contains the blacklisted keyword <code>{result['blocked_keyword'].strip()}</code> "
                "(case-sensitive). Try mixed-case (e.g. <code>oR</code>) — SQL is case-insensitive but the filter isn't.")
    if not result.get("success"):
        if "'" not in username and "'" not in password:
            return "No SQL injection attempt detected. Inject a quote and add your own SQL clause."
        return "Your payload didn't return any rows. Check the quoting — the WHERE clause must remain valid SQL."
    if result.get("logged_in_as") and result["logged_in_as"] != "admin":
        return (f"You logged in as <code>{result['logged_in_as']}</code> (great — the bypass works!), "
                "but the challenge needs <code>admin</code> specifically. Put <code>admin</code> at the start of your username.")
    return None


# ----- Stage 2 ------------------------------------------------------------- #
def stage2_search(term: str) -> dict:
    con = _build_db()
    query = f"SELECT name, price FROM products WHERE name LIKE '%{term}%'"
    try:
        rows = [dict(r) for r in con.execute(query).fetchall()]
        return {"query": query, "rows": rows, "error": None}
    except sqlite3.Error as e:
        return {"query": query, "rows": [], "error": str(e)}
    finally:
        con.close()


def stage2_check_key(submitted: str) -> bool:
    return (submitted or "").strip() == SECRET_API_KEY


def stage2_classify_failure(submitted: str) -> str | None:
    s = (submitted or "").strip()
    if not s:
        return "Submit the API key you extracted via UNION."
    if s == STAGING_API_KEY:
        return ("That's the <em>staging</em> key (the worked example). The challenge wants the <em>production</em> key. "
                "Look at the <code>env</code> column in your UNION output and pick the row where env=<code>production</code>.")
    if s.startswith("wg_") and len(s) >= 12:
        return "Close — the format is right, but that's not the production key. Re-run your UNION and pick the production row."
    return "That doesn't look like an API key. Use UNION SELECT api_key, env FROM secrets and copy the production row."


# ----- Stage 3 ------------------------------------------------------------- #
def stage3_available(username: str) -> dict:
    con = _build_db()
    query = f"SELECT 1 FROM demo_users WHERE username = '{username}'"
    try:
        row = con.execute(query).fetchone()
        return {"query": query, "taken": row is not None, "error": None}
    except sqlite3.Error as e:
        return {"query": query, "taken": False, "error": str(e)}
    finally:
        con.close()


def stage3_check_token(submitted: str) -> bool:
    return (submitted or "").strip() == ADMIN_RECOVERY_TOKEN


def stage3_classify_failure(submitted: str) -> str | None:
    s = (submitted or "").strip()
    if not s:
        return "Submit the 16-character admin recovery token."
    if s == ALICE_TOKEN_DEMO:
        return ("That's alice's token — the worked example. The challenge wants <em>admin</em>'s token. "
                "Repeat the SUBSTR probe but with <code>WHERE user='admin'</code>.")
    if len(s) != 16:
        return f"Wrong length. The admin recovery token is exactly 16 characters; you submitted {len(s)}."
    return "That's not the right token. Re-check each character — one mistake breaks the answer."
