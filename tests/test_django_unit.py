"""Simple unit tests for Django modules (no Django ORM needed)."""

import pytest
from query_pager.django.filtering import CelToDjangoVisitor
from query_pager.core.cel_parser import parse_cel_expression


class TestDjangoVisitor:
    """Test Django CEL visitor without Django ORM."""

    def test_get_field(self):
        """Test field name retrieval."""
        visitor = CelToDjangoVisitor({"price", "category"})
        assert visitor._get_field("price") == "price"
        assert visitor._get_field("category") == "category"

    def test_get_field_not_allowed(self):
        """Test disallowed field raises error."""
        visitor = CelToDjangoVisitor({"price"})
        with pytest.raises(ValueError, match="not allowed"):
            visitor._get_field("category")

    def test_create_comparison_equal(self):
        """Test equality comparison."""
        visitor = CelToDjangoVisitor({"price"})
        q = visitor._create_comparison("price", "==", 100)
        assert str(q) == "(AND: ('price__exact', 100))"

    def test_create_comparison_in(self):
        """Test IN operator."""
        visitor = CelToDjangoVisitor({"category"})
        q = visitor._create_comparison("category", "in", ["electronics", "books"])
        assert "price__in" in str(q) or "category__in" in str(q)

    def test_apply_method_contains(self):
        """Test contains method."""
        visitor = CelToDjangoVisitor({"name"})
        q = visitor._apply_method("name", "contains", ["test"])
        assert "icontains" in str(q)

    def test_full_expression(self):
        """Test full CEL expression parsing."""
        visitor = CelToDjangoVisitor({"price", "category"})
        ast = parse_cel_expression("price >= 20000 && category == 'electronics'")
        q = visitor.visit(ast)
        # Just check it doesn't raise
        assert q is not None


class TestDjangoOrdering:
    """Test Django ordering logic."""

    def test_parse_ordering_simple(self):
        """Test simple ordering parsing."""
        from query_pager.core.ordering import parse_ordering
        result = parse_ordering("price", {"price"})
        assert result == [("price", "asc")]

    def test_parse_ordering_desc(self):
        """Test descending ordering."""
        from query_pager.core.ordering import parse_ordering
        result = parse_ordering("-price", {"price"})
        assert result == [("price", "desc")]

    def test_parse_ordering_multiple(self):
        """Test multiple fields."""
        from query_pager.core.ordering import parse_ordering
        result = parse_ordering("category,-price,id", {"category", "price", "id"})
        assert result == [
            ("category", "asc"),
            ("price", "desc"),
            ("id", "asc"),
        ]
