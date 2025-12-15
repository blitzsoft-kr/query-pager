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

    def apply_cursor_filter(self, queryset: QuerySet, cursor_values: dict) -> QuerySet:
        """
        Apply cursor-based filter to Django QuerySet.

        Args:
            queryset: Django QuerySet
            cursor_values: Dictionary of field values from cursor

        Returns:
            Modified queryset with cursor filter applied
        """
        conditions_groups = self.build_cursor_filter_conditions(cursor_values)

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

        cursor_values = self.decode_cursor_values(options.cursor)

        if cursor_values:
            queryset = self.apply_cursor_filter(queryset, cursor_values)

        fetch_size = options.size + 1
        items = list(queryset[:fetch_size])

        total_size = queryset.count()
        has_previous = cursor_values is not None
        return self.create_paginated_response(
            items=items,
            total_size=total_size,
            requested_size=options.size,
            has_previous=has_previous,
        )
