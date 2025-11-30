"""CEL filtering for SQLAlchemy."""

from typing import Any, Dict, List

from sqlalchemy import and_, or_
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql import Select

from query_pager.core.cel_parser import parse_cel_expression, validate_fields
from query_pager.core.cel_visitor import BaseCelVisitor


class CelToSqlAlchemyVisitor(BaseCelVisitor):
    """
    Visitor class to convert CEL AST to SQLAlchemy filter conditions.
    
    Extends BaseCelVisitor with SQLAlchemy-specific implementations.
    """

    def __init__(self, allowed_fields: Dict[str, InstrumentedAttribute]):
        """
        Initialize the visitor with allowed fields.

        Args:
            allowed_fields: Dictionary mapping field names to SQLAlchemy column attributes
        """
        super().__init__(set(allowed_fields.keys()))
        self.field_columns = allowed_fields

    def _create_or_condition(self, conditions: List[Any]) -> Any:
        """Create SQLAlchemy OR condition."""
        return or_(*conditions)

    def _create_and_condition(self, conditions: List[Any]) -> Any:
        """Create SQLAlchemy AND condition."""
        return and_(*conditions)

    def _create_comparison(self, left: Any, operator: str, right: Any) -> Any:
        """Create SQLAlchemy comparison condition."""
        if operator == "==":
            return left == right
        elif operator == "!=":
            return left != right
        elif operator == "<":
            return left < right
        elif operator == "<=":
            return left <= right
        elif operator == ">":
            return left > right
        elif operator == ">=":
            return left >= right
        elif operator == "in":
            return left.in_(right)
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    def _get_field(self, field_name: str) -> Any:
        """Get SQLAlchemy column object."""
        if field_name not in self.field_columns:
            raise ValueError(f"Field '{field_name}' is not allowed in filters")
        return self.field_columns[field_name]

    def _apply_method(self, obj: Any, method_name: str, args: List[Any]) -> Any:
        """Apply string method to SQLAlchemy column."""
        if method_name == "contains":
            if len(args) != 1:
                raise ValueError("contains() requires exactly 1 argument")
            return obj.contains(args[0])
        elif method_name == "startsWith":
            if len(args) != 1:
                raise ValueError("startsWith() requires exactly 1 argument")
            return obj.startswith(args[0])
        elif method_name == "endsWith":
            if len(args) != 1:
                raise ValueError("endsWith() requires exactly 1 argument")
            return obj.endswith(args[0])
        else:
            raise ValueError(f"Unsupported method: {method_name}")


def apply_cel_filter(
    query: Select,
    expr: str | None = None,
    *,
    fields: Dict[str, InstrumentedAttribute],
) -> Select:
    """
    Apply CEL filter expression to SQLAlchemy query.

    Args:
        query: SQLAlchemy Select statement
        expr: CEL filter expression string
        fields: Dictionary of field names to SQLAlchemy columns

    Returns:
        Modified query with filter applied

    Raises:
        ValueError: If expression is invalid or uses disallowed fields

    Example:
        ```python
        from sqlalchemy import select
        from myapp.models import Product

        query = select(Product)
        allowed = {
            "price": Product.price,
            "category": Product.category,
        }

        filtered_query = apply_cel_filter(
            query,
            expr="price >= 20000 && category in ['electronics', 'books']",
            fields=allowed
        )
    ```
    """
    if not expr or not expr.strip():
        return query

    try:
        ast = parse_cel_expression(expr)
        validate_fields(ast, set(fields.keys()))

        visitor = CelToSqlAlchemyVisitor(fields)
        filter_condition = visitor.visit(ast)

        return query.where(filter_condition)

    except Exception as e:
        raise ValueError(f"Failed to apply CEL filter: {str(e)}") from e
