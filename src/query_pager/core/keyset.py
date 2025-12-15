"""ORM-agnostic keyset pagination logic."""

from typing import Any, List, Optional, Tuple

from query_pager.core.cursor import (
    decode_cursor,
    encode_cursor,
    validate_cursor_fields,
    validate_cursor_ordering,
)
from query_pager.core.exceptions import PaginationError
from query_pager.core.schemas import PageOptions, Paginated


class KeysetPaginator:
    """Base class for keyset-based pagination."""

    def __init__(self, order_fields: List[Tuple[str, str]]):
        """Initialize paginator with ordering fields."""
        if not order_fields:
            raise PaginationError("At least one ordering field is required")

        self.order_fields = order_fields
        self.field_names = [field for field, _ in order_fields]

    def decode_cursor_values(
        self, cursor: Optional[str]
    ) -> Tuple[Optional[dict], str]:
        """
        Decode cursor string to values dictionary, direction, and validate ordering.

        Args:
            cursor: Cursor string to decode

        Returns:
            Tuple of (cursor_values, direction) where:
            - cursor_values: Dictionary of field values, or None if cursor is None
            - direction: Cursor direction ("next" or "prev"), defaults to "next"

        Raises:
            CursorError: If cursor is invalid or ordering doesn't match
        """
        if not cursor:
            return None, "next"

        cursor_order_fields, cursor_values, direction = decode_cursor(cursor)

        # Validate ordering matches current query
        validate_cursor_ordering(cursor_order_fields, self.order_fields)

        # Validate field names (for extra safety)
        validate_cursor_fields(cursor_values, self.field_names)

        return cursor_values, direction

    def encode_cursor_values(self, item: Any, direction: str = "next") -> str:
        """
        Encode item's ordering field values to cursor string with ordering metadata.

        Args:
            item: ORM object to extract values from
            direction: Cursor direction ("next" or "prev")

        Returns:
            Base64-encoded cursor string with ordering, values, and direction
        """
        values = {}
        for field_name in self.field_names:
            values[field_name] = getattr(item, field_name)

        return encode_cursor(self.order_fields, values, direction)

    def build_cursor_filter_conditions(
        self, cursor_values: dict, is_prev: bool = False
    ) -> List[Tuple[str, str, Any]]:
        """
        Build filter conditions for cursor-based pagination.

        Creates conditions like (field1, field2) > (value1, value2)
        implemented as OR conditions.

        Args:
            cursor_values: Dictionary of field values from cursor
            is_prev: If True, reverse the comparison operators for backward navigation
        """
        if len(self.order_fields) == 1:
            field_name, direction = self.order_fields[0]
            # For "next": asc -> ">", desc -> "<"
            # For "prev": asc -> "<", desc -> ">" (reversed)
            if is_prev:
                op = "<" if direction == "asc" else ">"
            else:
                op = ">" if direction == "asc" else "<"
            value = cursor_values[field_name]
            return [[(field_name, op, value)]]

        return self._build_multi_field_conditions(cursor_values, is_prev)

    def _build_multi_field_conditions(
        self, cursor_values: dict, is_prev: bool = False
    ) -> List[Tuple[str, str, Any]]:
        """Build conditions for multi-field ordering."""
        conditions = []

        for i, (field_name, direction) in enumerate(self.order_fields):
            # For "next": asc -> ">", desc -> "<"
            # For "prev": asc -> "<", desc -> ">" (reversed)
            if is_prev:
                op = "<" if direction == "asc" else ">"
            else:
                op = ">" if direction == "asc" else "<"
            eq_op = "="
            condition = []

            for j in range(i):
                prev_field, _ = self.order_fields[j]
                prev_value = cursor_values[prev_field]
                condition.append((prev_field, eq_op, prev_value))

            current_value = cursor_values[field_name]
            condition.append((field_name, op, current_value))

            conditions.append(condition)

        return conditions

    def create_paginated_response(
        self,
        items: List[Any],
        total_size: int,
        requested_size: int,
        has_previous: bool,
        has_next: bool,
        include_prev_cursor: bool = False,
    ) -> Paginated:
        """
        Create Paginated response with cursors.

        Args:
            items: List of ORM objects (already trimmed to requested_size)
            total_size: Total number of items in dataset
            requested_size: Requested page size
            has_previous: Whether there's a previous page
            has_next: Whether there's a next page
            include_prev_cursor: If True, generate prev cursor even when has_previous is False (for incremental updates)

        Returns:
            Paginated response with prev/next cursors
        """
        prev_cursor = None
        next_cursor = None

        if items:
            # Generate prev cursor if:
            # 1. has_previous is True (normal case), OR
            # 2. include_prev_cursor is True (for incremental updates on first page)
            if has_previous or include_prev_cursor:
                # prev cursor points to first item, direction="prev" for backward nav
                prev_cursor = self.encode_cursor_values(items[0], direction="prev")
            if has_next:
                # next cursor points to last item, direction="next" for forward nav
                next_cursor = self.encode_cursor_values(items[-1], direction="next")

        return Paginated(
            total_size=total_size,
            prev=prev_cursor,
            next=next_cursor,
            items=items,
        )

    def extract_order_fields_from_query(self, query: Any) -> List[Tuple[str, str]]:
        """
        Extract ordering fields from ORM query.

        This method should be overridden by ORM-specific implementations.

        Args:
            query: ORM query object

        Returns:
            List of (field_name, direction) tuples

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclass must implement extract_order_fields_from_query")
