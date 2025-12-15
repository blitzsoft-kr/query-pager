# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-15

### Added
- **Cursor Ordering Metadata**: Cursors now include ordering information to prevent incorrect pagination when ordering changes
  - New compact cursor format: `{"o": ["+field1", "-field2"], "v": {"field1": value1, "field2": value2}}`
  - Automatic validation that cursor ordering matches current query ordering
  - Prevents silent pagination errors when switching between different orderings
- Comprehensive cursor ordering validation tests for both SQLAlchemy and Django
- `validate_cursor_ordering()` function in `core.cursor` module

### Fixed
- **Django total_size bug**: Fixed incorrect `total_size` calculation that returned total model count instead of filtered queryset count
  - Before: `queryset.model.objects.count()` (always returned all records)
  - After: `queryset.count()` (returns filtered count)
- Edge case handling for cursor field mismatches

### Changed
- **Breaking Change**: `encode_cursor()` signature changed from `encode_cursor(values)` to `encode_cursor(order_fields, values)`
- **Breaking Change**: `decode_cursor()` now returns `(order_fields, values)` tuple instead of just `values`
- Cursor format is more compact using single-character keys (`"o"` and `"v"`)
- Improved error messages for cursor validation failures

### Security
- Added ordering validation to prevent cursor reuse across different query orderings
- Enhanced cursor validation to catch field name, direction, and order mismatches

### Testing
- Added 149 comprehensive tests (100% passing)
- New test suites:
  - `tests/test_core/test_cursor.py`: 22 tests for cursor encoding/decoding
  - `tests/test_core/test_keyset.py`: 15 tests including ordering validation
  - `tests/test_sqlalchemy/test_cursor_ordering.py`: 5 tests for SQLAlchemy cursor validation
  - `tests/test_django/test_cursor_ordering.py`: 5 tests for Django cursor validation
- All existing tests updated to work with new cursor format

## [0.1.0] - Initial Release

### Added
- Cursor-based pagination using keyset method
- CEL (Common Expression Language) filtering support
- Dynamic multi-field ordering
- Dual ORM support (SQLAlchemy 1.x/2.x and Django 4.0+)
- Async support for SQLAlchemy
- Base64-encoded cursors for pagination state
- Custom exception hierarchy
- Pydantic schemas for type safety
