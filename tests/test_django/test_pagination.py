"""Simple tests for Django pagination."""

import pytest
from query_pager.core.schemas import PageOptions
from query_pager.django.pagination import paginate
from tests.django_app.models import Product

# Apply django_db marker to all tests in this file
pytestmark = pytest.mark.django_db


class TestDjangoPagination:
    """Simple Django pagination tests."""

    def test_first_page(self, products):
        """Test first page."""
        queryset = Product.objects.all().order_by('id')
        result = paginate(queryset, PageOptions(size=2))
        
        assert len(result.items) == 2
        assert result.items[0].id == 1
        assert result.items[1].id == 2
        assert result.next is not None
        assert result.prev is None

    def test_second_page(self, products):
        """Test second page."""
        queryset = Product.objects.all().order_by('id')
        
        # Get first page
        page1 = paginate(queryset, PageOptions(size=2))
        
        # Get second page
        page2 = paginate(queryset, PageOptions(cursor=page1.next, size=2))
        
        assert len(page2.items) == 2
        assert page2.items[0].id == 3
        assert page2.items[1].id == 4

    def test_last_page(self, products):
        """Test last page."""
        queryset = Product.objects.all().order_by('id')
        
        page1 = paginate(queryset, PageOptions(size=3))
        page2 = paginate(queryset, PageOptions(cursor=page1.next, size=3))
        
        assert len(page2.items) == 2
        assert page2.next is None

    def test_with_filter(self, products):
        """Test pagination with filter."""
        queryset = Product.objects.filter(category='electronics').order_by('id')
        result = paginate(queryset, PageOptions(size=2))
        
        assert len(result.items) == 2
        assert all(p.category == 'electronics' for p in result.items)

    def test_descending_order(self, products):
        """Test descending order."""
        queryset = Product.objects.all().order_by('-id')
        result = paginate(queryset, PageOptions(size=2))
        
        assert result.items[0].id > result.items[1].id
