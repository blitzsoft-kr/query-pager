"""Tests for cursor ordering validation in Django pagination."""

import pytest
from django.test import TestCase

from query_pager.core.exceptions import CursorError
from query_pager.core.schemas import PageOptions
from query_pager.django.pagination import paginate

from ..django_app.models import Product


@pytest.mark.django_db
class TestCursorOrderingValidation(TestCase):
    """Test class for cursor ordering validation."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        Product.objects.all().delete()

        # Create test products
        Product.objects.create(id=1, name="Apple", category="fruit", price=100, likes=10)
        Product.objects.create(id=2, name="Banana", category="fruit", price=150, likes=20)
        Product.objects.create(
            id=3, name="Cherry", category="fruit", price=120, likes=15
        )
        Product.objects.create(id=4, name="Date", category="fruit", price=200, likes=25)
        Product.objects.create(
            id=5, name="Elderberry", category="fruit", price=180, likes=30
        )

    def test_cursor_with_different_field_raises_error(self):
        """Test using cursor from different field ordering raises error."""
        # Get cursor with id ordering
        queryset_id = Product.objects.order_by("id")
        page1 = paginate(queryset_id, PageOptions(size=2))

        # Try to use cursor with price ordering
        queryset_price = Product.objects.order_by("price")
        with pytest.raises(CursorError, match="ordering mismatch"):
            paginate(queryset_price, PageOptions(cursor=page1.next, size=2))

    def test_cursor_with_different_direction_raises_error(self):
        """Test using cursor from different direction raises error."""
        # Get cursor with ASC ordering
        queryset_asc = Product.objects.order_by("id")
        page1 = paginate(queryset_asc, PageOptions(size=2))

        # Try to use cursor with DESC ordering
        queryset_desc = Product.objects.order_by("-id")
        with pytest.raises(CursorError, match="ordering mismatch"):
            paginate(queryset_desc, PageOptions(cursor=page1.next, size=2))

    def test_cursor_with_different_field_order_raises_error(self):
        """Test using cursor from different field order raises error."""
        # Get cursor with (name, id) ordering
        queryset_name_id = Product.objects.order_by("name", "id")
        page1 = paginate(queryset_name_id, PageOptions(size=2))

        # Try to use cursor with (id, name) ordering
        queryset_id_name = Product.objects.order_by("id", "name")
        with pytest.raises(CursorError, match="ordering mismatch"):
            paginate(queryset_id_name, PageOptions(cursor=page1.next, size=2))

    def test_cursor_with_matching_ordering_succeeds(self):
        """Test using cursor with matching ordering succeeds."""
        queryset = Product.objects.order_by("-name", "id")

        # First page
        page1 = paginate(queryset, PageOptions(size=2))
        assert page1.next is not None

        # Second page with same ordering
        page2 = paginate(queryset, PageOptions(cursor=page1.next, size=2))
        assert len(page2.items) > 0
        # Should not raise

    def test_multi_field_ordering_validation(self):
        """Test multi-field ordering is validated correctly."""
        # Get cursor with 3-field ordering
        queryset_3fields = Product.objects.order_by("category", "-price", "id")
        page1 = paginate(queryset_3fields, PageOptions(size=2))

        # Try with 2-field ordering (subset)
        queryset_2fields = Product.objects.order_by("category", "-price")
        with pytest.raises(CursorError, match="ordering mismatch"):
            paginate(queryset_2fields, PageOptions(cursor=page1.next, size=2))

        # Try with same 3 fields but different direction on middle field
        queryset_wrong_dir = Product.objects.order_by(
            "category", "price", "id"  # price ASC instead of DESC
        )
        with pytest.raises(CursorError, match="ordering mismatch"):
            paginate(queryset_wrong_dir, PageOptions(cursor=page1.next, size=2))
