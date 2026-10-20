#!/usr/bin/env python3
"""Render a śloka card (1080x1350 PNG) from a card spec.

All text is set by code from the repository, never painted by an image model,
so the Sanskrit is exactly the mūla. The scene image is optional; without one a
plain placeholder background is used.
Usage: render_card.py visual/specs/<id>.json
"""
import json, os, re, sys, html, pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent

def shloka_lines(book, n):
    txt = (ROOT / f'mula/{book}/001.deva.txt').read_text(encoding='utf8')
    for block in txt.strip().split('\n\n'):
        m = re.search(r'॥(\d+)॥', block)
        if m and int(m.group(1)) == n:
            body = re.sub(r'\s*\[.*?\]\s*$', '', block.strip())
            body = body.translate(str.maketrans('0123456789', '०१२३४५६७८९'))
            return [l.strip() for l in body.split('\n')]
    raise SystemExit(f'śloka {n} not found in {book}')

def main(spec_path):
    s = json.loads(open(spec_path, encoding='utf8').read())
    lines = shloka_lines(s['book'], s['shloka'])
    fonts = (ROOT / 'visual/fonts').as_uri()
    bg = (f"url('{(ROOT / s['background']).as_uri()}') center/cover"
          if s.get('background') else
          'radial-gradient(circle at 78% 16%, #e9e9e9 0 62px, #9a9a9a 63px, transparent 140px), linear-gradient(#141414, #050505)')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Tiro; src: url('{fonts}/tiro-devanagari-sanskrit-devanagari-400-normal.woff2'); }}
@font-face {{ font-family: TiroL; src: url('{fonts}/tiro-devanagari-sanskrit-latin-ext-400-normal.woff2'); }}
@font-face {{ font-family: TiroL; src: url('{fonts}/tiro-devanagari-sanskrit-latin-400-normal.woff2'); }}
html,body {{ margin:0; width:1080px; height:1350px; background:#000; }}
.card {{ position:relative; width:1080px; height:1350px; background:{bg}; color:#f2f2f2; font-family: TiroL, Tiro, serif; overflow:hidden; }}
.shade {{ position:absolute; inset:0; background:linear-gradient(rgba(0,0,0,.55), rgba(0,0,0,.05) 38%, rgba(0,0,0,.15) 62%, rgba(0,0,0,.82)); }}
.top {{ position:absolute; left:72px; top:70px; right:72px; }}
.title {{ font-family: Tiro, serif; font-size:150px; line-height:1; letter-spacing:2px; }}
.iast {{ font-size:40px; letter-spacing:10px; margin-top:6px; }}
.rule {{ width:420px; height:1px; background:#cfcfcf; margin:22px 0; }}
.gloss {{ font-size:32px; font-style:italic; max-width:640px; line-height:1.35; }}
.bottom {{ position:absolute; left:72px; right:72px; bottom:70px; }}
.shloka {{ font-family: Tiro, serif; font-size:44px; line-height:1.55; }}
.ref {{ font-size:24px; letter-spacing:4px; margin-top:18px; color:#cfcfcf; }}
.label {{ position:absolute; right:24px; bottom:18px; font-size:16px; color:#9a9a9a; }}
</style></head><body><div class="card"><div class="shade"></div>
<div class="top"><div class="title">{html.escape(s['title_deva'])}</div><div class="iast">{html.escape(s['title_iast'].upper())}</div>
<div class="rule"></div><div class="gloss">“{html.escape(s['gloss'])}”<br><span style="font-size:22px;font-style:normal;letter-spacing:3px">{html.escape(s['gloss_source'])}</span></div></div>
<div class="bottom"><div class="shloka">{'<br>'.join(html.escape(l) for l in lines)}</div><div class="ref">{html.escape(s['ref'])}</div></div>
<div class="label">{html.escape(s.get('label','Text set from the repository; image synthetic'))}</div>
</div></body></html>"""
    out = ROOT / 'visual/cards' / f"{s['id']}.png"
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width':1080,'height':1350})
        pg.set_content(page); pg.wait_for_timeout(400); pg.screenshot(path=str(out)); b.close()
    print(out)

if __name__ == '__main__':
    main(sys.argv[1])
