#!/usr/bin/env python3
"""Rebuild the English and Japanese static site using Python 3's standard library."""
from pathlib import Path
from html import escape
from hashlib import sha256
from urllib.parse import quote, urljoin, urlsplit
import xml.etree.ElementTree as ET
import json
import unicodedata
import re
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs'
DATA = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
PUBS = json.loads((ROOT / 'content/publications.json').read_text(encoding='utf-8'))
JOURNAL_METRICS = json.loads((ROOT / 'content/journal-metrics.json').read_text(encoding='utf-8'))
FUNDING = json.loads((ROOT / 'content/funding.json').read_text(encoding='utf-8'))
E = escape
PAGES = ['index', 'news', 'research', 'publications', 'services']
NAV = {'en': ['Home', 'News', 'Research', 'Publications', 'Services'], 'ja': ['ホーム', 'お知らせ', '研究内容', '研究業績', '学会活動']}
LANGS = ['en', 'ja']
CATEGORY_JA = {'Journal': '論文誌', 'Conference': '国際会議'}

def category_label(item, lang):
    return CATEGORY_JA.get(item['category'], item['category']) if lang == 'ja' else item['category']

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

def publication_field(p, field, lang):
    if lang == 'ja' and p['type'] == 'journal' and p.get('language') == 'ja':
        return p.get(field + '_ja', p[field])
    return p[field]

def publication_title(p, lang):
    return publication_field(p, 'title', lang)

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

def page_path(page, lang='en'):
    """Path from the site root. Japanese pages live under ja/ with the same file names."""
    return ('ja/' if lang == 'ja' else '') + ('' if page == 'index' else page + '.html')

def canonical_url(page, lang='en'):
    return site_url(page_path(page, lang))

def page_description(page, lang, news_item=None):
    if news_item is not None:
        if lang == 'ja':
            return news_item['text']['ja'] + ' ' + ' ／ '.join(publication_title(p, lang) for p in news_publications(news_item))
        return news_item['summary']
    if page == 'index':
        return DATA['description'][lang]
    return DATA['page_descriptions_ja' if lang == 'ja' else 'page_descriptions'][page]

def last_modified(news_item=None):
    """Date of the last substantive change, for sitemap lastmod and dateModified."""
    if news_item is not None:
        return news_item.get('updated', news_item['date'])
    dates = [DATA['content_checked'], news_items()[0]['date']]
    if DATA.get('last_updated'):
        dates.append(DATA['last_updated'])
    return max(dates)

def iso_datetime(day):
    """Structured-data date-time: Google expects a time and a time zone, not a bare date."""
    return f'{day}T00:00:00+09:00'

# Search and AI crawlers that are named explicitly in robots.txt. All are allowed.
AI_CRAWLERS = ['Googlebot', 'Bingbot', 'Google-Extended', 'GPTBot', 'OAI-SearchBot', 'ChatGPT-User',
               'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'PerplexityBot', 'Perplexity-User',
               'Applebot', 'Applebot-Extended', 'Amazonbot', 'DuckAssistBot', 'meta-externalagent',
               'MistralAI-User', 'CCBot']

def validate_search_metadata():
    url = urlsplit(DATA['site_url'])
    if url.scheme != 'https' or not url.netloc or url.query or url.fragment:
        raise ValueError('site_url must be an absolute HTTPS URL without a query or fragment')
    for page in PAGES[1:]:
        if not DATA['page_descriptions'].get(page) or not DATA['page_descriptions_ja'].get(page):
            raise ValueError(f'Missing search description for {page}')
    verification = DATA.get('google_site_verification', '')
    if not isinstance(verification, str) or (verification and not re.fullmatch(r'[A-Za-z0-9_-]+', verification)):
        raise ValueError('google_site_verification must contain only the token from the Google HTML tag, or be empty')
    for key in ('content_checked', 'last_updated'):
        if DATA.get(key):
            date.fromisoformat(DATA[key])

def scholarly_article(p, person_id, lang='en'):
    authors = []
    for raw_name in re.split(r'[,，、]', publication_field(p, 'authors', lang)):
        name = raw_name.strip().removeprefix('and ')
        author = {'@type': 'Person', 'name': name}
        if name == DATA['name']['en'] or re.sub(r'\s+', '', name) == re.sub(r'\s+', '', DATA['name']['ja']):
            author['@id'] = person_id
        authors.append(author)
    url = canonical_url('publications') + '#' + p['id']
    article = {
        '@type': 'ScholarlyArticle', '@id': url, 'url': url,
        'identifier': p['label'], 'name': publication_title(p, lang),
        'author': authors, 'description': publication_field(p, 'venue', lang),
    }
    if p['url']:
        article['sameAs'] = p['url']
    if p.get('language'):
        article['inLanguage'] = p['language']
    if not p['accepted'] and not p.get('scheduled') and re.fullmatch(r'\d{4}', str(p['year'])):
        article['datePublished'] = str(p['year'])
    if p['accepted']:
        article['creativeWorkStatus'] = 'Accepted'
    if p.get('scheduled'):
        article['creativeWorkStatus'] = 'Scheduled presentation'
    return article

def structured_data(page, title, description, news_item=None, lang='en'):
    person_id, website_id = site_url('#person'), site_url('#website')
    person = {
        '@type': 'Person', '@id': person_id, 'name': DATA['name']['en'],
        'alternateName': [DATA['name']['ja'], DATA['name']['ja'].replace(' ', '')],
        'url': canonical_url('index'),
        'image': site_url('assets/manato-fujimoto.png'),
        'jobTitle': DATA['appointments'][0]['title']['en'],
        'worksFor': {'@type': 'Organization', 'name': DATA['affiliation']['en'],
                     'alternateName': DATA['affiliation']['ja']},
        'affiliation': {'@type': 'Organization', 'name': DATA['lab']['en'], 'url': DATA['lab_url']},
        'description': DATA['intro']['en'],
        'knowsAbout': [keyword['en'] for keyword in DATA['keywords']],
        'sameAs': [profile['url'] for profile in DATA['profile_links']],
        'email': 'mailto:' + DATA['email'],
        'honorificSuffix': 'Ph.D.',
        'award': [f"{a['title']['en']} ({a['year']})" for a in sorted(DATA['awards'], key=lambda a: a['year'], reverse=True)],
        'memberOf': [{'@type': 'Organization', 'name': m['name']['en'], 'url': m['url']} for m in DATA['memberships']],
        'hasCredential': [{'@type': 'EducationalOccupationalCredential', 'name': e['title']['en'],
                           'credentialCategory': 'degree',
                           'recognizedBy': {'@type': 'CollegeOrUniversity', 'name': e['place']['en'].split(', ')[-1]}}
                          for e in DATA['education']],
        'workLocation': {'@type': 'Place', 'address': DATA['address']['en']},
    }
    university, alma_mater = DATA.get('university'), DATA.get('alma_mater')
    if university:
        person['worksFor']['parentOrganization'] = {
            '@type': 'CollegeOrUniversity', 'name': university['en'],
            'alternateName': university['ja'], 'url': university['url']}
    if alma_mater:
        person['alumniOf'] = {'@type': 'CollegeOrUniversity', 'name': alma_mater['en'],
                              'alternateName': alma_mater['ja'], 'url': alma_mater['url']}
    website = {
        '@type': 'WebSite', '@id': website_id, 'url': site_url(),
        'name': DATA['name']['en'], 'alternateName': DATA['name']['ja'].replace(' ', ''),
        'description': DATA['description']['en'], 'inLanguage': LANGS,
        'publisher': {'@id': person_id},
    }
    page_type = {'index': 'ProfilePage', 'news': 'CollectionPage', 'research': 'CollectionPage',
                 'publications': 'CollectionPage', 'services': 'WebPage'}.get(page, 'WebPage')
    webpage = {
        '@type': page_type, '@id': canonical_url(page, lang) + '#webpage',
        'url': canonical_url(page, lang), 'name': title, 'description': description,
        'inLanguage': lang, 'isPartOf': {'@id': website_id},
        'about': {'@id': person_id},
        'dateModified': iso_datetime(last_modified(news_item)),
    }
    graph = [person, website, webpage]
    if page != 'index':
        # Breadcrumb trail: Home > section (> article).
        section_page = 'news' if news_item is not None else page
        trail = [(NAV[lang][0], canonical_url('index', lang)), (NAV[lang][PAGES.index(section_page)], canonical_url(section_page, lang))]
        if news_item is not None:
            trail.append((news_item['text'][lang], canonical_url(page, lang)))
        breadcrumb_id = canonical_url(page, lang) + '#breadcrumb'
        graph.append({'@type': 'BreadcrumbList', '@id': breadcrumb_id, 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': name, 'item': url} for i, (name, url) in enumerate(trail, 1)]})
        webpage['breadcrumb'] = {'@id': breadcrumb_id}
    if news_item is not None:
        article = {
            '@type': 'Article', '@id': canonical_url(page, lang) + '#article',
            'headline': news_item['text'][lang], 'description': description,
            'datePublished': iso_datetime(news_item['date']), 'dateModified': iso_datetime(last_modified(news_item)),
            'inLanguage': lang, 'author': {'@id': person_id}, 'publisher': {'@id': person_id},
            'mainEntityOfPage': {'@id': canonical_url(page, lang) + '#webpage'},
            'citation': [scholarly_article(p, person_id, lang) for p in news_publications(news_item)],
        }
        image = news_item.get('social_image') or news_item.get('thumbnail')
        if image:
            article['image'] = {'@type': 'ImageObject', 'url': site_url(image['src']),
                                'width': image['width'], 'height': image['height']}
        webpage['mainEntity'] = article
    elif page == 'index':
        webpage['mainEntity'] = {'@id': person_id}
    elif page == 'publications':
        webpage['mainEntity'] = {
            '@type': 'ItemList', 'name': 'Publications by ' + DATA['name']['en'],
            'numberOfItems': len(PUBS),
            'itemListElement': [
                {'@type': 'ListItem', 'position': i, 'item': scholarly_article(p, person_id, lang)}
                for i, p in enumerate(PUBS, 1)
            ],
        }
    data = {'@context': 'https://schema.org', '@graph': graph}
    # Keep data inside the JSON-LD script even if a title contains HTML-like text.
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')

def write_discovery_files():
    namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', namespace)
    urls = ET.Element('{' + namespace + '}urlset')
    by_page = {news_path(item).removesuffix('.html'): item for item in news_items()}
    for lang in LANGS:
        for page in PAGES + [news_path(item).removesuffix('.html') for item in news_items()]:
            entry = ET.SubElement(urls, '{' + namespace + '}url')
            ET.SubElement(entry, '{' + namespace + '}loc').text = canonical_url(page, lang)
            ET.SubElement(entry, '{' + namespace + '}lastmod').text = last_modified(by_page.get(page))
    ET.ElementTree(urls).write(OUT / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    robots = ('# Search engines and AI search/assistant crawlers are welcome to crawl this site.\n'
              + ''.join(f'User-agent: {agent}\n' for agent in AI_CRAWLERS) + 'Allow: /\n\n'
              + 'User-agent: *\nAllow: /\n\nSitemap: ' + site_url('sitemap.xml') + '\n')
    (OUT / 'robots.txt').write_text(robots, encoding='utf-8')
    write_llms_files()

def publication_line(p):
    status = ' [Accepted]' if p['accepted'] else ' [Scheduled presentation]' if p.get('scheduled') else ''
    awards = ''.join(f' [{award}]' for award in p.get('awards', []))
    if p.get('invited'):
        status = ' [Invited paper]' + status
    title = f'[{p["title"]}]({p["url"]})' if p['url'] else p['title']
    return f'- {p["label"]}. {p["authors"]}. {title}. {p["venue"]}{status}{awards}'

def write_llms_files():
    """Plain-Markdown summaries for AI assistants: llms.txt (index) and llms-full.txt (all records)."""
    name, name_ja = DATA['name']['en'], DATA['name']['ja'].replace(' ', '')
    groups = [('journal', 'Journal Articles'), ('conference', 'International Conference Proceedings'),
              ('domestic-conference', 'Domestic Conference Presentations')]
    counts = {kind: sum(p['type'] == kind for p in PUBS) for kind, _ in groups}
    updated = last_modified()
    head = [
        f'# {name}（{name_ja}）',
        '',
        f'> {name}（{name_ja}） is an {DATA["appointments"][0]["title"]["en"]} (Ph.D. in Engineering) at the '
        f'{DATA["affiliation"]["en"]}（{DATA["affiliation"]["ja"]}）, Japan, and a member of the {DATA["lab"]["en"]}'
        f'（{DATA["lab"]["ja"]}）. Research areas: ' + ', '.join(k['en'] for k in DATA['keywords'])
        + '（' + '、'.join(k['ja'] for k in DATA['keywords']) + '）.',
        '',
        f'This is the official personal website of {name}. Last updated: {updated}.',
        '',
    ]
    facts = ['## Key facts', '',
             f'- Name: {name} (Japanese: {DATA["name"]["ja"]})',
             f'- Position: {DATA["position"]["en"]}',
             f'- Affiliation: {DATA["affiliation"]["en"]}',
             f'- Laboratory: [{DATA["lab"]["en"]}]({DATA["lab_url"]})',
             f'- Address: {DATA["address"]["en"]}',
             f'- Contact: {DATA["email"].replace("@", " [at] ")}',
             '- Research keywords: ' + ', '.join(k['en'] for k in DATA['keywords']),
             '- Publications listed on this site: ' + ', '.join(f'{counts[kind]} {label.lower()}' for kind, label in groups),
             ''] + [f'- {profile["label"]}: {profile["url"]}' for profile in DATA['profile_links']] + ['']
    pages = ['## Pages', '',
             f'- [Home]({canonical_url("index")}): {DATA["description"]["en"]}'] + [
             f'- [{NAV["en"][PAGES.index(page)]}]({canonical_url(page)}): {DATA["page_descriptions"][page]}'
             for page in ['research', 'publications', 'services', 'news']] + [
             f'- [日本語版 / Japanese version]({canonical_url("index", "ja")}): {DATA["description"]["ja"]}'] + [
             f'- [{NAV["ja"][PAGES.index(page)]}（日本語）]({canonical_url(page, "ja")}): {DATA["page_descriptions_ja"][page]}'
             for page in ['research', 'publications', 'services', 'news']] + ['']
    about = ['## About', ''] + [p['en'] for p in DATA['about']] + ['']
    career = ['## Employment', ''] + [f'- {a["period"]["en"]}: {a["title"]["en"]}, {" ".join(a["place"]["en"].split())}' for a in DATA['appointments']]
    career += ['', '## Education', ''] + [f'- {e["period"]["en"]}: {e["title"]["en"]}, {e["place"]["en"]}' for e in DATA['education']]
    career += ['', '## Awards', ''] + [f'- {a["year"]}: {a["title"]["en"]}. {a["detail"]["en"]}' for a in sorted(DATA['awards'], key=lambda a: a['year'], reverse=True)] + ['']
    research_md = ['## Research', '', DATA['research_intro']['en'], '']
    for r in DATA['research']:
        research_md += [f'### {r["title"]["en"]}', '', r['description']['en'], '', 'Topics: ' + r['topics']['en'], '']
    news_md = ['## Recent news', ''] + [f'- {n["date"]}: [{n["text"]["en"]}]({site_url(news_path(n))}) {n["summary"]}' for n in news_items()[:10]] + ['']
    optional = ['## Optional', '', f'- [Full text for AI assistants]({site_url("llms-full.txt")}): profile, research themes, and the complete publication list in Markdown',
                f'- [Sitemap]({site_url("sitemap.xml")})', '']
    (OUT / 'llms.txt').write_text('\n'.join(head + facts + pages + about + research_md + news_md + optional), encoding='utf-8')
    full = head + facts + about + career + research_md
    full += ['## Professional service', ''] + [f'- {s["year"]}: {s["role"]["en"]}, {s["event"]["en"]}' for s in DATA['services']]
    full += ['', '## Memberships', ''] + [f'- {m["name"]["en"]}' for m in DATA['memberships']] + ['']
    full += [f'## Publications ({len(PUBS)} records)', '', f'Source page: {canonical_url("publications")}', '']
    for kind, label in groups:
        full += [f'### {label} ({counts[kind]})', ''] + [publication_line(p) for p in PUBS if p['type'] == kind] + ['']
    (OUT / 'llms-full.txt').write_text('\n'.join(full + news_md), encoding='utf-8')

def shell(page, lang, body, news_item=None):
    lang_root = '../' if news_item is not None else ''   # to this language's home directory
    root = lang_root + ('../' if lang == 'ja' else '')    # to the site root, where assets live
    home_href = lang_root or './'
    name = text(DATA['name'], lang)
    active_page = 'news' if news_item is not None else page
    label = NAV[lang][PAGES.index(active_page)]
    title = (news_item['text'][lang] + ' — ' + DATA['name'][lang]) if news_item is not None else (DATA['name'][lang] if page == 'index' else f'{label} — {DATA["name"][lang]}')
    if page == 'index' and lang == 'en':
        title += '（' + DATA['name']['ja'].replace(' ', '') + '）'
    elif page == 'index':
        title += '（' + DATA['name']['en'] + '）'
    full_title = title + ' | ' + ('大阪公立大学' if lang == 'ja' else 'Osaka Metropolitan University')
    description = page_description(page, lang, news_item)
    canonical = canonical_url(page, lang)
    other = 'ja' if lang == 'en' else 'en'
    other_href = (root + page_path(page, other)) or './'
    alternates = ''.join(f'\n  <link rel="alternate" hreflang="{code}" href="{E(canonical_url(page, code), quote=True)}">' for code in LANGS)
    alternates += f'\n  <link rel="alternate" hreflang="x-default" href="{E(canonical_url(page, "en"), quote=True)}">'
    # ENG / JP switch: the current language is plain text, the other links to the same page in that language.
    switch_items = {
        'en': ('ENG', 'English'), 'ja': ('JP', '日本語')}
    switch = '<li class="lang-switch" role="group" aria-label="Language / 言語">'
    for code in LANGS:
        short, full = switch_items[code]
        if code == lang:
            switch += f'<span class="lang-current" lang="{code}" aria-current="true" title="{full}">{short}</span>'
        else:
            switch += f'<a class="lang-link" href="{E(other_href, quote=True)}" lang="{code}" hreflang="{code}" title="{full}">{short}</a>'
    switch += '</li>'
    social_image = news_item.get('social_image') if news_item is not None else None
    image_url = site_url(social_image['src'] if social_image else 'assets/manato-fujimoto.png')
    image_alt = social_image['alt'] if social_image else ('藤本まなとのポートレート' if lang == 'ja' else 'Portrait of Manato Fujimoto')
    social_tags = f'''
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="620">
  <meta property="og:image:height" content="560">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{E(full_title, quote=True)}">
  <meta name="twitter:description" content="{E(description, quote=True)}">
  <meta name="twitter:image" content="{E(image_url, quote=True)}">
  <meta name="twitter:image:alt" content="{E(image_alt, quote=True)}">'''
    if page == 'index':
        given, family = DATA['name']['en'].split(' ', 1)
        social_tags += f'''
  <meta property="profile:first_name" content="{E(given, quote=True)}">
  <meta property="profile:last_name" content="{E(family, quote=True)}">'''
    if social_image:
        social_tags = f'''
  <meta property="og:image:secure_url" content="{E(image_url, quote=True)}">
  <meta property="og:image:type" content="{E(social_image['type'], quote=True)}">
  <meta property="og:image:width" content="{social_image['width']}">
  <meta property="og:image:height" content="{social_image['height']}">
  <meta property="article:published_time" content="{E(news_item['date'], quote=True)}">
  <meta property="article:modified_time" content="{E(last_modified(news_item), quote=True)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{E(full_title, quote=True)}">
  <meta name="twitter:description" content="{E(description, quote=True)}">
  <meta name="twitter:image" content="{E(image_url, quote=True)}">
  <meta name="twitter:image:alt" content="{E(image_alt, quote=True)}">'''
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="10" fill="#111b29"/><text x="32" y="42" text-anchor="middle" fill="#85bcff" font-family="Arial,sans-serif" font-size="28">MF</text></svg>'
    nav = ''.join(f'<li><a href="{home_href if p == "index" else lang_root + p + ".html"}"' + (' aria-current="page"' if active_page == p else '') + f'>{NAV[lang][i]}</a></li>' for i,p in enumerate(PAGES)) + switch
    verification = DATA.get('google_site_verification', '')
    verification_meta = f'\n  <meta name="google-site-verification" content="{E(verification, quote=True)}">' if verification and page == 'index' and lang == 'en' else ''
    page_scripts = ''
    if page == 'publications':
        timeline_css_version = sha256((OUT / 'assets/timeline.css').read_bytes()).hexdigest()[:12]
        timeline_js_version = sha256((OUT / 'assets/timeline.js').read_bytes()).hexdigest()[:12]
        page_scripts = f'\n  <link rel="stylesheet" href="{root}assets/timeline.css?v={timeline_css_version}">\n  <script src="{root}assets/publications.js" defer></script>\n  <script src="{root}assets/timeline.js?v={timeline_js_version}" defer></script>'
    if page == 'publications':
        funding_css_version = sha256((OUT / 'assets/funding.css').read_bytes()).hexdigest()[:12]
        funding_js_version = sha256((OUT / 'assets/funding.js').read_bytes()).hexdigest()[:12]
        page_scripts += f'\n  <link rel="stylesheet" href="{root}assets/funding.css?v={funding_css_version}">\n  <script src="{root}assets/funding.js?v={funding_js_version}" defer></script>'
    if page == 'news':
        page_scripts += f'\n  <script src="{root}assets/news.js" defer></script>'
    return f'''<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{E(full_title)}</title>
  <meta name="description" content="{E(description, quote=True)}">
  <meta name="author" content="Manato Fujimoto">{verification_meta}
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
  <link rel="canonical" href="{E(canonical, quote=True)}">{alternates}
  <meta property="og:type" content="{'article' if news_item is not None else 'profile' if page == 'index' else 'website'}">
  <meta property="og:locale" content="{'ja_JP' if lang == 'ja' else 'en_US'}">
  <meta property="og:locale:alternate" content="{'en_US' if lang == 'ja' else 'ja_JP'}">
  <meta property="og:site_name" content="{text(DATA['name'],lang)}">
  <meta property="og:title" content="{E(full_title, quote=True)}">
  <meta property="og:description" content="{E(description, quote=True)}">
  <meta property="og:url" content="{E(canonical, quote=True)}">
  <meta property="og:image" content="{E(image_url, quote=True)}">
  <meta property="og:image:alt" content="{E(image_alt, quote=True)}">{social_tags}
  <script type="application/ld+json">{structured_data(page, full_title, description, news_item, lang)}</script>
  <link rel="sitemap" type="application/xml" href="{E(site_url('sitemap.xml'), quote=True)}">
  <link rel="alternate" type="text/markdown" title="Site summary for AI assistants (llms.txt)" href="{E(site_url('llms.txt'), quote=True)}">
  <meta name="theme-color" content="#090b10">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,{quote(svg)}">
  <link rel="stylesheet" href="{root}assets/style.css">
  <link rel="stylesheet" href="{root}assets/news.css">{page_scripts}
</head>
<body>
  <a class="skip-link" href="#main">{'本文へ移動' if lang == 'ja' else 'Skip to content'}</a>
  <header class="site-header"><div class="container header-inner">
    <a class="brand" href="{home_href}"><span class="brand-mark" aria-hidden="true">MF</span><span>Manato Fujimoto</span></a>
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
    return '<dl class="timeline">' + ''.join(f'<div class="timeline-row"><dt>{text(i["period"],lang)}</dt><dd>{text(i["title"],lang)}<span>{"<br>".join(text(i["place"],lang).splitlines())}</span></dd></div>' for i in items) + '</dl>'

def home(lang):
    ja = lang == 'ja'
    root = '../' if ja else ''
    name = '<h1>藤本 まなと</h1><p class="name-en" lang="en">Manato Fujimoto</p>' if ja else '<h1>Manato Fujimoto</h1>'
    profile_links = ''.join(f'<a href="{E(profile["url"], quote=True)}" class="profile-link" rel="me">{E(profile["label"])}</a>' for profile in DATA['profile_links'])
    body = f'''<section class="profile" aria-label="{'プロフィール' if ja else 'Profile'}">
  <div><p class="eyebrow">{'大阪公立大学' if ja else 'Osaka Metropolitan University'}</p>{name}
    <p class="position">{text(DATA['position'],lang)}</p>
    <p class="affiliation">{text(DATA['affiliation'],lang)}<br>{link(DATA['lab_url'],text(DATA['lab'],lang))}</p>
    <p class="lead">{text(DATA['intro'],lang)}</p>
    <dl class="contact-list"><dt>Email</dt><dd>{link('mailto:'+DATA['email'], E(DATA['email'].replace('@',' [at] ')))}</dd>
    <dt>{'所在地' if ja else 'Address'}</dt><dd><address>{text(DATA['address'],lang)}</address></dd></dl>
    <nav class="profile-links" aria-label="{'研究者プロフィール' if ja else 'Research profiles'}">{profile_links}</nav>
  </div>
  <figure class="profile-photo"><picture><source srcset="{root}assets/manato-fujimoto.webp" type="image/webp"><img src="{root}assets/manato-fujimoto.png" width="620" height="560" alt="{'藤本まなとのポートレート' if ja else 'Portrait of Manato Fujimoto'}" fetchpriority="high"></picture><figcaption>{'大阪公立大学<br>スマートプラットフォーム研究室' if ja else 'Smart Platform Research Group<br>Osaka Metropolitan University'}</figcaption></figure>
</section>'''
    about = ''.join(f'<p>{text(p,lang)}</p>' for p in DATA['about'])
    about += '<ul class="keywords">'+''.join(f'<li>{text(t,lang)}</li>' for t in DATA['keywords'])+'</ul>'
    body += section('プロフィール' if ja else 'About', '<div class="about-copy">'+about+'</div>')
    news_list = '<ul class="news-list">'+''.join(f'<li><time datetime="{E(n["date"])}">{E(n["date"].replace("-","."))}</time><span class="news-category">{E(category_label(n, lang))}</span><span class="news-item-title">{link(news_path(n),text(n["text"],lang))}</span></li>' for n in news_items()[:10])+'</ul>'
    all_news = link('news.html', 'お知らせ一覧 →' if ja else 'View all news →', 'news-all-link')
    body += f'<section class="section" id="recent-news"><div class="section-heading news-home-heading"><h2>{"お知らせ" if ja else "Recent News"}</h2>{all_news}</div>{news_list}</section>'
    body += '<div class="two-columns">'+section('職歴' if ja else 'Employment',timeline(DATA['appointments'],lang))+section('学歴' if ja else 'Education',timeline(DATA['education'],lang))+'</div>'
    a = DATA['awards'][0]
    award = f'<div class="award-highlight"><p class="award-year">{E(a["year"])}</p><h3>{link(a["url"],text(a["title"],lang))}</h3><p>{text(a["detail"],lang)}</p></div>'
    body += section('主な受賞' if ja else 'Selected Award',award)
    return body

def intro(title, subtitle='', eyebrow=''):
    return '<header class="page-intro">'+(f'<p class="eyebrow">{eyebrow}</p>' if eyebrow else '')+f'<h1>{title}</h1>'+(f'<p class="lead">{subtitle}</p>' if subtitle else '')+'</header>'

def research(lang):
    ja = lang == 'ja'
    body = intro('研究内容' if ja else 'Research', text(DATA['research_intro'],lang),'研究テーマ' if ja else 'Research interests')
    body += '<div class="research-grid">'
    for i,r in enumerate(DATA['research'],1):
        related = ''.join(link('publications.html#'+E(k),E(publication_title(next(p for p in PUBS if p['id']==k), lang))) for k in r['publications'])
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

BIB_MONTHS = {'jan': 'jan', 'feb': 'feb', 'mar': 'mar', 'apr': 'apr', 'april': 'apr', 'may': 'may', 'jun': 'jun', 'june': 'jun',
              'jul': 'jul', 'july': 'jul', 'aug': 'aug', 'sep': 'sep', 'sept': 'sep', 'oct': 'oct', 'nov': 'nov', 'dec': 'dec'}
BIB_STOPWORDS = {'a', 'an', 'the', 'of', 'on', 'for', 'and', 'in', 'to', 'with', 'by', 'from', 'using', 'toward', 'towards', 'via'}

def bib_escape(value):
    return re.sub(r'([&%$#_])', r'\\\1', value)

BIB_TYPES = {'journal': 'article', 'conference': 'inproceedings'}
BIB_NOTES = re.compile(r'(poster|demo|short paper|position paper|work[- ]in[- ]progress|mini-conference paper|doctoral symposium)', re.I)

def bib_eligible(p):
    """Only confirmed records: no Accepted flag, no xx placeholders in the venue line, and not opted out with "bibtex": false."""
    return (p['type'] in BIB_TYPES and not p['accepted'] and p.get('bibtex', True)
            and not re.search(r'\bx{2,}\b', p['venue']))

def bib_base_key(p):
    first_author = p['authors'].split(',')[0].split()[-1]
    family = re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', first_author).encode('ascii', 'ignore').decode().lower())
    words = [re.sub(r'[^a-z0-9]', '', w.lower()) for w in re.split(r'[\s\-:/]+', p['title'])]
    word = next((w for w in words if w and w not in BIB_STOPWORDS), 'paper')
    return f'{family}{p["year"]}{word}'

def bib_keys():
    """Citation key per record ID. Clashing keys get b, c, ... with the older paper keeping the plain key."""
    keys, used = {}, {}
    # Journal articles are numbered first so their keys never change when a conference paper is added.
    for p in sorted(reversed(PUBS), key=lambda p: list(BIB_TYPES).index(p['type']) if p['type'] in BIB_TYPES else len(BIB_TYPES)):
        if not bib_eligible(p):
            continue
        key = bib_base_key(p)
        used[key] = used.get(key, 0) + 1
        keys[p['id']] = key if used[key] == 1 else key + 'abcdefghijklmnopqrstuvwxyz'[used[key] - 1]
    return keys

BIB_KEYS = bib_keys()

def bib_key(p):
    return BIB_KEYS[p['id']]

def bib_date(part):
    if m := re.fullmatch(r'([A-Za-z]+)\.? (\d{4})', part):
        month = BIB_MONTHS.get(m.group(1).lower())
        return (month, m.group(2)) if month else None
    return None

def bib_conference_fields(venue):
    """Split a conference venue line: proceedings name, optional notes and pages, place, month and year."""
    parts = [part.strip() for part in venue.strip().rstrip('.').split(', ')]
    when = bib_date(parts[-1]) if len(parts) > 1 else None
    if when is None:
        return None
    fields, notes, parts = {'month': when[0], 'year': when[1]}, [], parts[:-1]
    markers = []
    for index, part in enumerate(parts):
        if m := re.fullmatch(r'pp\.? ?(\S+?)\s*[-–]\s*(\S+)', part, re.I):
            fields['pages'] = f'{m.group(1)}--{m.group(2)}'
        elif m := re.fullmatch(r'(\d+) pages?', part, re.I):
            fields['numpages'] = m.group(1)
        elif m := re.fullmatch(r'volume (\S+)', part, re.I):
            fields['volume'] = m.group(1)
        elif BIB_NOTES.fullmatch(part):
            notes.append(part)
        else:
            continue
        markers.append(index)
    if markers:
        first = markers[0]
    else:
        # No pages or notes: the proceedings name ends at the last part closing with ")", e.g. "(ISMICT 2026)".
        closing = [index for index, part in enumerate(parts) if part.endswith(')')]
        if not closing:
            return None
        first = closing[-1] + 1
    place = [part for index, part in enumerate(parts) if index >= first and index not in markers]
    if first == 0 or not place:
        return None
    fields['booktitle'], fields['address'] = ', '.join(parts[:first]), ', '.join(place)
    if notes:
        fields['note'] = ', '.join(notes)
    return fields

def bib_fields(venue, japanese=False):
    """Split a journal venue line into BibTeX fields. Returns None when a part is not recognised."""
    venue = venue.strip().rstrip('.．')
    if japanese:
        journal, *parts = [part.strip() for part in venue.split('，')]
    else:
        match = re.match(r'(.+?), (vol\. .+)$', venue, re.I)
        if not match:
            return None
        journal, parts = match.group(1), [part.strip() for part in match.group(2).split(', ')]
    fields = {'journal': journal}
    for part in parts:
        if m := re.fullmatch(r'vol\. ?(.+)', part, re.I):
            fields['volume'] = m.group(1)
        elif m := re.fullmatch(r'issue (.+)', part, re.I):
            fields['number'] = m.group(1)
        elif m := re.fullmatch(r'no\. ?(.+)', part, re.I):
            # "Issue 1, No. 13" (MDPI style): the second number is the article number.
            fields['articleno' if 'number' in fields else 'number'] = m.group(1)
        elif m := re.fullmatch(r'article (?:number:|id) ?(.+)', part, re.I):
            fields['articleno'] = m.group(1)
        elif m := re.fullmatch(r'pp\. ?(\w+)\s*[-–]\s*(\w+)', part, re.I):
            fields['pages'] = f'{m.group(1)}--{m.group(2)}'
        elif m := re.fullmatch(r'(\d+) pages', part, re.I):
            fields['numpages'] = m.group(1)
        elif m := re.fullmatch(r'([A-Za-z]+)\.? (\d{4})', part):
            if m.group(1).lower() not in BIB_MONTHS:
                return None
            fields['month'], fields['year'] = BIB_MONTHS[m.group(1).lower()], m.group(2)
        elif m := re.fullmatch(r'(\d{4})年(\d{1,2})月', part):
            fields['month'], fields['year'] = list(dict.fromkeys(BIB_MONTHS.values()))[int(m.group(2)) - 1], m.group(1)
        else:
            return None
    return fields if {'volume', 'year'} <= fields.keys() else None

def bibtex_entry(p, lang='en'):
    """BibTeX for a confirmed journal article or conference paper, or None when the record is unconfirmed or unparseable."""
    if not bib_eligible(p):
        return None
    japanese = lang == 'ja' and p.get('language') == 'ja' and all(p.get(k) for k in ('title_ja', 'authors_ja', 'venue_ja'))
    if p['type'] == 'journal':
        fields = bib_fields(p['venue_ja'] if japanese else p['venue'], japanese)
        order = ('journal', 'volume', 'number', 'pages', 'articleno', 'numpages', 'year')
    else:
        fields = bib_conference_fields(p['venue'])
        order = ('booktitle', 'volume', 'pages', 'numpages', 'address', 'year')
    if fields is None:
        return None
    authors = re.split(r'[，,]\s*', (p['authors_ja'] if japanese else p['authors']).strip())
    authors = [re.sub(r'^and\s+', '', a) for a in authors if a]
    entry = [('author', '{' + ' and '.join(bib_escape(a) for a in authors) + '}'),
             ('title', '{{' + bib_escape(p['title_ja'] if japanese else p['title']) + '}}')]
    entry += [(key, '{' + bib_escape(fields[key]) + '}') for key in order if key in fields]
    if 'month' in fields:
        entry.append(('month', fields['month']))
    doi = re.search(r'(?:doi\.org/|/doi/(?:abs/|full/|pdf/)?)(10\.\d{4,9}/[^\s?#]+)', p['url'])
    if doi:
        entry.append(('doi', '{' + doi.group(1).rstrip('/') + '}'))
    if p['url']:
        entry.append(('url', '{' + p['url'] + '}'))
    if 'note' in fields:
        entry.append(('note', '{' + bib_escape(fields['note']) + '}'))
    if p.get('language') == 'ja':
        entry.append(('language', '{Japanese}') if japanese else ('note', '{in Japanese}'))
    width = max(len(key) for key, _ in entry)
    return '@' + BIB_TYPES[p['type']] + '{' + bib_key(p) + ',\n' + ',\n'.join(f'  {key.ljust(width)} = {value}' for key, value in entry) + '\n}\n'

def bib_path(p, lang='en'):
    """Path of the .bib file from the site root. Japanese papers get a separate Japanese file."""
    japanese = lang == 'ja' and p.get('language') == 'ja'
    return f'bib/{p["id"]}{"-ja" if japanese else ""}.bib'

def write_bibtex_files():
    out = OUT / 'bib'
    out.mkdir(exist_ok=True)
    for old in out.glob('*.bib'):
        old.unlink()
    counts = {kind: 0 for kind in BIB_TYPES}
    for p in PUBS:
        if not bib_eligible(p):
            continue
        if bibtex_entry(p) is None:
            print(f'Note: no BibTeX for {p["label"]}; its venue line could not be split into fields: {p["venue"]}')
            continue
        counts[p['type']] += 1
        for lang in LANGS:
            (OUT / bib_path(p, lang)).write_text(bibtex_entry(p, lang), encoding='utf-8')
    return counts

def publication_item(p, lang, *, title_url=None, id_prefix='', bib_root=None):
    title = E(publication_title(p, lang))
    topic_title = f' data-topic-title="{E(p["title"], quote=True)}"' if publication_title(p, lang) != p['title'] else ''
    target = p['url'] if title_url is None else title_url
    if target:
        title = link(target,title)
    tags = ''
    if p['accepted']:
        tags += f'<span class="status">{"採択済み" if lang == "ja" else "Accepted"}</span>'
    if p.get('scheduled'):
        tags += '<span class="status status-scheduled">発表予定</span>'
    ja = lang == 'ja'
    if p.get('invited'):
        tags += f'<span class="status status-invited">{"招待論文" if ja else "Invited paper"}</span>'
    if p['type'] == 'journal' and p.get('language') == 'ja':
        tags += f'<span class="status status-japanese">{"和文" if ja else "Japanese"}</span>'
    if p['type'] == 'journal' and p.get('corresponding'):
        tags += f'<span class="status status-corresponding">{"責任著者" if ja else "Corresponding"}</span>'
    if p['type'] == 'journal' and p.get('international_coauthorship'):
        tags += f'<span class="status status-international">{"国際共著" if ja else "International coauthorship"}</span>'
    for award in p.get('awards', []):
        tags += f'<span class="status status-award">{E(award)}</span>'
    if bib_root is not None and bibtex_entry(p, lang) is not None:
        label = f'{p["label"]}のBibTeXをダウンロード' if ja else f'Download BibTeX for {p["label"]}'
        tags += f'<a class="pub-bibtex" href="{E(bib_root + bib_path(p, lang), quote=True)}" download="{E(bib_key(p), quote=True)}.bib" type="application/x-bibtex" aria-label="{E(label, quote=True)}" title="{E(label, quote=True)}"><span aria-hidden="true">↓</span>BibTeX</a>'
    authors = E(publication_field(p, 'authors', lang))
    metric = journal_metric(p)
    metrics = ''
    if metric:
        when = str(metric['year'])
        metric_label = f'Impact Factor: <strong>{E(metric["value"])}</strong> <span class="metric-year">({E(when)})</span>'
        metrics = '<p class="pub-metrics">' + link(metric['source_url'], metric_label, 'impact-factor') + '</p>'
    if tags:
        tags = f'<div class="pub-tags" aria-label="{"論文のタグ" if lang == "ja" else "Publication tags"}">' + tags + '</div>'
    return f'<li class="publication" id="{E(id_prefix + p["id"])}"{topic_title}><span class="pub-index">{E(p["label"])}</span><div class="pub-content"><h3 class="pub-title">{title}</h3><p class="pub-authors">{authors}</p><p class="pub-venue">{E(publication_field(p, "venue", lang))}</p>{metrics}{tags}</div></li>'

def news_meta(item, lang='en'):
    return f'<div class="news-card-meta"><span class="news-category">{E(category_label(item, lang))}</span><time class="news-date" datetime="{E(item["date"])}">{E(item["date"].replace("-", "."))}</time></div>'

def news_thumbnail(item, root='', *, article=False):
    thumbnail = item.get('thumbnail')
    if not thumbnail:
        return ''
    alt = thumbnail['alt'] if article else ''
    loading = 'eager' if article else 'lazy'
    return f'<img class="news-thumbnail" src="{E(root + thumbnail["src"], quote=True)}" width="{thumbnail["width"]}" height="{thumbnail["height"]}" alt="{E(alt, quote=True)}" loading="{loading}" decoding="async">'

def news_excerpt(item, lang):
    """Card excerpt. Japanese cards show the paper titles, because summaries are written in English."""
    if lang == 'ja':
        return ' ／ '.join(publication_title(p, lang) for p in news_publications(item))
    return item['summary']

def news(lang):
    ja = lang == 'ja'
    root = '../' if ja else ''
    body = intro('お知らせ' if ja else 'News', eyebrow='最新情報' if ja else 'Latest updates')
    items = news_items()
    body += f'<div data-news-index><div class="news-filters" role="group" aria-label="{"お知らせの絞り込み" if ja else "Filter news"}" hidden>'
    for value, label in [('all', 'すべて' if ja else 'All'), ('journal', '論文誌' if ja else 'Journal'), ('conference', '国際会議' if ja else 'Conference')]:
        count = sum(value == 'all' or item['category'].lower() == value for item in items)
        pressed = 'true' if value == 'all' else 'false'
        body += f'<button type="button" class="news-filter" data-news-filter="{value}" aria-pressed="{pressed}" aria-controls="news-results">{label}<span class="news-filter-count">{count}</span></button>'
    body += '</div><p class="news-filter-status" role="status" aria-live="polite" aria-atomic="true"></p><div id="news-results">'
    for year in sorted({item['date'][:4] for item in items}, reverse=True):
        yearly = [item for item in items if item['date'].startswith(year)]
        count_note = f'{len(yearly)}件' if ja else f'{len(yearly)} updates'
        body += f'<section class="news-archive" aria-labelledby="news-year-{E(year)}"><div class="section-heading"><h2 id="news-year-{E(year)}">{E(year)}</h2><span class="note" data-news-count>{count_note}</span></div><ol class="news-grid">'
        for item in yearly:
            summary = news_meta(item, lang) + f'<h3 class="news-card-title">{text(item["text"],lang)}</h3><p class="news-card-excerpt">{E(news_excerpt(item, lang))}</p><span class="news-read-link">{"記事を読む →" if ja else "Read article →"}</span>'
            card_class = 'news-card-link'
            if item.get('thumbnail'):
                summary = news_thumbnail(item, root) + '<div class="news-card-copy">' + summary + '</div>'
                card_class += ' news-card-with-thumbnail'
            body += f'<li class="news-card" id="news-{E(item["date"])}" data-news-category="{E(item["category"].lower())}">{link(news_path(item), summary, card_class)}</li>'
        body += '</ol></section>'
    return body + '</div></div><p class="news-return">' + link('./#recent-news', '← ホームのお知らせへ戻る' if ja else '← Back to Recent News') + '</p>'

def news_article(item, lang):
    ja = lang == 'ja'
    breadcrumb = link('../', NAV[lang][0]) + '<span aria-hidden="true">/</span>' + link('../news.html', NAV[lang][1]) + '<span aria-hidden="true">/</span>' + f'<span aria-current="page">{E(item["date"].replace("-", "."))}</span>'
    body = f'<nav class="article-breadcrumb" aria-label="{"パンくずリスト" if ja else "Breadcrumb"}">{breadcrumb}</nav><article aria-labelledby="news-article-title"><header class="article-heading">{news_meta(item, lang)}<h1 id="news-article-title">{text(item["text"],lang)}</h1></header>'
    # News stores only publication IDs; every bibliographic field comes from PUBS.
    records = news_publications(item)
    citations = ''.join(publication_item(p, lang, title_url='../publications.html#' + p['id'], id_prefix='news-') for p in records)
    publication_heading = heading('論文' if ja else ('Publications' if len(records) != 1 else 'Publication'))
    thumbnail = '<figure class="news-article-image">' + news_thumbnail(item, '../../' if ja else '../', article=True) + '</figure>' if item.get('thumbnail') else ''
    # The announcement text is stored in English only; the Japanese page uses the Japanese headline as the announcement.
    announcement = item['body_html'] if not ja else ''
    body += '<div class="article-body">' + thumbnail + '<div class="news-announcement">' + announcement + publication_heading + '<ol class="publications news-publications">' + citations + '</ol></div></div>'
    body += '<footer class="article-end"><p class="news-return">' + link('../news.html', '← お知らせ一覧' if ja else '← All news') + f'</p><nav class="article-neighbors" aria-label="{"ほかのお知らせ" if ja else "Other news articles"}">'
    items = news_items()
    index = next(i for i, other in enumerate(items) if other['slug'] == item['slug'])
    if index > 0:
        newer = items[index - 1]
        body += link(newer['slug'] + '.html', f'<span>{"← 新しい記事" if ja else "← Newer article"}</span>' + text(newer['text'], lang), 'article-neighbor')
    if index + 1 < len(items):
        older = items[index + 1]
        body += link(older['slug'] + '.html', f'<span>{"以前の記事 →" if ja else "Older article →"}</span>' + text(older['text'], lang), 'article-neighbor article-neighbor-older')
    return body + '</nav></footer></article>'

def research_funding(lang):
    records = json.dumps(FUNDING, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    ja = lang == 'ja'
    title = '研究費獲得実績' if ja else 'Research Funding'
    years = '年度 · 2014–2028' if ja else 'FISCAL YEARS · 2014–2028'
    caption = 'バーは研究期間を年度単位で示します。カーソルを合わせると研究課題名と藤本の役割が表示され、選択すると詳細を確認できます。' if ja else 'Bars show project periods by fiscal year. Hover for the project title and Fujimoto’s role, or tap for details.'
    other = 'その他の研究費' if ja else 'Other Funding'
    other_detail = '民間財団助成・Society 5.0 · 4件' if ja else 'Foundation grants &amp; Society 5.0 · 4 projects'
    note = '研究課題名は英語表記からの日本語訳です。' if ja else 'Project titles are English translations.'
    return f'<section id="research-funding" class="rf" lang="{lang}" aria-labelledby="rf-title">\n  <div class="rf-heading"><h3 id="rf-title">{title}</h3><span>{years}</span></div>\n  <p class="rf-caption">{caption}</p>\n  <div id="rf-main-chart"></div>\n  <details class="rf-more"><summary>{other} <span>{other_detail}</span></summary><div id="rf-other-chart"></div></details>\n  <div id="rf-detail" class="rf-detail" aria-live="polite" aria-atomic="true" hidden></div>\n  <p class="rf-source">{note}</p>\n</section>' + f'<script type="application/json" id="rf-data">{records}</script>'

def publications(lang):
    ja = lang == 'ja'
    body = intro('研究業績' if ja else 'Publications', eyebrow='業績一覧' if ja else 'Publications')
    groups = [('journal','学術論文' if ja else 'Journal Articles'),('conference','国際会議論文' if ja else 'International Conference Proceedings'),('domestic-conference','国内学会発表' if ja else 'Domestic Conference')]
    timeline_label = '業績タイムライン' if ja else 'Output Timeline'
    body += '<nav class="section-nav" aria-label="'+('業績の種別' if ja else 'Publication categories')+'">'+''.join(link('#'+key,label) for key,label in groups+[('output-timeline',timeline_label)])+'</nav>'
    for kind,label in groups:
        items = [p for p in PUBS if p['type']==kind]
        count_label = '件' if ja else 'papers'
        body += f'<section class="publication-group" id="{kind}">'+heading(label,f'<span class="note">{len(items)} {count_label}</span>')
        if kind == 'journal':
            year, release = JOURNAL_METRICS['metric_year'], JOURNAL_METRICS['release_year']
            metric_note = f'掲載誌の{year}年Journal Impact Factor（{release}年公表）を、確認できた誌に表示しています。数値から出典を確認できます。' if ja else f'Journal Impact Factors are {year} values, released in {release}, shown where verified. Each value links to its source.'
            body += f'<p class="metrics-note">{metric_note}</p>'
        body += '<ol class="publications">'+''.join(publication_item(p,lang,bib_root='../' if ja else '') for p in items)+'</ol>'
        body += '</section>'
    # Output Timeline: assets/timeline.js draws it from the lists above; only the years are passed here.
    kinds = {key for key,_ in groups}
    timeline_items = [p for p in PUBS if p['type'] in kinds]
    years = {p['id']: int(p['year']) for p in timeline_items}
    span = f'{min(years.values())}–{max(years.values())}'
    years_json = json.dumps(years, separators=(',',':')).replace('</','<\\/')
    fallback = 'このタイムラインの表示にはJavaScriptが必要です。' if ja else 'The timeline needs JavaScript. The full lists are available under the other tabs.'
    body += f'<section class="publication-group" id="output-timeline">'+heading(timeline_label,f'<span class="note">{len(timeline_items)} {"件" if ja else "items"}, {span}</span>')
    body += f'<div class="ot" id="ot-root"><noscript><p>{fallback}</p></noscript></div><script type="application/json" id="ot-years">{years_json}</script>' + research_funding(lang) + '</section>'
    return body

def services(lang):
    ja = lang == 'ja'
    body = intro('学会活動・受賞' if ja else 'Services & Awards', '主な学会活動と受賞歴。' if ja else 'Selected professional services and awards.','学会・コミュニティ' if ja else 'Academic community')
    # On the Japanese page the list is split into international and domestic roles;
    # the domestic roles (from researchmap) are kept in Japanese only.
    role_tag = 'h4' if ja else 'h3'
    rows = '<ul class="service-list committee-list">' if ja else '<ul class="service-list">'
    for s in DATA['services']:
        detail = f'<{role_tag}>{text(s["role"],lang)}</{role_tag}><p>{text(s["event"],lang)}</p>'
        rows += f'<li><span class="year">{E(s["year"])}</span>' + (detail if ja else f'<div>{detail}</div>') + '</li>'
    rows += '</ul>'
    if ja:
        domestic = '<ul class="service-list committee-list">'
        for c in DATA['domestic_committees_ja']:
            domestic += f'<li><span class="year">{E(c["period"])}</span><h4>{E(c["role"])}</h4><p>{E(c["event"])}</p></li>'
        domestic += '</ul>'
        columns = '<div class="committee-columns" aria-hidden="true"><span>年・任期</span><span>役職</span><span>会議・組織名</span></div>'
        rows = ('<h3 class="service-group-title">国際会議委員</h3>' + columns + rows
                + '<h3 class="service-group-title">国内委員</h3>' + columns + domestic
                + source_note(DATA['domestic_committees_ja_source'], lang))
    body += section('国際会議・研究会運営' if ja else 'Selected Conference Organization',rows)
    rows = '<ul class="service-list">'
    for a in sorted(DATA['awards'], key=lambda award: int(award['year']), reverse=True):
        title = text(a['title'], lang)
        if a.get('url'):
            title = link(a['url'], title)
        detail = '<br>'.join(text(a['detail'], lang).splitlines())
        rows += f'<li><span class="year">{E(a["year"])}</span><div><h3>{title}</h3><p>{detail}</p></div></li>'
    body += section('主な受賞' if ja else 'Selected Awards',rows+'</ul>')
    member = '<ul class="memberships">'+''.join(f'<li>{link(m["url"],text(m["name"],lang))}</li>' for m in DATA['memberships'])+'</ul>'
    body += section('所属学会' if ja else 'Memberships',member)
    return body

def main():
    validate_journal_metrics()
    validate_news()
    validate_search_metadata()
    OUT.mkdir(parents=True,exist_ok=True)
    for lang in LANGS:
        out = OUT / 'ja' if lang == 'ja' else OUT
        (out / 'news').mkdir(parents=True, exist_ok=True)
        for page, render in [('index',home),('news',news),('research',research),('publications',publications),('services',services)]:
            (out / (page+'.html')).write_text(shell(page,lang,render(lang)),encoding='utf-8')
        for item in news_items():
            path = news_path(item)
            (out / path).write_text(shell(path.removesuffix('.html'), lang, news_article(item, lang), item), encoding='utf-8')
    bib_count = write_bibtex_files()
    (OUT / '.nojekyll').touch()
    write_discovery_files()
    print(f'Generated {len(PAGES) + len(news_items())} HTML pages in each of English and Japanese with {len(PUBS)} publication records, plus sitemap.xml, robots.txt, llms.txt, llms-full.txt and BibTeX files for {bib_count['journal']} journal articles and {bib_count['conference']} conference papers.')

if __name__=='__main__':
    main()
