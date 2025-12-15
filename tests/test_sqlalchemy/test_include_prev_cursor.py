"""Tests for include_prev_cursor feature in SQLAlchemy pagination."""

import pytest
from sqlalchemy import select

from query_pager.core.schemas import PageOptions
from query_pager.sqlalchemy.pagination import paginate
from .conftest import Product


def test_include_prev_cursor_with_zero_results(sync_session):
    """Test include_prev_cursor with zero results - both cursors should be None."""
    query = select(Product).where(Product.category == "nonexistent").order_by(Product.id.desc())
    options = PageOptions(size=20, include_prev_cursor=True)

    result = paginate(sync_session, query, options)

    assert result.total_size == 0
    assert len(result.items) == 0
    assert result.prev is None
    assert result.next is None


def test_include_prev_cursor_with_few_results_no_more(sync_session):
    """Test include_prev_cursor with 2 results (< size, has_more=False).

    Should return prev cursor for incremental updates, but no next cursor.
    """
    # Filter to get only 2 items
    query = select(Product).where(Product.category == "books").order_by(Product.id.desc())
    options = PageOptions(size=20, include_prev_cursor=True)

    result = paginate(sync_session, query, options)

    assert result.total_size == 2
    assert len(result.items) == 2
    assert result.items[0].id == 5  # Magazine (desc order)
    assert result.items[1].id == 3  # Book
    assert result.prev is not None  # Should have prev for incremental updates
    assert result.next is None  # No more items


def test_include_prev_cursor_with_exact_page_size(sync_session):
    """Test include_prev_cursor with results exactly matching page size (has_more=False).

    Should return prev cursor, but no next cursor.
    """
    query = select(Product).order_by(Product.id.desc())
    options = PageOptions(size=5, include_prev_cursor=True)  # Exactly 5 items total

    result = paginate(sync_session, query, options)

    assert result.total_size == 5
    assert len(result.items) == 5
    assert result.items[0].id == 5  # Highest ID (desc order)
    assert result.items[-1].id == 1  # Lowest ID
    assert result.prev is not None  # Should have prev for incremental updates
    assert result.next is None  # No more items


def test_include_prev_cursor_with_more_results(sync_session):
    """Test include_prev_cursor with more results than page size (has_more=True).

    Should return both prev and next cursors.
    """
    query = select(Product).order_by(Product.id.desc())
    options = PageOptions(size=3, include_prev_cursor=True)  # 5 total, fetch 3

    result = paginate(sync_session, query, options)

    assert result.total_size == 5
    assert len(result.items) == 3
    assert result.items[0].id == 5  # Highest ID
    assert result.items[-1].id == 3
    assert result.prev is not None  # Should have prev for incremental updates
    assert result.next is not None  # Has more items


def test_include_prev_cursor_false_first_page(sync_session):
    """Test that include_prev_cursor=False maintains original behavior.

    First page should have no prev cursor.
    """
    query = select(Product).order_by(Product.id.desc())
    options = PageOptions(size=3, include_prev_cursor=False)

    result = paginate(sync_session, query, options)

    assert result.total_size == 5
    assert len(result.items) == 3
    assert result.prev is None  # Original behavior: no prev on first page
    assert result.next is not None


def test_include_prev_cursor_default_is_false(sync_session):
    """Test that include_prev_cursor defaults to False."""
    query = select(Product).order_by(Product.id.desc())
    options = PageOptions(size=3)  # Don't specify include_prev_cursor

    result = paginate(sync_session, query, options)

    assert result.prev is None  # Default behavior
    assert result.next is not None


def test_prev_cursor_can_fetch_new_items(sync_session):
    """Test that prev cursor from first page can be used to fetch newer items.

    Simulates chat app scenario: fetch initial messages, then check for new ones.
    """
    # Initial fetch: get latest messages
    query = select(Product).order_by(Product.id.desc())
    first_page = paginate(sync_session, query, PageOptions(size=3, include_prev_cursor=True))

    assert len(first_page.items) == 3
    assert first_page.items[0].id == 5  # Latest item
    assert first_page.prev is not None

    # Simulate using prev cursor to check for new items
    # In real scenario, this would fetch items with id > 5
    # Here we just verify the cursor is valid and points to correct item
    from query_pager.core.cursor import decode_cursor

    order_fields, cursor_values, direction = decode_cursor(first_page.prev)

    assert direction == "prev"
    assert cursor_values["id"] == 5  # Points to the first (newest) item
    assert order_fields == [("id", "desc")]


def test_prev_cursor_with_multi_field_ordering(sync_session):
    """Test include_prev_cursor with multi-field ordering."""
    query = select(Product).order_by(Product.price.desc(), Product.id.desc())
    options = PageOptions(size=2, include_prev_cursor=True)

    result = paginate(sync_session, query, options)

    assert len(result.items) == 2
    assert result.prev is not None
    assert result.next is not None

    # Verify cursor contains both fields
    from query_pager.core.cursor import decode_cursor

    order_fields, cursor_values, direction = decode_cursor(result.prev)

    assert direction == "prev"
    assert "price" in cursor_values
    assert "id" in cursor_values
    assert order_fields == [("price", "desc"), ("id", "desc")]
