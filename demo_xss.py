"""
Lesson 3: Reflected XSS.

A vulnerable greeting page renders the user's `name` query parameter directly
into HTML without escaping. Submitting a `<script>` tag (or any HTML tag with
an event handler) demonstrates the vulnerability. The secure version renders
the same input through Jinja2's auto-escape so it is shown as text.
"""
import re

# Heuristic: did the user submit a payload that would execute JS in a browser?
XSS_PATTERN = re.compile(
    r"<\s*script\b|on\w+\s*=|javascript:|<\s*img[^>]+onerror|<\s*svg[^>]+onload",
    re.IGNORECASE,
)


def is_xss_payload(text: str) -> bool:
    return bool(XSS_PATTERN.search(text or ""))
