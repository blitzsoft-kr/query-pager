"""Custom exceptions for QueryPager."""


class QueryPagerError(Exception):
    """Base exception for QueryPager."""


class CelParseError(QueryPagerError):
    """Raised when CEL expression parsing fails."""


class CelValidationError(QueryPagerError):
    """Raised when CEL expression validation fails."""


class OrderingError(QueryPagerError):
    """Raised when ordering specification is invalid."""


class CursorError(QueryPagerError):
    """Raised when cursor encoding/decoding fails."""


class PaginationError(QueryPagerError):
    """Raised when pagination fails."""
