"""Tests for cursor encoding/decoding."""

import pytest

from query_pager.core.cursor import (
    decode_cursor,
    encode_cursor,
    validate_cursor_fields,
    validate_cursor_ordering,
)
from query_pager.core.exceptions import CursorError


def test_encode_cursor_simple():
    """Test encoding simple cursor with ordering."""
    order_fields = [("id", "asc")]
    values = {"id": 10}
    cursor = encode_cursor(order_fields, values)
    assert isinstance(cursor, str)
    assert len(cursor) > 0


def test_encode_cursor_multiple_fields():
    """Test encoding cursor with multiple fields."""
    order_fields = [("name", "asc"), ("id", "desc")]
    values = {"id": 10, "name": "test"}
    cursor = encode_cursor(order_fields, values)
    assert isinstance(cursor, str)


def test_encode_cursor_empty_values_raises():
    """Test encoding with empty values raises error."""
    order_fields = [("id", "asc")]
    with pytest.raises(CursorError, match="values cannot be empty"):
        encode_cursor(order_fields, {})


def test_encode_cursor_empty_ordering_raises():
    """Test encoding with empty ordering raises error."""
    values = {"id": 10}
    with pytest.raises(CursorError, match="order_fields cannot be empty"):
        encode_cursor([], values)


def test_decode_cursor_simple():
    """Test decoding simple cursor."""
    order_fields = [("id", "asc")]
    values = {"id": 10}
    cursor = encode_cursor(order_fields, values)
    decoded_order, decoded_values = decode_cursor(cursor)
    assert decoded_order == order_fields
    assert decoded_values == values


def test_decode_cursor_multiple_fields():
    """Test decoding cursor with multiple fields."""
    order_fields = [("name", "asc"), ("id", "desc")]
    values = {"id": 10, "name": "test", "created_at": "2024-01-01"}
    cursor = encode_cursor(order_fields, values)
    decoded_order, decoded_values = decode_cursor(cursor)
    assert decoded_order == order_fields
    assert decoded_values == values


def test_decode_cursor_desc_ordering():
    """Test decoding cursor with descending order."""
    order_fields = [("price", "desc"), ("id", "asc")]
    values = {"price": 100, "id": 5}
    cursor = encode_cursor(order_fields, values)
    decoded_order, decoded_values = decode_cursor(cursor)
    assert decoded_order == order_fields
    assert decoded_values == values


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


def test_decode_cursor_missing_keys():
    """Test decoding cursor missing 'o' or 'v' keys."""
    import base64
    import json

    # Missing 'v' key
    invalid_data = base64.urlsafe_b64encode(json.dumps({"o": ["+id"]}).encode()).decode()
    with pytest.raises(CursorError, match="missing required keys"):
        decode_cursor(invalid_data)

    # Missing 'o' key
    invalid_data = base64.urlsafe_b64encode(json.dumps({"v": {"id": 1}}).encode()).decode()
    with pytest.raises(CursorError, match="missing required keys"):
        decode_cursor(invalid_data)


def test_decode_cursor_invalid_ordering_format():
    """Test decoding cursor with invalid ordering format."""
    import base64
    import json

    # Invalid direction character
    invalid_data = base64.urlsafe_b64encode(
        json.dumps({"o": ["*id"], "v": {"id": 1}}).encode()
    ).decode()
    with pytest.raises(CursorError, match="Invalid direction in ordering"):
        decode_cursor(invalid_data)


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


def test_validate_cursor_ordering_success():
    """Test validating matching ordering succeeds."""
    cursor_order = [("id", "asc"), ("name", "desc")]
    expected_order = [("id", "asc"), ("name", "desc")]
    validate_cursor_ordering(cursor_order, expected_order)
    # Should not raise


def test_validate_cursor_ordering_field_mismatch():
    """Test validating ordering with different fields raises error."""
    cursor_order = [("id", "asc")]
    expected_order = [("name", "asc")]
    with pytest.raises(CursorError, match="ordering mismatch"):
        validate_cursor_ordering(cursor_order, expected_order)


def test_validate_cursor_ordering_direction_mismatch():
    """Test validating ordering with different directions raises error."""
    cursor_order = [("id", "asc")]
    expected_order = [("id", "desc")]
    with pytest.raises(CursorError, match="ordering mismatch"):
        validate_cursor_ordering(cursor_order, expected_order)


def test_validate_cursor_ordering_order_mismatch():
    """Test validating ordering with different field order raises error."""
    cursor_order = [("name", "asc"), ("id", "asc")]
    expected_order = [("id", "asc"), ("name", "asc")]
    with pytest.raises(CursorError, match="ordering mismatch"):
        validate_cursor_ordering(cursor_order, expected_order)


def test_roundtrip_encoding():
    """Test encoding and decoding roundtrip."""
    order_fields = [("name", "desc"), ("id", "asc")]
    values = {"id": 42, "name": "product", "price": 99.99}
    cursor = encode_cursor(order_fields, values)
    decoded_order, decoded_values = decode_cursor(cursor)
    assert decoded_order == order_fields
    assert decoded_values == values


def test_cursor_format_compact():
    """Test that cursor format is compact."""
    order_fields = [("name", "asc"), ("id", "desc")]
    values = {"name": "Banana", "id": 2}
    cursor = encode_cursor(order_fields, values)

    # Decode to verify format
    import base64
    import json

    decoded_json = json.loads(base64.urlsafe_b64decode(cursor))
    assert "o" in decoded_json
    assert "v" in decoded_json
    assert decoded_json["o"] == ["+name", "-id"]
    assert decoded_json["v"] == {"name": "Banana", "id": 2}
