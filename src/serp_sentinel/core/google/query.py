from urllib.parse import urlencode
from .uule import encode_uule

def build_google_url(keyword:str, domain:str="google.com", hl:str="en", gl:str="us", start:int=0, location:str|None=None)->str:
    params={"q":keyword,"hl":hl,"gl":gl,"pws":"0","start":str(start)}
    if location: params["uule"]=encode_uule(location)
    return f"https://www.{domain}/search?{urlencode(params)}"
