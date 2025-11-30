"""Django implementation for QueryPager."""

from query_pager.django.filtering import apply_cel_filter
from query_pager.django.ordering import apply_ordering
from query_pager.django.pagination import paginate

__all__ = [
    "apply_cel_filter",
    "apply_ordering",
    "paginate",
]
