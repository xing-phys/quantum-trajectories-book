"""Fetch canonical BibTeX for central sources from Crossref (manual maintenance tool)."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
import json
import re
import time

SOURCES = {
    'Daley2014': '10.1080/00018732.2014.933502',
    'Lindblad1976': '10.1007/BF01608499',
    'GKS1976': '10.1063/1.522979',
    'DCM1992': '10.1103/PhysRevLett.68.580',
    'Dum1992': '10.1103/PhysRevA.45.4879',
    'Molmer1993': '10.1364/JOSAB.10.000524',
    'Carmichael1993': '10.1007/978-3-540-47620-7',
    'Plenio1998': '10.1103/RevModPhys.70.101',
    'Diehl2008': '10.1038/nphys1073',
    'Kraus2008': '10.1103/PhysRevA.78.042307',
    'Syassen2008': '10.1126/science.1155309',
    'GarciaRipoll2009': '10.1088/1367-2630/11/1/013053',
    'Daley2009': '10.1103/PhysRevLett.102.040402',
    'Diehl2011': '10.1038/nphys2106',
    'Barreiro2011': '10.1038/nature09801',
    'Baumann2010': '10.1038/nature09009',
    'Muller2012': '10.1016/B978-0-12-396482-3.00001-6',
    'Verstraete2009': '10.1038/nphys1342',
}
ROOT = Path(__file__).resolve().parents[1]

def fetch(item):
    key, doi = item
    base='https://api.crossref.org/works/'+quote(doi, safe='')
    cache=ROOT/'.research'/('crossref-'+key+'.json')
    cache.parent.mkdir(parents=True,exist_ok=True)
    if cache.exists():
        meta=json.loads(cache.read_text())
    else:
        for attempt in range(6):
            try:
                req=Request(base,headers={'User-Agent':'QuantumTrajectoriesBook/1.0 (bibliographic verification)'})
                with urlopen(req, timeout=60) as response:
                    meta=json.load(response)['message']
                cache.write_text(json.dumps(meta))
                break
            except Exception:
                if attempt==5: raise
                time.sleep(4*(attempt+1))
        time.sleep(1)
    clean=lambda value:re.sub(r'<[^>]*>','',value).replace('&amp;','&').replace('&','\\&').replace('\n',' ').strip()
    title=re.sub(r'\s+',' ',clean(meta['title'][0])).replace(' N -level',' N-level')
    authors=' and '.join(a.get('family','')+', '+a.get('given','') for a in meta.get('author',[])).replace('Ignacio Cirac, J.','Cirac, J. Ignacio')
    year=meta.get('published-print',meta['issued'])['date-parts'][0][0]
    kind={'journal-article':'article','book-chapter':'incollection'}.get(meta['type'],'book')
    fields={'title':'{'+title+'}', 'author':authors,'year':str(year),'doi':doi,'url':'https://doi.org/'+doi}
    if meta.get('container-title'):
        fields['journal' if kind=='article' else 'booktitle']=clean(meta['container-title'][0])
    for out, field in [('volume','volume'),('number','issue'),('pages','page'),('publisher','publisher')]:
        if meta.get(field): fields[out]=str(meta[field]).replace('–','--')
    if key=='Molmer1993': fields['pages']='524--538'
    bib='@'+kind+'{'+key+',\n'+',\n'.join('  '+k+' = {'+v+'}' for k,v in fields.items())+'\n}'
    audit={'key':key,'doi':doi,'title':title,'year':year,'source':base,'checked':'2026-10-20'}
    print(key, title, flush=True)
    return bib, audit

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=1) as pool:
        results=list(pool.map(fetch,SOURCES.items()))
    (ROOT/'assets/bibliography.bib').write_text('\n\n'.join(b for b,a in results)+'\n')
    (ROOT/'assets/source-audit.json').write_text(json.dumps([a for b,a in results],indent=2)+'\n')
