"""CEL filtering for Django."""

from typing import Any, List, Set

from django.db.models import Q, QuerySet

from query_pager.core.cel_parser import parse_cel_expression, validate_fields
from query_pager.core.cel_visitor import BaseCelVisitor


class CelToDjangoVisitor(BaseCelVisitor):
    """
    Visitor class to convert CEL AST to Django Q objects.
    
    Extends BaseCelVisitor with Django-specific implementations.
    """

    def __init__(self, allowed_fields: Set[str]):
        """
        Initialize the visitor with allowed fields.

        Args:
            allowed_fields: Set of field names that can be used in filters
        """
        super().__init__(allowed_fields)

    def _create_or_condition(self, conditions: List[Any]) -> Q:
        """Create Django OR condition."""
        result = Q()
        for cond in conditions:
            result |= cond
        return result

    def _create_and_condition(self, conditions: List[Any]) -> Q:
        """Create Django AND condition."""
        result = Q()
        for cond in conditions:
            result &= cond
        return result

    def _create_comparison(self, left: str, operator: str, right: Any) -> Q:
        """Create Django comparison condition."""
        if operator == "==":
            return Q(**{f"{left}__exact": right})
        elif operator == "!=":
            return ~Q(**{f"{left}__exact": right})
        elif operator == "<":
            return Q(**{f"{left}__lt": right})
        elif operator == "<=":
            return Q(**{f"{left}__lte": right})
        elif operator == ">":
            return Q(**{f"{left}__gt": right})
        elif operator == ">=":
            return Q(**{f"{left}__gte": right})
        elif operator == "in":
            return Q(**{f"{left}__in": right})
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    def _get_field(self, field_name: str) -> str:
        """Get field name (Django uses strings)."""
        if field_name not in self.allowed_fields:
            raise ValueError(f"Field '{field_name}' is not allowed in filters")
        return field_name

    def _apply_method(self, obj: str, method_name: str, args: List[Any]) -> Q:
        """Apply string method to Django field."""
        if method_name == "contains":
            if len(args) != 1:
                raise ValueError("contains() requires exactly 1 argument")
            return Q(**{f"{obj}__icontains": args[0]})
        elif method_name == "startsWith":
            if len(args) != 1:
                raise ValueError("startsWith() requires exactly 1 argument")
            return Q(**{f"{obj}__istartswith": args[0]})
        elif method_name == "endsWith":
            if len(args) != 1:
                raise ValueError("endsWith() requires exactly 1 argument")
            return Q(**{f"{obj}__iendswith": args[0]})
        else:
            raise ValueError(f"Unsupported method: {method_name}")


def apply_cel_filter(
    queryset: QuerySet,
    expr: str | None = None,
    *,
    fields: Set[str],
) -> QuerySet:
    """
    Apply CEL filter expression to Django QuerySet.

    Args:
        queryset: Django QuerySet
        expr: CEL filter expression string
        fields: Set of allowed field names

    Returns:
        Modified queryset with filter applied

    Raises:
        ValueError: If expression is invalid or uses disallowed fields

    Example:
        ```python
        from myapp.models import Product

        queryset = Product.objects.all()
        allowed = {"price", "category", "name"}

        filtered = apply_cel_filter(
            queryset,
            expr="price >= 20000 && category in ['electronics', 'books']",
            fields=allowed
        )
    ```
    """
    if not expr or not expr.strip():
        return queryset

    try:
        ast = parse_cel_expression(expr)
        validate_fields(ast, fields)

        visitor = CelToDjangoVisitor(fields)
        filter_condition = visitor.visit(ast)

        return queryset.filter(filter_condition)

    except Exception as e:
        raise ValueError(f"Failed to apply CEL filter: {str(e)}") from e
