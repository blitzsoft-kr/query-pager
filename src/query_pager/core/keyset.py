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

    def decode_cursor_values(self, cursor: Optional[str]) -> Optional[dict]:
        """
        Decode cursor string to values dictionary and validate ordering.

        Args:
            cursor: Cursor string to decode

        Returns:
            Dictionary of field values, or None if cursor is None

        Raises:
            CursorError: If cursor is invalid or ordering doesn't match
        """
        if not cursor:
            return None

        cursor_order_fields, cursor_values = decode_cursor(cursor)

        # Validate ordering matches current query
        validate_cursor_ordering(cursor_order_fields, self.order_fields)

        # Validate field names (for extra safety)
        validate_cursor_fields(cursor_values, self.field_names)

        return cursor_values

    def encode_cursor_values(self, item: Any) -> str:
        """
        Encode item's ordering field values to cursor string with ordering metadata.

        Args:
            item: ORM object to extract values from

        Returns:
            Base64-encoded cursor string with ordering and values
        """
        values = {}
        for field_name in self.field_names:
            values[field_name] = getattr(item, field_name)

        return encode_cursor(self.order_fields, values)

    def build_cursor_filter_conditions(
        self, cursor_values: dict
    ) -> List[Tuple[str, str, Any]]:
        """
        Build filter conditions for cursor-based pagination.
        
        Creates conditions like (field1, field2) > (value1, value2)
        implemented as OR conditions.
        """
        if len(self.order_fields) == 1:
            field_name, direction = self.order_fields[0]
            op = ">" if direction == "asc" else "<"
            value = cursor_values[field_name]
            return [[(field_name, op, value)]]

        return self._build_multi_field_conditions(cursor_values)

    def _build_multi_field_conditions(
        self, cursor_values: dict
    ) -> List[Tuple[str, str, Any]]:
        """Build conditions for multi-field ordering."""
        conditions = []

        for i, (field_name, direction) in enumerate(self.order_fields):
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
    ) -> Paginated:
        """
        Create Paginated response with cursors.

        Args:
            items: List of ORM objects
            total_size: Total number of items in dataset
            requested_size: Requested page size
            has_previous: Whether there's a previous page

        Returns:
            Paginated response with prev/next cursors
        """
        has_next = len(items) > requested_size

        if has_next:
            items = items[:requested_size]
        prev_cursor = None
        next_cursor = None

        if items:
            if has_previous:
                prev_cursor = self.encode_cursor_values(items[0])
            if has_next:
                next_cursor = self.encode_cursor_values(items[-1])

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
