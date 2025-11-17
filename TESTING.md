# Testing Guide for Medallion Phase 4

This guide provides steps for running tests for Phase 4 implementation (User Story 1 - Checkpoint Creation).

## Prerequisites

1. **Install dependencies** (if not already installed):
   ```bash
   uv sync --dev
   ```
   Or manually install dev dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

2. **Verify installation**:
   ```bash
   uv run pytest --version
   ```

## Running Tests

### 1. Run All Tests

Run all tests with coverage:
```bash
uv run pytest
```

This will:
- Run all tests in `tests/` directory
- Generate coverage reports (terminal, HTML, XML)
- Fail if coverage is below 90%

### 2. Run Specific Test Modules

Run tests for a specific module:

**Types tests:**
```bash
uv run pytest tests/unit/test_types.py
```

**Store Protocol tests:**
```bash
uv run pytest tests/unit/test_store.py
```

**SQLite Store tests:**
```bash
uv run pytest tests/unit/test_sqlite_store.py
```

**LLM tests:**
```bash
uv run pytest tests/unit/test_llm.py
```

**Session helper tests:**
```bash
uv run pytest tests/unit/test_session.py
```

**Integration tests:**
```bash
uv run pytest tests/integration/test_store_integration.py
```

**Contract tests:**
```bash
uv run pytest tests/contract/test_schema_contract.py
```

### 3. Run Tests by Category

Run only unit tests:
```bash
uv run pytest tests/unit/
```

Run only integration tests:
```bash
uv run pytest tests/integration/
```

Run only contract tests:
```bash
uv run pytest tests/contract/
```

### 4. Run Specific Test Classes or Functions

Run a specific test class:
```bash
uv run pytest tests/unit/test_sqlite_store.py::TestSQLiteMedallionStoreCreate
```

Run a specific test function:
```bash
uv run pytest tests/unit/test_sqlite_store.py::TestSQLiteMedallionStoreCreate::test_create_persists_medallion
```

### 5. Verbose Output

Get detailed output:
```bash
uv run pytest -v
```

Get even more verbose output:
```bash
uv run pytest -vv
```

Show print statements:
```bash
uv run pytest -s
```

### 6. Run Tests with Debugging

Drop into debugger on failures:
```bash
uv run pytest --pdb
```

Drop into debugger on first failure:
```bash
uv run pytest -x --pdb
```

### 7. Stop on First Failure

Stop after first test failure:
```bash
uv run pytest -x
```

Stop after N test failures:
```bash
uv run pytest --maxfail=3
```

## Coverage Reports

### View Terminal Coverage Report

Coverage is automatically shown when running tests:
```bash
uv run pytest
```

### View HTML Coverage Report

After running tests, open the HTML coverage report:
```bash
# On macOS
open htmlcov/index.html

# On Linux
xdg-open htmlcov/index.html

# On Windows
start htmlcov/index.html
```

### Check Coverage Only

Run tests and only show coverage (no test output):
```bash
uv run pytest --cov=medallion --cov-report=term-missing --quiet
```

### Check Coverage for Specific Module

Check coverage for a specific module:
```bash
uv run pytest --cov=medallion.sqlite_store --cov-report=term-missing tests/unit/test_sqlite_store.py
```

## Phase 4 Test Checklist

Run these tests to verify Phase 4 implementation:

### 1. Types Module (Phase 1-2)
```bash
uv run pytest tests/unit/test_types.py -v
uv run pytest tests/contract/test_schema_contract.py -v
```

### 2. Store Protocol (Phase 3)
```bash
uv run pytest tests/unit/test_store.py -v
```

### 3. SQLite Store (Phase 4)
```bash
uv run pytest tests/unit/test_sqlite_store.py -v
uv run pytest tests/integration/test_store_integration.py::test_create_and_get_round_trip -v
```

### 4. LLM Module (Phase 4)
```bash
uv run pytest tests/unit/test_llm.py -v
```

### 5. Session Helpers (Phase 4)
```bash
uv run pytest tests/unit/test_session.py -v
uv run pytest tests/integration/test_store_integration.py::test_checkpoint_session_end_to_end -v
```

### 6. Full Integration Test
```bash
uv run pytest tests/integration/test_store_integration.py -v
```

## Expected Results

### Successful Test Run

All tests should pass:
```
========================= test session starts =========================
platform darwin -- Python 3.14.0, pytest-9.0.1, pluggy-1.6.0
collected XX items

tests/unit/test_types.py ........                            [XX%]
tests/unit/test_store.py ..................                  [XX%]
tests/unit/test_sqlite_store.py ..........                   [XX%]
tests/unit/test_llm.py ..........                            [XX%]
tests/unit/test_session.py ...........                       [XX%]
tests/integration/test_store_integration.py ...              [XX%]
tests/contract/test_schema_contract.py ...                   [XX%]

========================= XX passed in X.XXs =========================

---------- coverage: platform darwin -----------
Name                              Stmts   Miss Branch BrPart     Cover
---------------------------------------------------------------------
medallion/__init__.py                 1      0      0      0   100%
medallion/store.py                   11      0      0      0   100%
medallion/types.py                   76      0      0      0   100%
medallion/sqlite_store.py            XXX      0      0      0   100%
medallion/llm.py                     XXX      0      0      0   100%
medallion/session.py                 XXX      0      0      0   100%
---------------------------------------------------------------------
TOTAL                                XXX      0      0      0   100%

Coverage HTML written to dir htmlcov
```

### Coverage Requirement

Coverage must be ≥90% for:
- `medallion/store.py` (Protocol)
- `medallion/sqlite_store.py` (Implementation)
- `medallion/session.py` (Session helpers)
- `medallion/llm.py` (LLM helpers)
- `medallion/types.py` (Data models)

## Troubleshooting

### Issue: Tests fail with "ModuleNotFoundError"

**Solution:** Ensure dependencies are installed:
```bash
uv sync --dev
```

### Issue: Coverage below 90%

**Solution:** Check which lines are missing coverage:
```bash
uv run pytest --cov=medallion --cov-report=term-missing
```

Then review the HTML report:
```bash
open htmlcov/index.html
```

### Issue: Async test warnings

**Solution:** Ensure `pytest-asyncio` is installed and `asyncio_mode = "auto"` is set in `pyproject.toml` (already configured).

### Issue: Tests hang or timeout

**Solution:** Check for unclosed database connections or event loops. Use `-v` flag to see which test is hanging:
```bash
uv run pytest -v --tb=short
```

## Continuous Integration

For CI/CD pipelines, use:
```bash
uv run pytest --cov=medallion --cov-report=xml --cov-report=term
```

This generates:
- Terminal coverage report
- XML coverage report (for CI integration)
- HTML coverage report (for local viewing)

## Quick Test Commands

```bash
# Run all tests once
uv run pytest

# Run all tests with verbose output
uv run pytest -v

# Run all tests and show coverage
uv run pytest --cov=medallion --cov-report=term-missing

# Run Phase 4 tests only
uv run pytest tests/unit/test_sqlite_store.py tests/unit/test_llm.py tests/unit/test_session.py tests/integration/test_store_integration.py -v

# Run a single test
uv run pytest tests/integration/test_store_integration.py::test_checkpoint_session_end_to_end -v

# Run tests with debugging
uv run pytest -vv -s --pdb

# Run tests and stop on first failure
uv run pytest -x
```

