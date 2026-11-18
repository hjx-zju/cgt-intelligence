#!/usr/bin/env python3
"""Public RSS candidate collector; no automatic fact verification."""
import json, os, html, re, hashlib, tempfile, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote, urlparse
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"data"
TOPICS=["遗传病","携带者筛查","罕见病","单基因","全外显子","全基因组","长读长","三代测序","PGT-M","WGS","WES","遗传性","基因筛查","新生儿筛查"]
QUERIES=[
("遗传病检测","遗传病 基因检测 when:7d"),
("携带者筛查","携带者筛查 基因检测 when:7d"),
("罕见病诊断","罕见病 基因诊断 测序 when:7d"),
("三代测序","遗传病 (三代测序 OR 长读长) when:7d"),
("医院招投标","遗传病 基因检测 (招标 OR 中标 OR 采购) when:7d"),
("医疗器械注册","遗传病 基因检测 (注册证 OR 获批) when:7d"),
("生殖与新生儿","(PGT-M OR 新生儿筛查) 遗传病 when:7d")]
def load(name,default):
 p=DATA/name
 return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
def save(name,value):
 DATA.mkdir(exist_ok=True)
 with tempfile.NamedTemporaryFile("w",encoding="utf-8",delete=False,dir=DATA) as f:
  json.dump(value,f,ensure_ascii=False,indent=2);f.write("\n");tmp=f.name
 os.replace(tmp,DATA/name)
def txt(x):
 return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",x or ""))).strip()
def child(e,n):
 c=e.find(n)
 return c.text.strip() if c is not None and c.text else ""
def category(t):
 for terms,cat in [(("注册证","获批","NMPA"),"产品/注册"),(("招标","中标","采购"),"医院招投标"),(("融资","并购"),"融资/资本"),(("论文","临床试验"),"临床/科研"),(("合作","签约"),"合作/战略"),(("测序","技术","发布"),"产品/技术")]:
  if any(term in t for term in terms):return cat
 return "其他"
def fetch(q):
 url="https://news.google.com/rss/search?q="+quote(q)+"&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
 req=Request(url,headers={"User-Agent":"CGT-Intelligence/1.0","Accept":"application/rss+xml"})
 with urlopen(req,timeout=22) as resp: data=resp.read(2500000)
 root=ET.fromstring(data)
 if root.find("channel") is None:raise ValueError("RSS channel missing")
 return root.findall("channel/item")[:40]
def run():
 now=datetime.now(timezone.utc);timestamp=now.isoformat(timespec="seconds")
 prior=load("events.json",[]);companies=load("companies.json",[]);verified=load("verified.json",[])
 index={str(e["id"]):e for e in prior if isinstance(e,dict) and e.get("id")}
 sources=[];new=0
 searches=QUERIES+[("企业 · "+c["name"],'"'+c["name"]+'" (遗传病 OR 基因检测 OR 罕见病 OR 携带者筛查 OR 三代测序) when:7d') for c in companies if c.get("name")]
 for name,q in searches:
  try:
   items=fetch(q);accepted=0
   for e in items:
    title=txt(child(e,"title"));url=child(e,"link");description=txt(child(e,"description"))
    parsed=urlparse(url)
    if not title or parsed.scheme not in ("https","http") or not parsed.netloc:continue
    combined=title+" "+description
    if not any(t.lower() in combined.lower() for t in TOPICS):continue
    accepted+=1
    pub=None
    try:pub=parsedate_to_datetime(child(e,"pubDate")).astimezone(timezone.utc).isoformat(timespec="seconds")
    except (ValueError,TypeError,IndexError,AttributeError):pass
    if pub and datetime.fromisoformat(pub)>now+timedelta(days=1):pub=None
    company=next((x["name"] for x in companies if x["name"] in combined),"")
    eid=hashlib.sha256((child(e,"guid") or url).lower().encode()).hexdigest()[:24]
    if eid not in index:
     index[eid]={"id":eid,"title":title[:250],"url":url,"company":company,"category":category(combined),"source":"Google News RSS · "+name,"source_type":"聚合检索","published_at":pub,"collected_at":timestamp,"summary":description[:700],"topics":[t for t in TOPICS if t.lower() in combined.lower()],"technology":[t for t in ("WES","WGS","NGS","PacBio","Nanopore","长读长","三代测序") if t.lower() in combined.lower()],"verification":"待核验"}
     new+=1
   sources.append({"name":name,"status":"ok","detail":str(len(items))+" RSS条目，"+str(accepted)+" 候选"})
  except Exception as e:
   sources.append({"name":name,"status":"error","detail":str(e)[:160]})
  time.sleep(.15)
 for x in verified:
  if not isinstance(x,dict) or not x.get("id") or not x.get("url"):continue
  y=dict(x)
  y["verification"]="已核验" if all(y.get(k) for k in ("reviewed_by","reviewed_at","official_source")) else "待核验"
  index[str(y["id"])]=y
 cutoff=now-timedelta(days=180);events=[]
 for e in index.values():
  try:d=datetime.fromisoformat((e.get("published_at") or e.get("collected_at") or timestamp).replace("Z","+00:00"))
  except (ValueError,AttributeError):d=now
  if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
  if d>=cutoff or e.get("verification")=="已核验":events.append(e)
 events.sort(key=lambda e:e.get("published_at") or e.get("collected_at") or "",reverse=True)
 events=events[:2000]
 errors=sum(x["status"]=="error" for x in sources)
 result="failed" if errors==len(sources) else "partial" if errors else "success"
 save("events.json",events)
 save("status.json",{"last_run_at":timestamp,"new_items":new,"total_items":len(events),"result":result,"sources":sources})
 print("new",new,"total",len(events),"failed",errors,"sources",len(sources))
 if result=="failed":raise SystemExit(2)
if __name__=="__main__":run()
