"""Tests for SQLAlchemy pagination (sync)."""

import pytest
from sqlalchemy import select

from query_pager.core.schemas import PageOptions
from query_pager.sqlalchemy.pagination import paginate
from .conftest import Product


def test_paginate_first_page(sync_session):
    """Test paginating first page."""
    query = select(Product).order_by(Product.id)
    options = PageOptions(cursor=None, size=2)

    result = paginate(sync_session, query, options)

    assert result.total_size == 5
    assert len(result.items) == 2
    assert result.items[0].id == 1
    assert result.items[1].id == 2
    assert result.prev is None
    assert result.next is not None


def test_paginate_second_page(sync_session):
    """Test paginating second page."""
    query = select(Product).order_by(Product.id)

    # Get first page to get cursor
    first_page = paginate(sync_session, query, PageOptions(size=2))
    cursor = first_page.next

    # Get second page
    result = paginate(sync_session, query, PageOptions(cursor=cursor, size=2))

    assert len(result.items) == 2
    assert result.items[0].id == 3
    assert result.items[1].id == 4
    assert result.prev is not None
    assert result.next is not None


def test_paginate_last_page(sync_session):
    """Test paginating last page."""
    query = select(Product).order_by(Product.id)

    # Navigate to last page
    page1 = paginate(sync_session, query, PageOptions(size=2))
    page2 = paginate(sync_session, query, PageOptions(cursor=page1.next, size=2))
    result = paginate(sync_session, query, PageOptions(cursor=page2.next, size=2))

    assert len(result.items) == 1
    assert result.items[0].id == 5
    assert result.prev is not None
    assert result.next is None


def test_paginate_with_filter(sync_session):
    """Test pagination with filtered query."""
    query = select(Product).where(Product.category == "electronics").order_by(Product.id)
    options = PageOptions(size=2)

    result = paginate(sync_session, query, options)

    assert result.total_size == 3
    assert len(result.items) == 2
    assert all(p.category == "electronics" for p in result.items)


def test_paginate_descending_order(sync_session):
    """Test pagination with descending order."""
    query = select(Product).order_by(Product.price.desc(), Product.id.desc())
    options = PageOptions(size=2)

    result = paginate(sync_session, query, options)

    assert len(result.items) == 2
    assert result.items[0].price >= result.items[1].price


def test_paginate_no_order_by_raises_error(sync_session):
    """Test pagination without ORDER BY raises error."""
    query = select(Product)  # No order_by
    options = PageOptions(size=2)

    with pytest.raises(ValueError, match="ORDER BY"):
        paginate(sync_session, query, options)


def test_paginate_custom_page_size(sync_session):
    """Test pagination with custom page size."""
    query = select(Product).order_by(Product.id)
    options = PageOptions(size=3)

    result = paginate(sync_session, query, options)

    assert len(result.items) == 3
    assert result.total_size == 5
