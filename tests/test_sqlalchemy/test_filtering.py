"""Tests for SQLAlchemy filtering."""

import pytest
from sqlalchemy import select

from query_pager.sqlalchemy.filtering import apply_cel_filter
from .conftest import Product


def test_filter_simple_comparison(sync_session):
    """Test simple comparison filter."""
    query = select(Product)
    allowed_fields = {"price": Product.price}

    filtered = apply_cel_filter(
        query,
        expr="price >= 50000",
        fields=allowed_fields,
    )
    results = sync_session.execute(filtered).scalars().all()

    assert len(results) == 3
    assert all(p.price >= 50000 for p in results)


def test_filter_equality(sync_session):
    """Test equality filter."""
    query = select(Product)
    allowed_fields = {"category": Product.category}

    filtered = apply_cel_filter(
        query,
        expr="category == 'electronics'",
        fields=allowed_fields,
    )
    results = sync_session.execute(filtered).scalars().all()

    assert len(results) == 3
    assert all(p.category == "electronics" for p in results)


def test_filter_and_condition(sync_session):
    """Test AND condition filter."""
    query = select(Product)
    allowed_fields = {
        "price": Product.price,
        "category": Product.category,
    }

    filtered = apply_cel_filter(
        query,
        expr="price >= 50000 && category == 'electronics'",
        fields=allowed_fields,
    )
    results = sync_session.execute(filtered).scalars().all()

    assert len(results) == 3
    assert all(p.price >= 50000 and p.category == "electronics" for p in results)


def test_filter_or_condition(sync_session):
    """Test OR condition filter."""
    query = select(Product)
    allowed_fields = {
        "category": Product.category,
    }

    filtered = apply_cel_filter(
        query,
        expr="category == 'electronics' || category == 'books'",
        fields=allowed_fields,
    )
    results = sync_session.execute(filtered).scalars().all()

    assert len(results) == 5  # All products


def test_filter_in_operator(sync_session):
    """Test IN operator with list literal."""
    query = select(Product)
    allowed_fields = {"category": Product.category}

    filtered = apply_cel_filter(
        query,
        expr="category in ['electronics', 'books']",
        fields=allowed_fields,
    )
    results = sync_session.execute(filtered).scalars().all()

    # Should return all products that are either electronics or books
    assert len(results) == 5
    categories = {p.category for p in results}
    assert categories == {"electronics", "books"}


def test_filter_string_contains(sync_session):
    """Test string contains method."""
    query = select(Product)
    allowed_fields = {"name": Product.name}

    filtered = apply_cel_filter(
        query,
        expr="name.contains('o')",
        fields=allowed_fields,
    )
    results = sync_session.execute(filtered).scalars().all()

    assert len(results) == 3  # Laptop, Phone, Book


def test_filter_string_startswith(sync_session):
    """Test string startsWith method."""
    query = select(Product)
    allowed_fields = {"name": Product.name}

    filtered = apply_cel_filter(
        query,
        expr="name.startsWith('P')",
        fields=allowed_fields,
    )
    results = sync_session.execute(filtered).scalars().all()

    assert len(results) == 1
    assert results[0].name == "Phone"


def test_filter_empty_expression(sync_session):
    """Test empty expression returns unfiltered query."""
    query = select(Product)
    allowed_fields = {"price": Product.price}

    filtered = apply_cel_filter(
        query,
        expr="",
        fields=allowed_fields,
    )
    results = sync_session.execute(filtered).scalars().all()

    assert len(results) == 5  # All products


def test_filter_disallowed_field(sync_session):
    """Test filtering with disallowed field raises error."""
    query = select(Product)
    allowed_fields = {"price": Product.price}

    with pytest.raises(ValueError, match="not allowed"):
        apply_cel_filter(
            query,
            expr="category == 'electronics'",
            fields=allowed_fields,
        )


def test_filter_invalid_expression(sync_session):
    """Test invalid expression raises error."""
    query = select(Product)
    allowed_fields = {"price": Product.price}

    with pytest.raises(ValueError, match="Failed to apply"):
        apply_cel_filter(
            query,
            expr="invalid && &&",
            fields=allowed_fields,
        )
