"""
FastAPI example using QueryPager with SQLAlchemy.

This example demonstrates how to use QueryPager in a FastAPI application
with SQLAlchemy for filtering, ordering, and pagination.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from query_pager.core import PageOptions
from query_pager.sqlalchemy import apply_cel_filter, apply_ordering, paginate_async


# Database setup
class Base(DeclarativeBase):
    pass


class Product(Base):
    """Product model."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    price = Column(Integer, nullable=False)
    likes = Column(Integer, default=0)


# Async engine and session
engine = create_async_engine("sqlite+aiosqlite:///./products.db")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        yield session


# Router
router = APIRouter(prefix="/api", tags=["products"])


# Field mappings (defined once, reused everywhere)
PRODUCT_FILTERABLE_FIELDS = {
    "price": Product.price,
    "category": Product.category,
    "name": Product.name,
    "likes": Product.likes,
}

PRODUCT_ORDERABLE_FIELDS = {
    "likes": Product.likes,
    "price": Product.price,
    "category": Product.category,
    "id": Product.id,
}


@router.get("/products")
async def list_products(
    filter: Optional[str] = Query(
        None,
        description="CEL filter expression (e.g., price >= 20000 && category == 'electronics')",
        example="price >= 20000",
    ),
    order_by: Optional[str] = Query(
        None,
        description="Comma-separated ordering fields, prefix - for desc (e.g., likes,-id)",
        example="-likes,id",
    ),
    cursor: Optional[str] = Query(None, description="Page cursor for pagination"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
):
    """
    List products with filtering, ordering, and pagination.

    **Filter Examples:**
    - `price >= 20000`
    - `category == 'electronics'`
    - `category in ['electronics', 'books']`
    - `name.contains('phone')`
    - `price >= 10000 && category == 'electronics'`

    **Ordering Examples:**
    - `likes` (ascending)
    - `-likes` (descending)
    - `category,-price,id` (multiple fields)

    **Pagination:**
    - Use `cursor` from response to get next/prev page
    - Adjust `size` for page size (1-100)
    """
    query = select(Product)

    # Apply filter
    if filter:
        query = apply_cel_filter(query, expr=filter, fields=PRODUCT_FILTERABLE_FIELDS)

    # Apply ordering
    query = apply_ordering(query, order_by or "id", PRODUCT_ORDERABLE_FIELDS)

    # Paginate
    return await paginate_async(db, query, PageOptions(cursor=cursor, size=size))


@router.get("/products/electronics")
async def list_electronics(
    min_price: int = Query(0, description="Minimum price"),
    order_by: Optional[str] = Query("-likes", description="Ordering"),
    cursor: Optional[str] = Query(None),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List electronics products with minimum price.

    This is a simplified endpoint that demonstrates combining
    hardcoded filters with dynamic ordering and pagination.
    """
    query = select(Product)

    # Hardcoded filter for electronics
    allowed_fields = {
        "category": Product.category,
        "price": Product.price,
    }
    filter_expr = f"category == 'electronics' && price >= {min_price}"
    query = apply_cel_filter(query, expr=filter_expr, fields=allowed_fields)

    # Dynamic ordering
    orderable_fields = {
        "likes": Product.likes,
        "price": Product.price,
        "id": Product.id,
    }
    query = apply_ordering(query, order_by, orderable_fields)

    # Paginate
    options = PageOptions(cursor=cursor, size=size)
    return await paginate_async(db, query, options)


# Example usage:
# uvicorn examples.fastapi_example:app --reload
#
# Then visit:
# - http://localhost:8000/api/products
# - http://localhost:8000/api/products?filter=price >= 50000
# - http://localhost:8000/api/products?filter=category == 'electronics'&order_by=-likes
# - http://localhost:8000/api/products/electronics?min_price=30000

if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI(title="QueryPager Example")
    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=8000)
