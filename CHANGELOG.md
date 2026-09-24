# Changelog

## 0.1.0 - 2026-09-24

### Added
* Initial Google query builder, UULE encoder, defensive organic parser, target matching and CLI.
* Read-only Playwright backend using persistent Chrome user-data directories.
* Persistent profile manager with stable generated fingerprint metadata.
* Proxy parser, block/CAPTCHA detection, async keyword checker and SQLite result store.
* Initial PySide6/qasync desktop UI with repeat-search count and non-clicking hover.
* Windows CI, PyInstaller and Inno Setup packaging scaffolding.

### Known limitations
* This first repository build does not yet implement every advanced page/action from the full product specification.
* Full dependency-backed tests must run in Windows CI because the authoring container does not include the declared runtime dependencies.
