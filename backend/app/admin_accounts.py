"""Admin accounts: usernames and hashed passwords, saved in a JSON file.

Only admins log in; everyone else uses the app without an account. The
accounts live in their own file (admins.json, kept out of git) instead of in
memory like the rest of the data for now, so logins survive a restart. When
the database arrives they can move into a table.

Passwords are never stored. Each one is run through scrypt, a hash designed
to be slow and memory-hungry, with a random salt. Checking a login means
hashing the typed password the same way and comparing the results. If the
file ever leaked, an attacker would have to guess passwords one slow hash at
a time, and the salt stops them from reusing work across accounts.

This module only uses the standard library, so the command-line tool
(manage_admins.py) can use it without starting the web app.
"""

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

ADMINS_FILE = Path(os.environ.get(
    "ADMINS_FILE", Path(__file__).resolve().parent.parent / "admins.json"))

MIN_PASSWORD_LENGTH = 10

# scrypt cost settings: about 16 MB of memory and a few dozen milliseconds per
# hash. Barely noticeable for one login, very expensive for millions of guesses.
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def hash_password(password: str) -> str:
    """Returns 'scrypt$n$r$p$salt$hash'. The settings are saved with the hash so
    they can be raised later without breaking passwords hashed with the old ones."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if (algorithm != "scrypt"):
        return False
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex),
                            n=int(n), r=int(r), p=int(p))
    # compare_digest takes the same time whether the first or last character
    # differs, so response times don't hint at how close a guess was
    return hmac.compare_digest(digest.hex(), digest_hex)


# Used when a login names a username that doesn't exist, so that case takes as
# long as a wrong password for a real admin. Otherwise the response time would
# reveal which usernames are real.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def normalize_username(username: str) -> str:
    """Usernames ignore case and surrounding spaces: ' Admin ' == 'admin'."""
    return username.strip().lower()


def load_accounts() -> dict[str, str]:
    """username -> password hash"""
    if (not ADMINS_FILE.exists()):
        return {}
    return json.loads(ADMINS_FILE.read_text())


def save_accounts(accounts: dict[str, str]) -> None:
    ADMINS_FILE.write_text(json.dumps(accounts, indent=2, sort_keys=True))


def set_password(username: str, password: str) -> str:
    """Creates the account, or changes its password if it exists. Returns the saved username."""
    name = normalize_username(username)
    if (name == ""):
        raise ValueError("The username can't be empty.")
    if (len(password) < MIN_PASSWORD_LENGTH):
        raise ValueError(f"The password must be at least {MIN_PASSWORD_LENGTH} characters.")
    accounts = load_accounts()
    accounts[name] = hash_password(password)
    save_accounts(accounts)
    return name


def remove_account(username: str) -> bool:
    """Returns False if there was no such account."""
    accounts = load_accounts()
    if (accounts.pop(normalize_username(username), None) is None):
        return False
    save_accounts(accounts)
    return True


def check_login(username: str, password: str) -> str | None:
    """The admin's username if the password is right, otherwise None."""
    name = normalize_username(username)
    stored = load_accounts().get(name)
    if (stored is None):
        verify_password(password, _DUMMY_HASH)   # same amount of work either way
        return None
    return name if verify_password(password, stored) else None
