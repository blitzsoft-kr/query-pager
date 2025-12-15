"""Integration tests combining filtering, ordering, and pagination for Django."""

import pytest
from query_pager.core.schemas import PageOptions
from query_pager.django.filtering import apply_cel_filter
from query_pager.django.ordering import apply_ordering
from query_pager.django.pagination import paginate
from tests.django_app.models import Product

pytestmark = pytest.mark.django_db


class TestFilterOrderPaginate:
    """Test combining filter, order, and pagination."""

    def test_filter_order_paginate(self, products):
        """Test combining filter, order, and pagination."""
        queryset = Product.objects.all()

        # Apply filter
        queryset = apply_cel_filter(
            queryset,
            expr="category == 'electronics'",
            fields={"category"},
        )

        # Apply ordering
        queryset = apply_ordering(
            queryset,
            order_by="-price,id",
            fields={"price", "id"},
        )

        # Paginate
        result = paginate(queryset, PageOptions(size=2))

        # Verify results
        assert result.total_size == 3  # 3 electronics products
        assert len(result.items) == 2
        assert all(p.category == "electronics" for p in result.items)
        assert result.items[0].price >= result.items[1].price  # Descending price

    def test_complex_filter_with_pagination(self, products):
        """Test complex filter with pagination."""
        queryset = Product.objects.all()

        # Complex filter: electronics OR (books AND price >= 10000)
        queryset = apply_cel_filter(
            queryset,
            expr="category == 'electronics' || (category == 'books' && price >= 10000)",
            fields={"category", "price"},
        )

        # Order by price
        queryset = apply_ordering(queryset, order_by="price,id", fields={"price", "id"})

        # Paginate
        result = paginate(queryset, PageOptions(size=10))

        # Should get 3 electronics + 1 book (Book with price 20000)
        assert result.total_size == 4
        assert len(result.items) == 4


class TestPaginationNavigation:
    """Test navigating through pages."""

    def test_pagination_navigation(self, products):
        """Test navigating through pages with filters and ordering."""
        queryset = Product.objects.all()

        # Filter to electronics only
        queryset = apply_cel_filter(
            queryset,
            expr="category == 'electronics'",
            fields={"category"},
        )

        # Order by id
        queryset = apply_ordering(queryset, order_by="id", fields={"id"})

        # Get first page
        page1 = paginate(queryset, PageOptions(size=2))
        assert len(page1.items) == 2
        assert page1.items[0].id == 1  # Laptop
        assert page1.next is not None

        # Get second page
        page2 = paginate(queryset, PageOptions(cursor=page1.next, size=2))
        assert len(page2.items) == 1
        assert page2.items[0].id == 4  # Tablet
        assert page2.next is None  # Last page

    def test_backward_navigation(self, products):
        """Test backward navigation with prev cursor."""
        queryset = Product.objects.all().order_by("id")

        # Get first page
        page1 = paginate(queryset, PageOptions(size=2))
        assert page1.prev is None

        # Get second page
        page2 = paginate(queryset, PageOptions(cursor=page1.next, size=2))
        assert page2.prev is not None

        # Using prev cursor returns items before current page position
        prev_page = paginate(queryset, PageOptions(cursor=page2.prev, size=2))
        assert len(prev_page.items) == 2
        # Prev returns items before page2's first item (id=3)
        assert all(item.id < page2.items[0].id for item in prev_page.items)


class TestEmptyResults:
    """Test pagination with empty results."""

    def test_empty_result_pagination(self, products):
        """Test pagination with filter that returns no results."""
        queryset = Product.objects.all()

        # Filter that matches nothing
        queryset = apply_cel_filter(
            queryset,
            expr="price > 1000000",
            fields={"price"},
        )

        # Order by id
        queryset = apply_ordering(queryset, order_by="id", fields={"id"})

        # Paginate
        result = paginate(queryset, PageOptions(size=10))

        assert result.total_size == 0
        assert len(result.items) == 0
        assert result.prev is None
        assert result.next is None
