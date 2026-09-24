from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .google.detect import detect_block
from .google.parser import parse_serp
from .google.query import build_google_url
from .matching import matches


@dataclass(slots=True)
class CheckResult:
    keyword: str
    position: int | None
    ranking_url: str | None
    status: str
    profile: str
    features: set[str]


async def check_keyword(
    backend: Any,
    keyword: str,
    target: str,
    profile: Path,
    depth: int = 10,
    google_domain: str = "google.com",
    gl: str = "us",
    hl: str = "en",
    match_mode: str = "domain",
    hover: bool = False,
) -> CheckResult:
    for start in range(0, depth, 10):
        url = build_google_url(
            keyword,
            google_domain,
            hl,
            gl,
            start,
        )
        page = await backend.fetch(
            url,
            profile,
            hover_target=target if hover else None,
        )

        block = detect_block(page.url, page.html, page.status)
        if block.blocked:
            return CheckResult(
                keyword,
                None,
                None,
                "blocked",
                profile.name,
                set(),
            )

        parsed = parse_serp(
            page.html,
            page=(start // 10) + 1,
            start=start,
        )
        for result in parsed.results:
            if matches(result.url, target, match_mode):
                return CheckResult(
                    keyword,
                    result.position,
                    result.url,
                    "ranked",
                    profile.name,
                    parsed.features,
                )

        await asyncio.sleep(0)

    return CheckResult(
        keyword,
        None,
        None,
        f"not_in_top_{depth}",
        profile.name,
        set(),
    )
