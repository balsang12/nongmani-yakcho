#!/usr/bin/env python3
"""농마니 약초 백과 — 정적 사이트 생성기

입력: base.json (앱의 품목 사전·고서 기록), data/ (앱 저장소 herbinfo 문서 JSON들)
출력: out/ (GitHub Pages에 그대로 올리는 HTML·sitemap·robots·llms.txt)

사용: python3 build.py --base https://아이디.github.io/저장소이름 [--data data/herbinfo] [--out out]
"""
import argparse, json, os, glob, html, shutil, datetime, urllib.parse

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="https://example.github.io/nongmani-yakcho")
ap.add_argument("--data", default=os.path.join(os.path.dirname(__file__), "data", "herbinfo"))
ap.add_argument("--src", default=os.path.join(os.path.dirname(__file__), "base.json"))
ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "out"))
a = ap.parse_args()
BASE = a.base.rstrip("/")
SITE = "농마니 약초 백과"
TODAY = datetime.date.today().isoformat()

E = lambda s: html.escape(str(s or ""), quote=True)
base = json.load(open(a.src, encoding="utf8"))
HERBS, CLASSIC = base["herbs"], base["classic"]
ST = {"ok": "식용 원료", "caution": "식용 · 주의", "check": "식품원료 확인 필요", "hanyak": "한약재 전용 · 판매 불가", "ban": "독초 · 먹으면 위험"}
ST_ORDER = ["ok", "caution", "check", "hanyak", "ban"]

# herbinfo 문서 읽기 (ArtifactData out_dir 형식 또는 단순 JSON)
INFO = {}
for f in glob.glob(os.path.join(a.data, "*.json")):
    try:
        d = json.load(open(f, encoding="utf8"))
    except Exception:
        continue
    d = d.get("data", d) if isinstance(d, dict) else d
    if isinstance(d, dict) and d.get("name"):
        INFO[d["name"]] = d

def classic_of(n):
    i = INFO.get(n, {})
    if (i.get("classic") or {}).get("has"):
        return i["classic"]
    for c in CLASSIC:
        if (n in c.get("alias", []) or c.get("name") == n) and not c.get("none"):
            return c
    return None

def none_note(n):
    for c in CLASSIC:
        if n in c.get("alias", []) and c.get("none"):
            return c
    return None

slug = lambda n: urllib.parse.quote(n)
url = lambda path: f"{BASE}/{path}"
herb_path = lambda n: f"yakcho/{slug(n)}/"
NAMES = {h["name"] for h in HERBS}
ALIAS = {al: h["name"] for h in HERBS for al in h["alias"]}
def link_name(n):
    t = n if n in NAMES else ALIAS.get(n)
    return f'<a href="{herb_path(t)}">{E(n)}</a>' if t else E(n)

def rich(n):
    """내용이 충분한 페이지만 검색에 내보낸다 (얇은 페이지는 noindex)"""
    i = INFO.get(n, {})
    score = 0
    score += 2 if (i.get("id") or {}).get("look") else 0
    score += 2 if i.get("lookalikes") else 0
    score += 2 if classic_of(n) else 0
    score += 1 if (i.get("modern") or {}).get("papers") else 0
    score += 1 if i.get("toxic") else 0
    score += 1 if i.get("traditional", {}).get("text") else 0
    return score >= 2

CSS = """
:root{--bg:#F4F6F1;--surface:#FFFFFF;--sunk:#E8EDE3;--line:#D3DCCD;--ink:#15201A;--muted:#566659;--pine:#2B5B41;--pine-ink:#fff;--pine-soft:#DAE9DE;--gold:#8A5B0B;--gold-soft:#F4E7CC;--gold-deep:#6E4705;--berry:#A3324A;--berry-soft:#F6E0E5;--display:"Gowun Batang","Nanum Myeongjo",serif;--body:"Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root{--bg:#111712;--surface:#19221B;--sunk:#222D24;--line:#334036;--ink:#E5ECE4;--muted:#9AAA9D;--pine:#7BBA94;--pine-ink:#0D1910;--pine-soft:#213628;--gold:#E2B45E;--gold-soft:#352A16;--gold-deep:#F0C878;--berry:#E57F95;--berry-soft:#3A2128;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 var(--body)}
a{color:var(--pine)}h1,h2,h3{font-family:var(--display);line-height:1.3;text-wrap:balance}
.wrap{max-width:860px;margin:0 auto;padding-inline:16px}
header.top{background:var(--surface);border-bottom:1px solid var(--line)}
header.top .wrap{display:flex;gap:12px;align-items:center;justify-content:space-between;padding-block:12px;flex-wrap:wrap}
.logo{font-family:var(--display);font-weight:700;font-size:21px;color:var(--pine);text-decoration:none}.logo i{font-style:normal;color:var(--gold)}
nav.top a{margin-left:14px;font-size:14px;color:var(--muted);text-decoration:none}nav.top a:first-child{margin-left:0}
main{padding-block:20px 60px}
.crumb{font-size:13px;color:var(--muted)}.crumb a{color:var(--muted)}
.chip{display:inline-block;font-size:12px;padding:1px 9px;border-radius:999px;background:var(--sunk);color:var(--muted);margin-right:4px}
.chip.ok{background:var(--pine-soft);color:var(--pine)}.chip.gold{background:var(--gold-soft);color:var(--gold-deep)}.chip.hot{background:var(--berry-soft);color:var(--berry)}
.han{font-family:var(--display);color:var(--gold-deep)}
.box{border:1px solid var(--line);background:var(--surface);border-radius:12px;padding:14px 16px;margin:12px 0}
.box.bad{border:1.5px solid var(--berry);background:var(--berry-soft)}
.box.gold{background:var(--gold-soft);border-color:var(--gold)}
dl.facts{display:grid;grid-template-columns:auto 1fr;gap:6px 16px;margin:0}dl.facts dt{color:var(--muted)}dl.facts dd{margin:0;min-width:0}
table.m{border-collapse:collapse;width:100%;font-size:12px;text-align:center}table.m td{border:1px solid var(--line);padding:3px 0}table.m td.on{background:var(--pine);color:var(--pine-ink);font-weight:700}table.m td.fl{background:var(--gold-soft);color:var(--gold-deep);font-weight:700}
.orig{font-family:var(--display);font-size:18px;letter-spacing:.05em;border-left:3px solid var(--gold);padding-left:14px}
.note{font-size:14px;color:var(--muted)}
ul.src{font-size:13px;color:var(--muted);padding-left:18px}ul.src a{color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.grid a{display:block;background:var(--surface);padding:8px 12px;text-decoration:none;color:var(--ink)}.grid a small{display:block;color:var(--muted);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.grid a:hover{background:var(--pine-soft)}
.search{width:100%;padding:12px 14px;font-size:16px;border:1.5px solid var(--pine);border-radius:12px;background:var(--surface);color:var(--ink)}
details{border:1px solid var(--line);border-radius:10px;padding:10px 14px;background:var(--surface);margin:6px 0}summary{cursor:pointer;font-weight:700}
footer{border-top:1px solid var(--line);padding-block:24px;font-size:13px;color:var(--muted)}
"""

def page(path, title, desc, body, jsonld=None, index=True, crumbs=None):
    canon = url(path)
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in (jsonld or []))
    cr = ""
    if crumbs:
        cr = '<div class="crumb">' + " › ".join(f'<a href="{p}">{E(t)}</a>' if p else E(t) for t, p in crumbs) + "</div>"
    doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">{'' if index else '<meta name="robots" content="noindex,follow">'}
<link rel="canonical" href="{E(canon)}"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="article"><meta property="og:url" content="{E(canon)}"><meta property="og:locale" content="ko_KR">
<base href="{E(BASE)}/"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700&family=Noto+Sans+KR:wght@400;700&display=swap">
<style>{CSS}</style>{ld}</head><body>
<header class="top"><div class="wrap"><a class="logo" href="./">농부와 <i>심마니</i> 약초 백과</a><nav class="top"><a href="./">전체 약초</a><a href="dokcho/">독초 구별</a><a href="jecheol/">제철 달력</a></nav></div></header>
<main class="wrap">{cr}{body}</main>
<footer><div class="wrap">{SITE}는 산나물·약초를 사고파는 '농부와 심마니'가 만드는 한국 약초 정보 모음입니다. 옛 의서의 기록과 연구를 소개할 뿐 효능을 보장하거나 치료를 권하지 않습니다. 몸이 불편하면 한의사·의사와 상의하세요. 마지막 업데이트 {TODAY}.</div></footer>
</body></html>"""
    dp = urllib.parse.unquote(path)
    fp = os.path.join(a.out, dp, "index.html") if (path == "" or path.endswith("/")) else os.path.join(a.out, dp)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, "w", encoding="utf8").write(doc)
    return canon if index else None

def srcs(lst):
    lst = [s for s in (lst or []) if isinstance(s, dict)]
    if not lst: return ""
    return '<ul class="src">' + "".join(f'<li><a href="{E(s.get("url"))}" rel="nofollow noopener" target="_blank">{E(s.get("title") or s.get("url"))}</a></li>' if str(s.get("url","")).startswith("https://") else f'<li>{E(s.get("title"))}</li>' for s in lst) + "</ul>"

def months(arr, cls):
    arr = arr or []
    return "<tr>" + "".join(f'<td class="{cls if m in arr else ""}">{m}</td>' for m in range(1, 13)) + "</tr>"

SITEMAP = []
LOOK_PAIRS = []
BY_MONTH = {m: [] for m in range(1, 13)}

for h in HERBS:
    n, i = h["name"], INFO.get(h["name"], {})
    ban = h["st"] == "ban"
    idn = i.get("id") or {}
    c = None if ban else classic_of(n)
    nn = none_note(n)
    lk = i.get("lookalikes") or []
    faq = i.get("faq") or []
    for l in lk:
        LOOK_PAIRS.append((n, l, ban))
    for m in (idn.get("season") or {}).get("collect") or []:
        if isinstance(m, int) and 1 <= m <= 12 and not ban:
            BY_MONTH[m].append(n)

    parts = []
    head = f'<h1>{E(n)} {f"<span class=han>{E(c.get(chr(104)+chr(97)+chr(110)))}</span>" if c and c.get("han") else ""}</h1>'
    parts.append(head)
    meta = f'<p><span class="chip {"hot" if ban or h["st"]=="hanyak" else "ok" if h["st"]=="ok" else "gold"}">{ST[h["st"]]}</span> <span class="chip">{E(h["cat"])}</span>' + (f' 다른 이름: {E(", ".join(h["alias"]))}' if h["alias"] else "") + "</p>"
    parts.append(meta)
    # 한 줄 요약 (AI가 인용하기 좋은 첫 문단)
    lead = []
    if idn.get("sci"): lead.append(f'{n}({idn["sci"]})는 {idn.get("family","")} 식물로'.replace("  ", " "))
    if ban:
        lead.append(f'{n}는 먹으면 위험한 독성 식물입니다.' if not lead else "먹으면 위험한 독성 식물입니다.")
        if i.get("toxic", {}).get("lookalike"): lead.append(f'{i["toxic"]["lookalike"]}와(과) 헷갈려 사고가 납니다.')
    else:
        if idn.get("habitat"): lead.append(f'{idn["habitat"]}에서 자랍니다.' if lead else f'{n}는 {idn["habitat"]}에서 자랍니다.')
        if idn.get("parts"): lead.append(f'주로 {idn["parts"]}을(를) 먹습니다.')
        col = (idn.get("season") or {}).get("collect")
        if col: lead.append(f'채취 시기는 {", ".join(str(x)+"월" for x in col)}입니다.')
    if h.get("note"): lead.append(h["note"].rstrip(".") + ".")
    if lead: parts.append(f'<p><strong>{E(" ".join(lead))}</strong></p>')

    if ban:
        t = i.get("toxic") or {}
        parts.append(f'<div class="box bad"><h2 style="margin-top:0">먹으면 위험합니다</h2><p>{E(t.get("text") or h["note"] or "산나물·약초로 잘못 알고 먹는 사고가 나는 독성 식물입니다.")}</p>{f"<p><b>잘못 알기 쉬운 산나물:</b> {E(t.get(chr(108)+chr(111)+chr(111)+chr(107)+chr(97)+chr(108)+chr(105)+chr(107)+chr(101)))}</p>" if t.get("lookalike") else ""}<p>먹었다면 바로 119에 신고하거나 가까운 응급실로 가세요. 먹고 남은 식물을 함께 가져가면 치료에 도움이 됩니다.</p></div>{srcs(t.get("sources"))}')

    if idn:
        f = []
        for k, lab in [("sci","학명"),("family","과"),("eng","영어 이름"),("parts","먹는 부위"),("habitat","자라는 곳"),("taste","맛과 향")]:
            if idn.get(k) and not (ban and k in ("parts","taste")):
                f.append(f"<dt>{lab}</dt><dd>{'<i>'+E(idn[k])+'</i>' if k=='sci' else E(idn[k])}</dd>")
        sea = idn.get("season") or {}
        if sea.get("collect") or sea.get("flower"):
            f.append(f'<dt>{"싹 나는 때" if ban else "제철"}</dt><dd><table class="m" aria-label="월별 시기">{months(sea.get("collect"),"on")}{months(sea.get("flower"),"fl") if sea.get("flower") else ""}</table><span class="note">초록: {"싹이 나는 달" if ban else "채취 시기"}{" · 노랑: 꽃 피는 달" if sea.get("flower") else ""}</span></dd>')
        if f: parts.append(f'<h2>한눈에 보기</h2><div class="box"><dl class="facts">{"".join(f)}</dl></div>')
        look = idn.get("look") or {}
        ll = [(lab, look.get(k)) for k, lab in [("leaf","잎"),("stem","줄기"),("flower","꽃"),("root","뿌리"),("fruit","열매"),("smell","냄새")] if look.get(k)]
        if ll:
            parts.append(f'<h2>{E(n)} 생김새</h2><dl class="facts box">' + "".join(f"<dt>{lab}</dt><dd>{E(v)}</dd>" for lab, v in ll) + "</dl>" + srcs(idn.get("sources")))
    if lk:
        parts.append(f'<h2>{E(n)}{"로 잘못 알기 쉬운 식물" if ban else "와 비슷한 식물 구별법"}</h2>')
        for l in lk:
            bad = "독" in str(l.get("danger",""))
            pts = "".join(f"<li>{E(p)}</li>" for p in (l.get("points") or []))
            parts.append(f'<div class="box {"bad" if bad else ""}"><h3 style="margin:0">{E(n)} vs {link_name(l.get("name",""))} <span class="chip {"hot" if bad else "gold"}">{E(l.get("danger","비슷함"))}</span></h3>{f"<p>{E(l.get(chr(104)+chr(111)+chr(119)))}</p>" if l.get("how") else ""}{f"<ul>{pts}</ul>" if pts else ""}</div>')
        parts.append(srcs(i.get("lookSources")) + '<p class="note">조금이라도 애매하면 먹지 마세요. 산나물 독초 사고는 대부분 비슷해 보여서 생깁니다.</p>')
    if not ban and (idn.get("prep") or idn.get("store") or idn.get("eat")):
        parts.append('<h2>손질·보관·먹는 법</h2><dl class="facts box">' + "".join(f"<dt>{lab}</dt><dd>{E(idn[k])}</dd>" for k, lab in [("prep","손질"),("store","보관"),("eat","먹는 법")] if idn.get(k)) + "</dl>")
    if c:
        parts.append(f'<h2>옛 의서의 기록 — {E(c.get("book","동의보감 탕액편"))}</h2>')
        if c.get("ki"): parts.append(f'<div class="box gold"><b>성질과 맛</b><div class="han" style="font-size:18px">{E(c["ki"])}</div>{E(c.get("kiKo",""))}</div>')
        if c.get("orig"): parts.append(f'<p class="orig">{E(c["orig"])}</p>')
        if c.get("easy"): parts.append("<ul>" + "".join(f"<li>{E(x)}</li>" for x in c["easy"]) + "</ul>")
        if c.get("warn"): parts.append(f'<p class="note">{E(c["warn"])}</p>')
        parts.append(srcs(c.get("sources")) + '<p class="note">옛 기록을 소개한 것이며 효능을 보장하지 않습니다.</p>')
    elif nn:
        parts.append("<h2>옛 의서의 기록</h2><ul>" + "".join(f"<li>{E(x)}</li>" for x in nn["easy"]) + f'</ul><p class="note">{E(nn["warn"])}</p>')
    if not ban and (i.get("traditional") or {}).get("text"):
        parts.append(f'<h2>전통적으로 알려진 쓰임</h2><p>{E(i["traditional"]["text"])}</p>{srcs(i["traditional"].get("sources"))}')
    mo = i.get("modern") or {}
    if not ban and (mo.get("summary") or mo.get("papers")):
        parts.append(f'<h2>{E(n)} 최근 연구</h2>' + (f"<p>{E(mo.get('summary'))}</p>" if mo.get("summary") else ""))
        for p in mo.get("papers") or []:
            t = f'<a href="{E(p.get("url"))}" rel="nofollow noopener" target="_blank">{E(p.get("title"))}</a>' if str(p.get("url","")).startswith("https://") else E(p.get("title"))
            parts.append(f'<div class="box"><b>{t}</b><div class="note">{E(p.get("journal"))} · {E(p.get("year"))} <span class="chip">{E(p.get("type"))}</span></div>{f"<div>{E(p.get(chr(110)+chr(111)+chr(116)+chr(101)))}</div>" if p.get("note") else ""}</div>')
        parts.append('<p class="note">연구 대부분은 세포·동물 실험이어서 사람에게 같은 효과가 있다는 뜻은 아닙니다.</p>')
    if faq:
        parts.append(f'<h2>{E(n)} 자주 묻는 질문</h2>' + "".join(f"<details open><summary>{E(q.get('q'))}</summary><p>{E(q.get('a'))}</p></details>" for q in faq))
    if h["st"] == "hanyak":
        parts.append('<div class="box bad">한약재 전용 품목이라 식품으로 사고팔 수 없습니다.</div>')
    if not rich(n):
        parts.append('<div class="box note">이 약초의 생김새·구별법·연구 자료는 지금 정리하고 있습니다. 매일 조금씩 채워집니다.</div>')
    rel = [x["name"] for x in HERBS if x["cat"] == h["cat"] and x["name"] != n and x["st"] == h["st"]][:12]
    if rel:
        parts.append(f'<h2>같은 분류의 다른 {E(h["cat"])}</h2><div class="grid">' + "".join(f'<a href="{herb_path(r)}">{E(r)}</a>' for r in rel) + "</div>")

    title = f'{n} 구별법·생김새·{"독성" if ban else "제철·옛 기록"} | {SITE}' if lk else f'{n} — {"독초 안내" if ban else "생김새·제철·옛 기록·최근 연구"} | {SITE}'
    desc = (" ".join(lead) or f"{n}의 생김새, 비슷한 식물 구별법, 제철, 손질법, 동의보감 기록과 최근 연구를 정리했습니다.")[:155]
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": f"{n} — {SITE}", "inLanguage": "ko", "dateModified": TODAY, "url": url(herb_path(n)), "description": desc,
           "about": {"@type": "Taxon", "name": idn.get("sci") or n, "alternateName": [n] + h["alias"], "taxonRank": "species"} if idn.get("sci") else {"@type": "Thing", "name": n, "alternateName": h["alias"]},
           "isPartOf": {"@type": "WebSite", "name": SITE, "url": BASE + "/"}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "전체 약초", "item": BASE + "/"}, {"@type": "ListItem", "position": 2, "name": n, "item": url(herb_path(n))}]}]
    if faq:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q.get("q"), "acceptedAnswer": {"@type": "Answer", "text": q.get("a")}} for q in faq if q.get("q") and q.get("a")]})
    u = page(herb_path(n), title, desc, "".join(parts), ld, index=rich(n), crumbs=[("전체 약초", "./"), (n, None)])
    if u: SITEMAP.append((u, i.get("updatedAt")))

# 독초 구별 가이드
bans = [h for h in HERBS if h["st"] == "ban"]
body = ['<h1>독초와 산나물 구별법 총정리</h1><p><strong>봄철 산나물을 뜯다가 독초를 잘못 먹는 사고가 해마다 납니다. 아래는 헷갈리기 쉬운 짝과 구별하는 방법입니다. 조금이라도 애매하면 먹지 마세요.</strong></p>']
seen = set()
if LOOK_PAIRS:
    body.append("<h2>헷갈리기 쉬운 짝</h2>")
    for n, l, ban in LOOK_PAIRS:
        if "독" not in str(l.get("danger", "")) and not ban: continue
        key = tuple(sorted([n, l.get("name", "")]))
        if key in seen: continue
        seen.add(key)
        pts = "".join(f"<li>{E(p)}</li>" for p in (l.get("points") or []))
        body.append(f'<div class="box bad"><h3 style="margin:0">{link_name(n)} vs {link_name(l.get("name",""))}</h3>{f"<p>{E(l.get(chr(104)+chr(111)+chr(119)))}</p>" if l.get("how") else ""}{f"<ul>{pts}</ul>" if pts else ""}</div>')
body.append(f'<h2>먹으면 위험한 독성 식물 {len(bans)}가지</h2><div class="grid">' + "".join(f'<a href="{herb_path(h["name"])}">{E(h["name"])}<small>{E(h["note"])}</small></a>' for h in bans) + "</div>")
body.append('<p class="note">먹었다면 바로 119에 신고하거나 응급실로 가세요. 먹고 남은 식물을 함께 가져가면 도움이 됩니다.</p>')
u = page("dokcho/", f"독초와 산나물 구별법 총정리 | {SITE}", "곰취와 동의나물, 산마늘과 박새처럼 헷갈리기 쉬운 산나물과 독초를 구별하는 방법을 정리했습니다.", "".join(body), [{"@context": "https://schema.org", "@type": "WebPage", "name": "독초와 산나물 구별법", "inLanguage": "ko", "dateModified": TODAY}], crumbs=[("전체 약초", "./"), ("독초 구별", None)])
SITEMAP.append((u, None))

# 제철 달력
mb = ['<h1>달마다 제철 산나물·약초</h1><p><strong>몇 월에 어떤 산나물과 약초를 캐는지 정리했습니다.</strong></p>']
for m in range(1, 13):
    if BY_MONTH[m]:
        mb.append(f'<h2><a href="jecheol/{m}/">{m}월 제철</a></h2><div class="grid">' + "".join(f'<a href="{herb_path(n)}">{E(n)}</a>' for n in BY_MONTH[m]) + "</div>")
        u = page(f"jecheol/{m}/", f"{m}월 제철 산나물·약초 {len(BY_MONTH[m])}가지 | {SITE}", f"{m}월에 채취하는 산나물과 약초: " + ", ".join(BY_MONTH[m][:12]), f'<h1>{m}월 제철 산나물·약초</h1><p><strong>{m}월에 캐는 산나물·약초는 {", ".join(BY_MONTH[m])}입니다.</strong></p><div class="grid">' + "".join(f'<a href="{herb_path(n)}">{E(n)}</a>' for n in BY_MONTH[m]) + '</div><p class="note">채취 전에는 꼭 비슷한 독초와의 구별법을 확인하세요. <a href="dokcho/">독초 구별법 보기</a></p>', index=len(BY_MONTH[m]) >= 3, crumbs=[("전체 약초", "./"), ("제철 달력", "jecheol/"), (f"{m}월", None)])
        if u: SITEMAP.append((u, None))
if len(mb) == 1: mb.append('<p class="note">제철 자료를 모으는 중입니다.</p>')
u = page("jecheol/", f"달마다 제철 산나물·약초 달력 | {SITE}", "1월부터 12월까지 달마다 채취하는 산나물과 약초를 정리했습니다.", "".join(mb), index=any(BY_MONTH.values()), crumbs=[("전체 약초", "./"), ("제철 달력", None)])
if u: SITEMAP.append((u, None))

# 홈 (전체 목록)
hb = [f'<h1>한국 산나물·약초 {len(HERBS)}가지 백과</h1><p><strong>산나물과 약초의 생김새, 헷갈리는 독초와 구별하는 법, 제철과 손질법, 동의보감 같은 옛 의서의 기록과 최근 연구까지 한곳에 모았습니다.</strong></p>',
      '<input class="search" id="q" placeholder="이름·다른 이름으로 찾기 (예: 딱주, 명이)" aria-label="약초 찾기">']
for st in ST_ORDER:
    g = [h for h in HERBS if h["st"] == st]
    hb.append(f'<h2>{ST[st]} <span class="note">{len(g)}가지</span></h2><div class="grid">' + "".join(f'<a href="{herb_path(h["name"])}" data-k="{E(" ".join([h["name"]] + h["alias"]))}">{E(h["name"])}<small>{E(", ".join(h["alias"]) or h["cat"])}</small></a>' for h in g) + "</div>")
hb.append('<script>document.getElementById("q").addEventListener("input",e=>{const q=e.target.value.trim();document.querySelectorAll(".grid a[data-k]").forEach(a=>{a.hidden=q&&!a.dataset.k.includes(q)})})</script>')
ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": SITE, "url": BASE + "/", "inLanguage": "ko", "description": "한국 산나물·약초의 생김새, 독초 구별법, 제철, 옛 의서 기록, 최근 연구"},
      {"@context": "https://schema.org", "@type": "ItemList", "name": "한국 산나물·약초 목록", "numberOfItems": len(HERBS), "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": h["name"], "url": url(herb_path(h["name"]))} for k, h in enumerate(HERBS)]}]
u = page("", f"{SITE} — 한국 산나물·약초 {len(HERBS)}가지 생김새·독초 구별법·제철", f"한국 산나물·약초 {len(HERBS)}가지의 생김새, 독초와 구별하는 법, 제철, 손질법, 동의보감 기록과 최근 연구를 정리한 백과입니다.", "".join(hb), ld)
SITEMAP.insert(0, (u, None))

# sitemap / robots / llms.txt / 404
def iso(ms):
    try: return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).date().isoformat()
    except Exception: return TODAY
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{E(u)}</loc><lastmod>{iso(t) if t else TODAY}</lastmod></url>\n" for u, t in SITEMAP) + "</urlset>\n"
open(os.path.join(a.out, "sitemap.xml"), "w", encoding="utf8").write(sm)
open(os.path.join(a.out, "robots.txt"), "w", encoding="utf8").write(
    "# 검색 엔진과 AI 검색 로봇 모두 환영합니다\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in ["*", "Googlebot", "Google-Extended", "Bingbot", "Yeti", "Daum", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User"]) + f"Sitemap: {BASE}/sitemap.xml\n")
rich_list = [h for h in HERBS if rich(h["name"])]
llms = [f"# {SITE}", "", f"> 한국 산나물·약초 {len(HERBS)}가지의 생김새, 독초와 구별하는 법, 제철·손질법, 『동의보감』 등 옛 의서 기록, 최근 연구를 정리한 한국어 백과. 효능을 보장하지 않으며 독초 25가지는 위험 안내만 싣는다.", "",
        "## 안내", f"- [전체 약초 목록]({BASE}/): 구분별 {len(HERBS)}가지", f"- [독초와 산나물 구별법]({BASE}/dokcho/): 헷갈리기 쉬운 짝과 구별 포인트", f"- [제철 달력]({BASE}/jecheol/): 달마다 채취하는 산나물·약초", "", "## 약초"]
llms += [f"- [{h['name']}]({url(herb_path(h['name']))}): {ST[h['st']]}" + (f", 다른 이름 {', '.join(h['alias'])}" if h["alias"] else "") for h in rich_list]
open(os.path.join(a.out, "llms.txt"), "w", encoding="utf8").write("\n".join(llms) + "\n")
page("404.html", f"찾는 페이지가 없습니다 | {SITE}", "", '<h1>찾는 페이지가 없습니다</h1><p><a href="./">전체 약초 목록으로 가기</a></p>', index=False)
open(os.path.join(a.out, ".nojekyll"), "w").write("")
print(f"pages: {len(HERBS)} herbs, indexed {len(SITEMAP)}, info docs {len(INFO)}, out={a.out}")
