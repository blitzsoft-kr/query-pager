"""Ordering string parsing utilities."""

from typing import List, Literal, Set, Tuple

from query_pager.core.exceptions import OrderingError

OrderDirection = Literal["asc", "desc"]


def parse_ordering(
    order_by: str,
    allowed_fields: Set[str],
) -> List[Tuple[str, OrderDirection]]:
    """
    Parse ordering string into (field_name, direction) tuples.
    
    Format: "field1,-field2,field3" where - prefix means descending.
    """
    if not order_by or not order_by.strip():
        raise OrderingError("Ordering string cannot be empty")

    result: List[Tuple[str, OrderDirection]] = []
    parts = [p.strip() for p in order_by.split(",") if p.strip()]

    if not parts:
        raise OrderingError("Ordering string must contain at least one field")

    for part in parts:
        if part.startswith("-"):
            field_name = part[1:]
            direction: OrderDirection = "desc"
        else:
            field_name = part
            direction = "asc"

        if not field_name:
            raise OrderingError(f"Invalid ordering field: '{part}'")

        if field_name not in allowed_fields:
            raise OrderingError(
                f"Field '{field_name}' not allowed. "
                f"Allowed: {', '.join(sorted(allowed_fields))}"
            )

        result.append((field_name, direction))

    return result


def validate_ordering_fields(order_by: str, allowed_fields: Set[str]) -> None:
    """Validate ordering string fields are allowed."""
    parse_ordering(order_by, allowed_fields)
