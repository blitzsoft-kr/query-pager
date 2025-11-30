"""Tests for CEL parser."""

import pytest

from query_pager.core.cel_parser import (
    extract_field_names,
    parse_cel_expression,
    validate_fields,
)
from query_pager.core.exceptions import CelParseError, CelValidationError


def test_parse_simple_expression():
    """Test parsing a simple CEL expression."""
    tree = parse_cel_expression("price >= 20000")
    assert tree is not None


def test_parse_complex_expression():
    """Test parsing a complex CEL expression."""
    tree = parse_cel_expression("price >= 20000 && category == 'electronics'")
    assert tree is not None


def test_parse_with_in_operator():
    """Test parsing expression with 'in' operator."""
    tree = parse_cel_expression("category in ['electronics', 'books']")
    assert tree is not None


def test_parse_with_string_methods():
    """Test parsing expression with string methods."""
    tree = parse_cel_expression("name.contains('phone')")
    assert tree is not None


def test_parse_empty_expression():
    """Test parsing empty expression raises error."""
    with pytest.raises(CelParseError, match="cannot be empty"):
        parse_cel_expression("")


def test_parse_invalid_expression():
    """Test parsing invalid expression raises error."""
    with pytest.raises(CelParseError, match="Failed to parse"):
        parse_cel_expression("invalid && &&")


def test_extract_field_names_simple():
    """Test extracting field names from simple expression."""
    tree = parse_cel_expression("price >= 20000")
    fields = extract_field_names(tree)
    assert fields == {"price"}


def test_extract_field_names_multiple():
    """Test extracting multiple field names."""
    tree = parse_cel_expression("price >= 20000 && category == 'electronics'")
    fields = extract_field_names(tree)
    assert fields == {"price", "category"}


def test_extract_field_names_with_method():
    """Test extracting field names with method calls."""
    tree = parse_cel_expression("name.contains('phone')")
    fields = extract_field_names(tree)
    # Note: cel-python includes method names as identifiers
    assert "name" in fields


def test_validate_fields_success():
    """Test field validation with allowed fields."""
    tree = parse_cel_expression("price >= 20000 && category == 'electronics'")
    validate_fields(tree, {"price", "category", "name"})
    # Should not raise


def test_validate_fields_failure():
    """Test field validation with disallowed fields."""
    tree = parse_cel_expression("price >= 20000 && secret == 'value'")

    with pytest.raises(CelValidationError, match="not allowed"):
        validate_fields(tree, {"price", "category"})


def test_validate_fields_partial_match():
    """Test field validation with partial match."""
    tree = parse_cel_expression("price >= 20000 && category == 'electronics'")

    with pytest.raises(CelValidationError, match="category"):
        validate_fields(tree, {"price"})
