# Secure Login Web Application with WebGoat-style Lessons

**Course:** Information Assurance and Security 1
**Project:** Final Project — Secure Login + WebGoat Lessons

## 🌐 Live application

**<https://secure-login-webgoat.onrender.com>**

> ⏱️ **First-load note for the grader:** the app is hosted on Render's free tier, which puts the service to sleep after 15 minutes of inactivity. The very first request after a long idle takes ~30–60 seconds to wake the container. After that, navigation is instant. If the page seems frozen on first visit, please give it a minute — it is starting up, not broken.

> 💾 **Database note:** the SQLite database lives at `/tmp/app.db` on Render's ephemeral filesystem and is wiped whenever the container restarts. This means accounts created in a previous session may no longer exist after the service has slept. Simply register a fresh account at the top of the grading session and complete the lessons in one sitting.

## 👥 Group members

1. Abdel-Aziz B. Tebbeng
2. Kendrick U. Serrano
3. John Erick C. Anacleto
4. Rean D. Pelota
5. Kristianni O. Lopez


## 🧭 What this project is

A Flask web application that demonstrates **secure user authentication** alongside **five hands-on, WebGoat-inspired security lessons** built directly into the app. Each lesson is broken into multiple stages following WebGoat's pedagogical pattern: the student first reads the lesson (concept + how-to + worked example with the answer visible), then completes the challenge (same technique applied to a different target).

Once a stage is solved, the completion is persisted in the database against the user's account, so the grader can log in, walk through every stage, and see verifiable progress in the dashboard and lesson catalog.

## 📚 The five lessons (18 stages total)

| # | Lesson | Stages | What it teaches |
|---|---|---|---|
| 1 | **Browser Devtools Primer** | 4 | View Source · Inspect Element · Console · Network tab — the foundational F12 skills. |
| 2 | **Client-Side Trust** | 4 | Hidden-field tampering · Cookie editing · localStorage forgery · Disabled-button bypass — why the browser is never authoritative. |
| 3 | **SQL Injection** | 3 | Filter-bypass auth · UNION-based extraction · Blind boolean inference. |
| 4 | **Cross-Site Scripting (XSS)** | 3 | Reflected XSS with tag-strip filter · Stored XSS via `iframe srcdoc` · DOM XSS via `location.hash`. |
| 5 | **Broken Access Control** | 4 | IDOR via predictable IDs · Encoded-ID tampering · Hidden-field tampering on a transfer form · Mass-assignment privilege escalation. |

Each stage page shows:

- 📖 **Lesson section** — concept, numbered how-to steps, worked example with a "Run" button against a demo target (no progress recorded).
- 🎯 **Your challenge** — apply the same technique to a different target. Smart wrong-attempt feedback explains *why* an attempt failed.
- 💡 **Progressive hints** — click to reveal one at a time. Powered by HTMX so the page does not reload.

When all stages of a lesson are solved, a celebration modal with confetti confirms completion.

## 🛡️ Security features (the surrounding application is hardened)

The lessons live in deliberately-vulnerable demo routes. The **real** authentication surface is hardened:

- Passwords hashed with **bcrypt** (cost factor 12) — never stored in plaintext.
- All real SQL uses **parameterized queries** (`?` placeholders) — no string concatenation in the production paths.
- **CSRF** protection on every form via Flask-WTF (with HTMX-friendly header token).
- **Rate limiting** on `/login` (5/min) and `/register` (10/hr) via Flask-Limiter — try logging in with five wrong passwords to see the 429 page.
- **HTTPS enforcement** on the hosted link — Render auto-issues a TLS certificate.
- Session cookies flagged `HttpOnly`, `SameSite=Lax`, and `Secure` (in production).
- Server-side input validation — username regex `^[A-Za-z0-9_.-]{3,32}$`, password length 8–128.
- Generic login error message — no user-enumeration leak, no DB error exposure.
- Reverse-proxy aware via `werkzeug.middleware.proxy_fix.ProxyFix` so request-scheme detection is correct behind Render's TLS proxy.

Full writeup with threat model and per-vulnerability defenses: [SECURITY.md](SECURITY.md) (also linked in the navigation as **"How this app stays safe"**, served at `/security`).

## ✅ Grading walkthrough

The fastest path to verify everything works:

1. Open <https://secure-login-webgoat.onrender.com> (allow ~30 s for the cold start on first visit).
2. Click **Register**. Use any username (3–32 chars: letters, digits, `.`, `_`, `-`) and any 8+ character password. Log in.
3. Open **Lessons** from the top nav. Five lessons appear, each with a `0/N` stage progress ring.
4. Open **Browser Devtools Primer**. Read the lesson briefing (concept, what you will learn, key terms, famous incidents, before-you-start). Click **Open challenge**.
5. Solve at least one stage — for example, **Stage 1 (View Source)** asks you to press `Ctrl+U` on the challenge page and find an HTML comment with a flag. Submit the value. A toast confirms the stage is solved and the catalog/dashboard counters update.
6. Continue through whichever lessons you'd like to spot-check. The full SQL Injection and XSS lessons demonstrate the OWASP-classic vulnerabilities; the Broken Access Control lesson shows IDOR and mass-assignment.
7. Toggle the **dark-mode** switch (moon/sun icon in the nav) to verify the UI is fully theme-aware.
8. Visit **How this app stays safe** in the nav for the security writeup.

If you would like to test the rate limiter, attempt to log in with five wrong passwords within a minute — the 429 "Too many attempts" page will appear.

## 🧪 End-to-end automated test

The repository ships with `smoke_test.py`, a headless walkthrough that registers a user, programmatically solves every one of the 18 stages, and asserts each completion row exists in the database:

```bash
python smoke_test.py
```

A successful run prints `ALL 18 STAGES SOLVED. Smoke test passed.`

## 🧱 Project structure

```
app.py                        # Flask routes, session, CSRF, rate limit, sandbox + hint endpoints
models.py                     # SQLite user store + per-stage completion tracking (parameterized queries)
security.py                   # bcrypt hashing + username/password validators
lessons.py                    # Lesson registry: concepts, stages, hints, vocabulary, real-world incidents
demo.py                       # SQL Injection lesson backend (3 stages)
demo_xss.py                   # XSS lesson backend (3 stages)
demo_idor.py                  # Broken Access Control lesson backend (4 stages)
demo_devtools.py              # Browser Devtools Primer backend (4 stages)
demo_clientside.py            # Client-Side Trust backend (4 stages)
templates/
  base.html                   # Master layout, nav, dark-mode toggle, toast bus, celebration modal
  _lesson_macros.html         # Reusable Jinja macros (stepper, lesson section, hints, banners)
  login.html, register.html
  dashboard.html, lessons_catalog.html
  lesson_intro.html           # 7-section WebGoat-style lesson briefing
  lesson_complete.html        # Per-lesson completion proof page
  lesson_challenge.html       # SQL Injection challenge (3-stage)
  xss_challenge.html          # XSS challenge (3-stage)
  idor_challenge.html         # Access-control challenge (4-stage)
  devtools_challenge.html     # Devtools primer challenge (4-stage)
  clientside_challenge.html   # Client-side trust challenge (4-stage)
  security.html, error.html
static/js/app.js              # Toast bus, copy-to-clipboard, HTMX integration
SECURITY.md                   # Threat model + per-vulnerability defense writeup
smoke_test.py                 # Headless 18-stage end-to-end smoke test
render.yaml, Procfile         # Render deployment config
requirements.txt
```

## 🛠️ Tech stack

- **Backend:** Python 3 · Flask 3 · SQLite · bcrypt · Flask-WTF · Flask-Limiter · Gunicorn
- **Frontend (all CDN, no build step):** Tailwind CSS · DaisyUI · Alpine.js · HTMX · Prism.js · canvas-confetti · Lucide icons · Inter / JetBrains Mono fonts
- **Deployment:** Render (free tier) — auto-deploys from `main` branch on every push.

## 💻 Running locally

```bash
python -m venv .venv
# Windows:        .venv\Scripts\activate
# macOS/Linux:    source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit SECRET_KEY
python app.py
```

Open <http://127.0.0.1:5000>.

## 🚀 Deployment

The repo is configured for **Render Blueprint** deployment. To redeploy:

1. Push to the `main` branch on GitHub.
2. Render auto-detects the push, runs `pip install -r requirements.txt`, then `gunicorn app:app`.
3. The build is live at <https://secure-login-webgoat.onrender.com> within ~2–3 minutes.

Configuration is in [render.yaml](render.yaml) (free plan, env vars, build/start commands).

---

> Selected WebGoat-aligned topics: **Browser Devtools fluency**, **Client-Side Trust** (hidden fields, cookies, localStorage, disabled buttons), **SQL Injection**, **Cross-Site Scripting**, and **Broken Access Control** — directly mirrored against the authentication and authorization surface this project defends. The lessons are original code in this repository; WebGoat is referenced as the inspiration and pedagogical model.
