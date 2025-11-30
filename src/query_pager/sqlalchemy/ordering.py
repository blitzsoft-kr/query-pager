"""Dynamic ordering for SQLAlchemy."""

from typing import Dict, Optional

from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql import Select

from query_pager.core.ordering import parse_ordering


def apply_ordering(
    query: Select,
    *,
    order_by: Optional[str],
    fields: Dict[str, InstrumentedAttribute],
) -> Select:
    """
    Apply dynamic ordering to a SQLAlchemy query.

    Args:
        query: SQLAlchemy Select statement
        order_by: Comma-separated ordering string (e.g., "likes,-created_at,id")
                 None or empty string means no ordering is applied
        fields: Dictionary of field names to SQLAlchemy columns

    Returns:
        New Select statement with ordering applied

    Raises:
        ValueError: If any field is not in orderable_fields

    Example:
        ```python
        from sqlalchemy import select
        from myapp.models import Product

        query = select(Product)
        orderable = {
            "likes": Product.likes,
            "created_at": Product.created_at,
            "id": Product.id,
        }

        # Example: likes ascending, id descending
        ordered_query = apply_ordering(query, order_by="likes,-id", fields=orderable)
        ```
    """
    if not order_by or not order_by.strip():
        return query

    try:
        ordering_specs = parse_ordering(order_by, set(fields.keys()))

        order_clauses = []
        for field_name, direction in ordering_specs:
            column = fields[field_name]
            if direction == "asc":
                order_clauses.append(column.asc())
            else:
                order_clauses.append(column.desc())

        return query.order_by(*order_clauses)

    except Exception as e:
        raise ValueError(f"Failed to apply ordering: {str(e)}") from e
