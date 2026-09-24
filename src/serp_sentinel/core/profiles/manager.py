from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import json, random, shutil

@dataclass(slots=True)
class Fingerprint:
    device:str; user_agent:str; width:int; height:int; viewport_w:int; viewport_h:int; dpr:float; locale:str; timezone_id:str; hardware_concurrency:int; device_memory:int

SCREENS=[(1920,1080),(1536,864),(1366,768),(2560,1440)]

def generate_fingerprint(chrome_major:int=140,device:str="desktop",locale:str="en-US",timezone_id:str="Asia/Dhaka")->Fingerprint:
    w,h=random.choice(SCREENS); mobile=device=="mobile"
    ua=(f"Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Mobile Safari/537.36" if mobile else f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Safari/537.36")
    return Fingerprint(device,ua,390 if mobile else w,844 if mobile else h,390 if mobile else max(1024,w-80),780 if mobile else max(650,h-140),3.0 if mobile else 1.0,locale,timezone_id,random.choice([4,8,12,16]),random.choice([4,8,16]))

class ProfileManager:
    def __init__(self,root:Path): self.root=root; root.mkdir(parents=True,exist_ok=True)
    def create(self,count:int,chrome_major:int=140,device:str="desktop")->list[Path]:
        made=[]
        for i in range(1,count+1):
            p=self.root/f"profile_{i:03d}"
            if p.exists(): continue
            (p/"user_data").mkdir(parents=True); fp=generate_fingerprint(chrome_major,device)
            (p/"profile.json").write_text(json.dumps({"name":p.name,"fingerprint":asdict(fp),"status":"ready","total_searches":0,"captcha_count":0,"consecutive_failures":0},indent=2),encoding="utf-8"); made.append(p)
        return made
    def reset(self,name:str)->None:
        p=self.root/name; shutil.rmtree(p/"user_data",ignore_errors=True); (p/"user_data").mkdir(parents=True)
    def delete(self,name:str)->None: shutil.rmtree(self.root/name,ignore_errors=True)
