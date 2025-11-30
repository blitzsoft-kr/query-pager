"""Tests for SQLAlchemy pagination (async)."""

import pytest
from sqlalchemy import select

from query_pager.core.schemas import PageOptions
from query_pager.sqlalchemy.pagination import paginate_async
from .conftest import Product


@pytest.mark.asyncio
async def test_paginate_async_first_page(async_session):
    """Test async paginating first page."""
    query = select(Product).order_by(Product.id)
    options = PageOptions(cursor=None, size=2)

    result = await paginate_async(async_session, query, options)

    assert result.total_size == 5
    assert len(result.items) == 2
    assert result.items[0].id == 1
    assert result.items[1].id == 2
    assert result.prev is None
    assert result.next is not None


@pytest.mark.asyncio
async def test_paginate_async_second_page(async_session):
    """Test async paginating second page."""
    query = select(Product).order_by(Product.id)

    # Get first page to get cursor
    first_page = await paginate_async(async_session, query, PageOptions(size=2))
    cursor = first_page.next

    # Get second page
    result = await paginate_async(async_session, query, PageOptions(cursor=cursor, size=2))

    assert len(result.items) == 2
    assert result.items[0].id == 3
    assert result.items[1].id == 4
    assert result.prev is not None
    assert result.next is not None


@pytest.mark.asyncio
async def test_paginate_async_last_page(async_session):
    """Test async paginating last page."""
    query = select(Product).order_by(Product.id)

    # Navigate to last page
    page1 = await paginate_async(async_session, query, PageOptions(size=2))
    page2 = await paginate_async(async_session, query, PageOptions(cursor=page1.next, size=2))
    result = await paginate_async(async_session, query, PageOptions(cursor=page2.next, size=2))

    assert len(result.items) == 1
    assert result.items[0].id == 5
    assert result.prev is not None
    assert result.next is None


@pytest.mark.asyncio
async def test_paginate_async_with_filter(async_session):
    """Test async pagination with filtered query."""
    query = select(Product).where(Product.category == "electronics").order_by(Product.id)
    options = PageOptions(size=2)

    result = await paginate_async(async_session, query, options)

    assert result.total_size == 3
    assert len(result.items) == 2
    assert all(p.category == "electronics" for p in result.items)


@pytest.mark.asyncio
async def test_paginate_async_no_order_by_raises_error(async_session):
    """Test async pagination without ORDER BY raises error."""
    query = select(Product)  # No order_by
    options = PageOptions(size=2)

    with pytest.raises(ValueError, match="ORDER BY"):
        await paginate_async(async_session, query, options)
