#!/usr/bin/env python3
"""Optional visual QA for a locally served book using isolated headless Chrome.

Install requirements-browser.txt, serve _site on port 4207, then run this script.
This never connects to an existing browser profile or user session.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.research'/'browser-qa'
OUT.mkdir(parents=True,exist_ok=True)
base=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:4207/'
paths=['index.html','02-master-equations.html','04-measurement.html','06-many-body-numerics.html','09-particle-loss.html','12-computational-lab.html']
report=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1100},device_scale_factor=1)
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda err:errors.append(str(err)))
    for name in paths:
        response=page.goto(base+name,wait_until='networkidle',timeout=60000)
        assert response.status==200,(name,response.status)
        page.evaluate('async () => { if (window.MathJax?.startup?.promise) await MathJax.startup.promise; }')
        count=page.locator('mjx-container').count()
        math_errors=page.locator('mjx-merror').count()
        assert math_errors==0,(name,math_errors)
        page.screenshot(path=str(OUT/(name+'.png')),full_page=False)
        report.append({'page':name,'status':response.status,'math_expressions':count,'math_errors':math_errors})
    page.goto(base+'04-measurement.html',wait_until='networkidle')
    page.evaluate('async () => { if (window.MathJax?.startup?.promise) await MathJax.startup.promise; }')
    page.locator('#fig-measurement-chain').scroll_into_view_if_needed()
    page.screenshot(path=str(OUT/'measurement-light.png'))
    page.locator('.quarto-color-scheme-toggle').first.click()
    page.wait_for_function("document.body.classList.contains('quarto-dark')")
    page.screenshot(path=str(OUT/'measurement-dark.png'))
    page.set_viewport_size({'width':390,'height':844})
    page.goto(base+'02-master-equations.html',wait_until='networkidle')
    page.evaluate('async () => { if (window.MathJax?.startup?.promise) await MathJax.startup.promise; }')
    overflow=page.evaluate('document.documentElement.scrollWidth>window.innerWidth+2')
    assert not overflow,'Whole page overflows mobile viewport'
    page.screenshot(path=str(OUT/'mobile.png'))
    assert not errors,errors
    browser.close()
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: six representative pages, rendered math without errors, light/dark figures, and mobile width.')
