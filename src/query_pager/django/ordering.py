"""Dynamic ordering for Django."""

from typing import Optional, Set

from django.db.models import QuerySet

from query_pager.core.ordering import parse_ordering


def apply_ordering(
    queryset: QuerySet,
    *,
    order_by: Optional[str],
    fields: Set[str],
) -> QuerySet:
    """
    Apply dynamic ordering to a Django QuerySet.

    Args:
        queryset: Django QuerySet
        order_by: Comma-separated ordering string (e.g., "likes,-created_at,id")
                 None or empty string means no ordering is applied
        fields: Set of allowed field names

    Returns:
        New QuerySet with ordering applied

    Raises:
        ValueError: If any field is not in orderable_fields

    Example:
        ```python
        from myapp.models import Product

        queryset = Product.objects.all()
        orderable = {"likes", "created_at", "id"}

        # Example: likes ascending, id descending
        ordered = apply_ordering(queryset, order_by="likes,-id", fields=orderable)
        ```
    """
    if not order_by or not order_by.strip():
        return queryset

    try:
        ordering_specs = parse_ordering(order_by, fields)

        order_fields = []
        for field_name, direction in ordering_specs:
            if direction == "asc":
                order_fields.append(field_name)
            else:
                order_fields.append(f"-{field_name}")

        return queryset.order_by(*order_fields)

    except Exception as e:
        raise ValueError(f"Failed to apply ordering: {str(e)}") from e
