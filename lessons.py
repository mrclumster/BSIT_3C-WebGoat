"""
Lesson registry. Drives the catalog page, dashboard progress, and breadcrumbs.
Each lesson_id maps to its three URL endpoints (intro, challenge, complete).
"""

LESSONS = [
    {
        "id":          "sql-injection-intro",
        "title":       "SQL Injection (intro)",
        "topic":       "Injection",
        "difficulty":  "Beginner",
        "duration":    "~10 min",
        "icon":        "database",
        "description": "Bypass a vulnerable login form by injecting SQL.",
        "intro_endpoint":     "lesson_sqli_intro",
        "challenge_endpoint": "lesson_sqli_challenge",
        "complete_endpoint":  "lesson_sqli_complete",
    },
    {
        "id":          "weak-hash-md5",
        "title":       "Weak Password Storage",
        "topic":       "Cryptography",
        "difficulty":  "Beginner",
        "duration":    "~5 min",
        "icon":        "key-round",
        "description": "Crack a leaked MD5 password hash using a wordlist. See why bcrypt is different.",
        "intro_endpoint":     "lesson_weakhash_intro",
        "challenge_endpoint": "lesson_weakhash_challenge",
        "complete_endpoint":  "lesson_weakhash_complete",
    },
    {
        "id":          "xss-reflected",
        "title":       "Reflected XSS",
        "topic":       "Injection",
        "difficulty":  "Beginner",
        "duration":    "~5 min",
        "icon":        "code-2",
        "description": "Inject a script payload into a page that renders input without escaping.",
        "intro_endpoint":     "lesson_xss_intro",
        "challenge_endpoint": "lesson_xss_challenge",
        "complete_endpoint":  "lesson_xss_complete",
    },
    {
        "id":          "idor-profile",
        "title":       "Insecure Direct Object Reference",
        "topic":       "Access Control",
        "difficulty":  "Intermediate",
        "duration":    "~5 min",
        "icon":        "user-x",
        "description": "Access another user's profile by changing the ID in the URL.",
        "intro_endpoint":     "lesson_idor_intro",
        "challenge_endpoint": "lesson_idor_challenge",
        "complete_endpoint":  "lesson_idor_complete",
    },
    {
        "id":          "brute-force",
        "title":       "Missing Rate Limit",
        "topic":       "Authentication",
        "difficulty":  "Beginner",
        "duration":    "~5 min",
        "icon":        "zap-off",
        "description": "Brute-force a 4-digit PIN against an endpoint with no throttling.",
        "intro_endpoint":     "lesson_brute_intro",
        "challenge_endpoint": "lesson_brute_challenge",
        "complete_endpoint":  "lesson_brute_complete",
    },
]

def lessons_with_status(is_complete_fn):
    """Returns LESSONS with a 'completed' bool added to each, using the given check."""
    out = []
    for L in LESSONS:
        out.append({**L, "completed": is_complete_fn(L["id"])})
    return out

def get_lesson(lesson_id: str):
    for L in LESSONS:
        if L["id"] == lesson_id:
            return L
    return None
