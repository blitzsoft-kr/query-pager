"""Django test configuration - simple version."""

import os
import sys
import django
from pathlib import Path

# Add tests directory to path
tests_dir = Path(__file__).parent.parent
sys.path.insert(0, str(tests_dir))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_settings')
django.setup()

import pytest
from tests.django_app.models import Product


@pytest.fixture
def products(db):
    """Create test products - db fixture enables Django ORM."""
    Product.objects.all().delete()
    
    products = [
        Product(id=1, name="Laptop", category="electronics", price=100000, likes=50),
        Product(id=2, name="Phone", category="electronics", price=80000, likes=100),
        Product(id=3, name="Book", category="books", price=20000, likes=30),
        Product(id=4, name="Tablet", category="electronics", price=60000, likes=70),
        Product(id=5, name="Magazine", category="books", price=5000, likes=10),
    ]
    Product.objects.bulk_create(products)
    
    return products
