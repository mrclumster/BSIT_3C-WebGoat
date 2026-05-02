"""
Client-Side Trust lesson backend.

Each stage demonstrates that the browser is attacker-controlled storage.
- S1: hidden price field — server accepts whatever client sends.
- S2: role cookie — server reads it without verifying.
- S3: localStorage session — student decodes, flips a flag, re-encodes.
- S4: disabled button — server has no enforcement, just a UI hint.
"""
import base64
import json

ADMIN_COOKIE_FLAG = "FLAG{ROLE_COOKIE_TAMPERED}"

# Stage 1 — hidden field tampering
DEMO_PRODUCT_PRICE     = 1.00     # worked example: $1 sticker
CHALLENGE_PRODUCT_PRICE = 999.99  # real product
SOLVED_PRICE_THRESHOLD = 1.00     # any price <= this counts


def stage1_solved(submitted_price: float) -> bool:
    try:
        return submitted_price is not None and float(submitted_price) <= SOLVED_PRICE_THRESHOLD
    except (TypeError, ValueError):
        return False


def stage1_classify_failure(submitted_price) -> str | None:
    try:
        p = float(submitted_price) if submitted_price not in (None, "") else None
    except (TypeError, ValueError):
        p = None
    if p is None:
        return "Submit a price. Use Inspect to edit the hidden <code>price</code> field's value."
    if p == CHALLENGE_PRODUCT_PRICE:
        return ("You sent the original price (<code>999.99</code>). Use F12 → Elements to find the hidden "
                "<code>&lt;input name=\"price\"&gt;</code> and change its value to anything ≤ $1 before submitting.")
    if p > SOLVED_PRICE_THRESHOLD:
        return f"Price ${p:.2f} is still too high. Lower it to $1.00 or less in the hidden field."
    return None


# Stage 2 — cookie tampering. Routes read request cookies directly.
def stage2_solved_for_cookie(role_cookie_value: str) -> bool:
    return (role_cookie_value or "").strip() == "admin"


def stage2_classify_failure(role_cookie_value: str | None) -> str | None:
    if not role_cookie_value or role_cookie_value == "guest":
        return ("Server still sees <code>role=guest</code>. Open F12 → Application → Cookies, "
                "edit the <code>role</code> cookie's value to <code>admin</code>, then click the button again.")
    if role_cookie_value != "admin":
        return f"Server received <code>role={role_cookie_value}</code> — needs to be exactly <code>admin</code>."
    return None


# Stage 3 — localStorage session: base64(JSON({user, is_admin}))
DEMO_LS_KEY      = "demo"
DEMO_LS_VALUE    = base64.b64encode(json.dumps({"hour": "night"}).encode()).decode()
DEMO_LS_GOAL     = "day"

SESSION_LS_KEY   = "session"
SESSION_LS_VALUE = base64.b64encode(json.dumps({"user": "you", "is_admin": False}).encode()).decode()


def parse_session(b64_value: str):
    try:
        decoded = base64.b64decode((b64_value or "").encode()).decode()
        return json.loads(decoded)
    except Exception:
        return None


def stage3_solved(b64_value: str) -> bool:
    parsed = parse_session(b64_value)
    return bool(parsed and parsed.get("is_admin") is True)


def stage3_classify_failure(b64_value: str | None) -> str | None:
    if not b64_value:
        return "Submit the modified <code>localStorage.session</code> value."
    parsed = parse_session(b64_value)
    if parsed is None:
        return "Couldn't decode that as base64-encoded JSON. Use <code>btoa(JSON.stringify({...}))</code> in the Console."
    if parsed.get("is_admin") is False:
        return ("Decoded fine but <code>is_admin</code> is still <code>false</code>. Build the new value with "
                "<code>btoa(JSON.stringify({user:'you', is_admin:true}))</code>.")
    if "is_admin" not in parsed:
        return "Your JSON doesn't have an <code>is_admin</code> key. Add it, set it to <code>true</code>, and re-encode."
    return None


# Stage 4 — disabled-button bypass. Marked solved on POST to the endpoint.
# (No special check — reaching the endpoint at all means the student
# bypassed the disabled attribute via devtools.)
def stage4_classify_failure(reached: bool) -> str | None:
    if not reached:
        return ("The 'Claim flag' button is disabled. Use F12 → Elements, find the button, delete the "
                "<code>disabled</code> attribute, and click it. Or run <code>document.getElementById('claim').click()</code> "
                "in the Console.")
    return None
