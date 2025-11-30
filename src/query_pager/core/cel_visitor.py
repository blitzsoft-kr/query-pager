"""Base CEL visitor for converting CEL AST to filter conditions."""

from typing import Any, Dict, List, Set, Tuple

from lark import Token, Tree


class BaseCelVisitor:
    """
    Base visitor class to convert CEL AST to filter conditions.
    
    This provides ORM-agnostic logic for traversing CEL expressions.
    Subclasses implement ORM-specific filter generation.
    """

    def __init__(self, allowed_fields: Set[str]):
        """
        Initialize visitor with allowed fields.

        Args:
            allowed_fields: Set of field names that can be used in filters
        """
        self.allowed_fields = allowed_fields

    def visit(self, node: Tree | Token) -> Any:
        """
        Visit a CEL AST node and convert it to filter expression.

        Args:
            node: Lark Tree or Token node

        Returns:
            ORM-specific filter expression

        Raises:
            ValueError: If operation is not supported
        """
        if isinstance(node, Token):
            return self._visit_token(node)

        if isinstance(node, Tree):
            return self._visit_tree(node)

        raise ValueError(f"Unsupported node type: {type(node)}")

    def _visit_token(self, token: Token) -> Any:
        """
        Process a Token node (literals and identifiers).

        Args:
            token: Lark Token

        Returns:
            Python value (int, float, str, bool, or identifier name)
        """
        if token.type == "INT_LIT":
            return int(token.value)
        elif token.type == "FLOAT_LIT":
            return float(token.value)
        elif token.type == "STRING_LIT":
            # Remove quotes from string literals
            return token.value.strip('"\'')
        elif token.type == "BOOL_LIT":
            return token.value.lower() == "true"
        elif token.type == "IDENT":
            return token.value
        else:
            return token.value

    def _visit_tree(self, tree: Tree) -> Any:
        """
        Process a Tree node based on its data type.

        This method handles the CEL expression structure and delegates
        to subclass methods for ORM-specific operations.

        Args:
            tree: Lark Tree node

        Returns:
            ORM-specific filter expression
        """
        data = tree.data

        # Expression wrapper - unwrap
        if data == "expr":
            return self.visit(tree.children[0])

        # Logical OR
        if data == "conditionalor":
            if len(tree.children) == 1:
                return self.visit(tree.children[0])
            conditions = [self.visit(child) for child in tree.children]
            return self._create_or_condition(conditions)

        # Logical AND
        if data == "conditionaland":
            if len(tree.children) == 1:
                return self.visit(tree.children[0])
            conditions = [self.visit(child) for child in tree.children]
            return self._create_and_condition(conditions)

        # Relation (comparison operations)
        if data == "relation":
            if len(tree.children) == 1:
                return self.visit(tree.children[0])
            elif len(tree.children) == 2:
                op_node = tree.children[0]
                right_node = tree.children[1]
                left, op_type = self._visit_relation_operator(op_node)
                right = self.visit(right_node)
                return self._create_comparison(left, op_type, right)

        # IN operator
        if data == "relation_in":
            left_node = tree.children[0]
            left = self.visit(left_node)
            return left  # Return for parent to handle

        # Addition/Subtraction
        if data == "addition":
            return self.visit(tree.children[0])

        # Multiplication/Division
        if data == "multiplication":
            return self.visit(tree.children[0])

        # Unary operations
        if data == "unary":
            return self.visit(tree.children[0])

        # Member access (field.method())
        if data == "member":
            return self._visit_member(tree)
        
        # Member dot arg (method call)
        if data == "member_dot_arg":
            return self._visit_member_dot_arg(tree)

        # Primary (wraps literals and identifiers)
        if data == "primary":
            return self.visit(tree.children[0])

        # Identifier (field name)
        if data == "ident":
            field_name = tree.children[0].value
            return self._get_field(field_name)

        # Literal value
        if data == "literal":
            return self.visit(tree.children[0])

        # List literal
        if data == "list_lit":
            if tree.children and isinstance(tree.children[0], Tree) and tree.children[0].data == "exprlist":
                exprlist = tree.children[0]
                return [self.visit(expr) for expr in exprlist.children]
            return [self.visit(child) for child in tree.children]

        # Expression list
        if data == "exprlist":
            return [self.visit(child) for child in tree.children]

        # If we reach here, try to visit first child
        if tree.children:
            return self.visit(tree.children[0])

        raise ValueError(f"Unsupported tree data type: {data}")

    def _visit_relation_operator(self, op_node: Tree) -> Tuple[Any, str]:
        """
        Visit a relation operator node and extract left operand and operator type.

        Args:
            op_node: Tree node containing the operator

        Returns:
            Tuple of (left_operand, operator_type)
        """
        data = op_node.data

        if data == "relation_in":
            # IN operator: left in [values]
            left = self.visit(op_node.children[0])
            return left, "in"

        # Standard comparison operators
        left = self.visit(op_node.children[0])

        if data == "relation_eq":
            return left, "=="
        elif data == "relation_ne":
            return left, "!="
        elif data == "relation_lt":
            return left, "<"
        elif data == "relation_le":
            return left, "<="
        elif data == "relation_gt":
            return left, ">"
        elif data == "relation_ge":
            return left, ">="

        raise ValueError(f"Unsupported relation operator: {data}")

    def _visit_member(self, tree: Tree) -> Any:
        """
        Visit a member access node (simple field access).

        Args:
            tree: Tree node for member access

        Returns:
            Field or primary value
        """
        # Just visit the child (could be primary, ident, etc.)
        return self.visit(tree.children[0])

    def _visit_member_dot_arg(self, tree: Tree) -> Any:
        """
        Visit a member_dot_arg node (method call like field.method(args)).

        Args:
            tree: Tree node for method call

        Returns:
            Result of method call
        """
        # First child is the object (member)
        obj = self.visit(tree.children[0])
        
        # Second child is the method name (Token)
        method_name = tree.children[1].value
        
        # Third child (if exists) is exprlist with arguments
        args = []
        if len(tree.children) > 2:
            args_tree = tree.children[2]
            if args_tree.data == "exprlist":
                for arg_expr in args_tree.children:
                    args.append(self.visit(arg_expr))
        
        return self._apply_method(obj, method_name, args)

    # Abstract methods to be implemented by subclasses

    def _create_or_condition(self, conditions: List[Any]) -> Any:
        """Create OR condition (ORM-specific)."""
        raise NotImplementedError("Subclass must implement _create_or_condition")

    def _create_and_condition(self, conditions: List[Any]) -> Any:
        """Create AND condition (ORM-specific)."""
        raise NotImplementedError("Subclass must implement _create_and_condition")

    def _create_comparison(self, left: Any, operator: str, right: Any) -> Any:
        """Create comparison condition (ORM-specific)."""
        raise NotImplementedError("Subclass must implement _create_comparison")

    def _get_field(self, field_name: str) -> Any:
        """Get field object (ORM-specific)."""
        raise NotImplementedError("Subclass must implement _get_field")

    def _apply_method(self, obj: Any, method_name: str, args: List[Any]) -> Any:
        """Apply method to field (ORM-specific)."""
        raise NotImplementedError("Subclass must implement _apply_method")
