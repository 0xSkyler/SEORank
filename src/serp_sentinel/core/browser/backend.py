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


class PlaywrightBackend:
    async def fetch(
        self,
        url: str,
        profile_dir: Path,
        proxy: dict[str, str] | None = None,
        hover_target: str | None = None,
    ) -> PageData:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        from playwright.async_api import async_playwright

        if not url.startswith("https://www.google."):
            raise ValueError("navigation restricted to Google Search")

        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                str(profile_dir / "user_data"),
                channel="chrome",
                headless=False,
                proxy=cast(Any, proxy),
            )
            page = context.pages[0] if context.pages else await context.new_page()
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=45000,
            )
            html = await page.content()

            if hover_target:
                try:
                    await page.locator(f'a[href*="{hover_target}"]').first.hover(timeout=1500)
                except PlaywrightTimeoutError:
                    pass

            final_url = page.url
            status = response.status if response else 200
            await context.close()
            return PageData(final_url, html, status)
