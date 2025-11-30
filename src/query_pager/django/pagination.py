"""Cursor-based pagination for Django."""

from typing import Any, TypeVar

from django.db.models import QuerySet

from query_pager.core.schemas import PageOptions, Paginated
from query_pager.django.keyset import DjangoKeysetPaginator

T = TypeVar("T")


def paginate(
    queryset: QuerySet,
    options: PageOptions,
) -> Paginated[Any]:
    """
    Paginate a Django QuerySet using keyset-based pagination.

    This function uses efficient cursor-based pagination with keyset method
    and performs a separate count query to get the total size.

    Args:
        queryset: Django QuerySet to paginate (must have ordering)
        options: Pagination options (cursor, size)

    Returns:
        Paginated response with total_size, prev/next cursors, and items

    Raises:
        ValueError: If queryset doesn't have ordering

    Example:
        ```python
        from myapp.models import User
        from query_pager.core import PageOptions
        from query_pager.django import paginate

        queryset = User.objects.filter(is_active=True).order_by('id')
        options = PageOptions(cursor=None, size=10)
        result = paginate(queryset, options)
        ```
    """
    paginator = DjangoKeysetPaginator(order_fields=[("_dummy", "asc")])
    return paginator.paginate(queryset, options)
