from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast


@dataclass(slots=True)
class PageData:
    url: str
    html: str
    status: int = 200
    screenshot: Path | None = None


class SearchBackend(Protocol):
    async def fetch(
        self,
        url: str,
        profile_dir: Path,
        proxy: dict[str, str] | None = None,
        hover_target: str | None = None,
    ) -> PageData: ...

    async def close_all(self) -> None: ...


class FakeBackend:
    def __init__(self, html: str):
        self.html = html

    async def fetch(
        self,
        url: str,
        profile_dir: Path,
        proxy: dict[str, str] | None = None,
        hover_target: str | None = None,
    ) -> PageData:
        return PageData(url, self.html, 200)

    async def close_all(self) -> None:
        return None


class PlaywrightBackend:
    """Reuse one persistent Chrome context and page per profile.

    The backend only navigates to Google Search pages. It never clicks search
    results or visits target websites. Visible mode supports user-driven CAPTCHA
    solving without automating or bypassing the challenge.
    """

    def __init__(self, *, headless: bool = True):
        self.headless = headless
        self._playwright: Any | None = None
        self._contexts: dict[str, Any] = {}
        self._pages: dict[str, Any] = {}

    @staticmethod
    def _profile_key(profile_dir: Path) -> str:
        return str(profile_dir.resolve())

    async def _ensure_started(self) -> Any:
        if self._playwright is None:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
        return self._playwright

    async def _get_page(
        self,
        profile_dir: Path,
        proxy: dict[str, str] | None,
    ) -> Any:
        key = self._profile_key(profile_dir)
        page = self._pages.get(key)
        if page is not None and not page.is_closed():
            return page

        playwright = await self._ensure_started()
        context = await playwright.chromium.launch_persistent_context(
            str(profile_dir / "user_data"),
            channel="chrome",
            headless=self.headless,
            proxy=cast(Any, proxy),
        )
        page = context.pages[0] if context.pages else await context.new_page()
        self._contexts[key] = context
        self._pages[key] = page
        return page

    async def fetch(
        self,
        url: str,
        profile_dir: Path,
        proxy: dict[str, str] | None = None,
        hover_target: str | None = None,
    ) -> PageData:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        if not url.startswith("https://www.google."):
            raise ValueError("navigation restricted to Google Search")

        page = await self._get_page(profile_dir, proxy)
        response = await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=45000,
        )
        html = await page.content()

        if hover_target:
            try:
                await page.locator(
                    f'a[href*="{hover_target}"]'
                ).first.hover(timeout=1500)
            except PlaywrightTimeoutError:
                pass

        return PageData(
            url=page.url,
            html=html,
            status=response.status if response else 200,
        )

    async def bring_to_front(self, profile_dir: Path) -> None:
        """Bring an already-open visible profile page forward for manual action."""
        page = self._pages.get(self._profile_key(profile_dir))
        if page is not None and not page.is_closed():
            await page.bring_to_front()

    async def close_all(self) -> None:
        for context in list(self._contexts.values()):
            await context.close()
        self._contexts.clear()
        self._pages.clear()

        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None
