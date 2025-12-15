"""Tests for edge cases in pagination."""

import pytest
from sqlalchemy import select

from query_pager.core.exceptions import CursorError
from query_pager.core.schemas import PageOptions
from query_pager.sqlalchemy.pagination import paginate

from .conftest import Product


def test_empty_result_set(sync_session):
    """Test pagination with empty result set."""
    query = select(Product).where(Product.price > 999999).order_by(Product.id)
    
    result = paginate(sync_session, query, PageOptions(size=10))
    
    assert result.total_size == 0
    assert len(result.items) == 0
    assert result.next is None
    assert result.prev is None


def test_single_item(sync_session):
    """Test pagination with single item."""
    # Delete all but one
    sync_session.query(Product).filter(Product.id != 1).delete()
    sync_session.commit()
    
    query = select(Product).order_by(Product.id)
    result = paginate(sync_session, query, PageOptions(size=10))
    
    assert result.total_size == 1
    assert len(result.items) == 1
    assert result.next is None
    assert result.prev is None


def test_exact_page_size(sync_session):
    """Test when result count equals page size."""
    query = select(Product).order_by(Product.id)
    
    # Request exactly 5 items (we have 5 in fixture)
    result = paginate(sync_session, query, PageOptions(size=5))
    
    assert len(result.items) == 5
    assert result.next is None  # No more items


def test_page_size_larger_than_total(sync_session):
    """Test when page size is larger than total items."""
    query = select(Product).order_by(Product.id)
    
    result = paginate(sync_session, query, PageOptions(size=100))
    
    assert len(result.items) == 5  # Only 5 items exist
    assert result.next is None


def test_last_page_partial(sync_session):
    """Test last page with partial results."""
    query = select(Product).order_by(Product.id)
    
    # First page: 3 items
    page1 = paginate(sync_session, query, PageOptions(size=3))
    assert len(page1.items) == 3
    assert page1.next is not None
    
    # Second page: 2 items (partial)
    page2 = paginate(sync_session, query, PageOptions(cursor=page1.next, size=3))
    assert len(page2.items) == 2
    assert page2.next is None


def test_cursor_with_no_more_items(sync_session):
    """Test using cursor when no more items exist."""
    query = select(Product).order_by(Product.id)
    
    # Get all items
    page1 = paginate(sync_session, query, PageOptions(size=5))
    
    # Try to get next page (should be empty)
    if page1.next:
        page2 = paginate(sync_session, query, PageOptions(cursor=page1.next, size=5))
        assert len(page2.items) == 0


def test_invalid_cursor_format(sync_session):
    """Test with invalid cursor format."""
    query = select(Product).order_by(Product.id)
    
    with pytest.raises(CursorError):
        paginate(sync_session, query, PageOptions(cursor="invalid!!!", size=10))


def test_cursor_field_mismatch(sync_session):
    """Test cursor with mismatched fields."""
    from query_pager.core.cursor import encode_cursor

    # Create cursor with wrong fields (ordering matches but values don't)
    wrong_cursor = encode_cursor([("id", "asc")], {"wrong_field": 10})

    query = select(Product).order_by(Product.id)

    with pytest.raises(CursorError, match="missing fields"):
        paginate(sync_session, query, PageOptions(cursor=wrong_cursor, size=10))


def test_minimum_page_size(sync_session):
    """Test with minimum page size (1)."""
    query = select(Product).order_by(Product.id)
    
    result = paginate(sync_session, query, PageOptions(size=1))
    
    assert len(result.items) == 1
    assert result.next is not None


def test_descending_order_edge_case(sync_session):
    """Test descending order with cursor."""
    query = select(Product).order_by(Product.id.desc())
    
    page1 = paginate(sync_session, query, PageOptions(size=2))
    assert page1.items[0].id > page1.items[1].id
    
    if page1.next:
        page2 = paginate(sync_session, query, PageOptions(cursor=page1.next, size=2))
        # Next page should have smaller IDs
        assert page2.items[0].id < page1.items[-1].id
