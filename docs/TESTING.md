# Testing Guide

## Fast Paths
- `pytest -q` for the full suite (~20s with stubs)
- `pytest tests/test_search_api.py` to focus on the API surface
- `KM_TEST_USE_REAL_EMBEDDER=1 pytest ...` if you need the real sentence-transformer

## Notes
- CI runs `pytest --cov=gateway --cov-report=term-missing`
- Run `ruff check .` and `black .` prior to committing
