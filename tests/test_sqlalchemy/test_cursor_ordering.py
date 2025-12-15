"""Tests for cursor ordering validation in SQLAlchemy pagination."""

import pytest
from sqlalchemy import select

from query_pager.core.exceptions import CursorError
from query_pager.core.schemas import PageOptions
from query_pager.sqlalchemy.pagination import paginate

from .conftest import Product


class TestCursorOrderingValidation:
    """Test class for cursor ordering validation."""

    def test_cursor_with_different_field_raises_error(self, sync_session):
        """Test using cursor from different field ordering raises error."""
        # Get cursor with id ordering
        query_id = select(Product).order_by(Product.id)
        page1 = paginate(sync_session, query_id, PageOptions(size=2))

        # Try to use cursor with price ordering
        query_price = select(Product).order_by(Product.price)
        with pytest.raises(CursorError, match="ordering mismatch"):
            paginate(sync_session, query_price, PageOptions(cursor=page1.next, size=2))

    def test_cursor_with_different_direction_raises_error(self, sync_session):
        """Test using cursor from different direction raises error."""
        # Get cursor with ASC ordering
        query_asc = select(Product).order_by(Product.id)
        page1 = paginate(sync_session, query_asc, PageOptions(size=2))

        # Try to use cursor with DESC ordering
        query_desc = select(Product).order_by(Product.id.desc())
        with pytest.raises(CursorError, match="ordering mismatch"):
            paginate(sync_session, query_desc, PageOptions(cursor=page1.next, size=2))

    def test_cursor_with_different_field_order_raises_error(self, sync_session):
        """Test using cursor from different field order raises error."""
        # Get cursor with (name, id) ordering
        query_name_id = select(Product).order_by(Product.name, Product.id)
        page1 = paginate(sync_session, query_name_id, PageOptions(size=2))

        # Try to use cursor with (id, name) ordering
        query_id_name = select(Product).order_by(Product.id, Product.name)
        with pytest.raises(CursorError, match="ordering mismatch"):
            paginate(sync_session, query_id_name, PageOptions(cursor=page1.next, size=2))

    def test_cursor_with_matching_ordering_succeeds(self, sync_session):
        """Test using cursor with matching ordering succeeds."""
        query = select(Product).order_by(Product.name.desc(), Product.id)

        # First page
        page1 = paginate(sync_session, query, PageOptions(size=2))
        assert page1.next is not None

        # Second page with same ordering
        page2 = paginate(sync_session, query, PageOptions(cursor=page1.next, size=2))
        assert len(page2.items) > 0
        # Should not raise

    def test_multi_field_ordering_validation(self, sync_session):
        """Test multi-field ordering is validated correctly."""
        # Get cursor with 3-field ordering
        query_3fields = select(Product).order_by(
            Product.category, Product.price.desc(), Product.id
        )
        page1 = paginate(sync_session, query_3fields, PageOptions(size=2))

        # Try with 2-field ordering (subset)
        query_2fields = select(Product).order_by(Product.category, Product.price.desc())
        with pytest.raises(CursorError, match="ordering mismatch"):
            paginate(sync_session, query_2fields, PageOptions(cursor=page1.next, size=2))

        # Try with same 3 fields but different direction on middle field
        query_wrong_dir = select(Product).order_by(
            Product.category, Product.price, Product.id  # price ASC instead of DESC
        )
        with pytest.raises(CursorError, match="ordering mismatch"):
            paginate(sync_session, query_wrong_dir, PageOptions(cursor=page1.next, size=2))
