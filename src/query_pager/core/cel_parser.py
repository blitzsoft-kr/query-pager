"""CEL expression parsing utilities."""

from typing import Set

import celpy
from lark import Token, Tree

from query_pager.core.exceptions import CelParseError, CelValidationError


def parse_cel_expression(expr: str) -> Tree:
    """Parse CEL expression into AST."""
    if not expr or not expr.strip():
        raise CelParseError("CEL expression cannot be empty")

    try:
        env = celpy.Environment()
        ast = env.compile(expr)
        return ast
    except Exception as e:
        raise CelParseError(f"Failed to parse CEL expression: {str(e)}") from e


def extract_field_names(node: Tree | Token) -> Set[str]:
    """Extract all field names from CEL AST."""
    fields = set()

    if isinstance(node, Token):
        if node.type == "IDENT":
            fields.add(node.value)
        return fields

    if isinstance(node, Tree):
        # Skip member_dot_arg to avoid extracting method names
        if node.data == "member_dot_arg":
            # Only extract from the first child (the object)
            if node.children:
                fields.update(extract_field_names(node.children[0]))
            return fields
        
        if node.data == "ident" and node.children:
            if isinstance(node.children[0], Token):
                fields.add(node.children[0].value)

        for child in node.children:
            fields.update(extract_field_names(child))

    return fields


def validate_fields(ast: Tree, allowed_fields: Set[str]) -> None:
    """Validate all fields in expression are allowed."""
    used_fields = extract_field_names(ast)
    invalid_fields = used_fields - allowed_fields

    if invalid_fields:
        raise CelValidationError(
            f"Fields not allowed: {', '.join(sorted(invalid_fields))}. "
            f"Allowed: {', '.join(sorted(allowed_fields))}"
        )
