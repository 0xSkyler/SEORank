from pathlib import Path
import sqlite3, json
SCHEMA="""CREATE TABLE IF NOT EXISTS results(id INTEGER PRIMARY KEY, keyword TEXT NOT NULL,target TEXT NOT NULL,checked_at TEXT NOT NULL,position INTEGER,ranking_url TEXT,status TEXT NOT NULL,features TEXT NOT NULL DEFAULT '[]',profile TEXT);CREATE INDEX IF NOT EXISTS idx_results_kw_time ON results(keyword,checked_at);"""
class Database:
    def __init__(self,path:Path): self.path=path; self.conn=sqlite3.connect(path); self.conn.executescript(SCHEMA); self.conn.commit()
    def add_result(self,**r): self.conn.execute("INSERT INTO results(keyword,target,checked_at,position,ranking_url,status,features,profile) VALUES(?,?,?,?,?,?,?,?)",(r['keyword'],r['target'],r['checked_at'],r.get('position'),r.get('ranking_url'),r['status'],json.dumps(r.get('features',[])),r.get('profile'))); self.conn.commit()
