from dataclasses import dataclass
from urllib.parse import urlsplit

@dataclass(slots=True)
class Proxy:
    scheme:str; host:str; port:int; username:str|None=None; password:str|None=None

def parse_proxy(line:str)->Proxy:
    s=line.strip()
    if "://" not in s:
        parts=s.split(":")
        if len(parts)==4: return Proxy("http",parts[0],int(parts[1]),parts[2],parts[3])
        s="http://"+s
    p=urlsplit(s)
    if not p.hostname or not p.port: raise ValueError("invalid proxy")
    return Proxy(p.scheme or "http",p.hostname,p.port,p.username,p.password)
