# Secure Login Web Application with WebGoat Lesson Integration

**Course:** Information Assurance and Security 1
**Project:** Final Project — Secure Login + WebGoat Lesson

## Hosted link

> https://YOUR-RENDER-URL.onrender.com  *(replace after deploying)*

## Group members (max 5)

1. Abdel-Aziz B. Tebbeng
2. Kendrick U. Serrano
3. *(member 3)*
4. *(member 4)*
5. *(member 5)*

## What this project is

A small Flask web app that demonstrates **secure user authentication** and
hosts a **WebGoat-style lesson** (SQL Injection — intro) built directly into
the application. After login, the user opens the lesson, exploits a
deliberately-vulnerable login form using SQL injection, and the app records
the lesson as completed against their account.

### Why this design

The project spec says the application must "display or link to one selected
WebGoat lesson" and "the selected lesson must be completed by the student."
We built the lesson *into* the app so completion is verifiable end-to-end on
the hosted link itself — the grader can log in, perform the injection, and
see the completion recorded in the database. No external setup required.

## Security features

- Passwords hashed with **bcrypt** (cost 12) — never stored in plaintext.
- All SQL uses **parameterized queries** (no string concatenation).
- **CSRF** protection on every form via Flask-WTF.
- **Rate limiting** on `/login` (5/min) and `/register` (10/hr) via Flask-Limiter.
- Session cookies flagged `HttpOnly`, `SameSite=Lax`, and `Secure` (in production).
- Server-side input validation (username regex, password length).
- Generic login error message — no user enumeration, no DB error leakage.

Full writeup: [SECURITY.md](SECURITY.md) (also rendered in-app at `/security`).

## Project structure

```
app.py                       # Flask routes
models.py                    # SQLite user store + lesson completions (parameterized queries)
security.py                  # bcrypt + input validators
demo.py                      # Vulnerable + secure login helpers for the lesson
templates/
  base.html
  login.html, register.html
  dashboard.html
  lesson_intro.html          # WebGoat-style lesson brief
  lesson_challenge.html      # Hands-on SQLi challenge (vuln vs secure)
  lesson_complete.html       # Completion proof page
  security.html, error.html
static/style.css             # Styles
SECURITY.md                  # Vulnerability awareness writeup
render.yaml                  # Render deploy config
requirements.txt
```

## Run locally

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # then edit SECRET_KEY
python app.py
```

Open http://127.0.0.1:5000 — register an account, log in, follow the dashboard
link to the lesson, and complete the SQLi challenge.

## Completing the lesson (how the grader verifies it)

1. Register / log in.
2. Click **Open lesson** on the dashboard → read the SQL Injection intro.
3. Click **Start the challenge** → use a SQL injection payload such as
   `admin' --` in the username field (any password) on the **vulnerable** form.
4. The page shows the executed SQL, the matched rows, and marks the lesson
   **Completed ✓** — the completion is persisted in the `lesson_completions`
   table against the user's account.
5. Try the same payload on the **secure** form on the same page — it fails,
   demonstrating the parameterized-query defense.

## Deploy (Render)

1. Push this repo to GitHub.
2. On [render.com](https://render.com), **New → Blueprint** and point at the repo.
3. Render reads `render.yaml`, provisions the service, generates a `SECRET_KEY`,
   and builds with `pip install -r requirements.txt`.
4. Once live, paste the URL into the **Hosted link** section above.

## Selected WebGoat lesson

**SQL Injection (intro).** Chosen because it directly mirrors the authentication
attack surface this project defends against — making the connection between
"what we built" and "what we learned" explicit. The lesson content (intro,
challenge, completion) is implemented as original code in this repository;
WebGoat is referenced only as the inspiration and topic source.
