"""Django-specific keyset pagination."""

from typing import Any, List, Tuple

from django.db.models import Q, QuerySet

from query_pager.core.keyset import KeysetPaginator
from query_pager.core.schemas import PageOptions, Paginated


class DjangoKeysetPaginator(KeysetPaginator):
    """Keyset paginator for Django QuerySets."""

    def extract_order_fields_from_query(self, queryset: QuerySet) -> List[Tuple[str, str]]:
        """
        Extract ordering fields from Django QuerySet.

        Args:
            queryset: Django QuerySet

        Returns:
            List of (field_name, direction) tuples

        Raises:
            ValueError: If queryset has no ordering
        """
        ordering = queryset.query.order_by
        
        if not ordering:
            raise ValueError("QuerySet must have ordering for pagination")

        order_fields = []
        for field_name in ordering:
            if field_name.startswith('-'):
                order_fields.append((field_name[1:], 'desc'))
            else:
                order_fields.append((field_name, 'asc'))

        return order_fields

    def apply_cursor_filter(
        self, queryset: QuerySet, cursor_values: dict, is_prev: bool = False
    ) -> QuerySet:
        """
        Apply cursor-based filter to Django QuerySet.

        Args:
            queryset: Django QuerySet
            cursor_values: Dictionary of field values from cursor
            is_prev: If True, reverse comparison operators for backward navigation

        Returns:
            Modified queryset with cursor filter applied
        """
        conditions_groups = self.build_cursor_filter_conditions(cursor_values, is_prev)

        or_conditions = Q()

        for condition_group in conditions_groups:
            and_conditions = Q()

            for field_name, operator, value in condition_group:
                if operator == '>':
                    lookup = f'{field_name}__gt'
                elif operator == '<':
                    lookup = f'{field_name}__lt'
                elif operator == '=':
                    lookup = f'{field_name}__exact'
                else:
                    raise ValueError(f"Unsupported operator: {operator}")

                and_conditions &= Q(**{lookup: value})

            or_conditions |= and_conditions

        return queryset.filter(or_conditions)

    def reverse_ordering(self, queryset: QuerySet) -> QuerySet:
        """
        Reverse the ordering of a QuerySet.

        Args:
            queryset: Django QuerySet with ordering

        Returns:
            QuerySet with reversed ordering
        """
        current_ordering = list(queryset.query.order_by)
        reversed_ordering = []
        for field in current_ordering:
            if field.startswith('-'):
                reversed_ordering.append(field[1:])
            else:
                reversed_ordering.append(f'-{field}')
        return queryset.order_by(*reversed_ordering)

    def paginate(
        self,
        queryset: QuerySet,
        options: PageOptions,
    ) -> Paginated:
        """
        Paginate a Django QuerySet.

        Args:
            queryset: Django QuerySet with ordering
            options: Pagination options (cursor, size)

        Returns:
            Paginated response

        Raises:
            ValueError: If queryset has no ordering
        """
        self.order_fields = self.extract_order_fields_from_query(queryset)
        self.field_names = [field for field, _ in self.order_fields]

        cursor_values, direction = self.decode_cursor_values(options.cursor)
        is_prev = direction == "prev"

        # Get total count before filtering
        base_queryset = queryset
        total_size = base_queryset.count()

        if cursor_values:
            queryset = self.apply_cursor_filter(queryset, cursor_values, is_prev)

        # For backward navigation, reverse the ordering to fetch items before cursor
        if is_prev:
            queryset = self.reverse_ordering(queryset)

        fetch_size = options.size + 1
        items = list(queryset[:fetch_size])

        # Check if there are more items
        has_more = len(items) > options.size
        if has_more:
            items = items[:options.size]

        # For backward navigation, reverse items back to original order
        if is_prev:
            items = list(reversed(items))

        # Determine has_previous and has_next based on direction
        if is_prev:
            # Going backward: has_more means there are more items before
            # has_next is True because we came from a next page
            has_previous = has_more
            has_next = True
        else:
            # Going forward: has_more means there are more items after
            # has_previous is True if we used a cursor (came from somewhere)
            has_previous = cursor_values is not None
            has_next = has_more

        return self.create_paginated_response(
            items=items,
            total_size=total_size,
            requested_size=options.size,
            has_previous=has_previous,
            has_next=has_next,
            include_prev_cursor=options.include_prev_cursor,
        )
