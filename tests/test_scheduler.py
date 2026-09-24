import asyncio
from pathlib import Path
from serp_sentinel.core.browser.backend import FakeBackend
from serp_sentinel.core.scheduler import check_keyword

def test_scheduler_fixture():
    html=Path("tests/fixtures/serp/desktop_basic.html").read_text()
    r=asyncio.run(check_keyword(FakeBackend(html),"k","example.com",Path("p"),10))
    assert r.position==2 and r.status=="ranked"
