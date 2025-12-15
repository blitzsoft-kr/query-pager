"""Tests for keyset pagination logic."""

import pytest

from query_pager.core.keyset import KeysetPaginator
from query_pager.core.exceptions import CursorError, PaginationError


def test_init_with_order_fields():
    """Test initializing with order fields."""
    paginator = KeysetPaginator([("id", "asc")])
    assert paginator.order_fields == [("id", "asc")]
    assert paginator.field_names == ["id"]


def test_init_empty_order_fields_raises():
    """Test initializing with empty order fields raises error."""
    with pytest.raises(PaginationError, match="At least one ordering field is required"):
        KeysetPaginator([])


def test_decode_cursor_values_none():
    """Test decoding None cursor returns (None, 'next')."""
    paginator = KeysetPaginator([("id", "asc")])
    values, direction = paginator.decode_cursor_values(None)
    assert values is None
    assert direction == "next"


def test_decode_cursor_values_valid():
    """Test decoding valid cursor."""
    from query_pager.core.cursor import encode_cursor

    paginator = KeysetPaginator([("id", "asc")])
    cursor = encode_cursor([("id", "asc")], {"id": 10})
    values, direction = paginator.decode_cursor_values(cursor)
    assert values == {"id": 10}
    assert direction == "next"


def test_decode_cursor_values_with_prev_direction():
    """Test decoding cursor with prev direction."""
    from query_pager.core.cursor import encode_cursor

    paginator = KeysetPaginator([("id", "asc")])
    cursor = encode_cursor([("id", "asc")], {"id": 10}, direction="prev")
    values, direction = paginator.decode_cursor_values(cursor)
    assert values == {"id": 10}
    assert direction == "prev"


def test_decode_cursor_values_field_mismatch():
    """Test decoding cursor with mismatched fields raises error."""
    from query_pager.core.cursor import encode_cursor

    paginator = KeysetPaginator([("id", "asc"), ("name", "asc")])
    cursor = encode_cursor([("id", "asc"), ("name", "asc")], {"id": 10})  # Missing 'name' value

    with pytest.raises(CursorError, match="missing fields"):
        paginator.decode_cursor_values(cursor)


def test_decode_cursor_values_ordering_mismatch():
    """Test decoding cursor with mismatched ordering raises error."""
    from query_pager.core.cursor import encode_cursor

    # Cursor was created with id ASC
    cursor = encode_cursor([("id", "asc")], {"id": 10})

    # But paginator expects id DESC
    paginator = KeysetPaginator([("id", "desc")])

    with pytest.raises(CursorError, match="ordering mismatch"):
        paginator.decode_cursor_values(cursor)


def test_decode_cursor_values_field_order_mismatch():
    """Test decoding cursor with different field order raises error."""
    from query_pager.core.cursor import encode_cursor

    # Cursor was created with (name, id) ordering
    cursor = encode_cursor([("name", "asc"), ("id", "asc")], {"name": "test", "id": 10})

    # But paginator expects (id, name) ordering
    paginator = KeysetPaginator([("id", "asc"), ("name", "asc")])

    with pytest.raises(CursorError, match="ordering mismatch"):
        paginator.decode_cursor_values(cursor)


def test_build_cursor_filter_single_field_asc():
    """Test building filter conditions for single field ascending."""
    paginator = KeysetPaginator([("id", "asc")])
    conditions = paginator.build_cursor_filter_conditions({"id": 10})
    
    assert conditions == [[("id", ">", 10)]]


def test_build_cursor_filter_single_field_desc():
    """Test building filter conditions for single field descending."""
    paginator = KeysetPaginator([("id", "desc")])
    conditions = paginator.build_cursor_filter_conditions({"id": 10})
    
    assert conditions == [[("id", "<", 10)]]


def test_build_cursor_filter_multi_field():
    """Test building filter conditions for multiple fields."""
    paginator = KeysetPaginator([("name", "asc"), ("id", "asc")])
    conditions = paginator.build_cursor_filter_conditions({"name": "test", "id": 5})
    
    # Should create: (name > 'test') OR (name = 'test' AND id > 5)
    assert len(conditions) == 2
    assert conditions[0] == [("name", ">", "test")]
    assert conditions[1] == [("name", "=", "test"), ("id", ">", 5)]


def test_build_cursor_filter_three_fields():
    """Test building filter conditions for three fields."""
    paginator = KeysetPaginator([
        ("category", "asc"),
        ("price", "desc"),
        ("id", "asc")
    ])
    conditions = paginator.build_cursor_filter_conditions({
        "category": "electronics",
        "price": 100,
        "id": 5
    })
    
    # Should create 3 OR conditions
    assert len(conditions) == 3
    assert conditions[0] == [("category", ">", "electronics")]
    assert conditions[1] == [("category", "=", "electronics"), ("price", "<", 100)]
    assert conditions[2] == [
        ("category", "=", "electronics"),
        ("price", "=", 100),
        ("id", ">", 5)
    ]


def test_encode_cursor_values():
    """Test encoding cursor values from item."""

    class MockItem:
        id = 10
        name = "test"

    paginator = KeysetPaginator([("id", "asc"), ("name", "asc")])
    cursor = paginator.encode_cursor_values(MockItem())

    assert isinstance(cursor, str)

    # Decode to verify
    from query_pager.core.cursor import decode_cursor

    decoded_order, decoded_values, direction = decode_cursor(cursor)
    assert decoded_order == [("id", "asc"), ("name", "asc")]
    assert decoded_values == {"id": 10, "name": "test"}
    assert direction == "next"


def test_encode_cursor_values_with_direction():
    """Test encoding cursor values with prev direction."""

    class MockItem:
        id = 10
        name = "test"

    paginator = KeysetPaginator([("id", "asc"), ("name", "asc")])
    cursor = paginator.encode_cursor_values(MockItem(), direction="prev")

    from query_pager.core.cursor import decode_cursor

    decoded_order, decoded_values, direction = decode_cursor(cursor)
    assert decoded_order == [("id", "asc"), ("name", "asc")]
    assert decoded_values == {"id": 10, "name": "test"}
    assert direction == "prev"


def test_create_paginated_response_no_items():
    """Test creating response with no items."""
    paginator = KeysetPaginator([("id", "asc")])
    result = paginator.create_paginated_response(
        items=[],
        total_size=0,
        requested_size=10,
        has_previous=False,
        has_next=False,
    )

    assert result.total_size == 0
    assert len(result.items) == 0
    assert result.prev is None
    assert result.next is None


def test_create_paginated_response_with_next():
    """Test creating response with next cursor."""
    class MockItem:
        def __init__(self, id):
            self.id = id

    paginator = KeysetPaginator([("id", "asc")])
    items = [MockItem(1), MockItem(2)]

    result = paginator.create_paginated_response(
        items=items,
        total_size=10,
        requested_size=2,
        has_previous=False,
        has_next=True,
    )

    assert len(result.items) == 2
    assert result.next is not None  # Has more items
    assert result.prev is None  # First page


def test_create_paginated_response_with_prev():
    """Test creating response with prev cursor."""
    class MockItem:
        def __init__(self, id):
            self.id = id

    paginator = KeysetPaginator([("id", "asc")])
    items = [MockItem(3), MockItem(4)]

    result = paginator.create_paginated_response(
        items=items,
        total_size=10,
        requested_size=2,
        has_previous=True,
        has_next=False,
    )

    assert len(result.items) == 2
    assert result.prev is not None  # Has previous page
    assert result.next is None  # Last page


def test_create_paginated_response_with_both():
    """Test creating response with both prev and next cursors."""
    class MockItem:
        def __init__(self, id):
            self.id = id

    paginator = KeysetPaginator([("id", "asc")])
    items = [MockItem(3), MockItem(4)]

    result = paginator.create_paginated_response(
        items=items,
        total_size=10,
        requested_size=2,
        has_previous=True,
        has_next=True,
    )

    assert len(result.items) == 2
    assert result.prev is not None  # Has previous page
    assert result.next is not None  # Has next page
