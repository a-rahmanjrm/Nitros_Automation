"""Optional dialer credentials (e.g. Genesys WWE), kept in the OS keyring
(Windows Credential Manager / macOS Keychain).

They are only needed when a flow uses {genesys_user}, {genesys_password} or {genesys_place}.
The password is never returned to the UI or written to disk or git.
"""
import keyring

SERVICE = "NitrosAutomation"
_KEYS = {"user": "genesys_user", "password": "genesys_password", "place": "genesys_place"}


def _get(field):
    return keyring.get_password(SERVICE, _KEYS[field]) or ""


def describe():
    """What the UI may show: never the password itself."""
    return {"user": _get("user"), "place": _get("place"), "has_password": bool(_get("password"))}


def save(user, password, place):
    """Blank fields keep their stored value, so the password can be left alone on edit."""
    if user:
        keyring.set_password(SERVICE, _KEYS["user"], user)
    if place:
        keyring.set_password(SERVICE, _KEYS["place"], place)
    if password:
        keyring.set_password(SERVICE, _KEYS["password"], password)


def is_configured():
    return all(_get(field) for field in _KEYS)


def run_variables():
    """Saved credentials as flow variables. Unsaved ones are left out, so a flow that uses
    one fails with a clear 'variable has no value' error instead of typing an empty string."""
    return {key: value for field, key in _KEYS.items() if (value := _get(field))}
