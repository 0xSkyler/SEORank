from dataclasses import dataclass, field
from urllib.parse import urlparse, parse_qs, unquote
try:
    from selectolax.parser import HTMLParser
except Exception:
    HTMLParser=None

@dataclass(slots=True)
class OrganicResult:
    position:int; title:str; url:str; displayed_url:str=""; snippet:str=""; page:int=1
@dataclass(slots=True)
class ParsedSerp:
    results:list[OrganicResult]=field(default_factory=list); features:set[str]=field(default_factory=set); parse_suspect:bool=False

def _unwrap(href:str)->str:
    if href.startswith("/url?"):
        q=parse_qs(urlparse(href).query); return unquote((q.get("q") or q.get("url") or [href])[0])
    return href

def parse_serp(html:str,page:int=1,start:int=0)->ParsedSerp:
    if HTMLParser is None: raise RuntimeError("selectolax is required")
    tree=HTMLParser(html); out=ParsedSerp()
    text=tree.text(separator=" ").lower()
    feature_words={"people_also_ask":"people also ask","ai_overview":"ai overview","shopping":"shopping","top_stories":"top stories","images":"images","videos":"videos"}
    for k,v in feature_words.items():
        if v in text: out.features.add(k)
    seen=set(); pos=start
    for node in tree.css("div.MjjYud, div.g"):
        if any(x in (node.attributes.get("class") or "") for x in ["commercial-unit","pla-unit"]): continue
        link=node.css_first("a") ; h=node.css_first("h3")
        if not link or not h: continue
        href=_unwrap(link.attributes.get("href", ""))
        if not href.startswith("http") or "google." in (urlparse(href).hostname or ""): continue
        if href in seen: continue
        seen.add(href); pos+=1
        snippet_node=node.css_first("div.VwiC3b") or node.css_first("span")
        out.results.append(OrganicResult(pos,h.text(strip=True),href,href,snippet_node.text(strip=True) if snippet_node else "",page))
    out.parse_suspect=(page==1 and len(out.results)<5)
    return out
