"""
Lesson 5: Missing Rate Limit (brute force).

A demo login accepts a 4-digit PIN with no throttling. The student is shown
the username and a small list of 'common' PINs to try; submitting the correct
one within a short time window completes the lesson. The number of attempts
is tracked so the page can show 'tries N / N' counters.
"""
DEMO_USERNAME = "victim"
DEMO_PIN = "1337"

COMMON_PINS = [
    "0000", "1111", "1234", "1212", "1004", "2000",
    "2580", "0852", "4321", "1122", "1313", "6969",
    "2580", "1990", "1991", "0007", "1337", "9999",
]


def check_pin(pin: str) -> bool:
    return pin == DEMO_PIN
