# SEORank — Serp Sentinel

Serp Sentinel is a Windows-first, open-source Google rank-tracking application built with Python 3.12, PySide6, qasync, Playwright, selectolax, SQLite, and PyInstaller.

## Safety boundary

The application is intentionally read-only. It loads Google Search result pages, parses organic results, and can optionally hover the matched organic result. It does **not** click organic results, ads, shopping units, or outbound links, and it does not navigate to the target website.

## Current repository status

This branch contains the initial v0.1 implementation:

- CLI keyword check with depth-based Google pagination
- Google query builder with `q`, `hl`, `gl`, `pws=0`, `start`, and optional UULE
- Defensive organic parser with basic SERP-feature detection
- Domain, subdomain, and exact-URL matching helpers
- Persistent Chrome profile directories and stable fingerprint metadata generation
- HTTP/SOCKS proxy parser
- CAPTCHA/block signal detection
- Async keyword checker with a backend interface and offline fake backend
- SQLite result-store foundation
- PySide6/qasync desktop UI with target, keywords, profile count, depth, repeat count, progress, and live results
- Optional non-clicking cursor hover over a matched result
- Windows CI, PyInstaller spec, Inno Setup script, and release workflow

The original product specification is broader than this initial implementation. Advanced profile health/cooldown orchestration, full seven-page GUI management, proxy country testing/alignment, rich history charts, export UI, detailed diagnostics retention, and Windows Task Scheduler integration remain follow-up work.

## Requirements

- Windows 10/11 x64
- Python 3.12 for source installs
- Google Chrome installed
- Roughly 300–500 MB RAM per concurrently open Chrome instance

## Install from source

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
```

Run the GUI:

```powershell
serp-sentinel-gui
```

Run an offline fixture check:

```powershell
serp-sentinel check "blue widgets" --target example.com --depth 30 --fixture tests/fixtures/serp/desktop_basic.html
```

Run a live check:

```powershell
serp-sentinel check "blue widgets" --target example.com --depth 30
```

## Repeat searches

The GUI includes **Number of searches**. If set to `2`, each keyword is checked twice. When a match is found, the live backend may move the cursor over the matching Google organic result. It never clicks the result.

## Profiles

Profiles are stored under:

```text
%APPDATA%\SerpSentinel\profiles\profile_NNN\
  user_data\
  profile.json
```

Chrome is launched with Playwright `launch_persistent_context`, so browser state can persist in the profile directory.

## Proxy input formats

```text
host:port
host:port:user:pass
http://user:pass@host:port
socks5://user:pass@host:port
```

## Search depth

Depth 10/20/30/50/100 uses Google pagination with `start=0,10,20,...`. The implementation does not rely on `num=100`.

## CAPTCHA / blocks

The initial detector recognizes HTTP 429, `/sorry/`, reCAPTCHA markup, and “unusual traffic” text. No CAPTCHA-solving service, stealth plugin, account-login automation, or result-clicking automation is included.

## Development

```powershell
pip install -e ".[dev]"
ruff check src tests
mypy src/serp_sentinel/core
pytest -q
```

Tests are designed to be offline. The CI workflow installs dependencies on `windows-latest`.

## Packaging

```powershell
pip install -e ".[build]"
pyinstaller packaging/serp_sentinel.spec
```

The Inno Setup definition is in `packaging/installer.iss`.

## Responsible use

Automated querying of Google may conflict with Google's Terms of Service. Users are responsible for their own usage. For high-volume or production rank data, an official or licensed SERP data provider is the more appropriate integration path.

## License

MIT.
