"""Pytest fixtures for SQLAlchemy tests."""

import pytest
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for test models."""

    pass


class Product(Base):
    """Test Product model."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    price = Column(Integer, nullable=False)
    likes = Column(Integer, default=0)


@pytest.fixture
def sync_engine():
    """Create a synchronous in-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def sync_session(sync_engine):
    """Create a synchronous session."""
    SessionLocal = sessionmaker(bind=sync_engine)
    session = SessionLocal()

    # Add test data
    products = [
        Product(id=1, name="Laptop", category="electronics", price=100000, likes=50),
        Product(id=2, name="Phone", category="electronics", price=80000, likes=100),
        Product(id=3, name="Book", category="books", price=20000, likes=30),
        Product(id=4, name="Tablet", category="electronics", price=60000, likes=70),
        Product(id=5, name="Magazine", category="books", price=5000, likes=10),
    ]
    session.add_all(products)
    session.commit()

    yield session
    session.close()


@pytest.fixture
async def async_engine():
    """Create an asynchronous in-memory SQLite engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Create an asynchronous session."""
    AsyncSessionLocal = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    session = AsyncSessionLocal()

    # Add test data
    products = [
        Product(id=1, name="Laptop", category="electronics", price=100000, likes=50),
        Product(id=2, name="Phone", category="electronics", price=80000, likes=100),
        Product(id=3, name="Book", category="books", price=20000, likes=30),
        Product(id=4, name="Tablet", category="electronics", price=60000, likes=70),
        Product(id=5, name="Magazine", category="books", price=5000, likes=10),
    ]
    session.add_all(products)
    await session.commit()

    yield session
    await session.close()
