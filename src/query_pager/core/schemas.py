"""Core schemas for pagination."""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    """
    Generic pagination response schema.

    Attributes:
        total_size: Total number of items in the dataset
        prev: Cursor for the previous page (None if first page)
        next: Cursor for the next page (None if last page)
        items: List of items for the current page
    """

    total_size: int = Field(..., description="Total number of items in the dataset")
    prev: Optional[str] = Field(None, description="Previous page cursor")
    next: Optional[str] = Field(None, description="Next page cursor")
    items: list[T] = Field(..., description="Items in current page")

    model_config = {"from_attributes": True}


class PageOptions(BaseModel):
    """
    Pagination options.

    Attributes:
        cursor: Page cursor (bookmark) for the current position
        size: Number of items per page (1-100)
        include_prev_cursor: If True, generate prev cursor even on first page (useful for incremental updates)
    """

    cursor: Optional[str] = Field(None, description="Page cursor")
    size: int = Field(20, ge=1, le=100, description="Page size")
    include_prev_cursor: bool = Field(
        False, description="Generate prev cursor on first page for incremental updates"
    )

    model_config = {"frozen": True}
