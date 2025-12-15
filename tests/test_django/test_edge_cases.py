"""Tests for edge cases in Django pagination."""

import pytest
from query_pager.core.exceptions import CursorError
from query_pager.core.schemas import PageOptions
from query_pager.django.pagination import paginate
from tests.django_app.models import Product

pytestmark = pytest.mark.django_db


class TestEmptyAndSingleResults:
    """Test empty and single item results."""

    def test_empty_result_set(self, products):
        """Test pagination with empty result set."""
        queryset = Product.objects.filter(price__gt=999999).order_by("id")

        result = paginate(queryset, PageOptions(size=10))

        assert result.total_size == 0
        assert len(result.items) == 0
        assert result.next is None
        assert result.prev is None

    def test_single_item(self, products):
        """Test pagination with single item."""
        # Delete all but one
        Product.objects.exclude(id=1).delete()

        queryset = Product.objects.all().order_by("id")
        result = paginate(queryset, PageOptions(size=10))

        assert result.total_size == 1
        assert len(result.items) == 1
        assert result.next is None
        assert result.prev is None


class TestPageSizeBoundaries:
    """Test page size boundary conditions."""

    def test_exact_page_size(self, products):
        """Test when result count equals page size."""
        queryset = Product.objects.all().order_by("id")

        # Request exactly 5 items (we have 5 in fixture)
        result = paginate(queryset, PageOptions(size=5))

        assert len(result.items) == 5
        assert result.next is None  # No more items

    def test_page_size_larger_than_total(self, products):
        """Test when page size is larger than total items."""
        queryset = Product.objects.all().order_by("id")

        result = paginate(queryset, PageOptions(size=100))

        assert len(result.items) == 5  # Only 5 items exist
        assert result.next is None

    def test_last_page_partial(self, products):
        """Test last page with partial results."""
        queryset = Product.objects.all().order_by("id")

        # First page: 3 items
        page1 = paginate(queryset, PageOptions(size=3))
        assert len(page1.items) == 3
        assert page1.next is not None

        # Second page: 2 items (partial)
        page2 = paginate(queryset, PageOptions(cursor=page1.next, size=3))
        assert len(page2.items) == 2
        assert page2.next is None

    def test_minimum_page_size(self, products):
        """Test with minimum page size (1)."""
        queryset = Product.objects.all().order_by("id")

        result = paginate(queryset, PageOptions(size=1))

        assert len(result.items) == 1
        assert result.next is not None


class TestCursorEdgeCases:
    """Test cursor edge cases."""

    def test_cursor_with_no_more_items(self, products):
        """Test using cursor when no more items exist."""
        queryset = Product.objects.all().order_by("id")

        # Get all items
        page1 = paginate(queryset, PageOptions(size=5))

        # Try to get next page (should be empty)
        if page1.next:
            page2 = paginate(queryset, PageOptions(cursor=page1.next, size=5))
            assert len(page2.items) == 0

    def test_invalid_cursor_format(self, products):
        """Test with invalid cursor format."""
        queryset = Product.objects.all().order_by("id")

        with pytest.raises(CursorError):
            paginate(queryset, PageOptions(cursor="invalid!!!", size=10))

    def test_cursor_field_mismatch(self, products):
        """Test cursor with mismatched fields."""
        from query_pager.core.cursor import encode_cursor

        # Create cursor with wrong fields
        wrong_cursor = encode_cursor([("id", "asc")], {"wrong_field": 10})

        queryset = Product.objects.all().order_by("id")

        with pytest.raises(CursorError, match="missing fields"):
            paginate(queryset, PageOptions(cursor=wrong_cursor, size=10))


class TestOrderingEdgeCases:
    """Test ordering edge cases."""

    def test_descending_order_edge_case(self, products):
        """Test descending order with cursor."""
        queryset = Product.objects.all().order_by("-id")

        page1 = paginate(queryset, PageOptions(size=2))
        assert page1.items[0].id > page1.items[1].id

        if page1.next:
            page2 = paginate(queryset, PageOptions(cursor=page1.next, size=2))
            # Next page should have smaller IDs
            assert page2.items[0].id < page1.items[-1].id

    def test_multi_field_ordering(self, products):
        """Test ordering by multiple fields."""
        queryset = Product.objects.all().order_by("category", "-price", "id")

        page1 = paginate(queryset, PageOptions(size=3))
        assert len(page1.items) == 3

        if page1.next:
            page2 = paginate(queryset, PageOptions(cursor=page1.next, size=3))
            assert len(page2.items) == 2
