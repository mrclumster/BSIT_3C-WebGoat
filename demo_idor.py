"""
Lesson 4: Insecure Direct Object Reference (IDOR).

A vulnerable route `/demo/idor/profile/<id>` returns the profile for any ID
without checking whether the requester owns that record. The student is
"logged in" as profile #1 in the demo; they complete the lesson by changing
the URL to view profile #2 or #3.
"""

PROFILES = {
    1: {"name": "Alice Reyes",   "email": "alice@example.com",   "ssn_last4": "0123", "balance": 142.50},
    2: {"name": "Bob Cruz",      "email": "bob@example.com",     "ssn_last4": "8421", "balance":  87.10},
    3: {"name": "Charlie Tan",   "email": "charlie@example.com", "ssn_last4": "5567", "balance": 999.99},
}

DEMO_OWNER_ID = 1  # the profile the student "owns" inside this lesson


def get_profile_vulnerable(profile_id: int):
    """No authorization check - any ID is returned."""
    return PROFILES.get(profile_id)


def get_profile_secure(profile_id: int, requester_id: int):
    """Returns the profile only if the requester owns it."""
    if profile_id != requester_id:
        return None
    return PROFILES.get(profile_id)
