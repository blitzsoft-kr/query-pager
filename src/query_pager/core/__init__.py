"""Core module for QueryPager - shared schemas, utilities."""

from query_pager.core.cel_visitor import BaseCelVisitor
from query_pager.core.cursor import decode_cursor, encode_cursor
from query_pager.core.exceptions import (
    CelParseError,
    CelValidationError,
    CursorError,
    OrderingError,
    PaginationError,
    QueryPagerError,
)
from query_pager.core.schemas import PageOptions, Paginated

__all__ = [
    # Schemas
    "Paginated",
    "PageOptions",
    # Functions
    "encode_cursor",
    "decode_cursor",
    # Exceptions
    "QueryPagerError",
    "CelParseError",
    "CelValidationError",
    "CursorError",
    "OrderingError",
    "PaginationError",
    # Base classes
    "BaseCelVisitor",
]
