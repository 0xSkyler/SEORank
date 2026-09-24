from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import tldextract

TRACKING={"gclid","fbclid","utm_source","utm_medium","utm_campaign","utm_term","utm_content"}

def normalize_url(url:str, ignore_query:bool=False)->str:
    p=urlsplit(url if "://" in url else "https://"+url)
    host=(p.hostname or "").lower().rstrip(".")
    path=p.path or "/"
    if path!="/": path=path.rstrip("/")
    q="" if ignore_query else urlencode([(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if k.lower() not in TRACKING])
    return urlunsplit(("https",host,path,q,""))

def matches(url:str,target:str,mode:str="domain",ignore_query:bool=False)->bool:
    uh=(urlsplit(url if "://" in url else "https://"+url).hostname or "").lower()
    th=(urlsplit(target if "://" in target else "https://"+target).hostname or "").lower()
    if mode=="exact_url": return normalize_url(url,ignore_query)==normalize_url(target,ignore_query)
    if mode=="domain_subdomains": return uh==th or uh.endswith("."+th)
    u=tldextract.extract(uh); t=tldextract.extract(th)
    return f"{u.domain}.{u.suffix}"==f"{t.domain}.{t.suffix}" and uh.replace("www.","")==th.replace("www.","")
