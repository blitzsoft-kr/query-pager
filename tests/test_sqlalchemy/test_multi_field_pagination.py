"""Tests for multi-field ordering pagination."""

import pytest
from sqlalchemy import select

from query_pager.core.schemas import PageOptions
from query_pager.sqlalchemy.pagination import paginate

from .conftest import Product


class TestMultiFieldPagination:
    """Test class for multi-field ordering pagination."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, sync_session):
        """Setup and teardown for each test."""
        # Setup: Clear existing data
        sync_session.query(Product).delete()
        sync_session.commit()
        
        self.session = sync_session
        
        yield
        
        # Teardown: Clean up
        sync_session.query(Product).delete()
        sync_session.commit()

    def test_multi_field_ordering_name_id(self):
        """Test pagination with multi-field ordering (name, id)."""
        # Add products with same names
        products = [
            Product(id=1, name="Apple", category="fruit", price=100, likes=10),
            Product(id=2, name="Apple", category="fruit", price=200, likes=20),
            Product(id=3, name="Banana", category="fruit", price=150, likes=15),
            Product(id=4, name="Banana", category="fruit", price=250, likes=25),
            Product(id=5, name="Cherry", category="fruit", price=300, likes=30),
        ]
        self.session.add_all(products)
        self.session.commit()

        # Order by name, then id
        query = select(Product).order_by(Product.name, Product.id)
        
        # First page
        page1 = paginate(self.session, query, PageOptions(size=2))
        assert len(page1.items) == 2
        assert page1.items[0].name == "Apple"
        assert page1.items[0].id == 1
        assert page1.items[1].name == "Apple"
        assert page1.items[1].id == 2
        assert page1.next is not None

        # Second page
        page2 = paginate(self.session, query, PageOptions(cursor=page1.next, size=2))
        assert len(page2.items) == 2
        assert page2.items[0].name == "Banana"
        assert page2.items[0].id == 3
        assert page2.items[1].name == "Banana"
        assert page2.items[1].id == 4

    def test_multi_field_ordering_category_price(self):
        """Test pagination with category and price ordering."""
        # Add test data
        products = [
            Product(id=10, name="A", category="books", price=100, likes=1),
            Product(id=11, name="B", category="books", price=200, likes=2),
            Product(id=12, name="C", category="electronics", price=150, likes=3),
        ]
        self.session.add_all(products)
        self.session.commit()
        
        query = select(Product).order_by(Product.category, Product.price)
        
        page1 = paginate(self.session, query, PageOptions(size=2))
        assert len(page1.items) == 2
        
        # Should be ordered by category first, then price
        if page1.items[0].category == page1.items[1].category:
            assert page1.items[0].price <= page1.items[1].price

    def test_multi_field_desc_ordering(self):
        """Test multi-field with descending order."""
        # Add test data
        products = [
            Product(id=20, name="X", category="A", price=100, likes=1),
            Product(id=21, name="Y", category="B", price=200, likes=2),
        ]
        self.session.add_all(products)
        self.session.commit()
        
        query = select(Product).order_by(Product.category.desc(), Product.price)
        
        page1 = paginate(self.session, query, PageOptions(size=2))
        assert len(page1.items) == 2

    def test_three_field_ordering(self):
        """Test pagination with three fields."""
        # Add test data
        products = [
            Product(id=30, name="P1", category="A", price=300, likes=1),
            Product(id=31, name="P2", category="A", price=200, likes=2),
            Product(id=32, name="P3", category="B", price=100, likes=3),
        ]
        self.session.add_all(products)
        self.session.commit()
        
        query = select(Product).order_by(
            Product.category,
            Product.price.desc(),
            Product.id
        )
        
        page1 = paginate(self.session, query, PageOptions(size=2))
        assert len(page1.items) == 2
        assert page1.next is not None
        
        # Navigate to next page
        page2 = paginate(self.session, query, PageOptions(cursor=page1.next, size=2))
        assert len(page2.items) > 0
