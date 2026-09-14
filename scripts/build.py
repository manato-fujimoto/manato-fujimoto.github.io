#!/usr/bin/env python3
"""Rebuild the English static site using Python 3's standard library."""
from pathlib import Path
from html import escape
from urllib.parse import quote
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs'
DATA = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
PUBS = json.loads((ROOT / 'content/publications.json').read_text(encoding='utf-8'))
JOURNAL_METRICS = json.loads((ROOT / 'content/journal-metrics.json').read_text(encoding='utf-8'))
E = escape
PAGES = ['index', 'research', 'publications', 'services']
NAV = {'en': ['Home', 'Research', 'Publications', 'Services'], 'ja': ['ホーム', '研究内容', '研究業績', '学会活動']}

def validate_journal_metrics():
    year = JOURNAL_METRICS['metric_year']
    if not isinstance(year, int):
        raise ValueError('Journal Impact Factor metric_year must be an integer')
    for metric in JOURNAL_METRICS['journals']:
        if metric.get('year') != year:
            raise ValueError(f'Journal Impact Factor for {metric["venue_name"]} must use metric year {year}')

def text(value, lang):
    return E(value[lang] if isinstance(value, dict) else str(value))

def link(url, label, cls=''):
    return f'<a href="{E(url, quote=True)}"' + (f' class="{cls}"' if cls else '') + f'>{label}</a>'

def heading(title, extra=''):
    return f'<div class="section-heading"><h2>{title}</h2>{extra}</div>'

def section(title, body, id=''):
    return f'<section class="section"' + (f' id="{id}"' if id else '') + f'>{heading(title)}{body}</section>'

def source_note(url, lang):
    return '<p class="source-note">' + link(url, '掲載情報の出典' if lang == 'ja' else 'Source') + '</p>'

def shell(page, lang, body):
    root = '../' if lang == 'ja' else ''
    name = text(DATA['name'], lang)
    label = NAV[lang][PAGES.index(page)]
    title = name if page == 'index' else f'{label} — {name}'
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="10" fill="#111b29"/><text x="32" y="42" text-anchor="middle" fill="#85bcff" font-family="Arial,sans-serif" font-size="28">MF</text></svg>'
    nav = ''.join(f'<li><a href="{p}.html"' + (' aria-current="page"' if page == p else '') + f'>{NAV[lang][i]}</a></li>' for i,p in enumerate(PAGES))
    return f'''<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | {'大阪公立大学' if lang == 'ja' else 'Osaka Metropolitan University'}</title>
  <meta name="description" content="{text(DATA['description'],lang)}">
  <meta name="author" content="Manato Fujimoto">
  <meta name="theme-color" content="#090b10">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,{quote(svg)}">
  <link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
  <a class="skip-link" href="#main">{'本文へ移動' if lang == 'ja' else 'Skip to content'}</a>
  <header class="site-header"><div class="container header-inner">
    <a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">MF</span><span>Manato Fujimoto</span></a>
    <nav aria-label="{'メインナビゲーション' if lang == 'ja' else 'Main navigation'}"><ul class="navigation">{nav}</ul></nav>
  </div></header>
  <main id="main" class="container">{body}</main>
  <footer class="site-footer"><div class="container footer-inner">
    <p>© {E(DATA['copyright_year'])} {name}<br>{'大阪公立大学 大学院情報学研究科' if lang == 'ja' else 'Graduate School of Informatics, Osaka Metropolitan University'}</p>
    <div class="footer-links">{link(DATA['lab_url'], '研究室' if lang == 'ja' else 'Laboratory')}{link('mailto:' + DATA['email'], 'お問い合わせ' if lang == 'ja' else 'Contact')}<a href="#main">{'ページ上部へ' if lang == 'ja' else 'Back to top'}</a></div>
  </div></footer>
</body>
</html>
'''

def timeline(items, lang):
    return '<dl class="timeline">' + ''.join(f'<div class="timeline-row"><dt>{text(i["period"],lang)}</dt><dd>{text(i["title"],lang)}<span>{text(i["place"],lang)}</span></dd></div>' for i in items) + '</dl>'

def home(lang):
    ja = lang == 'ja'
    root = '../' if ja else ''
    name = '<h1>藤本 まなと</h1><p class="name-en" lang="en">Manato Fujimoto</p>' if ja else '<h1>Manato Fujimoto</h1>'
    body = f'''<section class="profile" aria-label="{'プロフィール' if ja else 'Profile'}">
  <div><p class="eyebrow">Osaka Metropolitan University</p>{name}
    <p class="position">{text(DATA['position'],lang)}</p>
    <p class="affiliation">{text(DATA['affiliation'],lang)}<br>{link(DATA['lab_url'],text(DATA['lab'],lang))}</p>
    <p class="lead">{text(DATA['intro'],lang)}</p>
    <dl class="contact-list"><dt>Email</dt><dd>{link('mailto:'+DATA['email'], E(DATA['email'].replace('@',' [at] ')))}</dd>
    <dt>{'所在地' if ja else 'Address'}</dt><dd><address>{text(DATA['address'],lang)}</address></dd></dl>
  </div>
  <figure class="profile-photo"><img src="{root}assets/manato-fujimoto.png" width="620" height="560" alt="{'藤本まなとのポートレート' if ja else 'Portrait of Manato Fujimoto'}" fetchpriority="high"><figcaption>{'大阪公立大学<br>スマートプラットフォーム研究室' if ja else 'Smart Platform Research Group<br>Osaka Metropolitan University'}</figcaption></figure>
</section>'''
    about = ''.join(f'<p>{text(p,lang)}</p>' for p in DATA['about'])
    about += '<ul class="keywords">'+''.join(f'<li>{text(t,lang)}</li>' for t in DATA['keywords'])+'</ul>'
    body += section('プロフィール' if ja else 'About', '<div class="about-copy">'+about+'</div>')
    news = '<ul class="news-list">'+''.join(f'<li><time datetime="{E(n["date"])}">{E(n["date"].replace("-","."))}</time><span>{link(n["url"],text(n["text"],lang))}</span></li>' for n in DATA['news'])+'</ul>'
    body += section('お知らせ' if ja else 'Recent News',news)
    body += '<div class="two-columns">'+section('職歴' if ja else 'Appointments',timeline(DATA['appointments'],lang))+section('学歴' if ja else 'Education',timeline(DATA['education'],lang))+'</div>'
    a = DATA['awards'][0]
    award = f'<div class="award-highlight"><p class="award-year">{E(a["year"])}</p><h3>{link(a["url"],text(a["title"],lang))}</h3><p>{text(a["detail"],lang)}</p></div>'
    body += section('主な受賞' if ja else 'Selected Award',award)
    return body

def intro(title, subtitle='', eyebrow=''):
    return '<header class="page-intro">'+(f'<p class="eyebrow">{eyebrow}</p>' if eyebrow else '')+f'<h1>{title}</h1>'+(f'<p class="lead">{subtitle}</p>' if subtitle else '')+'</header>'

def research(lang):
    ja = lang == 'ja'
    body = intro('研究内容' if ja else 'Research', text(DATA['research_intro'],lang),'Research interests')
    for i,r in enumerate(DATA['research'],1):
        related = ''.join(link('publications.html#'+E(k),E(next(p['title'] for p in PUBS if p['id']==k))) for k in r['publications'])
        body += f'<section class="research-row" id="{E(r["id"])}"><div><p class="research-number">{i:02}</p><h2>{text(r["title"],lang)}</h2></div><div><p>{text(r["description"],lang)}</p><h3>{"主な取り組み" if ja else "Topics"}</h3><p>{text(r["topics"],lang)}</p><div class="related"><h3>{"関連論文" if ja else "Related publications"}</h3>{related}</div></div></section>'
    return body

def journal_metric(p):
    if p['type'] != 'journal':
        return None
    matches = [m for m in JOURNAL_METRICS['journals'] if any(
        p['venue'].startswith(m['venue_name'] + separator) for separator in (',', ' —')
    ) or p['venue'] == m['venue_name']]
    if len(matches) > 1:
        raise ValueError(f'Ambiguous journal metric for {p["id"]}')
    return matches[0] if matches else None

def publication_item(p, lang):
    title = E(p['title'])
    if p['url']:
        title = link(p['url'],title)
    if p['accepted']:
        title += f'<span class="status">{"採択済み" if lang == "ja" else "Accepted"}</span>'
    if p['type'] == 'journal' and p.get('language') == 'ja':
        title += '<span class="status">Japanese</span>'
    if p['type'] == 'journal' and p.get('corresponding'):
        title += '<span class="status">Corresponding</span>'
    if p['type'] == 'journal' and p.get('international_coauthorship'):
        title += '<span class="status status-international">International coauthorship</span>'
    authors = E(p['authors'])
    metric = journal_metric(p)
    metrics = ''
    if metric:
        when = str(metric['year'])
        metric_label = f'Impact Factor: <strong>{E(metric["value"])}</strong> <span class="metric-year">({E(when)})</span>'
        metrics = '<p class="pub-metrics">' + link(metric['source_url'], metric_label, 'impact-factor') + '</p>'
    return f'<li class="publication" id="{E(p["id"])}"><span class="pub-index">{E(p["label"])}</span><h3 class="pub-title">{title}</h3><p class="pub-authors">{authors}</p><p class="pub-venue">{E(p["venue"])}</p>{metrics}</li>'

def publications(lang):
    ja = lang == 'ja'
    body = intro('研究業績' if ja else 'Publications', eyebrow='Publications')
    groups = [('journal','学術論文' if ja else 'Journal Articles'),('conference','国際会議論文' if ja else 'International Conference Proceedings')]
    body += '<nav class="section-nav" aria-label="'+('業績の種別' if ja else 'Publication categories')+'">'+''.join(link('#'+key,label) for key,label in groups)+'</nav>'
    for kind,label in groups:
        items = [p for p in PUBS if p['type']==kind]
        body += f'<section class="publication-group" id="{kind}">'+heading(label,f'<span class="note">{len(items)} {"件" if ja else "entries"}</span>')
        if kind == 'journal':
            year, release = JOURNAL_METRICS['metric_year'], JOURNAL_METRICS['release_year']
            metric_note = f'掲載誌の{year}年Journal Impact Factor（{release}年公表）を、確認できた誌に表示しています。数値から出典を確認できます。' if ja else f'Journal Impact Factors are {year} values, released in {release}, shown where verified. Each value links to its source.'
            body += f'<p class="metrics-note">{metric_note}</p>'
        body += '<ol class="publications">'+''.join(publication_item(p,lang) for p in items)+'</ol>'
        body += '</section>'
    body += '<p class="source-note">'+('国内研究会発表等は' if ja else 'For domestic presentations and additional records, see the ')+link(DATA['publications_url'],'業績一覧' if ja else 'full publication record')+('もご覧ください。' if ja else '.')+'</p>'
    return body

def services(lang):
    ja = lang == 'ja'
    body = intro('学会活動・受賞' if ja else 'Services & Awards', '主な学会活動と受賞歴。' if ja else 'Selected professional services and awards.','Academic community')
    rows = '<ul class="service-list">'
    for s in DATA['services']:
        rows += f'<li><span class="year">{E(s["year"])}</span><div><h3>{text(s["role"],lang)}</h3><p>{text(s["event"],lang)}</p></div></li>'
    body += section('国際会議・研究会運営' if ja else 'Conference Organization',rows+'</ul>')
    rows = '<ul class="service-list">'
    for a in sorted(DATA['awards'], key=lambda award: int(award['year']), reverse=True):
        title = text(a['title'], lang)
        if a.get('url'):
            title = link(a['url'], title)
        rows += f'<li><span class="year">{E(a["year"])}</span><div><h3>{title}</h3><p>{text(a["detail"],lang)}</p></div></li>'
    body += section('主な受賞' if ja else 'Selected Awards',rows+'</ul>')
    member = '<ul class="memberships">'+''.join(f'<li>{link(m["url"],text(m["name"],lang))}</li>' for m in DATA['memberships'])+'</ul>'
    body += section('所属学会' if ja else 'Memberships',member)
    return body

def main():
    validate_journal_metrics()
    OUT.mkdir(parents=True,exist_ok=True)
    for page, render in [('index',home),('research',research),('publications',publications),('services',services)]:
        (OUT / (page+'.html')).write_text(shell(page,'en',render('en')),encoding='utf-8')
    for page in PAGES:
        (OUT / 'ja' / (page+'.html')).unlink(missing_ok=True)
    japanese_output = OUT / 'ja'
    if japanese_output.is_dir() and not any(japanese_output.iterdir()):
        japanese_output.rmdir()
    (OUT / '.nojekyll').touch()
    print(f'Generated 4 English HTML pages with {len(PUBS)} publication records.')

if __name__=='__main__':
    main()
