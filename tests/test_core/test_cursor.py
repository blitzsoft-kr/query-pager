"""Tests for cursor encoding/decoding."""

import pytest

from query_pager.core.cursor import decode_cursor, encode_cursor, validate_cursor_fields
from query_pager.core.exceptions import CursorError


def test_encode_cursor_simple():
    """Test encoding simple cursor."""
    cursor = encode_cursor({"id": 10})
    assert isinstance(cursor, str)
    assert len(cursor) > 0


def test_encode_cursor_multiple_fields():
    """Test encoding cursor with multiple fields."""
    cursor = encode_cursor({"id": 10, "name": "test"})
    assert isinstance(cursor, str)


def test_encode_cursor_empty_raises():
    """Test encoding empty cursor raises error."""
    with pytest.raises(CursorError, match="cannot be empty"):
        encode_cursor({})


def test_decode_cursor_simple():
    """Test decoding simple cursor."""
    cursor = encode_cursor({"id": 10})
    decoded = decode_cursor(cursor)
    assert decoded == {"id": 10}


def test_decode_cursor_multiple_fields():
    """Test decoding cursor with multiple fields."""
    original = {"id": 10, "name": "test", "created_at": "2024-01-01"}
    cursor = encode_cursor(original)
    decoded = decode_cursor(cursor)
    assert decoded == original


def test_decode_cursor_empty_raises():
    """Test decoding empty cursor raises error."""
    with pytest.raises(CursorError, match="cannot be empty"):
        decode_cursor("")


def test_decode_cursor_invalid_base64():
    """Test decoding invalid base64 raises error."""
    with pytest.raises(CursorError, match="Invalid cursor format"):
        decode_cursor("not-valid-base64!!!")


def test_decode_cursor_invalid_json():
    """Test decoding invalid JSON raises error."""
    import base64
    invalid_json = base64.urlsafe_b64encode(b"not json").decode("utf-8")
    with pytest.raises(CursorError, match="Invalid cursor format"):
        decode_cursor(invalid_json)


def test_decode_cursor_not_dict():
    """Test decoding non-dict JSON raises error."""
    import base64
    import json
    not_dict = base64.urlsafe_b64encode(json.dumps([1, 2, 3]).encode()).decode()
    with pytest.raises(CursorError, match="must decode to a dictionary"):
        decode_cursor(not_dict)


def test_validate_cursor_fields_success():
    """Test validating cursor fields succeeds."""
    cursor_values = {"id": 10, "name": "test"}
    validate_cursor_fields(cursor_values, ["id", "name"])
    # Should not raise


def test_validate_cursor_fields_missing():
    """Test validating cursor with missing fields raises error."""
    cursor_values = {"id": 10}
    with pytest.raises(CursorError, match="missing fields: name"):
        validate_cursor_fields(cursor_values, ["id", "name"])


def test_validate_cursor_fields_multiple_missing():
    """Test validating cursor with multiple missing fields."""
    cursor_values = {"id": 10}
    with pytest.raises(CursorError, match="missing fields"):
        validate_cursor_fields(cursor_values, ["id", "name", "created_at"])


def test_roundtrip_encoding():
    """Test encoding and decoding roundtrip."""
    original = {"id": 42, "name": "product", "price": 99.99}
    cursor = encode_cursor(original)
    decoded = decode_cursor(cursor)
    assert decoded == original
