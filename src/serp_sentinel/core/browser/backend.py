from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

@dataclass(slots=True)
class PageData:
    url:str; html:str; status:int=200; screenshot:Path|None=None
class SearchBackend(Protocol):
    async def fetch(self,url:str,profile_dir:Path,proxy:dict|None=None,hover_target:str|None=None)->PageData: ...

class FakeBackend:
    def __init__(self,html:str): self.html=html
    async def fetch(self,url:str,profile_dir:Path,proxy:dict|None=None,hover_target:str|None=None)->PageData: return PageData(url,self.html,200)

class PlaywrightBackend:
    async def fetch(self,url:str,profile_dir:Path,proxy:dict|None=None,hover_target:str|None=None)->PageData:
        from playwright.async_api import async_playwright
        if not url.startswith("https://www.google."): raise ValueError("navigation restricted to Google Search")
        async with async_playwright() as p:
            ctx=await p.chromium.launch_persistent_context(str(profile_dir/"user_data"),channel="chrome",headless=False,proxy=proxy)
            page=ctx.pages[0] if ctx.pages else await ctx.new_page(); resp=await page.goto(url,wait_until="domcontentloaded",timeout=45000)
            html=await page.content()
            if hover_target:
                # Hover only; never click or navigate to the result URL.
                try: await page.locator(f'a[href*="{hover_target}"]').first.hover(timeout=1500)
                except Exception: pass
            await ctx.close(); return PageData(page.url if not page.is_closed() else url,html,resp.status if resp else 200)
