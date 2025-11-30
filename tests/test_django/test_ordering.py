"""Simple tests for Django ordering."""

import pytest
from query_pager.django.ordering import apply_ordering
from tests.django_app.models import Product

# Apply django_db marker to all tests in this file
pytestmark = pytest.mark.django_db


class TestDjangoOrdering:
    """Simple Django ordering tests."""

    def test_single_field_asc(self, products):
        """Test single field ascending."""
        queryset = Product.objects.all()
        ordered = apply_ordering(queryset, order_by="price", fields={"price"})
        
        results = list(ordered)
        assert results[0].price == 5000
        assert results[-1].price == 100000

    def test_single_field_desc(self, products):
        """Test single field descending."""
        queryset = Product.objects.all()
        ordered = apply_ordering(queryset, order_by="-price", fields={"price"})
        
        results = list(ordered)
        assert results[0].price == 100000
        assert results[-1].price == 5000

    def test_multiple_fields(self, products):
        """Test multiple fields."""
        queryset = Product.objects.all()
        ordered = apply_ordering(queryset, order_by="category,-price", fields={"category", "price"})
        
        results = list(ordered)
        # First should be books category
        assert results[0].category == "books"

    def test_empty_ordering(self, products):
        """Test empty ordering."""
        queryset = Product.objects.all()
        ordered = apply_ordering(queryset, order_by="", fields={"price"})
        
        assert ordered == queryset
