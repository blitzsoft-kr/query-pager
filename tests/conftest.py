"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        "items": [
            {"id": 1, "name": "Item 1", "price": 100},
            {"id": 2, "name": "Item 2", "price": 200},
            {"id": 3, "name": "Item 3", "price": 300},
        ]
    }
