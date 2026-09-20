#!/usr/bin/env python3
"""Rebuild the English static site using Python 3's standard library."""
from pathlib import Path
from html import escape
from urllib.parse import quote, urljoin, urlsplit
import xml.etree.ElementTree as ET
import json
import re
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs'
DATA = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
PUBS = json.loads((ROOT / 'content/publications.json').read_text(encoding='utf-8'))
JOURNAL_METRICS = json.loads((ROOT / 'content/journal-metrics.json').read_text(encoding='utf-8'))
E = escape
PAGES = ['index', 'news', 'research', 'publications', 'services']
NAV = {'en': ['Home', 'News', 'Research', 'Publications', 'Services'], 'ja': ['ホーム', 'お知らせ', '研究内容', '研究業績', '学会活動']}

def news_items():
    return sorted(DATA['news'], key=lambda item: item['date'], reverse=True)

def news_path(item):
    return 'news/' + item['slug'] + '.html'

def news_publications(item):
    records = {p['id']: p for p in PUBS}
    return [records[publication_id] for publication_id in item['publications']]

def validate_news():
    ids = [p['id'] for p in PUBS]
    if len(ids) != len(set(ids)):
        raise ValueError('Publication IDs must be unique')
    slugs = set()
    for item in news_items():
        slug = item['slug']
        date.fromisoformat(item['date'])
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug) or slug in slugs:
            raise ValueError(f'Invalid or duplicate News slug: {slug}')
        slugs.add(slug)
        if len(item['publications']) != len(set(item['publications'])):
            raise ValueError(f'Duplicate publication reference in News: {slug}')
        missing = set(item['publications']) - set(ids)
        if missing:
            raise ValueError(f'Unknown publication IDs in {slug}: {sorted(missing)}')

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

def site_url(path=''):
    return urljoin(DATA['site_url'].rstrip('/') + '/', path)

def canonical_url(page):
    return site_url('' if page == 'index' else page + '.html')

def validate_search_metadata():
    url = urlsplit(DATA['site_url'])
    if url.scheme != 'https' or not url.netloc or url.query or url.fragment:
        raise ValueError('site_url must be an absolute HTTPS URL without a query or fragment')
    for page in PAGES[1:]:
        if not DATA['page_descriptions'].get(page):
            raise ValueError(f'Missing search description for {page}')

def scholarly_article(p, person_id):
    authors = []
    for raw_name in p['authors'].split(','):
        name = raw_name.strip().removeprefix('and ')
        author = {'@type': 'Person', 'name': name}
        if name == DATA['name']['en']:
            author['@id'] = person_id
        authors.append(author)
    url = canonical_url('publications') + '#' + p['id']
    article = {
        '@type': 'ScholarlyArticle', '@id': url, 'url': url,
        'identifier': p['label'], 'name': p['title'],
        'author': authors, 'description': p['venue'],
    }
    if p['url']:
        article['sameAs'] = p['url']
    if p.get('language'):
        article['inLanguage'] = p['language']
    if p['accepted']:
        article['creativeWorkStatus'] = 'Accepted'
    return article

def structured_data(page, title, description, news_item=None):
    person_id, website_id = site_url('#person'), site_url('#website')
    person = {
        '@type': 'Person', '@id': person_id, 'name': DATA['name']['en'],
        'url': canonical_url('index'),
        'image': site_url('assets/manato-fujimoto.png'),
        'jobTitle': DATA['appointments'][0]['title']['en'],
        'worksFor': {'@type': 'Organization', 'name': DATA['affiliation']['en']},
        'affiliation': {'@type': 'Organization', 'name': DATA['lab']['en'], 'url': DATA['lab_url']},
        'description': DATA['intro']['en'],
        'knowsAbout': [keyword['en'] for keyword in DATA['keywords']],
        'sameAs': [profile['url'] for profile in DATA['profile_links']],
        'email': 'mailto:' + DATA['email'],
    }
    website = {
        '@type': 'WebSite', '@id': website_id, 'url': site_url(),
        'name': DATA['name']['en'], 'inLanguage': 'en',
        'publisher': {'@id': person_id},
    }
    page_type = {'index': 'ProfilePage', 'news': 'CollectionPage', 'research': 'CollectionPage',
                 'publications': 'CollectionPage', 'services': 'WebPage'}.get(page, 'WebPage')
    webpage = {
        '@type': page_type, '@id': canonical_url(page) + '#webpage',
        'url': canonical_url(page), 'name': title, 'description': description,
        'inLanguage': 'en', 'isPartOf': {'@id': website_id},
        'about': {'@id': person_id},
    }
    if news_item is not None:
        webpage['mainEntity'] = {
            '@type': 'Article', 'headline': news_item['text']['en'],
            'datePublished': news_item['date'], 'author': {'@id': person_id},
            'citation': [scholarly_article(p, person_id) for p in news_publications(news_item)],
        }
    elif page == 'index':
        webpage['mainEntity'] = {'@id': person_id}
    elif page == 'publications':
        webpage['mainEntity'] = {
            '@type': 'ItemList', 'name': 'Publications by ' + DATA['name']['en'],
            'numberOfItems': len(PUBS),
            'itemListElement': [
                {'@type': 'ListItem', 'position': i, 'item': scholarly_article(p, person_id)}
                for i, p in enumerate(PUBS, 1)
            ],
        }
    data = {'@context': 'https://schema.org', '@graph': [person, website, webpage]}
    # Keep data inside the JSON-LD script even if a title contains HTML-like text.
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')

def write_discovery_files():
    namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', namespace)
    urls = ET.Element('{' + namespace + '}urlset')
    for page in PAGES + [news_path(item).removesuffix('.html') for item in news_items()]:
        entry = ET.SubElement(urls, '{' + namespace + '}url')
        ET.SubElement(entry, '{' + namespace + '}loc').text = canonical_url(page)
    ET.ElementTree(urls).write(OUT / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    robots = 'User-agent: *\nAllow: /\n\nSitemap: ' + site_url('sitemap.xml') + '\n'
    (OUT / 'robots.txt').write_text(robots, encoding='utf-8')

def shell(page, lang, body, news_item=None):
    root = '../' if lang == 'ja' or news_item is not None else ''
    name = text(DATA['name'], lang)
    active_page = 'news' if news_item is not None else page
    label = NAV[lang][PAGES.index(active_page)]
    title = (news_item['text'][lang] + ' — ' + DATA['name'][lang]) if news_item is not None else (DATA['name'][lang] if page == 'index' else f'{label} — {DATA["name"][lang]}')
    full_title = title + ' | ' + ('大阪公立大学' if lang == 'ja' else 'Osaka Metropolitan University')
    description = news_item['summary'] if news_item is not None else (DATA['description'][lang] if page == 'index' else DATA['page_descriptions'][page])
    canonical = canonical_url(page)
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="10" fill="#111b29"/><text x="32" y="42" text-anchor="middle" fill="#85bcff" font-family="Arial,sans-serif" font-size="28">MF</text></svg>'
    nav = ''.join(f'<li><a href="{root}{p}.html"' + (' aria-current="page"' if active_page == p else '') + f'>{NAV[lang][i]}</a></li>' for i,p in enumerate(PAGES))
    page_scripts = f'\n  <script src="{root}assets/publications.js" defer></script>' if page == 'publications' else ''
    return f'''<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{E(full_title)}</title>
  <meta name="description" content="{E(description, quote=True)}">
  <meta name="author" content="Manato Fujimoto">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
  <link rel="canonical" href="{E(canonical, quote=True)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{text(DATA['name'],lang)}">
  <meta property="og:title" content="{E(full_title, quote=True)}">
  <meta property="og:description" content="{E(description, quote=True)}">
  <meta property="og:url" content="{E(canonical, quote=True)}">
  <meta property="og:image" content="{E(site_url('assets/manato-fujimoto.png'), quote=True)}">
  <meta property="og:image:alt" content="Portrait of Manato Fujimoto">
  <script type="application/ld+json">{structured_data(page, full_title, description, news_item)}</script>
  <meta name="theme-color" content="#090b10">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,{quote(svg)}">
  <link rel="stylesheet" href="{root}assets/style.css">
  <link rel="stylesheet" href="{root}assets/news.css">{page_scripts}
</head>
<body>
  <a class="skip-link" href="#main">{'本文へ移動' if lang == 'ja' else 'Skip to content'}</a>
  <header class="site-header"><div class="container header-inner">
    <a class="brand" href="{root}index.html"><span class="brand-mark" aria-hidden="true">MF</span><span>Manato Fujimoto</span></a>
    <nav aria-label="{'メインナビゲーション' if lang == 'ja' else 'Main navigation'}"><ul class="navigation">{nav}</ul></nav>
  </div></header>
  <main id="main" class="container{' news-article-page' if news_item is not None else ''}">{body}</main>
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
    profile_links = ''.join(link(profile['url'], E(profile['label']), 'profile-link') for profile in DATA['profile_links'])
    body = f'''<section class="profile" aria-label="{'プロフィール' if ja else 'Profile'}">
  <div><p class="eyebrow">Osaka Metropolitan University</p>{name}
    <p class="position">{text(DATA['position'],lang)}</p>
    <p class="affiliation">{text(DATA['affiliation'],lang)}<br>{link(DATA['lab_url'],text(DATA['lab'],lang))}</p>
    <p class="lead">{text(DATA['intro'],lang)}</p>
    <dl class="contact-list"><dt>Email</dt><dd>{link('mailto:'+DATA['email'], E(DATA['email'].replace('@',' [at] ')))}</dd>
    <dt>{'所在地' if ja else 'Address'}</dt><dd><address>{text(DATA['address'],lang)}</address></dd></dl>
    <nav class="profile-links" aria-label="Research profiles">{profile_links}</nav>
  </div>
  <figure class="profile-photo"><img src="{root}assets/manato-fujimoto.png" width="620" height="560" alt="{'藤本まなとのポートレート' if ja else 'Portrait of Manato Fujimoto'}" fetchpriority="high"><figcaption>{'大阪公立大学<br>スマートプラットフォーム研究室' if ja else 'Smart Platform Research Group<br>Osaka Metropolitan University'}</figcaption></figure>
</section>'''
    about = ''.join(f'<p>{text(p,lang)}</p>' for p in DATA['about'])
    about += '<ul class="keywords">'+''.join(f'<li>{text(t,lang)}</li>' for t in DATA['keywords'])+'</ul>'
    body += section('プロフィール' if ja else 'About', '<div class="about-copy">'+about+'</div>')
    news_list = '<ul class="news-list">'+''.join(f'<li><time datetime="{E(n["date"])}">{E(n["date"].replace("-","."))}</time><span>{link(news_path(n),text(n["text"],lang))}</span></li>' for n in news_items())+'</ul>'
    all_news = link('news.html', 'View all news →', 'news-all-link')
    body += f'<section class="section" id="recent-news"><div class="section-heading news-home-heading"><h2>{"お知らせ" if ja else "Recent News"}</h2>{all_news}</div>{news_list}</section>'
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
    body += '<div class="research-grid">'
    for i,r in enumerate(DATA['research'],1):
        related = ''.join(link('publications.html#'+E(k),E(next(p['title'] for p in PUBS if p['id']==k))) for k in r['publications'])
        body += f'<section class="research-row" id="{E(r["id"])}" aria-labelledby="{E(r["id"])}-title"><p class="research-number">{i:02}</p><h2 id="{E(r["id"])}-title">{text(r["title"],lang)}</h2><p class="research-description">{text(r["description"],lang)}</p><p class="research-topics">{text(r["topics"],lang)}</p><details class="related"><summary>{"関連論文" if ja else "Related publications"} <span class="related-count">({len(r["publications"])})</span></summary><div class="related-links">{related}</div></details></section>'
    return body + '</div>'

def journal_metric(p):
    if p['type'] != 'journal':
        return None
    matches = [m for m in JOURNAL_METRICS['journals'] if any(
        p['venue'].startswith(m['venue_name'] + separator) for separator in (',', ' —')
    ) or p['venue'] == m['venue_name']]
    if len(matches) > 1:
        raise ValueError(f'Ambiguous journal metric for {p["id"]}')
    return matches[0] if matches else None

def publication_item(p, lang, *, title_url=None, id_prefix=''):
    title = E(p['title'])
    target = p['url'] if title_url is None else title_url
    if target:
        title = link(target,title)
    tags = ''
    if p['accepted']:
        tags += f'<span class="status">{"採択済み" if lang == "ja" else "Accepted"}</span>'
    if p['type'] == 'journal' and p.get('language') == 'ja':
        tags += '<span class="status status-japanese">Japanese</span>'
    if p['type'] == 'journal' and p.get('corresponding'):
        tags += '<span class="status status-corresponding">Corresponding</span>'
    if p['type'] == 'journal' and p.get('international_coauthorship'):
        tags += '<span class="status status-international">International coauthorship</span>'
    authors = E(p['authors'])
    metric = journal_metric(p)
    metrics = ''
    if metric:
        when = str(metric['year'])
        metric_label = f'Impact Factor: <strong>{E(metric["value"])}</strong> <span class="metric-year">({E(when)})</span>'
        metrics = '<p class="pub-metrics">' + link(metric['source_url'], metric_label, 'impact-factor') + '</p>'
    if tags:
        tags = '<div class="pub-tags" aria-label="Publication tags">' + tags + '</div>'
    return f'<li class="publication" id="{E(id_prefix + p["id"])}"><span class="pub-index">{E(p["label"])}</span><div class="pub-content"><h3 class="pub-title">{title}</h3><p class="pub-authors">{authors}</p><p class="pub-venue">{E(p["venue"])}</p>{metrics}{tags}</div></li>'

def news_meta(item):
    return f'<div class="news-card-meta"><span class="news-category">{E(item["category"])}</span><time class="news-date" datetime="{E(item["date"])}">{E(item["date"].replace("-", "."))}</time></div>'

def news(lang):
    body = intro('News', eyebrow='Latest updates')
    items = news_items()
    for year in sorted({item['date'][:4] for item in items}, reverse=True):
        yearly = [item for item in items if item['date'].startswith(year)]
        body += f'<section class="news-archive" aria-labelledby="news-year-{E(year)}"><div class="section-heading"><h2 id="news-year-{E(year)}">{E(year)}</h2><span class="note">{len(yearly)} updates</span></div><ol class="news-grid">'
        for item in yearly:
            summary = news_meta(item) + f'<h3 class="news-card-title">{text(item["text"],lang)}</h3><p class="news-card-excerpt">{E(item["summary"])}</p><span class="news-read-link">Read article →</span>'
            body += f'<li class="news-card" id="news-{E(item["date"])}">{link(news_path(item), summary, "news-card-link")}</li>'
        body += '</ol></section>'
    return body + '<p class="news-return">' + link('index.html#recent-news', '← Back to Recent News') + '</p>'

def news_article(item, lang):
    breadcrumb = link('../index.html', 'Home') + '<span aria-hidden="true">/</span>' + link('../news.html', 'News') + '<span aria-hidden="true">/</span>' + f'<span aria-current="page">{E(item["date"].replace("-", "."))}</span>'
    body = f'<nav class="article-breadcrumb" aria-label="Breadcrumb">{breadcrumb}</nav><article aria-labelledby="news-article-title"><header class="article-heading">{news_meta(item)}<h1 id="news-article-title">{text(item["text"],lang)}</h1></header>'
    # News stores only publication IDs; every bibliographic field comes from PUBS.
    records = news_publications(item)
    citations = ''.join(publication_item(p, lang, title_url='../publications.html#' + p['id'], id_prefix='news-') for p in records)
    publication_heading = heading('Publications' if len(records) != 1 else 'Publication')
    body += '<div class="article-body"><div class="news-announcement">' + item['body_html'] + publication_heading + '<ol class="publications news-publications">' + citations + '</ol></div></div>'
    body += '<footer class="article-end"><p class="news-return">' + link('../news.html', '← All news') + '</p><nav class="article-neighbors" aria-label="Other news articles">'
    items = news_items()
    index = next(i for i, other in enumerate(items) if other['slug'] == item['slug'])
    if index > 0:
        newer = items[index - 1]
        body += link(newer['slug'] + '.html', '<span>← Newer article</span>' + text(newer['text'], lang), 'article-neighbor')
    if index + 1 < len(items):
        older = items[index + 1]
        body += link(older['slug'] + '.html', '<span>Older article →</span>' + text(older['text'], lang), 'article-neighbor article-neighbor-older')
    return body + '</nav></footer></article>'

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
    return body

def services(lang):
    ja = lang == 'ja'
    body = intro('学会活動・受賞' if ja else 'Services & Awards', '主な学会活動と受賞歴。' if ja else 'Selected professional services and awards.','Academic community')
    rows = '<ul class="service-list">'
    for s in DATA['services']:
        rows += f'<li><span class="year">{E(s["year"])}</span><div><h3>{text(s["role"],lang)}</h3><p>{text(s["event"],lang)}</p></div></li>'
    body += section('国際会議・研究会運営' if ja else 'Selected Conference Organization',rows+'</ul>')
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
    validate_news()
    validate_search_metadata()
    OUT.mkdir(parents=True,exist_ok=True)
    for page, render in [('index',home),('news',news),('research',research),('publications',publications),('services',services)]:
        (OUT / (page+'.html')).write_text(shell(page,'en',render('en')),encoding='utf-8')
    (OUT / 'news').mkdir(parents=True, exist_ok=True)
    for item in news_items():
        path = news_path(item)
        (OUT / path).write_text(shell(path.removesuffix('.html'), 'en', news_article(item, 'en'), item), encoding='utf-8')
    for page in PAGES:
        (OUT / 'ja' / (page+'.html')).unlink(missing_ok=True)
    japanese_output = OUT / 'ja'
    if japanese_output.is_dir() and not any(japanese_output.iterdir()):
        japanese_output.rmdir()
    (OUT / '.nojekyll').touch()
    write_discovery_files()
    print(f'Generated {len(PAGES) + len(news_items())} English HTML pages with {len(PUBS)} publication records.')

if __name__=='__main__':
    main()
