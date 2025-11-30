"""Cursor encoding and decoding utilities."""

import base64
import json
from typing import Any, Dict, Optional

from query_pager.core.exceptions import CursorError


def encode_cursor(values: Dict[str, Any]) -> str:
    """Encode cursor values to base64 string."""
    if not values:
        raise CursorError("Cursor values cannot be empty")

    json_str = json.dumps(values, sort_keys=True, default=str)
    encoded = base64.urlsafe_b64encode(json_str.encode("utf-8"))
    return encoded.decode("utf-8")


def decode_cursor(cursor: str) -> Dict[str, Any]:
    """Decode base64 cursor string to values."""
    if not cursor or not cursor.strip():
        raise CursorError("Cursor cannot be empty")

    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        values = json.loads(decoded.decode("utf-8"))

        if not isinstance(values, dict):
            raise CursorError("Cursor must decode to a dictionary")

        return values
    except (json.JSONDecodeError, Exception) as e:
        raise CursorError(f"Invalid cursor format: {str(e)}") from e


def validate_cursor_fields(cursor_values: Dict[str, Any], expected_fields: list) -> None:
    """Validate cursor contains all expected fields."""
    missing_fields = set(expected_fields) - set(cursor_values.keys())
    if missing_fields:
        raise CursorError(
            f"Cursor missing fields: {', '.join(sorted(missing_fields))}"
        )
