from datetime import date, datetime
from typing import Optional


def parse_date_string(date_str: Optional[str]) -> Optional[date]:
    """
    Converts a YYYY-MM-DD string from LLM output to Python date object.
    Returns None if date_str is None or empty.
    Returns date(1900, 1, 1) if parsing fails (safe default for DB).
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m").date()
        except ValueError:
            return date(1900, 1, 1)


def safe_date(date_str: Optional[str], default: date = date(1900, 1, 1)) -> date:
    """
    Same as parse_date_string but always returns a date — never None.
    Uses provided default if parsing fails or input is null.
    """
    result = parse_date_string(date_str)
    return result if result is not None else default
