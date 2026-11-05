"""Genesys credentials, kept in Windows Credential Manager via keyring.

The password is never returned to the UI or written to disk or git.
"""
import keyring

SERVICE = "NitrosAutomation"
_KEYS = {"user": "genesys_user", "password": "genesys_password", "place": "genesys_place"}


class MissingCredentials(Exception):
    pass


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


def load_for_run():
    if not is_configured():
        raise MissingCredentials("Genesys user, password and place ID must be saved in the Setup tab first")
    return {field: _get(field) for field in _KEYS}
