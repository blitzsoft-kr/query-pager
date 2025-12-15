"""SQLAlchemy-specific keyset pagination."""

from typing import Any, List, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from query_pager.core.keyset import KeysetPaginator
from query_pager.core.schemas import PageOptions, Paginated


class SQLAlchemyKeysetPaginator(KeysetPaginator):
    """Keyset paginator for SQLAlchemy queries."""

    def extract_order_fields_from_query(self, query: Select) -> List[Tuple[str, str]]:
        """
        Extract ordering fields from SQLAlchemy query.

        Args:
            query: SQLAlchemy Select statement

        Returns:
            List of (field_name, direction) tuples

        Raises:
            ValueError: If query has no ORDER BY clause
        """
        from sqlalchemy.sql.elements import UnaryExpression
        
        if not query._order_by_clauses:
            raise ValueError("Query must have ORDER BY clause for pagination")

        order_fields = []
        for clause in query._order_by_clauses:
            if isinstance(clause, UnaryExpression):
                field_name = clause.element.key
                direction = "desc" if clause.modifier.__name__ == "desc_op" else "asc"
            else:
                field_name = clause.key
                direction = "asc"

            order_fields.append((field_name, direction))

        return order_fields

    def apply_cursor_filter(
        self, query: Select, cursor_values: dict, is_prev: bool = False
    ) -> Select:
        """
        Apply cursor-based filter to SQLAlchemy query.

        This converts the abstract filter conditions into SQLAlchemy WHERE clauses.
        For example, with order_by=[("id", "asc")] and cursor={"id": 10},
        this adds: WHERE id > 10

        Args:
            query: SQLAlchemy Select statement
            cursor_values: Dictionary of field values from cursor
            is_prev: If True, reverse comparison operators for backward navigation

        Returns:
            Modified query with cursor filter applied
        """
        conditions_groups = self.build_cursor_filter_conditions(cursor_values, is_prev)
        model = self._extract_model_from_query(query)

        or_conditions = []
        for condition_group in conditions_groups:
            and_conditions = []

            for field_name, operator, value in condition_group:
                if model and hasattr(model, field_name):
                    column = getattr(model, field_name)
                else:
                    raise ValueError(f"Field '{field_name}' not found in model")

                if operator == ">":
                    and_conditions.append(column > value)
                elif operator == "<":
                    and_conditions.append(column < value)
                elif operator == "=":
                    and_conditions.append(column == value)

            if and_conditions:
                or_conditions.append(and_(*and_conditions))

        if or_conditions:
            query = query.where(or_(*or_conditions))

        return query

    def reverse_ordering(self, query: Select) -> Select:
        """
        Reverse the ordering of a SQLAlchemy query.

        Args:
            query: SQLAlchemy Select statement with ORDER BY

        Returns:
            Query with reversed ordering
        """
        from sqlalchemy.sql.elements import UnaryExpression

        model = self._extract_model_from_query(query)
        reversed_order = []

        for clause in query._order_by_clauses:
            if isinstance(clause, UnaryExpression):
                field_name = clause.element.key
                is_desc = clause.modifier.__name__ == "desc_op"
            else:
                field_name = clause.key
                is_desc = False

            column = getattr(model, field_name)
            if is_desc:
                reversed_order.append(column.asc())
            else:
                reversed_order.append(column.desc())

        # Remove existing order and apply reversed
        query = query.order_by(None).order_by(*reversed_order)
        return query

    def _extract_model_from_query(self, query: Select) -> Any:
        """
        Extract the model class from a SQLAlchemy query.

        This is needed to access column objects for building WHERE clauses.

        Args:
            query: SQLAlchemy Select statement

        Returns:
            Model class or None
        """
        if hasattr(query, "column_descriptions") and query.column_descriptions:
            return query.column_descriptions[0]["entity"]
        
        if hasattr(query, "_raw_columns") and query._raw_columns:
            first_col = query._raw_columns[0]
            if hasattr(first_col, "entity"):
                return first_col.entity
            elif hasattr(first_col, "table"):
                return first_col.table
        
        return None

    def paginate(
        self,
        db: Session,
        query: Select,
        options: PageOptions,
    ) -> Paginated:
        """
        Paginate a SQLAlchemy query (sync version).

        Args:
            db: Synchronous database session
            query: SQLAlchemy Select statement with ORDER BY
            options: Pagination options (cursor, size)

        Returns:
            Paginated response

        Raises:
            ValueError: If query has no ORDER BY clause
        """
        self.order_fields = self.extract_order_fields_from_query(query)
        self.field_names = [field for field, _ in self.order_fields]

        cursor_values, direction = self.decode_cursor_values(options.cursor)
        is_prev = direction == "prev"

        # Get total count from base query
        base_query = query
        count_query = select(func.count()).select_from(base_query.subquery())
        total_size = db.execute(count_query).scalar_one()

        if cursor_values:
            query = self.apply_cursor_filter(query, cursor_values, is_prev)

        # For backward navigation, reverse the ordering
        if is_prev:
            query = self.reverse_ordering(query)

        fetch_size = options.size + 1
        items_query = query.limit(fetch_size)

        result = db.execute(items_query)
        items = [row[0] for row in result.fetchall()]

        # Check if there are more items
        has_more = len(items) > options.size
        if has_more:
            items = items[:options.size]

        # For backward navigation, reverse items back to original order
        if is_prev:
            items = list(reversed(items))

        # Determine has_previous and has_next based on direction
        if is_prev:
            has_previous = has_more
            has_next = True
        else:
            has_previous = cursor_values is not None
            has_next = has_more

        return self.create_paginated_response(
            items=items,
            total_size=total_size,
            requested_size=options.size,
            has_previous=has_previous,
            has_next=has_next,
            include_prev_cursor=options.include_prev_cursor,
        )

    async def paginate_async(
        self,
        db: AsyncSession,
        query: Select,
        options: PageOptions,
    ) -> Paginated:
        """
        Paginate a SQLAlchemy query (async version).

        Args:
            db: Async database session
            query: SQLAlchemy Select statement with ORDER BY
            options: Pagination options (cursor, size)

        Returns:
            Paginated response

        Raises:
            ValueError: If query has no ORDER BY clause
        """
        self.order_fields = self.extract_order_fields_from_query(query)
        self.field_names = [field for field, _ in self.order_fields]

        cursor_values, direction = self.decode_cursor_values(options.cursor)
        is_prev = direction == "prev"

        # Get total count from base query
        base_query = query
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total_size = total_result.scalar_one()

        if cursor_values:
            query = self.apply_cursor_filter(query, cursor_values, is_prev)

        # For backward navigation, reverse the ordering
        if is_prev:
            query = self.reverse_ordering(query)

        fetch_size = options.size + 1
        items_query = query.limit(fetch_size)

        result = await db.execute(items_query)
        items = [row[0] for row in result.fetchall()]

        # Check if there are more items
        has_more = len(items) > options.size
        if has_more:
            items = items[:options.size]

        # For backward navigation, reverse items back to original order
        if is_prev:
            items = list(reversed(items))

        # Determine has_previous and has_next based on direction
        if is_prev:
            has_previous = has_more
            has_next = True
        else:
            has_previous = cursor_values is not None
            has_next = has_more

        return self.create_paginated_response(
            items=items,
            total_size=total_size,
            requested_size=options.size,
            has_previous=has_previous,
            has_next=has_next,
            include_prev_cursor=options.include_prev_cursor,
        )
