import os
from datetime import timedelta
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort,
)
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models import UserStore
from security import (
    hash_password, verify_password,
    validate_username, validate_password,
)
from demo import vulnerable_login, secure_login, is_injection_payload, DEMO_USERS
import demo_weakhash, demo_xss, demo_idor, demo_brute
from lessons import LESSONS, lessons_with_status

LESSON_SQLI       = "sql-injection-intro"
LESSON_WEAKHASH   = "weak-hash-md5"
LESSON_XSS        = "xss-reflected"
LESSON_IDOR       = "idor-profile"
LESSON_BRUTE      = "brute-force"

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


def _is_complete(lesson_id):
    return users.is_lesson_complete(session["user_id"], lesson_id)


def _mark(lesson_id):
    if not _is_complete(lesson_id):
        users.mark_lesson_complete(session["user_id"], lesson_id)
        return True
    return False


@app.route("/dashboard")
@login_required
def dashboard():
    lessons = lessons_with_status(_is_complete)
    done = sum(1 for L in lessons if L["completed"])
    return render_template(
        "dashboard.html",
        username=session.get("username"),
        lessons=lessons,
        done=done,
        total=len(lessons),
    )


@app.route("/lessons")
@login_required
def lessons_catalog():
    lessons = lessons_with_status(_is_complete)
    done = sum(1 for L in lessons if L["completed"])
    return render_template(
        "lessons_catalog.html",
        lessons=lessons,
        done=done,
        total=len(lessons),
    )


@app.route("/lesson/sqli")
@login_required
def lesson_sqli_intro():
    completed = users.is_lesson_complete(session["user_id"], LESSON_SQLI)
    return render_template("lesson_intro.html", completed=completed)


@app.route("/lesson/sqli/challenge", methods=["GET", "POST"])
@login_required
def lesson_sqli_challenge():
    result_vuln = None
    result_secure = None
    just_completed = False

    if request.method == "POST":
        username = request.form.get("username") or ""
        password = request.form.get("password") or ""
        mode = request.form.get("mode", "vulnerable")

        if mode == "secure":
            result_secure = secure_login(username, password)
        else:
            result_vuln = vulnerable_login(username, password)
            # Mark lesson complete only if (a) the vulnerable login succeeded
            # AND (b) the input looks like an injection payload (so guessing a
            # real password doesn't accidentally count as completion).
            if (
                result_vuln["success"]
                and is_injection_payload(username, password)
                and not users.is_lesson_complete(session["user_id"], LESSON_SQLI)
            ):
                users.mark_lesson_complete(session["user_id"], LESSON_SQLI)
                just_completed = True

    completed = users.is_lesson_complete(session["user_id"], LESSON_SQLI)
    return render_template(
        "lesson_challenge.html",
        result_vuln=result_vuln,
        result_secure=result_secure,
        completed=completed,
        just_completed=just_completed,
        demo_usernames=[u for u, _ in DEMO_USERS],
    )


@app.route("/lesson/sqli/complete")
@login_required
def lesson_sqli_complete():
    if not _is_complete(LESSON_SQLI):
        flash("Complete the challenge first.", "warning")
        return redirect(url_for("lesson_sqli_challenge"))
    return render_template("lesson_complete.html")


# ---------------------------------------------------------------------------
# Lesson 2: Weak Password Storage (MD5)
# ---------------------------------------------------------------------------
@app.route("/lesson/weak-hash")
@login_required
def lesson_weakhash_intro():
    return render_template("weakhash_intro.html", completed=_is_complete(LESSON_WEAKHASH))


@app.route("/lesson/weak-hash/challenge", methods=["GET", "POST"])
@login_required
def lesson_weakhash_challenge():
    md5_result = None
    bcrypt_result = None
    just_completed = False
    target = request.form.get("target_user") or "alice"

    target_hash = next((u["md5"] for u in demo_weakhash.LEAKED_USERS if u["username"] == target), None)

    if request.method == "POST":
        candidate = request.form.get("candidate") or ""
        mode = request.form.get("mode", "md5")
        if mode == "bcrypt":
            ok = demo_weakhash.bcrypt_check(candidate)
            bcrypt_result = {"candidate": candidate, "matched": ok}
        else:
            ok = demo_weakhash.crack_md5(target_hash or "", candidate)
            md5_result = {"candidate": candidate, "target": target, "matched": ok, "hash": target_hash}
            if ok:
                just_completed = _mark(LESSON_WEAKHASH)

    return render_template(
        "weakhash_challenge.html",
        leaked_users=demo_weakhash.LEAKED_USERS,
        wordlist=demo_weakhash.WORDLIST,
        bcrypt_sample=demo_weakhash.BCRYPT_SAMPLE.decode("utf-8"),
        target=target,
        md5_result=md5_result,
        bcrypt_result=bcrypt_result,
        just_completed=just_completed,
        completed=_is_complete(LESSON_WEAKHASH),
    )


@app.route("/lesson/weak-hash/complete")
@login_required
def lesson_weakhash_complete():
    if not _is_complete(LESSON_WEAKHASH):
        flash("Complete the challenge first.", "warning")
        return redirect(url_for("lesson_weakhash_challenge"))
    return render_template("weakhash_complete.html")


# ---------------------------------------------------------------------------
# Lesson 3: Reflected XSS
# ---------------------------------------------------------------------------
@app.route("/lesson/xss")
@login_required
def lesson_xss_intro():
    return render_template("xss_intro.html", completed=_is_complete(LESSON_XSS))


@app.route("/lesson/xss/challenge", methods=["GET", "POST"])
@login_required
def lesson_xss_challenge():
    payload = ""
    just_completed = False
    triggered = False
    if request.method == "POST":
        payload = request.form.get("name") or ""
        if demo_xss.is_xss_payload(payload):
            triggered = True
            just_completed = _mark(LESSON_XSS)

    return render_template(
        "xss_challenge.html",
        payload=payload,
        triggered=triggered,
        just_completed=just_completed,
        completed=_is_complete(LESSON_XSS),
    )


@app.route("/lesson/xss/complete")
@login_required
def lesson_xss_complete():
    if not _is_complete(LESSON_XSS):
        flash("Complete the challenge first.", "warning")
        return redirect(url_for("lesson_xss_challenge"))
    return render_template("xss_complete.html")


# ---------------------------------------------------------------------------
# Lesson 4: IDOR
# ---------------------------------------------------------------------------
@app.route("/lesson/idor")
@login_required
def lesson_idor_intro():
    return render_template("idor_intro.html", completed=_is_complete(LESSON_IDOR))


@app.route("/lesson/idor/challenge")
@login_required
def lesson_idor_challenge():
    return render_template(
        "idor_challenge.html",
        owner_id=demo_idor.DEMO_OWNER_ID,
        profiles=demo_idor.PROFILES,
        completed=_is_complete(LESSON_IDOR),
    )


@app.route("/lesson/idor/profile/<int:profile_id>")
@login_required
def lesson_idor_view(profile_id):
    profile = demo_idor.get_profile_vulnerable(profile_id)
    just_completed = False
    if profile and profile_id != demo_idor.DEMO_OWNER_ID:
        just_completed = _mark(LESSON_IDOR)
    return render_template(
        "idor_view.html",
        profile=profile,
        profile_id=profile_id,
        owner_id=demo_idor.DEMO_OWNER_ID,
        just_completed=just_completed,
        completed=_is_complete(LESSON_IDOR),
    )


@app.route("/lesson/idor/complete")
@login_required
def lesson_idor_complete():
    if not _is_complete(LESSON_IDOR):
        flash("Complete the challenge first.", "warning")
        return redirect(url_for("lesson_idor_challenge"))
    return render_template("idor_complete.html")


# ---------------------------------------------------------------------------
# Lesson 5: Missing Rate Limit (brute force)
# ---------------------------------------------------------------------------
@app.route("/lesson/brute-force")
@login_required
def lesson_brute_intro():
    return render_template("brute_intro.html", completed=_is_complete(LESSON_BRUTE))


@app.route("/lesson/brute-force/challenge", methods=["GET", "POST"])
@login_required
def lesson_brute_challenge():
    attempts = session.get("brute_attempts", 0)
    cracked = session.get("brute_cracked", False)
    just_completed = False
    last_pin = ""

    if request.method == "POST":
        last_pin = (request.form.get("pin") or "").strip()
        attempts += 1
        if demo_brute.check_pin(last_pin):
            cracked = True
            just_completed = _mark(LESSON_BRUTE)
        session["brute_attempts"] = attempts
        session["brute_cracked"] = cracked

    return render_template(
        "brute_challenge.html",
        username=demo_brute.DEMO_USERNAME,
        common_pins=demo_brute.COMMON_PINS,
        attempts=attempts,
        cracked=cracked,
        last_pin=last_pin,
        just_completed=just_completed,
        completed=_is_complete(LESSON_BRUTE),
    )


@app.route("/lesson/brute-force/reset", methods=["POST"])
@login_required
def lesson_brute_reset():
    session["brute_attempts"] = 0
    session["brute_cracked"] = False
    return redirect(url_for("lesson_brute_challenge"))


@app.route("/lesson/brute-force/complete")
@login_required
def lesson_brute_complete():
    if not _is_complete(LESSON_BRUTE):
        flash("Complete the challenge first.", "warning")
        return redirect(url_for("lesson_brute_challenge"))
    return render_template("brute_complete.html")


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
