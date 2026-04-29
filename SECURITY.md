# Security Writeup — Vulnerability Awareness

This document explains the vulnerabilities our login system could face, what would
happen if no security measures were in place, and how each implemented defense
mitigates the risk. It supports rubric criterion **#4 — Vulnerability Awareness
and Security Explanation**.

## 1. SQL Injection

**The threat.** A login query built by string concatenation —
`"SELECT * FROM users WHERE username='" + u + "' AND password='" + p + "'"` —
can be bypassed with a payload like `' OR '1'='1`. The injected SQL turns the
WHERE clause always-true and an attacker logs in without valid credentials. Worse
payloads can dump or destroy data (`'; DROP TABLE users;--`).

**Our defense.** Every database call in `models.py` uses **parameterized queries**
(`?` placeholders). Input is bound as a value, never parsed as SQL.

## 2. Broken Authentication — Plaintext Passwords

**The threat.** If the user table leaks (a single backup, an SQL injection, an
insider), plaintext passwords are immediately usable. Because users reuse
passwords across services, attackers pivot via credential stuffing.

**Our defense.** Passwords are hashed with **bcrypt** (cost factor 12). Bcrypt is
salted (rainbow tables don't apply) and intentionally slow (brute force is
expensive).

## 3. Username Enumeration

**The threat.** Different error messages for "user not found" vs. "wrong
password" let attackers list valid usernames, which they then attack with
credential stuffing.

**Our defense.** A single generic message — *"Invalid username or password."* —
is returned for every failed login.

## 4. Brute Force / Credential Stuffing

**The threat.** Without rate limiting, attackers script thousands of login
attempts per minute.

**Our defense.** Flask-Limiter caps `/login` at **5 attempts per minute per IP**
and `/register` at 10 per hour. Limit hits return HTTP 429.

## 5. Cross-Site Request Forgery (CSRF)

**The threat.** A malicious site auto-submits a form to our app using the
victim's session cookie — performing actions the user never intended.

**Our defense.** Flask-WTF's `CSRFProtect` requires a per-session token on every
state-changing form (login, register, logout).

## 6. Session Hijacking

**The threat.** A stolen session cookie = a stolen account. Common theft vectors
are XSS reading `document.cookie`, and HTTP downgrade attacks.

**Our defense.** Session cookies are flagged:
- `HttpOnly` — JavaScript cannot read them (mitigates XSS theft).
- `SameSite=Lax` — not sent on cross-origin requests.
- `Secure` (in production) — only sent over HTTPS.
Sessions also expire after 1 hour.

## 7. Weak Input Validation

**The threat.** Unvalidated input is a vector for injection, XSS, and resource
exhaustion (oversized payloads).

**Our defense.** Server-side validation in `security.py`:
- Username regex `^[A-Za-z0-9_.-]{3,32}$`.
- Password length 8–128.
Jinja2 auto-escapes all template output, mitigating reflected XSS.

## What if none of these were implemented?

| Missing defense | Likely outcome |
|---|---|
| Hashing | Full credential compromise on any DB leak; cross-service account takeover. |
| Parameterized SQL | Trivial login bypass with `' OR '1'='1`; database dump possible. |
| Rate limiting | Online brute force succeeds against weak passwords within hours. |
| CSRF token | Forced logout, account changes from any malicious site the user visits. |
| Generic errors | Username enumeration; targeted credential stuffing. |
| Secure cookie flags | Session theft via XSS or HTTP sniffing. |
