"""
Lesson 2: Weak Password Storage (MD5 cracking).

A leaked database dump of MD5-hashed passwords is shown. The student picks a
target user and tries to crack the hash by selecting a candidate from a small
wordlist. If the MD5 of the candidate matches the stored hash, the lesson is
complete. The contrast: bcrypt-hashed passwords cannot be cracked the same way
because bcrypt is slow and salted.
"""
import hashlib
import bcrypt

# Pretend leaked database. MD5 is fast and unsalted - dump + wordlist = cracked.
LEAKED_USERS = [
    {"username": "alice",   "md5": hashlib.md5(b"password123").hexdigest()},
    {"username": "bob",     "md5": hashlib.md5(b"qwerty").hexdigest()},
    {"username": "charlie", "md5": hashlib.md5(b"letmein").hexdigest()},
]

# Tiny wordlist - in reality attackers use rockyou.txt (14M+ entries).
WORDLIST = [
    "123456", "password", "qwerty", "letmein", "iloveyou",
    "admin", "welcome", "monkey", "password123", "dragon",
    "sunshine", "princess", "football", "hello", "freedom",
]

# A bcrypt-hashed equivalent of "password123" - shown for contrast.
BCRYPT_SAMPLE = bcrypt.hashpw(b"password123", bcrypt.gensalt(rounds=12))


def crack_md5(target_hash: str, candidate: str) -> bool:
    """Return True if md5(candidate) matches target_hash."""
    return hashlib.md5(candidate.encode("utf-8")).hexdigest() == target_hash


def bcrypt_check(candidate: str) -> bool:
    """For demonstration: even with the right password, bcrypt verification
    is intentionally slow per attempt - infeasible to brute-force online."""
    try:
        return bcrypt.checkpw(candidate.encode("utf-8"), BCRYPT_SAMPLE)
    except (ValueError, TypeError):
        return False
