"""Tests for SQLAlchemy ordering."""

import pytest
from sqlalchemy import select

from query_pager.sqlalchemy.ordering import apply_ordering
from .conftest import Product


def test_ordering_single_field_asc(sync_session):
    """Test ordering by single field ascending."""
    query = select(Product)
    orderable = {"price": Product.price}

    ordered = apply_ordering(query, order_by="price", fields=orderable)
    results = sync_session.execute(ordered).scalars().all()

    prices = [p.price for p in results]
    assert prices == sorted(prices)


def test_ordering_single_field_desc(sync_session):
    """Test ordering by single field descending."""
    query = select(Product)
    orderable = {"price": Product.price}

    ordered = apply_ordering(query, order_by="-price", fields=orderable)
    results = sync_session.execute(ordered).scalars().all()

    prices = [p.price for p in results]
    assert prices == sorted(prices, reverse=True)


def test_ordering_multiple_fields(sync_session):
    """Test ordering by multiple fields."""
    query = select(Product)
    orderable = {
        "category": Product.category,
        "price": Product.price,
    }

    ordered = apply_ordering(query, order_by="category,-price", fields=orderable)
    results = sync_session.execute(ordered).scalars().all()

    # Check that results are ordered by category asc, then price desc
    assert results[0].category == "books"
    assert results[1].category == "books"
    # Within books, higher price first
    assert results[0].price > results[1].price


def test_ordering_by_likes(sync_session):
    """Test ordering by likes field."""
    query = select(Product)
    orderable = {"likes": Product.likes}

    ordered = apply_ordering(query, order_by="-likes", fields=orderable)
    results = sync_session.execute(ordered).scalars().all()

    likes = [p.likes for p in results]
    assert likes == sorted(likes, reverse=True)
    assert results[0].likes == 100  # Phone has most likes


def test_ordering_empty_string(sync_session):
    """Test empty ordering string returns unordered query."""
    query = select(Product)
    orderable = {"price": Product.price}

    ordered = apply_ordering(query, order_by="", fields=orderable)
    results = sync_session.execute(ordered).scalars().all()

    assert len(results) == 5


def test_ordering_none(sync_session):
    """Test None ordering returns unordered query."""
    query = select(Product)
    orderable = {"price": Product.price}

    ordered = apply_ordering(query, order_by=None, fields=orderable)
    results = sync_session.execute(ordered).scalars().all()

    assert len(results) == 5


def test_ordering_disallowed_field(sync_session):
    """Test ordering with disallowed field raises error."""
    query = select(Product)
    orderable = {"price": Product.price}

    with pytest.raises(ValueError, match="not allowed"):
        apply_ordering(query, order_by="category", fields=orderable)


def test_ordering_invalid_format(sync_session):
    """Test invalid ordering format raises error."""
    query = select(Product)
    orderable = {"price": Product.price}

    with pytest.raises(ValueError):
        apply_ordering(query, order_by="-", fields=orderable)
