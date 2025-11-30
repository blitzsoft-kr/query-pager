"""Tests for core schemas."""

import pytest
from pydantic import ValidationError

from query_pager.core.schemas import PageOptions, Paginated


def test_paginated_basic():
    """Test basic Paginated schema."""
    result = Paginated(
        total_size=100,
        prev=None,
        next="cursor123",
        items=[1, 2, 3],
    )

    assert result.total_size == 100
    assert result.prev is None
    assert result.next == "cursor123"
    assert result.items == [1, 2, 3]


def test_paginated_with_dict():
    """Test Paginated with dict items."""
    items = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
    ]

    result = Paginated(
        total_size=2,
        prev=None,
        next=None,
        items=items,
    )

    assert len(result.items) == 2
    assert result.items[0]["id"] == 1


def test_page_options_defaults():
    """Test PageOptions default values."""
    options = PageOptions()

    assert options.cursor is None
    assert options.size == 20


def test_page_options_custom():
    """Test PageOptions with custom values."""
    options = PageOptions(cursor="abc123", size=50)

    assert options.cursor == "abc123"
    assert options.size == 50


def test_page_options_validation_min():
    """Test PageOptions size minimum validation."""
    with pytest.raises(ValidationError):
        PageOptions(size=0)


def test_page_options_validation_max():
    """Test PageOptions size maximum validation."""
    with pytest.raises(ValidationError):
        PageOptions(size=101)


def test_page_options_immutable():
    """Test that PageOptions is immutable."""
    options = PageOptions(size=10)

    with pytest.raises(ValidationError):
        options.size = 20
