from pathlib import Path
from serp_sentinel.core.google.uule import encode_uule
from serp_sentinel.core.google.query import build_google_url
from serp_sentinel.core.google.parser import parse_serp
from serp_sentinel.core.matching import matches,normalize_url
from serp_sentinel.core.proxies.parser import parse_proxy

def test_uule():
    assert encode_uule("Dhaka,Bangladesh").startswith("w+CAIQICI")

def test_query():
    u=build_google_url("blue widgets","google.com.bd","en","bd",20,"Dhaka,Bangladesh")
    assert "q=blue+widgets" in u and "start=20" in u and "pws=0" in u

def test_matching():
    assert matches("https://www.example.com/a","example.com","domain")
    assert matches("https://blog.example.com/a","example.com","domain_subdomains")
    assert normalize_url("https://EXAMPLE.com/a/?utm_source=x")=="https://example.com/a"

def test_proxy():
    p=parse_proxy("host:8080:user:pass")
    assert (p.host,p.port,p.username)==("host",8080,"user")

def test_parser():
    html=Path("tests/fixtures/serp/desktop_basic.html").read_text()
    p=parse_serp(html)
    assert p.results[1].position==2
    assert p.results[1].url=="https://example.com/article"
    assert not p.parse_suspect
