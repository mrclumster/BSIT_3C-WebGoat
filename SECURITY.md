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

---

## Appendix: WebGoat-Intermediate Lesson Exploits

The five lessons under `/lessons` deliberately demonstrate working exploit chains in isolated demo routes. Each chain teaches *why* common naive defenses fail. None of these vulnerabilities exist in the surrounding production routes (`/login`, `/register`).

### SQL Injection (`/lesson/sqli`)
- **S1 — case-sensitive blacklist bypass.** A naive WAF rejects `UNION`, `OR `, `SELECT`. SQL is case-insensitive, so `oR` / `UnIoN sElEcT` sail past. Real fix: parameterized queries (input is data, not code), not keyword filtering.
- **S2 — UNION-based extraction.** A `LIKE '%term%'` interpolation lets an attacker `UNION SELECT` arbitrary columns from any table. Mitigation: parameterize, plus principle-of-least-privilege on the DB user.
- **S3 — blind boolean SQLi.** Even with no error output, a binary "exists/doesn't" response leaks one bit per request — enough to extract any string with `SUBSTR()` probes. Mitigation: parameterize, generic responses, anomaly detection on probe-shaped traffic.

### Browser Devtools Primer (`/lesson/devtools`)
- **S1 — View Source.** HTML comments ship to the browser. Anything stored in a comment is reachable via `Ctrl+U` regardless of the rendered UI. Never put secrets, TODOs, or hints in the served HTML.
- **S2 — Inspect Element.** `type="hidden"` controls visual rendering only — the DOM still holds the value, and any user can read it via the Elements panel.
- **S3 — Console.** Any global JS variable is reachable from the Console. Base64 / character-substitution "obfuscation" is reversible in one line (`atob(...)`).
- **S4 — Network tab.** Every request and its full headers (request and response) are visible. Diagnostic data left in `X-*` headers leaks to anyone with devtools.

### Client-Side Trust (`/lesson/client-side`)
- **S1 — hidden price field.** Server trusted a price the client sent. Always re-look-up the canonical price on the server using a product id, never accept a price from the form.
- **S2 — role cookie.** A cookie containing `role=guest` is just attacker-writable storage. Authorization data must be a server-side session lookup or a signed token that the server validates.
- **S3 — localStorage session.** localStorage is fully readable/writable by the user. Don't store authorization claims there; if you must, sign them with a server-only key and verify the signature.
- **S4 — disabled button.** The `disabled` attribute is a UI hint, not an authorization check. Servers must reject the action regardless of how the request was submitted.

### Cross-Site Scripting (`/lesson/xss`)
- **S1 — tag-stripping naive sanitizer.** Stripping `<script>` does nothing about event handlers (`onerror=`). Use context-aware output encoding and CSP, not blocklists.
- **S2 — stored XSS, on*= filter.** `<iframe srcdoc="...">` carries inner HTML through the outer-attribute filter. Mitigation: a real HTML sanitizer (DOMPurify) and CSP without `unsafe-inline`.
- **S3 — DOM XSS.** `innerHTML = location.hash` is a sink → source flow. Use `textContent` for untrusted strings, or template engines that escape.

### Broken Access Control (`/lesson/access-control`)
- **S1 — predictable IDs.** No ownership check on `/profile/<id>`. Always check `current_user.id == requested_resource.owner_id`.
- **S2 — encoded IDs.** Base64 is encoding, not authorization. The vulnerability is identical to S1.
- **S3 — hidden-field tampering.** `<input type=hidden name=from_account>` lives in the client; never trust it. Derive the source account from the session.
- **S4 — mass assignment.** `dict.update(form)` lets clients set fields the form never showed (`role=admin`). Allowlist updateable fields.

