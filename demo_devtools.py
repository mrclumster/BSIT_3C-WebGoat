"""
Browser Devtools Primer — backend for the four panel-introducing stages.

Each stage hides a flag in a place reachable only via the corresponding
devtools panel: View Source, Inspect Element, Console, Network.
Worked-example flags are simpler/more visible; challenge flags require
the student to actually use the panel.
"""

# Stage 1 — View Source (HTML comments)
DEMO_FLAG_VS = "warm-up"
FLAG_VS      = "tower-river"

# Stage 2 — Inspect Element (hidden input value)
DEMO_FLAG_INSPECT = "pillow"
FLAG_INSPECT      = "breeze-island"

# Stage 3 — Console (base64 in JS variable)
DEMO_FLAG_CONSOLE = "rocket"          # atob('cm9ja2V0')
FLAG_CONSOLE      = "canvas-field"    # atob('Y2FudmFzLWZpZWxk')
DEMO_FLAG_CONSOLE_B64 = "cm9ja2V0"
FLAG_CONSOLE_B64      = "Y2FudmFzLWZpZWxk"

# Stage 4 — Network (response header)
DEMO_FLAG_NETWORK = "bridge"
FLAG_NETWORK      = "lantern-window"


def stage1_solved(s: str) -> bool: return (s or "").strip().lower() == FLAG_VS.lower()
def stage2_solved(s: str) -> bool: return (s or "").strip().lower() == FLAG_INSPECT.lower()
def stage3_solved(s: str) -> bool: return (s or "").strip().lower() == FLAG_CONSOLE.lower()
def stage4_solved(s: str) -> bool: return (s or "").strip().lower() == FLAG_NETWORK.lower()


def classify_failure(stage_n: int, submitted: str, demo_value: str, real_value: str) -> str | None:
    s = (submitted or "").strip()
    if not s:
        return f"Submit the flag you found via the devtools panel for stage {stage_n}."
    if s.lower() == demo_value.lower():
        return ("That's the worked-example value. The challenge flag is different — find the OTHER one in the same panel.")
    if "-" not in s and stage_n != 1:
        return "Hint: most challenge flags here are two short words separated by a dash."
    return "Not the right flag. Re-open the panel; you may be looking at the wrong element/header."
