# Architecture

```text
PySide6/qasync UI -> Scheduler -> SearchBackend
                         |-> PlaywrightBackend -> Google Search only
                         |-> FakeBackend -> offline fixtures
                         -> Parser -> Matcher -> SQLite

ProfileManager -> persistent Chrome user-data dirs + stable fingerprint metadata
```

## One keyword check
1. Select a persistent profile.
2. Build a Google Search URL using q/hl/gl/pws/start and optional UULE.
3. Load only the Google URL. The backend never clicks an organic result or navigates to the target.
4. Detect CAPTCHA/block signals.
5. Parse organic results.
6. Match normalized URLs against the configured target.
7. Return the result to CLI/UI and persist as applicable.

Logged-out stable profiles are the default to reduce account personalization.
