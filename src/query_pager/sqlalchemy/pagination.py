"""Cursor-based pagination for SQLAlchemy."""

from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from query_pager.core.schemas import PageOptions, Paginated
from query_pager.sqlalchemy.keyset import SQLAlchemyKeysetPaginator

T = TypeVar("T")


def paginate(
    db: Session,
    query: Select,
    options: PageOptions,
) -> Paginated[Any]:
    """
    Paginate a SQLAlchemy query using keyset-based pagination (sync version).

    This function uses efficient cursor-based pagination with keyset method
    and performs a separate count query to get the total size.

    Args:
        db: Synchronous database session
        query: SQLAlchemy Select statement to paginate (must have ORDER BY)
        options: Pagination options (cursor, size)

    Returns:
        Paginated response with total_size, prev/next cursors, and items

    Raises:
        ValueError: If query doesn't have ORDER BY clause

    Example:
        ```python
        from sqlalchemy import select
        from sqlalchemy.orm import Session
        from myapp.models import User
        from query_pager.core import PageOptions
        from query_pager.sqlalchemy import paginate

        query = select(User).where(User.is_active == True).order_by(User.id)
        options = PageOptions(cursor=None, size=10)
        result = paginate(db, query, options)
        ```
    """
    paginator = SQLAlchemyKeysetPaginator(order_fields=[("_dummy", "asc")])
    return paginator.paginate(db, query, options)


async def paginate_async(
    db: AsyncSession,
    query: Select,
    options: PageOptions,
) -> Paginated[Any]:
    """
    Paginate a SQLAlchemy query using keyset-based pagination (async version).

    This function uses efficient cursor-based pagination with keyset method
    and performs a separate count query to get the total size.

    Args:
        db: Async database session
        query: SQLAlchemy Select statement to paginate (must have ORDER BY)
        options: Pagination options (cursor, size)

    Returns:
        Paginated response with total_size, prev/next cursors, and items

    Raises:
        ValueError: If query doesn't have ORDER BY clause

    Example:
        ```python
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession
        from myapp.models import User
        from query_pager.core import PageOptions
        from query_pager.sqlalchemy import paginate_async

        query = select(User).where(User.is_active == True).order_by(User.id)
        options = PageOptions(cursor=None, size=10)
        result = await paginate_async(db, query, options)
        ```
    """
    paginator = SQLAlchemyKeysetPaginator(order_fields=[("_dummy", "asc")])
    return await paginator.paginate_async(db, query, options)
