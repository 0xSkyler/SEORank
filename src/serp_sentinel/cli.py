import argparse,asyncio
from pathlib import Path
from .core.browser.backend import FakeBackend,PlaywrightBackend
from .core.scheduler import check_keyword

def main():
    p=argparse.ArgumentParser(prog="serp-sentinel"); sub=p.add_subparsers(dest="cmd",required=True)
    c=sub.add_parser("check"); c.add_argument("keyword"); c.add_argument("--target",required=True); c.add_argument("--depth",type=int,default=30); c.add_argument("--fixture"); c.add_argument("--profile",default=str(Path.home()/"AppData/Roaming/SerpSentinel/profiles/profile_001"))
    a=p.parse_args()
    if a.cmd=="check":
        backend=FakeBackend(Path(a.fixture).read_text(encoding="utf-8")) if a.fixture else PlaywrightBackend()
        r=asyncio.run(check_keyword(backend,a.keyword,a.target,Path(a.profile),a.depth)); print(f"{r.keyword}: {r.position or '-'} {r.ranking_url or ''} [{r.status}]")
if __name__=="__main__": main()
