"""농마니 약초 사전의 '식약처 인정 건강기능식품 원료' 칸(HFOOD)을 식품안전나라 오픈API로 갱신한다.
사용: python3 update_hfood.py <앱 index.html 경로> <인증키>
- I-0040(개별인정형 원료 인정현황)을 100건씩 받아 사전 약초 이름·다른 이름과 맞춘다.
- 고시형 원료는 아래 GOSI 표를 쓴다(공전 개정 시 손으로 고칠 것).
- index.html 안의 `const HFOOD=...;` 한 줄과 HF_CHECKED 날짜를 바꿔 쓰고, 바뀐 게 있으면 'CHANGED' 를 출력한다."""
import json,re,sys,time,datetime,urllib.request
path,key=sys.argv[1],sys.argv[2]
h=open(path,encoding='utf8').read()
src=h[h.index('const HERB_SRC=`')+16:];src=src[:src.index('`')]
herbs=[l.split('|') for l in src.strip().split('\n') if l.count('|')>=3][1:]
rows=[];a=1
while True:
  url=f"https://openapi.foodsafetykorea.go.kr/api/{key}/I-0040/json/{a}/{a+99}"
  for t in range(4):
    try:
      d=json.load(urllib.request.urlopen(url,timeout=60))["I-0040"];break
    except Exception as e:
      if t==3: raise
      time.sleep(3)
  r=d.get("row") or []
  rows+=r
  total=int(d.get("total_count") or 0)
  a+=100
  if not r or a>total: break
if len(rows)<500: sys.exit(f"too few rows: {len(rows)}")
GOSI={
 "인삼":[["고시","인삼","면역력 증진·피로개선에 도움을 줄 수 있음"],["고시","홍삼 (인삼을 쪄서 말린 것)","면역력 증진·피로개선·혈소판 응집억제를 통한 혈액흐름·기억력 개선·항산화·갱년기 여성의 건강에 도움을 줄 수 있음"]],
 "녹차":[["고시","녹차추출물","항산화·체지방 감소·혈중 콜레스테롤 개선에 도움을 줄 수 있음"]],
 "은행":[["고시","은행잎추출물 (열매가 아닌 잎 추출물)","기억력 개선·혈행 개선에 도움을 줄 수 있음"]],
 "매실":[["고시","매실추출물","피로 개선에 도움을 줄 수 있음"]],
 "상황":[["고시","상황버섯추출물","면역기능 개선에 도움을 줄 수 있음"]],
 "영지":[["고시","영지버섯 자실체 추출물","혈행 개선에 도움을 줄 수 있음"]],
 "목이":[["고시","목이버섯 식이섬유","배변 활동 원활에 도움을 줄 수 있음"]],
}
DROP={"비름","뽕잎","구릿대","마"}
EXCL={"쑥":["쑥부쟁이"],"밤":["레몬"],"생강":["파비플로라"],"목이":["흰목이"],"쑥부쟁이":["섬쑥부쟁이"],"오가피":["가시오가피","가시오갈피"],"인삼":["가시오갈피"]}
def clean(f):
  f=re.sub(r"[\r\n]+"," ",(f or "")).strip().strip('“”"').strip()
  f=re.sub(r"\s*\((생리활성기능|기타기능|질병발생위험감소기능)[^)]*\)","",f)
  f=re.sub(r"\s*\(기타기능\s*[ⅠⅡⅢI]+\)","",f).strip().rstrip(".").strip()
  return "" if f in ("","-",".") else f[:140]
out={}
for x in herbs:
  n,st=x[0],x[3]
  if st=="ban" or n in DROP: continue
  keys=[n]+[a for a in x[1].split(',') if len(a)>=2]
  got=[];seen=set()
  for r in sorted(rows,key=lambda r:r.get('PRMS_DT',''),reverse=True):
    nm=(r.get('APLC_RAWMTRL_NM') or '').strip()
    if not any(k in nm for k in keys) or any(e in nm for e in EXCL.get(n,[])): continue
    f=clean(r.get('FNCLTY_CN'));k=(re.sub(r"\s","",nm),f)
    if k in seen: continue
    seen.add(k);got.append(["개별",nm,f,(r.get('BSSH_NM') or '').strip(),(r.get('PRMS_DT') or '')[:4]])
  w=set(re.sub(r"\s","",g[1]) for g in got if g[2])
  got=[g for g in got if g[2] or re.sub(r"\s","",g[1]) not in w]
  for g in got: g[2]=g[2].strip().strip('"“”').strip()
  l=GOSI.get(n,[])+got
  if l: out[n]=l
out.setdefault("엉겅퀴",[]).append(["주의","밀크씨슬(카르두스 마리아누스) 추출물","'간 건강' 고시형 원료인 밀크씨슬은 국내 산 엉겅퀴와 다른 식물입니다."])
js="const HFOOD="+json.dumps(out,ensure_ascii=False,separators=(",",":"))+";"
m=re.search(r"const HFOOD=.*?;\n",h)
if not m: sys.exit("HFOOD not found")
changed=m.group(0).strip()!=js
h=h[:m.start()]+js+"\n"+h[m.end():]
h=re.sub(r'const HF_CHECKED="[0-9-]+";',f'const HF_CHECKED="{datetime.date.today().isoformat()}";',h)
h=re.sub(r'I-0040\)」 \d+건',f'I-0040)」 {len(rows)}건',h)
open(path,'w',encoding='utf8').write(h)
print(("CHANGED" if changed else "UNCHANGED"),len(rows),"rows",len(out),"herbs")
