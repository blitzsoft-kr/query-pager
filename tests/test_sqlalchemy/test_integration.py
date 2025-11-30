"""Integration tests combining filtering, ordering, and pagination."""

import pytest
from sqlalchemy import select

from query_pager.core.schemas import PageOptions
from query_pager.sqlalchemy.filtering import apply_cel_filter
from query_pager.sqlalchemy.ordering import apply_ordering
from query_pager.sqlalchemy.pagination import paginate, paginate_async
from .conftest import Product


def test_filter_order_paginate_sync(sync_session):
    """Test combining filter, order, and pagination (sync)."""
    # Build query with filter, order, and pagination
    query = select(Product)

    # Apply filter
    allowed_fields = {"category": Product.category, "price": Product.price}
    query = apply_cel_filter(
        query,
        expr="category == 'electronics'",
        fields=allowed_fields,
    )

    # Apply ordering
    orderable_fields = {"price": Product.price, "id": Product.id}
    query = apply_ordering(query, order_by="-price,id", fields=orderable_fields)

    # Paginate
    options = PageOptions(size=2)
    result = paginate(sync_session, query, options)

    # Verify results
    assert result.total_size == 3  # 3 electronics products
    assert len(result.items) == 2
    assert result.items[0].category == "electronics"
    assert result.items[0].price >= result.items[1].price  # Descending price


@pytest.mark.asyncio
async def test_filter_order_paginate_async(async_session):
    """Test combining filter, order, and pagination (async)."""
    # Build query with filter, order, and pagination
    query = select(Product)

    # Apply filter
    allowed_fields = {"price": Product.price}
    query = apply_cel_filter(
        query,
        expr="price >= 50000",
        fields=allowed_fields,
    )

    # Apply ordering
    orderable_fields = {"likes": Product.likes, "id": Product.id}
    query = apply_ordering(query, order_by="-likes", fields=orderable_fields)

    # Paginate
    options = PageOptions(size=2)
    result = await paginate_async(async_session, query, options)

    # Verify results
    assert result.total_size == 3  # 3 products with price >= 50000
    assert len(result.items) == 2
    assert all(p.price >= 50000 for p in result.items)
    assert result.items[0].likes >= result.items[1].likes  # Descending likes


def test_complex_filter_with_pagination(sync_session):
    """Test complex filter with pagination."""
    query = select(Product)

    # Complex filter: electronics OR (books AND price >= 10000)
    allowed_fields = {
        "category": Product.category,
        "price": Product.price,
    }
    query = apply_cel_filter(
        query,
        expr="category == 'electronics' || (category == 'books' && price >= 10000)",
        fields=allowed_fields,
    )

    # Order by price
    orderable_fields = {"price": Product.price, "id": Product.id}
    query = apply_ordering(query, order_by="price,id", fields=orderable_fields)

    # Paginate
    options = PageOptions(size=10)
    result = paginate(sync_session, query, options)

    # Should get 3 electronics + 1 book (Book with price 20000)
    assert result.total_size == 4
    assert len(result.items) == 4


def test_pagination_navigation(sync_session):
    """Test navigating through pages with filters and ordering."""
    query = select(Product)

    # Filter to electronics only
    allowed_fields = {"category": Product.category}
    query = apply_cel_filter(
        query,
        expr="category == 'electronics'",
        fields=allowed_fields,
    )

    # Order by id
    orderable_fields = {"id": Product.id}
    query = apply_ordering(query, order_by="id", fields=orderable_fields)

    # Get first page
    page1 = paginate(sync_session, query, PageOptions(size=2))
    assert len(page1.items) == 2
    assert page1.items[0].id == 1  # Laptop
    assert page1.next is not None

    # Get second page
    page2 = paginate(sync_session, query, PageOptions(cursor=page1.next, size=2))
    assert len(page2.items) == 1
    assert page2.items[0].id == 4  # Tablet
    assert page2.next is None  # Last page


def test_empty_result_pagination(sync_session):
    """Test pagination with filter that returns no results."""
    query = select(Product)

    # Filter that matches nothing
    allowed_fields = {"price": Product.price}
    query = apply_cel_filter(
        query,
        expr="price > 1000000",
        fields=allowed_fields,
    )

    # Order by id
    orderable_fields = {"id": Product.id}
    query = apply_ordering(query, order_by="id", fields=orderable_fields)

    # Paginate
    result = paginate(sync_session, query, PageOptions(size=10))

    assert result.total_size == 0
    assert len(result.items) == 0
    assert result.prev is None
    assert result.next is None
