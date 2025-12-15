"""Cursor encoding and decoding utilities."""

import base64
import json
from typing import Any, Dict, List, Tuple

from query_pager.core.exceptions import CursorError


def encode_cursor(
    order_fields: List[Tuple[str, str]],
    values: Dict[str, Any],
    direction: str = "next",
) -> str:
    """
    Encode cursor with ordering metadata, values, and direction to base64 string.

    Args:
        order_fields: List of (field_name, direction) tuples, e.g., [("name", "asc"), ("id", "desc")]
        values: Dictionary of field values, e.g., {"name": "Banana", "id": 2}
        direction: Cursor direction, either "next" or "prev"

    Returns:
        Base64-encoded cursor string

    Raises:
        CursorError: If order_fields or values are empty, or direction is invalid
    """
    if not order_fields:
        raise CursorError("Cursor order_fields cannot be empty")
    if not values:
        raise CursorError("Cursor values cannot be empty")
    if direction not in ("next", "prev"):
        raise CursorError(f"Invalid cursor direction: {direction}")

    # Convert order_fields to compact format: ["+name", "-id"]
    ordering = []
    for field, dir_ in order_fields:
        prefix = "+" if dir_ == "asc" else "-"
        ordering.append(f"{prefix}{field}")

    cursor_data = {"o": ordering, "v": values, "d": direction}
    json_str = json.dumps(cursor_data, separators=(",", ":"), default=str)
    encoded = base64.urlsafe_b64encode(json_str.encode("utf-8"))
    return encoded.decode("utf-8")


def decode_cursor(cursor: str) -> Tuple[List[Tuple[str, str]], Dict[str, Any], str]:
    """
    Decode base64 cursor string to ordering, values, and direction.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Tuple of (order_fields, values, direction) where:
        - order_fields: List of (field_name, direction) tuples
        - values: Dictionary of field values
        - direction: Cursor direction ("next" or "prev")

    Raises:
        CursorError: If cursor is invalid or malformed
    """
    if not cursor or not cursor.strip():
        raise CursorError("Cursor cannot be empty")

    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        cursor_data = json.loads(decoded.decode("utf-8"))

        if not isinstance(cursor_data, dict):
            raise CursorError("Cursor must decode to a dictionary")

        # Validate cursor structure
        if "o" not in cursor_data or "v" not in cursor_data:
            raise CursorError("Cursor missing required keys: 'o' (ordering) and 'v' (values)")

        ordering = cursor_data["o"]
        values = cursor_data["v"]
        # Default to "next" for backward compatibility with old cursors
        direction = cursor_data.get("d", "next")

        if not isinstance(ordering, list) or not isinstance(values, dict):
            raise CursorError("Invalid cursor format: 'o' must be list, 'v' must be dict")

        if direction not in ("next", "prev"):
            raise CursorError(f"Invalid cursor direction: {direction}")

        # Parse ordering: ["+name", "-id"] -> [("name", "asc"), ("id", "desc")]
        order_fields = []
        for field_str in ordering:
            if not isinstance(field_str, str) or len(field_str) < 2:
                raise CursorError(f"Invalid ordering format: {field_str}")

            direction_char = field_str[0]
            field_name = field_str[1:]

            if direction_char == "+":
                dir_ = "asc"
            elif direction_char == "-":
                dir_ = "desc"
            else:
                raise CursorError(f"Invalid direction in ordering: {field_str}")

            order_fields.append((field_name, dir_))

        return order_fields, values, direction

    except CursorError:
        raise
    except (json.JSONDecodeError, Exception) as e:
        raise CursorError(f"Invalid cursor format: {str(e)}") from e


def validate_cursor_ordering(
    cursor_order_fields: List[Tuple[str, str]], expected_order_fields: List[Tuple[str, str]]
) -> None:
    """
    Validate cursor ordering matches expected ordering.

    Args:
        cursor_order_fields: Ordering from cursor
        expected_order_fields: Expected ordering from current query

    Raises:
        CursorError: If ordering doesn't match
    """
    if cursor_order_fields != expected_order_fields:
        cursor_fmt = ", ".join([f"{f} {d}" for f, d in cursor_order_fields])
        expected_fmt = ", ".join([f"{f} {d}" for f, d in expected_order_fields])
        raise CursorError(
            f"Cursor ordering mismatch. Expected: [{expected_fmt}], Got: [{cursor_fmt}]"
        )


def validate_cursor_fields(cursor_values: Dict[str, Any], expected_fields: List[str]) -> None:
    """
    Validate cursor contains all expected fields.

    Args:
        cursor_values: Values from cursor
        expected_fields: Expected field names

    Raises:
        CursorError: If fields are missing
    """
    missing_fields = set(expected_fields) - set(cursor_values.keys())
    if missing_fields:
        raise CursorError(f"Cursor missing fields: {', '.join(sorted(missing_fields))}")
