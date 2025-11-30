"""Simple tests for Django filtering."""

import pytest
from query_pager.django.filtering import apply_cel_filter
from tests.django_app.models import Product

# Apply django_db marker to all tests in this file
pytestmark = pytest.mark.django_db


class TestDjangoFiltering:
    """Simple Django filtering tests."""

    def test_simple_comparison(self, products):
        """Test simple comparison."""
        queryset = Product.objects.all()
        filtered = apply_cel_filter(
            queryset,
            expr="price >= 50000",
            fields={"price"},
        )
        
        results = list(filtered)
        assert len(results) == 3  # Laptop(100000), Phone(80000), Tablet(60000)

    def test_equality(self, products):
        """Test equality."""
        queryset = Product.objects.all()
        filtered = apply_cel_filter(
            queryset,
            expr="category == 'electronics'",
            fields={"category"},
        )
        
        results = list(filtered)
        assert len(results) == 3

    def test_in_operator(self, products):
        """Test IN operator."""
        queryset = Product.objects.all()
        filtered = apply_cel_filter(
            queryset,
            expr="category in ['electronics', 'books']",
            fields={"category"},
        )
        
        results = list(filtered)
        assert len(results) == 5

    def test_and_condition(self, products):
        """Test AND condition."""
        queryset = Product.objects.all()
        filtered = apply_cel_filter(
            queryset,
            expr="price >= 50000 && category == 'electronics'",
            fields={"price", "category"},
        )
        
        results = list(filtered)
        assert len(results) == 3

    def test_string_contains(self, products):
        """Test string contains."""
        queryset = Product.objects.all()
        filtered = apply_cel_filter(
            queryset,
            expr="name.contains('o')",
            fields={"name"},
        )
        
        results = list(filtered)
        assert len(results) == 3  # Laptop, Phone, Book

    def test_empty_expression(self, products):
        """Test empty expression."""
        queryset = Product.objects.all()
        filtered = apply_cel_filter(
            queryset,
            expr="",
            fields={"price"},
        )
        
        assert filtered == queryset
