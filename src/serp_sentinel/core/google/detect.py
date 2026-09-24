from dataclasses import dataclass

@dataclass(slots=True)
class BlockState:
    blocked: bool
    reason: str|None=None

def detect_block(url:str, html:str, status:int=200)->BlockState:
    low=html.lower()
    if status==429: return BlockState(True,"http_429")
    if "/sorry/" in url: return BlockState(True,"sorry_redirect")
    if "recaptcha" in low or "unusual traffic" in low: return BlockState(True,"captcha_or_unusual_traffic")
    return BlockState(False)
