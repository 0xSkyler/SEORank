# Contributing

Use Python 3.12. Create a virtual environment, install `.[dev]`, and run `ruff check src tests`, `mypy src/serp_sentinel/core`, and `pytest -q` before opening a pull request.

Do not commit cookies, browser profiles, proxy lists, diagnostic captures containing personal data, or databases. Tests must remain offline and may not contact Google. New parser fixes should include a minimal sanitized fixture and regression test.
