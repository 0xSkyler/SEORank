from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, cast

import psutil


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

    _LOCK_NAMES = (
        "SingletonCookie",
        "SingletonLock",
        "SingletonSocket",
        "lockfile",
    )

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

    @staticmethod
    def _processes_using_profile(user_data: Path) -> list[int]:
        needle = str(user_data.resolve()).lower()
        pids: list[int] = []

        for process in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = (process.info.get("name") or "").lower()
                if "chrome" not in name and "msedge" not in name:
                    continue

                cmdline = process.info.get("cmdline") or []
                command = " ".join(str(part) for part in cmdline).lower()
                if needle in command:
                    pids.append(int(process.info["pid"]))
            except (psutil.AccessDenied, psutil.NoSuchProcess, TypeError, ValueError):
                continue

        return pids

    @classmethod
    def _clean_stale_profile_locks(cls, user_data: Path) -> None:
        for name in cls._LOCK_NAMES:
            candidate = user_data / name
            try:
                if candidate.is_dir():
                    shutil.rmtree(candidate)
                elif candidate.exists() or candidate.is_symlink():
                    candidate.unlink(missing_ok=True)
            except OSError:
                continue

    @staticmethod
    def _backup_and_recreate_user_data(user_data: Path) -> Path | None:
        if not user_data.exists():
            user_data.mkdir(parents=True, exist_ok=True)
            return None

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = user_data.parent / f"user_data_backup_{stamp}"

        try:
            user_data.replace(backup)
        except OSError:
            return None

        user_data.mkdir(parents=True, exist_ok=True)
        return backup

    async def _launch_context(
        self,
        profile_dir: Path,
        proxy: dict[str, str] | None,
    ) -> Any:
        playwright = await self._ensure_started()
        user_data = profile_dir / "user_data"
        user_data.mkdir(parents=True, exist_ok=True)

        active_pids = self._processes_using_profile(user_data)
        if active_pids:
            joined = ", ".join(str(pid) for pid in active_pids)
            raise RuntimeError(
                "This Serp Sentinel browser profile is already open in another "
                f"Chrome process (PID {joined}). Close that old Serp Sentinel "
                "browser/app window and press Start again."
            )

        async def launch() -> Any:
            return await playwright.chromium.launch_persistent_context(
                str(user_data),
                channel="chrome",
                headless=self.headless,
                proxy=cast(Any, proxy),
            )

        try:
            return await launch()
        except Exception as first_error:
            # A previous crash can leave Chrome's profile singleton files behind.
            # They are safe to remove only after confirming no live Chrome process
            # is using this Serp Sentinel profile.
            if self._processes_using_profile(user_data):
                raise RuntimeError(
                    "Chrome is still using this Serp Sentinel profile. Close the "
                    "old Serp Sentinel browser window and try again."
                ) from first_error

            self._clean_stale_profile_locks(user_data)
            await asyncio.sleep(0.5)

            try:
                return await launch()
            except Exception as second_error:
                # Preserve the old profile instead of deleting it. A clean Chrome
                # data directory is then created and tried once. The backup can
                # be restored manually if its cookies/history are needed later.
                backup = self._backup_and_recreate_user_data(user_data)
                if backup is None:
                    raise RuntimeError(
                        "Chrome closed before Serp Sentinel could attach. Close "
                        "all Serp Sentinel/Chrome windows and try again. If it "
                        "continues, use a new profile number."
                    ) from second_error

                await asyncio.sleep(0.5)
                try:
                    return await launch()
                except Exception as final_error:
                    raise RuntimeError(
                        "Chrome still closes immediately after a clean profile "
                        "recovery. Restart Windows, make sure Google Chrome opens "
                        "normally by itself, then start Serp Sentinel again. "
                        f"The previous profile was preserved at: {backup}"
                    ) from final_error

    async def _get_page(
        self,
        profile_dir: Path,
        proxy: dict[str, str] | None,
    ) -> Any:
        key = self._profile_key(profile_dir)
        page = self._pages.get(key)
        if page is not None and not page.is_closed():
            return page

        context = await self._launch_context(profile_dir, proxy)
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

        try:
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=45000,
            )
            html = await page.content()
        except Exception as exc:
            key = self._profile_key(profile_dir)
            self._pages.pop(key, None)
            context = self._contexts.pop(key, None)
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass
            raise RuntimeError(
                "The Chrome session closed while loading Google. Press Start "
                "again; Serp Sentinel will recover the profile automatically."
            ) from exc

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
        page = self._pages.get(self._profile_key(profile_dir))
        if page is not None and not page.is_closed():
            await page.bring_to_front()

    async def close_all(self) -> None:
        for context in list(self._contexts.values()):
            try:
                await context.close()
            except Exception:
                pass
        self._contexts.clear()
        self._pages.clear()

        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None
