import re


def slugify(value: str) -> str:
    value = value.strip().lower()
    # Replace non-alphanumeric with hyphens
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "item"

