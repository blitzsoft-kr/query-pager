# QueryPager

**Cursor-based pagination and CEL filtering for Django and SQLAlchemy**

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/blitzsoft-kr/query-pager)
[![Tests](https://img.shields.io/badge/tests-149%20passing-brightgreen.svg)](https://github.com/blitzsoft-kr/query-pager)

---

## 🎯 Features

- ✅ **Cursor-based Pagination** - Efficient keyset pagination for large datasets with ordering metadata
- ✅ **CEL Filtering** - Dynamic filtering using Common Expression Language
- ✅ **Dynamic Ordering** - Runtime-specified multi-field sorting
- ✅ **Dual ORM Support** - Works with both SQLAlchemy (1.x & 2.x) and Django (4.0+)
- ✅ **Ordering Validation** - Automatic validation prevents cursor reuse across different orderings
- ✅ **Compact Cursor Format** - Space-efficient cursor encoding with ordering metadata

---

## 📦 Installation

```bash
pip install query-pager

# With SQLAlchemy support
pip install query-pager[sqlalchemy]

# With Django support
pip install query-pager[django]
```

---

## 🚀 Quick Start

### SQLAlchemy

```python
from sqlalchemy import select
from query_pager.core import PageOptions
from query_pager.sqlalchemy import apply_cel_filter, apply_ordering, paginate

query = select(Product)

# Apply CEL filter
if filter:
    allowed_fields = {
        "price": Product.price,
        "category": Product.category,
        "name": Product.name,
    }
    query = apply_cel_filter(query, expr=filter, fields=allowed_fields)

# Apply dynamic ordering
if order_by:
    orderable_fields = {
        "likes": Product.likes,
        "created_at": Product.created_at,
        "id": Product.id,
    }
    query = apply_ordering(query, order_by=order_by, fields=orderable_fields)

# Paginate
result = paginate(db, query, PageOptions(size=20))
```

### Django

```python
from django.db.models import Q
from query_pager.core import PageOptions
from query_pager.django import apply_cel_filter, apply_ordering, paginate

queryset = Product.objects.all()

# Apply CEL filter
if filter:
    allowed_fields = {"price", "category", "name"}
    queryset = apply_cel_filter(queryset, expr=filter, fields=allowed_fields)

# Apply dynamic ordering
if order_by:
    orderable_fields = {"likes", "created_at", "id"}
    queryset = apply_ordering(queryset, order_by=order_by, fields=orderable_fields)

# Paginate
result = paginate(queryset, PageOptions(size=20))
```

---

## 🔐 Cursor Format & Security

QueryPager uses a compact, secure cursor format that includes ordering metadata to prevent pagination errors:

```python
# Cursor structure (Base64-encoded JSON)
{
  "o": ["+name", "-id"],  # Ordering: name ASC, id DESC
  "v": {                   # Values at cursor position
    "name": "Product",
    "id": 123
  }
}
```

### Key Features

- **Ordering Validation**: Cursors include ordering metadata and are validated on decode
- **Tamper Detection**: Changing query ordering with an existing cursor raises `CursorError`
- **Compact Format**: Uses single-character keys (`o`, `v`) for minimal overhead
- **Type Safety**: Supports various data types (strings, numbers, dates) via JSON serialization

### Example

```python
from query_pager.core.cursor import decode_cursor

# Cursor: eyJvIjpbIituYW1lIiwiLWlkIl0sInYiOnsibmFtZSI6IlByb2R1Y3QiLCJpZCI6MTIzfX0=
order_fields, values = decode_cursor(cursor)
# order_fields: [("name", "asc"), ("id", "desc")]
# values: {"name": "Product", "id": 123}
```

### Security Considerations

- ✅ Prevents cursor reuse across different query orderings
- ✅ Validates field names match between cursor and query
- ✅ Detects direction changes (ASC ↔ DESC)
- ✅ Catches field order mismatches
- ⚠️ Cursors are not encrypted - avoid sensitive data in ordering fields

---

## 🏗️ Architecture

### Code Structure

```
QueryPager/
├── src/query_pager/
│   ├── core/                    # Shared logic
│   │   ├── cel_parser.py        # CEL parsing
│   │   ├── cel_visitor.py       # Base CEL visitor
│   │   ├── cursor.py            # Cursor encoding/decoding
│   │   ├── keyset.py            # Keyset pagination logic
│   │   ├── ordering.py          # Ordering parser
│   │   ├── exceptions.py        # Custom exceptions
│   │   └── schemas.py           # Pydantic models
│   │
│   ├── sqlalchemy/              # SQLAlchemy implementation
│   │   ├── filtering.py         # CEL → SQLAlchemy
│   │   ├── ordering.py          # Dynamic ordering
│   │   ├── pagination.py        # Pagination wrapper
│   │   └── keyset.py            # SQLAlchemy keyset
│   │
│   └── django/                  # Django implementation
│       ├── filtering.py         # CEL → Django Q
│       ├── ordering.py          # Dynamic ordering
│       ├── pagination.py        # Pagination wrapper
│       └── keyset.py            # Django keyset
│
└── tests/                       # 149 tests (100% passing)
    ├── test_core/               # Core logic tests (59 tests)
    │   ├── test_cursor.py       # Cursor encoding/decoding (22 tests)
    │   ├── test_keyset.py       # Keyset pagination (15 tests)
    │   └── ...                  # CEL, ordering, schemas tests
    ├── test_sqlalchemy/         # SQLAlchemy tests (70 tests)
    │   ├── test_cursor_ordering.py  # Cursor validation (5 tests)
    │   └── ...                  # Pagination, filtering, ordering tests
    └── test_django/             # Django tests (20 tests)
        ├── test_cursor_ordering.py  # Cursor validation (5 tests)
        └── ...                  # Pagination, filtering, ordering tests
```

---

## 🎨 Custom Exceptions

```python
from query_pager.core.exceptions import (
    QueryPagerError,        # Base exception
    CelParseError,          # CEL parsing failed
    CelValidationError,     # Invalid fields in CEL
    OrderingError,          # Invalid ordering spec
    CursorError,            # Cursor encoding/decoding failed
    PaginationError,        # Pagination failed
)

try:
    result = paginate(queryset, options)
except CursorError:
    # Handle invalid cursor
    pass
except OrderingError:
    # Handle invalid ordering
    pass
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/query_pager --cov-report=html

# Run specific module
pytest tests/test_core/
pytest tests/test_sqlalchemy/
```

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- Built with [Pydantic](https://pydantic.dev/) for schemas
- Uses [cel-python](https://github.com/cloud-custodian/cel-python) for CEL parsing
- Inspired by [sqlakeyset](https://github.com/djrobstep/sqlakeyset)
