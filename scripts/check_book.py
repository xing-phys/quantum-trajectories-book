#!/usr/bin/env python3
"""Validate the rendered Quarto book with Python standard libraries only.

Resolve each local link relative to its containing page, including fragments.
Do not make network requests. This checks publication structure, not physics.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from collections import Counter
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'_site'

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.images, self.text = [], [], [], []
        self.feed(path.read_text())
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag=='a' and a.get('href'): self.links.append(a['href'])
        if tag=='img' and a.get('src'): self.images.append(a['src'])
    def handle_data(self, data): self.text.append(data)

errors=[]
pages={p.resolve():Page(p) for p in SITE.glob('*.html')}
expected=[p.with_suffix('.html').name for p in ROOT.glob('*.qmd')]
for name in expected:
    if not (SITE/name).is_file(): errors.append('Missing rendered chapter: '+name)
links=0
for path,page in pages.items():
    # Quarto uses paired light/dark stylesheet IDs for its color-mode toggle.
    paired_styles={'quarto-bootstrap','quarto-text-highlighting-styles'}
    dup=[k for k,n in Counter(page.ids).items() if n>1 and k not in paired_styles]
    if dup: errors.append(f'{path.name}: duplicate IDs: {dup}')
    raw=path.read_text()
    for marker in ('quarto-unresolved-ref','citeproc-not-found','[citation needed]'):
        if marker in raw: errors.append(f'{path.name}: unresolved marker {marker}')
    # This pattern is specific to Quarto's unresolved cross-reference output.
    if re.search(r'<strong>\?\?(?:</strong>|[a-z])',raw):
        errors.append(f'{path.name}: unresolved reference text')
    for href in page.links+page.images:
        u=urlsplit(href)
        if u.scheme or u.netloc or href.startswith('data:'): continue
        local=unquote(u.path)
        # A leading slash is a site-root link, not a filesystem-root link.
        target=(SITE/local.lstrip('/') if local.startswith('/') else path.parent/local).resolve() if local else path
        if target.is_dir(): target=target/'index.html'
        if not target.exists():
            errors.append(f'{path.name}: missing target {href}')
            continue
        links+=1
        if u.fragment and target.suffix=='.html':
            target_page=pages.get(target)
            if target_page is None:
                target_page=Page(target); pages[target]=target_page
            fragment=unquote(u.fragment)
            if fragment not in target_page.ids:
                errors.append(f'{path.name}: missing anchor {href}')

pdf=SITE/'quantum-trajectories-book.pdf'
if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):
    errors.append('Missing or invalid combined PDF')
index=pages.get((SITE/'index.html').resolve())
if not index or not any(urlsplit(h).path.endswith('quantum-trajectories-book.pdf') for h in index.links):
    errors.append('Home page has no PDF download link')
if not (SITE/'search.json').is_file():
    errors.append('Missing full-text search index')
else:
    search=json.loads((SITE/'search.json').read_text())
    if not search: errors.append('Empty search index')

# Chapter source labels must be globally unique for combined PDF references.
labels=[]
for p in ROOT.glob('*.qmd'):
    labels.extend(re.findall(r'\{#((?:eq|fig|sec|tbl)-[\w-]+)',p.read_text()))
duplicates=[k for k,n in Counter(labels).items() if n>1]
if duplicates: errors.append('Duplicate source labels: '+', '.join(duplicates))
if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    sys.exit(1)
print(f'PASS: {len(expected)} chapter pages, {links} local links/images, {len(labels)} labeled targets, search index, and PDF download.')
