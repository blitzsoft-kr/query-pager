"""Tests for include_prev_cursor feature in Django pagination."""

import pytest
from query_pager.core.schemas import PageOptions
from query_pager.django.pagination import paginate
from tests.django_app.models import Product

# Apply django_db marker to all tests in this file
pytestmark = pytest.mark.django_db


class TestIncludePrevCursor:
    """Tests for include_prev_cursor feature."""

    def test_include_prev_cursor_with_zero_results(self, products):
        """Test include_prev_cursor with zero results - both cursors should be None."""
        queryset = Product.objects.filter(category="nonexistent").order_by("-id")
        result = paginate(queryset, PageOptions(size=20, include_prev_cursor=True))

        assert result.total_size == 0
        assert len(result.items) == 0
        assert result.prev is None
        assert result.next is None

    def test_include_prev_cursor_with_few_results_no_more(self, products):
        """Test include_prev_cursor with 2 results (< size, has_more=False).

        Should return prev cursor for incremental updates, but no next cursor.
        """
        # Filter to get only 2 items
        queryset = Product.objects.filter(category="books").order_by("-id")
        result = paginate(queryset, PageOptions(size=20, include_prev_cursor=True))

        assert result.total_size == 2
        assert len(result.items) == 2
        assert result.items[0].id == 5  # Magazine (desc order)
        assert result.items[1].id == 3  # Book
        assert result.prev is not None  # Should have prev for incremental updates
        assert result.next is None  # No more items

    def test_include_prev_cursor_with_exact_page_size(self, products):
        """Test include_prev_cursor with results exactly matching page size (has_more=False).

        Should return prev cursor, but no next cursor.
        """
        queryset = Product.objects.all().order_by("-id")
        result = paginate(queryset, PageOptions(size=5, include_prev_cursor=True))

        assert result.total_size == 5
        assert len(result.items) == 5
        assert result.items[0].id == 5  # Highest ID (desc order)
        assert result.items[-1].id == 1  # Lowest ID
        assert result.prev is not None  # Should have prev for incremental updates
        assert result.next is None  # No more items

    def test_include_prev_cursor_with_more_results(self, products):
        """Test include_prev_cursor with more results than page size (has_more=True).

        Should return both prev and next cursors.
        """
        queryset = Product.objects.all().order_by("-id")
        result = paginate(queryset, PageOptions(size=3, include_prev_cursor=True))

        assert result.total_size == 5
        assert len(result.items) == 3
        assert result.items[0].id == 5  # Highest ID
        assert result.items[-1].id == 3
        assert result.prev is not None  # Should have prev for incremental updates
        assert result.next is not None  # Has more items

    def test_include_prev_cursor_false_first_page(self, products):
        """Test that include_prev_cursor=False maintains original behavior.

        First page should have no prev cursor.
        """
        queryset = Product.objects.all().order_by("-id")
        result = paginate(queryset, PageOptions(size=3, include_prev_cursor=False))

        assert result.total_size == 5
        assert len(result.items) == 3
        assert result.prev is None  # Original behavior: no prev on first page
        assert result.next is not None

    def test_include_prev_cursor_default_is_false(self, products):
        """Test that include_prev_cursor defaults to False."""
        queryset = Product.objects.all().order_by("-id")
        result = paginate(queryset, PageOptions(size=3))

        assert result.prev is None  # Default behavior
        assert result.next is not None

    def test_prev_cursor_can_fetch_new_items(self, products):
        """Test that prev cursor from first page can be used to fetch newer items.

        Simulates chat app scenario: fetch initial messages, then check for new ones.
        """
        # Initial fetch: get latest messages
        queryset = Product.objects.all().order_by("-id")
        first_page = paginate(queryset, PageOptions(size=3, include_prev_cursor=True))

        assert len(first_page.items) == 3
        assert first_page.items[0].id == 5  # Latest item
        assert first_page.prev is not None

        # Verify the cursor is valid and points to correct item
        from query_pager.core.cursor import decode_cursor

        order_fields, cursor_values, direction = decode_cursor(first_page.prev)

        assert direction == "prev"
        assert cursor_values["id"] == 5  # Points to the first (newest) item
        assert order_fields == [("id", "desc")]

    def test_prev_cursor_with_multi_field_ordering(self, products):
        """Test include_prev_cursor with multi-field ordering."""
        queryset = Product.objects.all().order_by("-price", "-id")
        result = paginate(queryset, PageOptions(size=2, include_prev_cursor=True))

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

    def test_navigation_with_prev_cursor_enabled(self, products):
        """Test that navigation still works correctly with include_prev_cursor=True."""
        queryset = Product.objects.all().order_by("-id")

        # First page
        page1 = paginate(queryset, PageOptions(size=2, include_prev_cursor=True))
        assert len(page1.items) == 2
        assert page1.items[0].id == 5
        assert page1.items[1].id == 4
        assert page1.prev is not None
        assert page1.next is not None

        # Navigate to second page using next cursor
        page2 = paginate(queryset, PageOptions(cursor=page1.next, size=2))
        assert len(page2.items) == 2
        assert page2.items[0].id == 3
        assert page2.items[1].id == 2
        assert page2.prev is not None  # Normal behavior: has prev because we used cursor
        assert page2.next is not None
