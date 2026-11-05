"""Message templates: plain .txt files with {placeholders} filled from variables at run time."""
import os
import re
import string

from core import config

NAME_PATTERN = re.compile(r"^[A-Za-z0-9_\- ]{1,60}$")

DEFAULT_TEMPLATES = {
    "SMS_1": (
        "Hello {CX_name}, Please reply with 1, 2, or 3 regarding your recent service request "
        "for case {case_number}.\n"
        "1. Issue Resolved  2. Need Assistance  3. Stop Text Messages.\n"
        "If there is no reply, we will contact you by phone within 24 hours between 8:00 AM - 6:00 PM local time.\n"
        "- {agent_name}"
    ),
}


class MissingVariable(Exception):
    pass


def _path(name):
    if not NAME_PATTERN.match(name or ""):
        raise ValueError("Template name may only use letters, numbers, spaces, '_' and '-'")
    return os.path.join(config.TEMPLATE_DIR, f"{name}.txt")


def seed_defaults():
    """Write the starter templates the first time the app runs."""
    if not any(f.endswith(".txt") for f in os.listdir(config.TEMPLATE_DIR)):
        for name, text in DEFAULT_TEMPLATES.items():
            write_template(name, text)


def list_templates():
    names = [f[:-4] for f in os.listdir(config.TEMPLATE_DIR) if f.endswith(".txt")]
    return sorted(names, key=str.lower)


def read_template(name):
    with open(_path(name), encoding="utf-8") as f:
        return f.read()


def write_template(name, text):
    path = _path(name)
    os.makedirs(config.TEMPLATE_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def delete_template(name):
    path = _path(name)
    if os.path.exists(path):
        os.remove(path)


def render(text, variables):
    """Fill {placeholders}. Raises MissingVariable if a placeholder has no value."""
    try:
        return string.Formatter().vformat(text, (), _Strict(variables))
    except KeyError as e:
        raise MissingVariable(f"variable {e} has no value") from None


class _Strict(dict):
    def __missing__(self, key):
        raise KeyError(key)
