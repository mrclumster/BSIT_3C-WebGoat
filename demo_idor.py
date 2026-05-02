"""
Broken Access Control lesson — four stages.

Each stage has a worked-example target (sandbox) and a separate challenge target:
- S1: demo target = profile #2 (Bob); challenge target = profile #3 (Charlie).
- S2: demo = decode your own acct; challenge = submit a victim transaction id.
- S3: demo = $1 transfer from your own acct; challenge = drain victim's balance.
- S4: demo = mass-assign theme=dark (benign); challenge = role=admin + flag.
"""
import base64
from copy import deepcopy

DEMO_OWNER_ID = 1
DEMO_TARGET_ID = 2     # Bob — used by the worked example for S1
CHALLENGE_TARGET_ID = 3  # Charlie — required for S1 completion
VICTIM_ID = 2          # Bob — victim for S2/S3 (transactions + balance)

ADMIN_FLAG = "FLAG{ma55-a55ignment-w1ns}"

_BASE_PROFILES = {
    1: {"id": 1, "name": "Alice Reyes",   "email": "alice@example.com",   "ssn_last4": "0123", "role": "user"},
    2: {"id": 2, "name": "Bob Cruz",      "email": "bob@example.com",     "ssn_last4": "8421", "role": "user"},
    3: {"id": 3, "name": "Charlie Tan",   "email": "charlie@example.com", "ssn_last4": "5567", "role": "user"},
}

_BASE_ACCOUNTS = {
    101: {"acct_id": 101, "owner_id": 1, "balance": 142.50},
    102: {"acct_id": 102, "owner_id": 2, "balance": 999.99},
    103: {"acct_id": 103, "owner_id": 3, "balance":  87.10},
}

_BASE_TRANSACTIONS = {
    101: [{"id": "T-1001", "memo": "coffee",     "amount":  -4.50}],
    102: [{"id": "T-1042", "memo": "dividend",   "amount": +500.00},
          {"id": "T-1043", "memo": "rent paid",  "amount": -800.00}],
    103: [{"id": "T-1099", "memo": "refund",     "amount":  +12.00}],
}

PROFILES = deepcopy(_BASE_PROFILES)
ACCOUNTS = deepcopy(_BASE_ACCOUNTS)
TRANSACTIONS = deepcopy(_BASE_TRANSACTIONS)


def reset_state() -> None:
    global PROFILES, ACCOUNTS, TRANSACTIONS
    PROFILES = deepcopy(_BASE_PROFILES)
    ACCOUNTS = deepcopy(_BASE_ACCOUNTS)
    TRANSACTIONS = deepcopy(_BASE_TRANSACTIONS)


# ----- Stage 1 ------------------------------------------------------------- #
def get_profile_vulnerable(profile_id: int):
    return PROFILES.get(profile_id)


def stage1_solved(profile_id: int) -> bool:
    """Challenge requires profile #3 specifically (not just any non-owner)."""
    return profile_id == CHALLENGE_TARGET_ID


def stage1_classify_failure(profile_id: int) -> str | None:
    if profile_id == DEMO_OWNER_ID:
        return "That's your own profile. The challenge wants profile #3."
    if profile_id == DEMO_TARGET_ID:
        return "Profile #2 (Bob) is the worked example — viewing it confirms the bug works. The challenge wants profile #3 (Charlie)."
    if profile_id is None or PROFILES.get(profile_id) is None:
        return f"Profile #{profile_id} doesn't exist. Try id 3."
    return None


# ----- Stage 2 ------------------------------------------------------------- #
def encode_acct(acct_id: int) -> str:
    return base64.b64encode(str(acct_id).encode()).decode()


def decode_acct(encoded: str):
    try:
        return int(base64.b64decode(encoded.encode()).decode())
    except Exception:
        return None


def get_transactions(acct_id: int):
    return TRANSACTIONS.get(acct_id, [])


VICTIM_TX_IDS = {tx["id"] for tx in _BASE_TRANSACTIONS[102]}
OWN_TX_IDS    = {tx["id"] for tx in _BASE_TRANSACTIONS[101]}


def stage2_check_tx(submitted: str) -> bool:
    return (submitted or "").strip() in VICTIM_TX_IDS


def stage2_classify_failure(submitted: str) -> str | None:
    s = (submitted or "").strip()
    if not s:
        return "Submit a transaction id from the victim's account."
    if s in OWN_TX_IDS:
        return "That's a transaction from your own account. Decode the encoded URL param, increment the integer, and re-encode to reach the victim's account."
    if not s.startswith("T-"):
        return "Transaction ids look like <code>T-1042</code>. Read them off the listing for the victim's account."
    return "That id doesn't belong to the victim. Open <code>/lesson/access-control/tx?acct=&lt;encoded victim id&gt;</code> first."


# ----- Stage 3 ------------------------------------------------------------- #
def transfer(from_acct: int, to_acct: int, amount: float) -> dict:
    src = ACCOUNTS.get(from_acct)
    dst = ACCOUNTS.get(to_acct)
    if not src or not dst:
        return {"ok": False, "reason": "unknown account"}
    if amount <= 0:
        return {"ok": False, "reason": "amount must be positive"}
    if src["balance"] < amount:
        return {"ok": False, "reason": "insufficient funds"}
    src["balance"] = round(src["balance"] - amount, 2)
    dst["balance"] = round(dst["balance"] + amount, 2)
    return {"ok": True, "src": src, "dst": dst}


def stage3_solved() -> bool:
    return ACCOUNTS.get(102, {}).get("balance", 1) <= 0.001


def stage3_classify_failure(from_acct: int | None, to_acct: int | None, amount: float, transfer_result: dict | None) -> str | None:
    if from_acct == 101:
        return ("You transferred from your own account. The challenge needs you to drain the <em>victim's</em> account. "
                "Edit the hidden <code>from_account</code> field to the victim's encoded id (<code>MTAy</code>).")
    if from_acct is None:
        return "Couldn't decode <code>from_account</code>. It must be base64 of an integer like 101 or 102."
    if transfer_result and not transfer_result.get("ok"):
        return f"Transfer failed: {transfer_result.get('reason')}. Try a smaller amount or check the encoded ids."
    if from_acct == 102 and ACCOUNTS.get(102, {}).get("balance", 0) > 0.001:
        return "Almost — funds left in the victim's account. Submit one more transfer for the remaining balance."
    return None


# ----- Stage 4 ------------------------------------------------------------- #
def update_profile(profile_id: int, fields: dict) -> dict:
    p = PROFILES.get(profile_id)
    if not p:
        return {"ok": False}
    p.update(fields)
    return {"ok": True, "profile": p}


def stage4_check_flag(submitted: str) -> bool:
    return (submitted or "").strip() == ADMIN_FLAG


def stage4_classify_failure(submitted: str, my_role: str) -> str | None:
    s = (submitted or "").strip()
    if not s:
        return "Submit the admin flag once you've promoted yourself."
    if my_role != "admin":
        return ("Your profile still has <code>role=user</code>. Add a <code>role</code> field to the profile-update form "
                "with value <code>admin</code> and save first — the admin panel will then reveal the flag.")
    if not s.startswith("FLAG{"):
        return "Flag format is <code>FLAG{...}</code>. Copy it from the admin panel."
    return "Wrong flag. Re-check the value shown in the admin panel."
