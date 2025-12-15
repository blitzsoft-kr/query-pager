"""Tests for custom exceptions."""

import pytest

from query_pager.core.exceptions import (
    QueryPagerError,
    CelParseError,
    CelValidationError,
    OrderingError,
    CursorError,
    PaginationError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_base_exception(self):
        """Test base exception can be raised."""
        with pytest.raises(QueryPagerError):
            raise QueryPagerError("base error")

    def test_cel_parse_error_inherits_base(self):
        """Test CelParseError inherits from QueryPagerError."""
        assert issubclass(CelParseError, QueryPagerError)
        with pytest.raises(QueryPagerError):
            raise CelParseError("parse error")

    def test_cel_validation_error_inherits_base(self):
        """Test CelValidationError inherits from QueryPagerError."""
        assert issubclass(CelValidationError, QueryPagerError)
        with pytest.raises(QueryPagerError):
            raise CelValidationError("validation error")

    def test_ordering_error_inherits_base(self):
        """Test OrderingError inherits from QueryPagerError."""
        assert issubclass(OrderingError, QueryPagerError)
        with pytest.raises(QueryPagerError):
            raise OrderingError("ordering error")

    def test_cursor_error_inherits_base(self):
        """Test CursorError inherits from QueryPagerError."""
        assert issubclass(CursorError, QueryPagerError)
        with pytest.raises(QueryPagerError):
            raise CursorError("cursor error")

    def test_pagination_error_inherits_base(self):
        """Test PaginationError inherits from QueryPagerError."""
        assert issubclass(PaginationError, QueryPagerError)
        with pytest.raises(QueryPagerError):
            raise PaginationError("pagination error")


class TestExceptionMessages:
    """Test exception messages."""

    def test_cel_parse_error_message(self):
        """Test CelParseError preserves message."""
        msg = "Invalid CEL syntax at position 10"
        exc = CelParseError(msg)
        assert str(exc) == msg

    def test_cel_validation_error_message(self):
        """Test CelValidationError preserves message."""
        msg = "Field 'unknown' is not allowed"
        exc = CelValidationError(msg)
        assert str(exc) == msg

    def test_ordering_error_message(self):
        """Test OrderingError preserves message."""
        msg = "Invalid ordering field: invalid_field"
        exc = OrderingError(msg)
        assert str(exc) == msg

    def test_cursor_error_message(self):
        """Test CursorError preserves message."""
        msg = "Invalid cursor format"
        exc = CursorError(msg)
        assert str(exc) == msg

    def test_pagination_error_message(self):
        """Test PaginationError preserves message."""
        msg = "Page size must be positive"
        exc = PaginationError(msg)
        assert str(exc) == msg


class TestExceptionCatching:
    """Test catching specific exceptions."""

    def test_catch_specific_cel_errors(self):
        """Test catching specific CEL errors."""
        # Should be able to catch CelParseError specifically
        try:
            raise CelParseError("parse error")
        except CelParseError as e:
            assert "parse" in str(e)
        except CelValidationError:
            pytest.fail("Should not catch CelValidationError")

    def test_catch_all_query_pager_errors(self):
        """Test catching all QueryPager errors with base class."""
        errors = [
            CelParseError("parse"),
            CelValidationError("validation"),
            OrderingError("ordering"),
            CursorError("cursor"),
            PaginationError("pagination"),
        ]

        for error in errors:
            try:
                raise error
            except QueryPagerError:
                pass  # Expected
            except Exception:
                pytest.fail(f"{type(error).__name__} should be caught by QueryPagerError")
