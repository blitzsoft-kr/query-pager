"""
Advanced FastAPI example with helper class for cleaner code.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from query_pager.core import PageOptions, Paginated
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


engine = create_async_engine("sqlite+aiosqlite:///./products.db")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        yield session


# ============================================================================
# Helper Class for Cleaner Code
# ============================================================================


class QueryBuilder:
    """Helper class to build filtered, ordered, and paginated queries."""

    def __init__(
        self,
        model,
        filterable_fields: dict,
        orderable_fields: dict,
        default_order: str = "id",
    ):
        self.model = model
        self.filterable_fields = filterable_fields
        self.orderable_fields = orderable_fields
        self.default_order = default_order

    async def paginate(
        self,
        db: AsyncSession,
        filter: Optional[str] = None,
        order_by: Optional[str] = None,
        cursor: Optional[str] = None,
        size: int = 20,
    ) -> Paginated:
        """Build and execute paginated query."""
        query = select(self.model)

        if filter:
            query = apply_cel_filter(
                query,
                expr=filter,
                fields=self.filterable_fields,
            )

        query = apply_ordering(
            query, order_by or self.default_order, self.orderable_fields
        )

        return await paginate_async(db, query, PageOptions(cursor=cursor, size=size))


# Product query builder instance
product_query = QueryBuilder(
    model=Product,
    filterable_fields={
        "price": Product.price,
        "category": Product.category,
        "name": Product.name,
        "likes": Product.likes,
    },
    orderable_fields={
        "likes": Product.likes,
        "price": Product.price,
        "category": Product.category,
        "id": Product.id,
    },
    default_order="id",
)


# ============================================================================
# Routes - Now Super Clean!
# ============================================================================

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products")
async def list_products(
    filter: Optional[str] = Query(None, description="CEL filter"),
    order_by: Optional[str] = Query(None, description="Ordering fields"),
    cursor: Optional[str] = Query(None, description="Page cursor"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
):
    """List products with filtering, ordering, and pagination."""
    return await product_query.paginate(db, filter, order_by, cursor, size)


@router.get("/products/electronics")
async def list_electronics(
    min_price: int = Query(0),
    order_by: Optional[str] = Query("-likes"),
    cursor: Optional[str] = Query(None),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List electronics with minimum price."""
    filter_expr = f"category == 'electronics' && price >= {min_price}"
    return await product_query.paginate(db, filter_expr, order_by, cursor, size)


@router.get("/products/search")
async def search_products(
    keyword: str = Query(..., description="Search keyword"),
    order_by: Optional[str] = Query("-likes"),
    cursor: Optional[str] = Query(None),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search products by name."""
    filter_expr = f"name.contains('{keyword}')"
    return await product_query.paginate(db, filter_expr, order_by, cursor, size)


# Example usage:
# uvicorn examples.fastapi_example_advanced:app --reload

if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI(title="QueryPager Advanced Example")
    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=8000)
