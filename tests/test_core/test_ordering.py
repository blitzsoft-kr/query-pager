"""Tests for ordering parser."""

import pytest

from query_pager.core.ordering import parse_ordering, validate_ordering_fields
from query_pager.core.exceptions import OrderingError


def test_parse_single_field_asc():
    """Test parsing single field ascending."""
    result = parse_ordering("likes", {"likes", "id"})
    assert result == [("likes", "asc")]


def test_parse_single_field_desc():
    """Test parsing single field descending."""
    result = parse_ordering("-likes", {"likes", "id"})
    assert result == [("likes", "desc")]


def test_parse_multiple_fields():
    """Test parsing multiple fields."""
    result = parse_ordering("likes,-created_at,id", {"likes", "created_at", "id"})
    assert result == [
        ("likes", "asc"),
        ("created_at", "desc"),
        ("id", "asc"),
    ]


def test_parse_with_spaces():
    """Test parsing with spaces."""
    result = parse_ordering("likes, -created_at, id", {"likes", "created_at", "id"})
    assert result == [
        ("likes", "asc"),
        ("created_at", "desc"),
        ("id", "asc"),
    ]


def test_parse_empty_string():
    """Test parsing empty string raises error."""
    with pytest.raises(OrderingError, match="cannot be empty"):
        parse_ordering("", {"likes"})


def test_parse_only_commas():
    """Test parsing only commas raises error."""
    with pytest.raises(OrderingError, match="at least one field"):
        parse_ordering(",,,", {"likes"})


def test_parse_invalid_field():
    """Test parsing with invalid field raises error."""
    with pytest.raises(OrderingError, match="not allowed"):
        parse_ordering("likes,-secret", {"likes", "id"})


def test_parse_empty_field_name():
    """Test parsing with empty field name raises error."""
    with pytest.raises(OrderingError, match="Invalid ordering field"):
        parse_ordering("-", {"likes"})


def test_validate_ordering_fields_success():
    """Test validation with valid fields."""
    validate_ordering_fields("likes,-id", {"likes", "id"})
    # Should not raise


def test_validate_ordering_fields_failure():
    """Test validation with invalid fields."""
    with pytest.raises(OrderingError, match="not allowed"):
        validate_ordering_fields("likes,-secret", {"likes", "id"})
