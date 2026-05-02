import os
from datetime import timedelta
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, make_response,
)
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models import UserStore
from security import (
    hash_password, verify_password,
    validate_username, validate_password,
)
import demo, demo_xss, demo_idor, demo_devtools, demo_clientside
from lessons import (
    LESSONS, lessons_with_status, get_lesson, get_stage, stage_id,
)

LESSON_DEVTOOLS   = "devtools"
LESSON_CLIENTSIDE = "client-side"
LESSON_SQLI       = "sql-injection"
LESSON_XSS        = "xss"
LESSON_IDOR       = "access-control"

load_dotenv()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
    WTF_CSRF_TIME_LIMIT=3600,
)

csrf = CSRFProtect(app)
# Allow Flask-WTF to read the CSRF token from the X-CSRFToken header (HTMX sends it that way).
app.config["WTF_CSRF_HEADERS"] = ["X-CSRFToken", "X-CSRF-Token"]
limiter = Limiter(get_remote_address, app=app, default_limits=[])
users = UserStore(os.environ.get("DATABASE_PATH", "app.db"))

GENERIC_LOGIN_ERROR = "Invalid username or password."


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# --------------------------------------------------------------------------- #
# Auth (real, secure)                                                         #
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        err = validate_username(username) or validate_password(password)
        if err:
            flash(err, "error")
            return render_template("register.html", username=username), 400
        if not users.create_user(username, hash_password(password)):
            flash("That username is already taken.", "error")
            return render_template("register.html", username=username), 400
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", username="")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if validate_username(username) or validate_password(password):
            flash(GENERIC_LOGIN_ERROR, "error")
            return render_template("login.html", username=username), 401
        user = users.get_user(username)
        if user is None or not verify_password(password, user["password_hash"]):
            flash(GENERIC_LOGIN_ERROR, "error")
            return render_template("login.html", username=username), 401
        session.clear()
        session.permanent = True
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("dashboard"))
    return render_template("login.html", username="")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# --------------------------------------------------------------------------- #
# Stage tracking helpers                                                      #
# --------------------------------------------------------------------------- #
def _is_stage_complete(lesson_id: str, n: int) -> bool:
    return users.is_lesson_complete(session["user_id"], stage_id(lesson_id, n))


def _mark_stage(lesson_id: str, n: int) -> bool:
    sid = stage_id(lesson_id, n)
    if users.is_lesson_complete(session["user_id"], sid):
        return False
    users.mark_lesson_complete(session["user_id"], sid)
    return True


def _completed_set(lesson_id: str) -> set:
    L = get_lesson(lesson_id)
    if not L:
        return set()
    out = set()
    for s in L["stages"]:
        if _is_stage_complete(lesson_id, s["n"]):
            out.add(stage_id(lesson_id, s["n"]))
    return out


def _is_lesson_complete(lesson_id: str) -> bool:
    L = get_lesson(lesson_id)
    if not L:
        return False
    return all(_is_stage_complete(lesson_id, s["n"]) for s in L["stages"])


def _is_complete_for_status(lid):
    return users.is_lesson_complete(session["user_id"], lid)


def _next_unsolved(lesson_id: str, after_n: int):
    L = get_lesson(lesson_id)
    if not L:
        return None
    for s in L["stages"]:
        if s["n"] > after_n and not _is_stage_complete(lesson_id, s["n"]):
            return s["n"]
    return None


def _hint_count(lesson_id: str, n: int) -> int:
    return int(session.get(f"hints_{lesson_id}_{n}", 0))


def _reveal_hint(lesson_id: str, n: int, max_hints: int) -> None:
    key = f"hints_{lesson_id}_{n}"
    session[key] = min(int(session.get(key, 0)) + 1, max_hints)


def _stage_for_request(lesson_id: str, default: int = 1):
    L = get_lesson(lesson_id)
    try:
        n = int(request.args.get("stage", request.form.get("stage", default)))
    except (TypeError, ValueError):
        n = default
    n = max(1, min(n, len(L["stages"])))
    if n > 1 and not _is_stage_complete(lesson_id, n - 1) and not _is_stage_complete(lesson_id, n):
        for s in L["stages"]:
            if not _is_stage_complete(lesson_id, s["n"]):
                n = s["n"]
                break
    return L, n


def _hint_endpoint(lesson_id: str):
    n = int(request.form.get("stage") or 1)
    L = get_lesson(lesson_id)
    if L:
        s = get_stage(lesson_id, n)
        if s:
            _reveal_hint(lesson_id, n, len(s["hints"]))
    # HTMX request? Return just the hint partial so the page doesn't reload.
    if request.headers.get("HX-Request") == "true":
        from flask import render_template_string
        s = get_stage(lesson_id, n)
        # Build a tiny shim that calls the macro.
        return render_template_string(
            "{% from '_lesson_macros.html' import progressive_hint_inner %}"
            "{{ progressive_hint_inner(stage, revealed, reveal_url, csrf) }}",
            stage=s,
            revealed=_hint_count(lesson_id, n),
            reveal_url=request.path,
            csrf=request.headers.get("X-CSRFToken", ""),
        )
    return redirect(request.referrer or url_for("dashboard"))


# --------------------------------------------------------------------------- #
# Dashboard / catalog                                                         #
# --------------------------------------------------------------------------- #
@app.route("/dashboard")
@login_required
def dashboard():
    lessons = lessons_with_status(_is_complete_for_status)
    done = sum(1 for L in lessons if L["completed"])
    total_stages = sum(L["stages_total"] for L in lessons)
    done_stages = sum(L["stages_done"] for L in lessons)
    return render_template(
        "dashboard.html",
        username=session.get("username"),
        lessons=lessons,
        done=done, total=len(lessons),
        done_stages=done_stages, total_stages=total_stages,
    )


@app.route("/lessons")
@login_required
def lessons_catalog():
    lessons = lessons_with_status(_is_complete_for_status)
    done = sum(1 for L in lessons if L["completed"])
    return render_template("lessons_catalog.html", lessons=lessons, done=done, total=len(lessons))


# --------------------------------------------------------------------------- #
# Lesson 1: Browser Devtools Primer                                           #
# --------------------------------------------------------------------------- #
@app.route("/lesson/devtools")
@login_required
def lesson_devtools_intro():
    L = get_lesson(LESSON_DEVTOOLS)
    return render_template("lesson_intro.html", lesson=L,
                           completed=_is_lesson_complete(LESSON_DEVTOOLS),
                           completed_set=_completed_set(LESSON_DEVTOOLS))


def _devtools_ctx(stage_n, sandbox_result=None, **extra):
    if sandbox_result is None:
        sandbox_result = session.pop(f"sandbox_{LESSON_DEVTOOLS}_{stage_n}", None)
    L = get_lesson(LESSON_DEVTOOLS)
    base = {
        "lesson": L,
        "stage": get_stage(LESSON_DEVTOOLS, stage_n),
        "completed_set": _completed_set(LESSON_DEVTOOLS),
        "lesson_complete": _is_lesson_complete(LESSON_DEVTOOLS),
        "hints_revealed": _hint_count(LESSON_DEVTOOLS, stage_n),
        "demo_vs": demo_devtools.DEMO_FLAG_VS,
        "real_vs": demo_devtools.FLAG_VS,
        "demo_inspect": demo_devtools.DEMO_FLAG_INSPECT,
        "real_inspect": demo_devtools.FLAG_INSPECT,
        "demo_console_b64": demo_devtools.DEMO_FLAG_CONSOLE_B64,
        "real_console_b64": demo_devtools.FLAG_CONSOLE_B64,
        "submit_msg": None, "submit_ok": False, "feedback": None,
        "sandbox_result": sandbox_result,
        "just_solved": False, "next_stage_n": None,
    }
    base.update(extra)
    return base


@app.route("/lesson/devtools/challenge", methods=["GET", "POST"])
@login_required
def lesson_devtools_challenge():
    L, n = _stage_for_request(LESSON_DEVTOOLS)
    feedback = None
    submit_msg, submit_ok = None, False
    just_solved = False
    next_stage_n = None
    if request.method == "POST":
        n = int(request.form.get("stage") or n)
        ans = request.form.get("answer") or ""
        checker = {1: demo_devtools.stage1_solved, 2: demo_devtools.stage2_solved,
                   3: demo_devtools.stage3_solved, 4: demo_devtools.stage4_solved}[n]
        if checker(ans):
            if _mark_stage(LESSON_DEVTOOLS, n):
                just_solved = True
                next_stage_n = _next_unsolved(LESSON_DEVTOOLS, n)
            submit_msg, submit_ok = "Correct! Stage solved.", True
        else:
            demo_value = [demo_devtools.DEMO_FLAG_VS, demo_devtools.DEMO_FLAG_INSPECT,
                          demo_devtools.DEMO_FLAG_CONSOLE, demo_devtools.DEMO_FLAG_NETWORK][n - 1]
            real_value = [demo_devtools.FLAG_VS, demo_devtools.FLAG_INSPECT,
                          demo_devtools.FLAG_CONSOLE, demo_devtools.FLAG_NETWORK][n - 1]
            feedback = demo_devtools.classify_failure(n, ans, demo_value, real_value)
            submit_msg, submit_ok = "Wrong flag.", False
    ctx = _devtools_ctx(n, submit_msg=submit_msg, submit_ok=submit_ok, feedback=feedback,
                        just_solved=just_solved, next_stage_n=next_stage_n)
    return render_template("devtools_challenge.html", **ctx)


@app.route("/lesson/devtools/sandbox", methods=["POST"])
@login_required
def lesson_devtools_sandbox():
    n = int(request.form.get("stage") or 1)
    demo_payloads = {
        1: demo_devtools.DEMO_FLAG_VS,
        2: demo_devtools.DEMO_FLAG_INSPECT,
        3: demo_devtools.DEMO_FLAG_CONSOLE,
        4: demo_devtools.DEMO_FLAG_NETWORK,
    }
    msg = (f"Worked example for stage {n}: the demo flag is "
           f"\"{demo_payloads.get(n, '?')}\". The challenge flag is different — find it via the same panel.")
    session[f"sandbox_{LESSON_DEVTOOLS}_{n}"] = msg
    return redirect(url_for("lesson_devtools_challenge", stage=n))


@app.route("/lesson/devtools/network/<kind>")
def lesson_devtools_network(kind):
    """Returns a tiny JSON body with a custom header. Used by stage 4."""
    if kind == "demo":
        resp = make_response('{"ok":true,"hint":"check response headers"}', 200)
        resp.headers["X-Demo-Flag"] = demo_devtools.DEMO_FLAG_NETWORK
    else:
        resp = make_response('{"ok":true,"hint":"check response headers"}', 200)
        resp.headers["X-Flag"] = demo_devtools.FLAG_NETWORK
    resp.headers["Content-Type"] = "application/json"
    return resp


@app.route("/lesson/devtools/hint", methods=["POST"])
@login_required
def lesson_devtools_hint():
    return _hint_endpoint(LESSON_DEVTOOLS)


@app.route("/lesson/devtools/complete")
@login_required
def lesson_devtools_complete():
    if not _is_lesson_complete(LESSON_DEVTOOLS):
        flash("Solve all stages first.", "warning")
        return redirect(url_for("lesson_devtools_challenge"))
    return render_template("lesson_complete.html", lesson=get_lesson(LESSON_DEVTOOLS))


# --------------------------------------------------------------------------- #
# Lesson 2: Client-Side Trust                                                 #
# --------------------------------------------------------------------------- #
@app.route("/lesson/client-side")
@login_required
def lesson_clientside_intro():
    L = get_lesson(LESSON_CLIENTSIDE)
    return render_template("lesson_intro.html", lesson=L,
                           completed=_is_lesson_complete(LESSON_CLIENTSIDE),
                           completed_set=_completed_set(LESSON_CLIENTSIDE))


def _clientside_ctx(stage_n, sandbox_result=None, **extra):
    if sandbox_result is None:
        sandbox_result = session.pop(f"sandbox_{LESSON_CLIENTSIDE}_{stage_n}", None)
    L = get_lesson(LESSON_CLIENTSIDE)
    base = {
        "lesson": L,
        "stage": get_stage(LESSON_CLIENTSIDE, stage_n),
        "completed_set": _completed_set(LESSON_CLIENTSIDE),
        "lesson_complete": _is_lesson_complete(LESSON_CLIENTSIDE),
        "hints_revealed": _hint_count(LESSON_CLIENTSIDE, stage_n),
        "challenge_price": demo_clientside.CHALLENGE_PRODUCT_PRICE,
        "demo_price": demo_clientside.DEMO_PRODUCT_PRICE,
        "session_ls_value": demo_clientside.SESSION_LS_VALUE,
        "demo_ls_value": demo_clientside.DEMO_LS_VALUE,
        "current_role":  request.cookies.get("role", "guest"),
        "current_theme": request.cookies.get("theme", "light"),
        "buy_result": None, "cookie_result": None, "feedback": None,
        "submit_msg": None, "submit_ok": False,
        "reset_acked": False, "claim_acked": False,
        "sandbox_result": sandbox_result,
        "just_solved": False, "next_stage_n": None,
    }
    base.update(extra)
    return base


def _set_default_cookies(resp):
    """First-visit: plant the role + theme cookies for the user to tamper."""
    if request.cookies.get("role") is None:
        resp.set_cookie("role", "guest", samesite="Lax")
    if request.cookies.get("theme") is None:
        resp.set_cookie("theme", "light", samesite="Lax")
    return resp


@app.route("/lesson/client-side/challenge", methods=["GET", "POST"])
@login_required
def lesson_clientside_challenge():
    L, n = _stage_for_request(LESSON_CLIENTSIDE)
    feedback = None
    just_solved = False
    next_stage_n = None
    extra = {}

    if request.method == "POST":
        n = int(request.form.get("stage") or n)
        if n == 1:
            try:
                price = float(request.form.get("price") or "0")
            except ValueError:
                price = -1.0
            extra["buy_result"] = {"ok": demo_clientside.stage1_solved(price), "price": price}
            if demo_clientside.stage1_solved(price):
                if _mark_stage(LESSON_CLIENTSIDE, 1):
                    just_solved = True
                    next_stage_n = _next_unsolved(LESSON_CLIENTSIDE, 1)
            else:
                feedback = demo_clientside.stage1_classify_failure(price)
        elif n == 2:
            role_cookie = request.cookies.get("role")
            extra["cookie_result"] = {
                "role": role_cookie or "(unset)",
                "is_admin": demo_clientside.stage2_solved_for_cookie(role_cookie or ""),
                "flag": demo_clientside.ADMIN_COOKIE_FLAG,
            }
            if demo_clientside.stage2_solved_for_cookie(role_cookie or ""):
                if _mark_stage(LESSON_CLIENTSIDE, 2):
                    just_solved = True
                    next_stage_n = _next_unsolved(LESSON_CLIENTSIDE, 2)
            else:
                feedback = demo_clientside.stage2_classify_failure(role_cookie)
        elif n == 3:
            b64 = request.form.get("session_b64") or ""
            if demo_clientside.stage3_solved(b64):
                if _mark_stage(LESSON_CLIENTSIDE, 3):
                    just_solved = True
                    next_stage_n = _next_unsolved(LESSON_CLIENTSIDE, 3)
                extra["submit_msg"], extra["submit_ok"] = "Decoded session has is_admin=true. Stage solved.", True
            else:
                feedback = demo_clientside.stage3_classify_failure(b64)
                extra["submit_msg"] = "is_admin still false."
        elif n == 4:
            action = request.form.get("action")
            if action == "reset":
                extra["reset_acked"] = True
            elif action == "claim":
                extra["claim_acked"] = True
                if _mark_stage(LESSON_CLIENTSIDE, 4):
                    just_solved = True
                    next_stage_n = _next_unsolved(LESSON_CLIENTSIDE, 4)

    ctx = _clientside_ctx(n, feedback=feedback, just_solved=just_solved,
                          next_stage_n=next_stage_n, **extra)
    resp = make_response(render_template("clientside_challenge.html", **ctx))
    return _set_default_cookies(resp)


@app.route("/lesson/client-side/sandbox", methods=["POST"])
@login_required
def lesson_clientside_sandbox():
    n = int(request.form.get("stage") or 1)
    msgs = {
        1: f"Worked example: lower the demo $1 sticker price by editing the hidden price input. Server accepts any price ≤ $1.",
        2: f"Worked example: change the 'theme' cookie to 'dark'. Server side now sees theme={request.cookies.get('theme', 'light')}.",
        3: f"Worked example: localStorage.demo holds a base64'd JSON object {{\"hour\":\"night\"}}. In the Console, run  JSON.parse(atob(localStorage.demo))  to see it.",
        4: f"Worked example: a disabled 'Reset' button is on the page. Inspect → delete disabled → click → server replies \"reset acknowledged\".",
    }
    session[f"sandbox_{LESSON_CLIENTSIDE}_{n}"] = msgs.get(n, "")
    resp = redirect(url_for("lesson_clientside_challenge", stage=n))
    return _set_default_cookies(resp)


@app.route("/lesson/client-side/hint", methods=["POST"])
@login_required
def lesson_clientside_hint():
    return _hint_endpoint(LESSON_CLIENTSIDE)


@app.route("/lesson/client-side/complete")
@login_required
def lesson_clientside_complete():
    if not _is_lesson_complete(LESSON_CLIENTSIDE):
        flash("Solve all stages first.", "warning")
        return redirect(url_for("lesson_clientside_challenge"))
    return render_template("lesson_complete.html", lesson=get_lesson(LESSON_CLIENTSIDE))


# --------------------------------------------------------------------------- #
# Lesson 3: SQL Injection                                                     #
# --------------------------------------------------------------------------- #
def _sqli_ctx(stage_n, sandbox_result=None, **extra):
    if sandbox_result is None:
        sandbox_result = session.pop(f"sandbox_{LESSON_SQLI}_{stage_n}", None)
    L = get_lesson(LESSON_SQLI)
    base = {
        "lesson": L, "stage": get_stage(LESSON_SQLI, stage_n),
        "completed_set": _completed_set(LESSON_SQLI),
        "lesson_complete": _is_lesson_complete(LESSON_SQLI),
        "hints_revealed": _hint_count(LESSON_SQLI, stage_n),
        "form": {}, "result": None, "search_result": None, "probe_result": None,
        "submit_msg": None, "submit_ok": False, "feedback": None,
        "sandbox_result": None,
        "just_solved": False, "next_stage_n": None,
    }
    base.update(extra)
    return base


@app.route("/lesson/sqli")
@login_required
def lesson_sqli_intro():
    return render_template("lesson_intro.html", lesson=get_lesson(LESSON_SQLI),
                           completed=_is_lesson_complete(LESSON_SQLI),
                           completed_set=_completed_set(LESSON_SQLI))


@app.route("/lesson/sqli/challenge", methods=["GET", "POST"])
@login_required
def lesson_sqli_challenge():
    L, n = _stage_for_request(LESSON_SQLI)
    extra = {}
    feedback = None
    just_solved = False
    next_stage_n = None

    if request.method == "POST":
        n = int(request.form.get("stage") or n)
        if n == 1:
            uname = request.form.get("username") or ""
            pwd = request.form.get("password") or ""
            extra["form"] = {"username": uname, "password": pwd}
            r = demo.stage1_login(uname, pwd)
            extra["result"] = r
            if demo.stage1_solved(r):
                if _mark_stage(LESSON_SQLI, 1):
                    just_solved = True
                    next_stage_n = _next_unsolved(LESSON_SQLI, 1)
            else:
                feedback = demo.stage1_classify_failure(uname, pwd, r)
        elif n == 2:
            action = request.form.get("action")
            if action == "search":
                term = request.form.get("term") or ""
                extra["form"] = {"term": term}
                extra["search_result"] = demo.stage2_search(term)
            elif action == "submit":
                key = request.form.get("api_key") or ""
                if demo.stage2_check_key(key):
                    if _mark_stage(LESSON_SQLI, 2):
                        just_solved = True
                        next_stage_n = _next_unsolved(LESSON_SQLI, 2)
                    extra["submit_msg"], extra["submit_ok"] = "Correct API key. Stage 2 solved.", True
                else:
                    feedback = demo.stage2_classify_failure(key)
                    extra["submit_msg"] = "That is not the production key."
        elif n == 3:
            action = request.form.get("action")
            if action == "probe":
                u = request.form.get("probe_username") or ""
                extra["form"] = {"probe_username": u}
                extra["probe_result"] = demo.stage3_available(u)
            elif action == "submit":
                tok = request.form.get("token") or ""
                if demo.stage3_check_token(tok):
                    if _mark_stage(LESSON_SQLI, 3):
                        just_solved = True
                        next_stage_n = _next_unsolved(LESSON_SQLI, 3)
                    extra["submit_msg"], extra["submit_ok"] = "Token correct. Stage 3 solved.", True
                else:
                    feedback = demo.stage3_classify_failure(tok)
                    extra["submit_msg"] = "Token does not match."

    ctx = _sqli_ctx(n, feedback=feedback, just_solved=just_solved, next_stage_n=next_stage_n, **extra)
    return render_template("lesson_challenge.html", **ctx)


@app.route("/lesson/sqli/sandbox", methods=["POST"])
@login_required
def lesson_sqli_sandbox():
    n = int(request.form.get("stage") or 1)
    L = get_lesson(LESSON_SQLI)
    if n == 1:
        r = demo.stage1_login(demo.WORKED_S1_USERNAME, demo.WORKED_S1_PASSWORD)
        result = (f"username = {demo.WORKED_S1_USERNAME!r}\n"
                  f"password = {demo.WORKED_S1_PASSWORD!r}\n"
                  f"// query: {r['query']}\n"
                  f"// rows: {len(r['rows'])}\n"
                  f"// logged in as: {r.get('logged_in_as') or 'no row'}")
    elif n == 2:
        r = demo.stage2_search(demo.WORKED_S2_TERM)
        rows_txt = "\n".join(f"  {row['name']} | {row['price']}" for row in r["rows"])
        result = f"// query: {r['query']}\nrows:\n{rows_txt or '  (none)'}\n// staging key visible above"
    else:  # n == 3
        r = demo.stage3_available(demo.WORKED_S3_PROBE)
        result = (f"// payload: {demo.WORKED_S3_PROBE}\n"
                  f"// response: {'taken' if r['taken'] else 'available'}\n"
                  "// 'taken' confirms the guessed character is correct")
    session[f"sandbox_{LESSON_SQLI}_{n}"] = result
    return redirect(url_for("lesson_sqli_challenge", stage=n))


@app.route("/lesson/sqli/hint", methods=["POST"])
@login_required
def lesson_sqli_hint():
    return _hint_endpoint(LESSON_SQLI)


@app.route("/lesson/sqli/complete")
@login_required
def lesson_sqli_complete():
    if not _is_lesson_complete(LESSON_SQLI):
        flash("Solve all stages first.", "warning")
        return redirect(url_for("lesson_sqli_challenge"))
    return render_template("lesson_complete.html", lesson=get_lesson(LESSON_SQLI))


# --------------------------------------------------------------------------- #
# Lesson 4: XSS                                                               #
# --------------------------------------------------------------------------- #
def _xss_ctx(stage_n, sandbox_result=None, **extra):
    if sandbox_result is None:
        sandbox_result = session.pop(f"sandbox_{LESSON_XSS}_{stage_n}", None)
    L = get_lesson(LESSON_XSS)
    base = {
        "lesson": L, "stage": get_stage(LESSON_XSS, stage_n),
        "completed_set": _completed_set(LESSON_XSS),
        "lesson_complete": _is_lesson_complete(LESSON_XSS),
        "hints_revealed": _hint_count(LESSON_XSS, stage_n),
        "form": {}, "view_result": None,
        "stored_comments": demo_xss.stage2_latest_comments(),
        "feedback": None, "sandbox_result": None,
        "just_solved": False, "next_stage_n": None,
    }
    base.update(extra)
    return base


@app.route("/lesson/xss")
@login_required
def lesson_xss_intro():
    return render_template("lesson_intro.html", lesson=get_lesson(LESSON_XSS),
                           completed=_is_lesson_complete(LESSON_XSS),
                           completed_set=_completed_set(LESSON_XSS))


@app.route("/lesson/xss/challenge", methods=["GET", "POST"])
@login_required
def lesson_xss_challenge():
    L, n = _stage_for_request(LESSON_XSS)
    extra = {}
    feedback = None
    just_solved = False
    next_stage_n = None

    if request.method == "POST":
        n = int(request.form.get("stage") or n)
        if n == 1:
            payload = request.form.get("payload") or ""
            extra["form"] = {"payload": payload}
            r = demo_xss.stage1_admin_view(payload)
            extra["view_result"] = r
            if r["exfil"]:
                if _mark_stage(LESSON_XSS, 1):
                    just_solved = True
                    next_stage_n = _next_unsolved(LESSON_XSS, 1)
            else:
                feedback = demo_xss.classify_failure(1, r, payload)
        elif n == 2:
            action = request.form.get("action")
            if action == "post":
                payload = request.form.get("payload") or ""
                extra["form"] = {"payload": payload}
                demo_xss.stage2_post_comment(demo_xss.stage2_filter(payload))
                extra["stored_comments"] = demo_xss.stage2_latest_comments()
            elif action == "admin_view":
                comments = demo_xss.stage2_latest_comments()
                if comments:
                    r = demo_xss.stage2_admin_view(comments[-1])
                    extra["view_result"] = r
                    if r["exfil"]:
                        if _mark_stage(LESSON_XSS, 2):
                            just_solved = True
                            next_stage_n = _next_unsolved(LESSON_XSS, 2)
                    else:
                        feedback = demo_xss.classify_failure(2, r, comments[-1])
        elif n == 3:
            url_in = request.form.get("url") or ""
            extra["form"] = {"url": url_in}
            r = demo_xss.stage3_admin_view(url_in)
            extra["view_result"] = r
            if r["exfil"]:
                if _mark_stage(LESSON_XSS, 3):
                    just_solved = True
                    next_stage_n = _next_unsolved(LESSON_XSS, 3)
            else:
                feedback = demo_xss.classify_failure(3, r, url_in)

    ctx = _xss_ctx(n, feedback=feedback, just_solved=just_solved, next_stage_n=next_stage_n, **extra)
    return render_template("xss_challenge.html", **ctx)


@app.route("/lesson/xss/sandbox", methods=["POST"])
@login_required
def lesson_xss_sandbox():
    n = int(request.form.get("stage") or 1)
    if n == 1:
        payload = "<img src=x onerror=alert(1)>"
        r = demo_xss.stage1_admin_view(payload)
        result = (f"payload: {payload}\nrendered (post-filter): {r['rendered']}\n"
                  f"executable handler present: {r['has_exec']}\n"
                  "// the worked example only proves the filter is bypassable; the challenge needs the /steal call too")
    elif n == 2:
        payload = '<iframe srcdoc="&lt;img src=x onerror=parent.alert(1)&gt;"></iframe>'
        r = demo_xss.stage2_admin_view(payload)
        result = (f"payload: {payload}\nrendered (post-filter): {r['rendered']}\n"
                  f"executable handler present: {r['has_exec']}\n"
                  "// srcdoc carries inner HTML through the on*= filter")
    else:
        url = "/lesson/xss/dom#<img src=x onerror=document.title='hi'>"
        r = demo_xss.stage3_admin_view(url)
        result = (f"url: {url}\nfragment: {r['rendered']}\n"
                  f"would execute via innerHTML: {r['has_exec']}\n"
                  "// innerHTML refuses <script> but runs onerror on inserted nodes")
    session[f"sandbox_{LESSON_XSS}_{n}"] = result
    return redirect(url_for("lesson_xss_challenge", stage=n))


@app.route("/lesson/xss/hint", methods=["POST"])
@login_required
def lesson_xss_hint():
    return _hint_endpoint(LESSON_XSS)


@app.route("/lesson/xss/steal")
def lesson_xss_steal():
    return ("", 204)


@app.route("/lesson/xss/complete")
@login_required
def lesson_xss_complete():
    if not _is_lesson_complete(LESSON_XSS):
        flash("Solve all stages first.", "warning")
        return redirect(url_for("lesson_xss_challenge"))
    return render_template("lesson_complete.html", lesson=get_lesson(LESSON_XSS))


# --------------------------------------------------------------------------- #
# Lesson 5: Broken Access Control                                             #
# --------------------------------------------------------------------------- #
def _idor_ctx(stage_n, sandbox_result=None, **extra):
    if sandbox_result is None:
        sandbox_result = session.pop(f"sandbox_{LESSON_IDOR}_{stage_n}", None)
    L = get_lesson(LESSON_IDOR)
    base = {
        "lesson": L, "stage": get_stage(LESSON_IDOR, stage_n),
        "completed_set": _completed_set(LESSON_IDOR),
        "lesson_complete": _is_lesson_complete(LESSON_IDOR),
        "hints_revealed": _hint_count(LESSON_IDOR, stage_n),
        "owner_id": demo_idor.DEMO_OWNER_ID,
        "victim_id": demo_idor.VICTIM_ID,
        "profiles": demo_idor.PROFILES,
        "accounts": demo_idor.ACCOUNTS,
        "encode_acct": demo_idor.encode_acct,
        "my_encoded": demo_idor.encode_acct(101),
        "my_profile": demo_idor.PROFILES[demo_idor.DEMO_OWNER_ID],
        "admin_flag": demo_idor.ADMIN_FLAG,
        "form": {}, "tx_listing": None, "transfer_result": None,
        "submit_msg": None, "submit_ok": False, "feedback": None,
        "sandbox_result": None,
        "just_solved": False, "next_stage_n": None,
    }
    base.update(extra)
    return base


@app.route("/lesson/access-control")
@login_required
def lesson_idor_intro():
    return render_template("lesson_intro.html", lesson=get_lesson(LESSON_IDOR),
                           completed=_is_lesson_complete(LESSON_IDOR),
                           completed_set=_completed_set(LESSON_IDOR))


@app.route("/lesson/access-control/challenge", methods=["GET", "POST"])
@login_required
def lesson_idor_challenge():
    L, n = _stage_for_request(LESSON_IDOR)
    extra = {}
    feedback = None
    just_solved = False
    next_stage_n = None

    if request.method == "POST":
        n = int(request.form.get("stage") or n)
        if n == 2:
            tx = request.form.get("tx_id") or ""
            if demo_idor.stage2_check_tx(tx):
                if _mark_stage(LESSON_IDOR, 2):
                    just_solved = True
                    next_stage_n = _next_unsolved(LESSON_IDOR, 2)
                extra["submit_msg"], extra["submit_ok"] = "Transaction belongs to the victim. Stage solved.", True
            else:
                feedback = demo_idor.stage2_classify_failure(tx)
                extra["submit_msg"] = "Not a victim transaction id."
        elif n == 3:
            if request.form.get("action") == "reset":
                demo_idor.reset_state()
                extra["accounts"] = demo_idor.ACCOUNTS
            else:
                from_e = request.form.get("from_account") or ""
                to_e = request.form.get("to_account") or ""
                amt = request.form.get("amount") or "0"
                extra["form"] = {"from_account": from_e, "to_account": to_e, "amount": amt}
                src = demo_idor.decode_acct(from_e)
                dst = demo_idor.decode_acct(to_e)
                try:
                    amount = float(amt)
                except ValueError:
                    amount = 0.0
                if src is not None and dst is not None:
                    extra["transfer_result"] = demo_idor.transfer(src, dst, amount)
                else:
                    extra["transfer_result"] = {"ok": False, "reason": "invalid encoded account"}
                if demo_idor.stage3_solved():
                    if _mark_stage(LESSON_IDOR, 3):
                        just_solved = True
                        next_stage_n = _next_unsolved(LESSON_IDOR, 3)
                else:
                    feedback = demo_idor.stage3_classify_failure(src, dst, amount, extra["transfer_result"])
        elif n == 4:
            action = request.form.get("action")
            if action == "update":
                fields = {
                    "name":  request.form.get("name")  or demo_idor.PROFILES[demo_idor.DEMO_OWNER_ID]["name"],
                    "email": request.form.get("email") or demo_idor.PROFILES[demo_idor.DEMO_OWNER_ID]["email"],
                }
                if request.form.get("role"):
                    fields["role"] = request.form.get("role")
                demo_idor.update_profile(demo_idor.DEMO_OWNER_ID, fields)
                extra["form"] = {"role": fields.get("role", "user")}
            elif action == "submit_flag":
                flag = request.form.get("flag") or ""
                my_role = demo_idor.PROFILES[demo_idor.DEMO_OWNER_ID].get("role", "user")
                if demo_idor.stage4_check_flag(flag):
                    if _mark_stage(LESSON_IDOR, 4):
                        just_solved = True
                        next_stage_n = _next_unsolved(LESSON_IDOR, 4)
                    extra["submit_msg"], extra["submit_ok"] = "Flag accepted. Stage solved.", True
                else:
                    feedback = demo_idor.stage4_classify_failure(flag, my_role)
                    extra["submit_msg"] = "Wrong flag."

    extra["my_profile"] = demo_idor.PROFILES[demo_idor.DEMO_OWNER_ID]
    ctx = _idor_ctx(n, feedback=feedback, just_solved=just_solved, next_stage_n=next_stage_n, **extra)
    return render_template("idor_challenge.html", **ctx)


@app.route("/lesson/access-control/sandbox", methods=["POST"])
@login_required
def lesson_idor_sandbox():
    n = int(request.form.get("stage") or 1)
    if n == 1:
        bob = demo_idor.PROFILES.get(2)
        result = f"opening profile #2 (worked example):\n  name = {bob['name']}\n  email = {bob['email']}\n  ssn_last4 = {bob['ssn_last4']}\n// no ownership check ran"
    elif n == 2:
        result = f"atob('MTAx') = '101' (your own acct)\nVictim is base64('102') = '{demo_idor.encode_acct(102)}'"
    elif n == 3:
        result = f"$1 transfer FROM your own acct (MTAx) → demonstrates the form works.\nNow change from_account to MTAy (victim) and drain."
    else:
        result = f"benign mass-assignment example: theme=dark would be saved on your profile.\nThe role field works the same way — and there is no allowlist."
    session[f"sandbox_{LESSON_IDOR}_{n}"] = result
    return redirect(url_for("lesson_idor_challenge", stage=n))


@app.route("/lesson/access-control/profile/<int:profile_id>")
@login_required
def lesson_idor_view(profile_id):
    profile = demo_idor.get_profile_vulnerable(profile_id)
    just_completed = False
    if profile and demo_idor.stage1_solved(profile_id):
        just_completed = _mark_stage(LESSON_IDOR, 1)
    return render_template(
        "idor_view.html",
        profile=profile, profile_id=profile_id,
        owner_id=demo_idor.DEMO_OWNER_ID,
        just_completed=just_completed,
        completed=_is_lesson_complete(LESSON_IDOR),
    )


@app.route("/lesson/access-control/tx")
@login_required
def lesson_idor_tx():
    L = get_lesson(LESSON_IDOR)
    encoded = request.args.get("acct") or demo_idor.encode_acct(101)
    acct = demo_idor.decode_acct(encoded)
    tx_listing = demo_idor.get_transactions(acct) if acct else []
    ctx = _idor_ctx(2, form={"acct": encoded}, tx_listing=tx_listing,
                    my_profile=demo_idor.PROFILES[demo_idor.DEMO_OWNER_ID])
    return render_template("idor_challenge.html", **ctx)


@app.route("/lesson/access-control/hint", methods=["POST"])
@login_required
def lesson_idor_hint():
    return _hint_endpoint(LESSON_IDOR)


@app.route("/lesson/access-control/complete")
@login_required
def lesson_idor_complete():
    if not _is_lesson_complete(LESSON_IDOR):
        flash("Solve all stages first.", "warning")
        return redirect(url_for("lesson_idor_challenge"))
    return render_template("lesson_complete.html", lesson=get_lesson(LESSON_IDOR))


# --------------------------------------------------------------------------- #
# Static                                                                      #
# --------------------------------------------------------------------------- #
@app.route("/security")
def security_page():
    return render_template("security.html")


@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template("error.html", message="Too many attempts. Please try again later."), 429


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Page not found."), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
