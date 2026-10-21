# build_post.py HEAD OUT: docs/blog/show-and-tell.md -> one self-contained HTML page (images embedded). The hero, time strip and
# [[SLIDER]] come from ~/.cache/home-alone-board/hero/hero.json (tools/blog/hero_assets.py) and tools/blog/hero.html. Publish OUT to https://claude.ai/artifact/U88DkFDMdj4v2coLFrtVLL
import re, io, base64, sys, json, html as H
from pathlib import Path
import markdown
from PIL import Image
src = Path('/Users/dlo/Dev/home-alone/docs/blog/show-and-tell.md').read_text()
body, _, imgs = src.partition('\n## Images')
imgmap = {}
for m in re.finditer(r'^\| IMG (\d+) \| (\S+) \| [^|]+ \| ([^|]+) \|', imgs, re.M):
    imgmap[m.group(1)] = (m.group(2), m.group(3).strip())
def uri(p):
    im = Image.open(p).convert('RGB')
    if im.width > 1600: im = im.resize((1600, round(im.height*1600/im.width)), Image.LANCZOS)
    if im.height > 2400: im = im.resize((round(im.width*2400/im.height), 2400), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=80, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
lines = body.split('\n')
# drop H1, H2 subtitle and the draft note; they go in the header
title = lines[0].lstrip('# ').strip(); sub = lines[2].lstrip('# ').strip()
rest = '\n'.join(l for l in lines[3:] if not l.startswith('*Draft for'))
rest = re.sub(r'```mermaid\n(.*?)```', lambda m: '<pre class="mermaid">' + m.group(1) + '</pre>', rest, flags=re.S)
def fig(m):
    p, c = imgmap[m.group(1)]
    return f'<figure><img alt="{c}" src="{uri(p)}"><figcaption>{c}</figcaption></figure>'
rest = re.sub(r'\[\[IMG (\d+)\]\]', fig, rest)
D = json.loads((Path.home() / '.cache/home-alone-board/hero/hero.json').read_text())
A = lambda v: H.escape(v, quote=True)
def slider():
    P = D['slider']
    tabs = ''.join(f'<button type="button" aria-pressed="{str(i == 0).lower()}" data-k="{q["key"]}" data-note="{A(q["note"])}">{A(q["label"])}</button>' for i, q in enumerate(P))
    imgs = ''.join(f'<img class="film" data-k="{q["key"]}" alt="{A(q["label"])}, the film"{" hidden" if i else ""} src="{q["film"]}">'
                   f'<img class="ours" data-k="{q["key"]}" alt="{A(q["label"])}, our render"{" hidden" if i else ""} src="{q["ours"]}">' for i, q in enumerate(P))
    return (f'<figure class="slider-fig"><div class="slider-tabs" role="group" aria-label="Pick a pair">{tabs}</div>'
            f'<div class="slider">{imgs}<span class="tag" style="left:10px">Ours</span><span class="tag" style="right:10px">Film</span><span class="bar"></span>'
            f'<input type="range" min="0" max="1000" value="500" aria-label="Divider: drag or use the arrow keys to compare our render with the film"></div>'
            f'<figcaption>{A(P[0]["note"])}</figcaption></figure>')
rest = rest.replace('[[SLIDER]]', slider())
strip = ('<section class="strip" aria-label="Ten days in screenshots, oldest first"><div class="strip-hint">The house over time: drag or scroll sideways</div>'
         '<div class="strip-track" tabindex="0" aria-label="Dated screenshots; use the arrow keys to scroll">'
         + ''.join(f'<figure data-when="{A(q["when"])}" data-cap="{A(q["cap"])}"><img loading="lazy" alt="{A(q["cap"])}" src="{q["src"]}"><span class="when">{A(q["when"])}</span></figure>' for q in D['strip'])
         + '</div><p class="strip-cap" aria-live="polite"></p></section>')
hero = Path(sys.argv[1]).with_name('hero.html').read_text().replace('__HERO_DATA__', json.dumps({k: v for k, v in D.items() if k not in ('slider', 'strip')}).replace('</', '<\\/'))
html = markdown.markdown(rest, extensions=['tables', 'fenced_code'])
html = re.sub(r'<table>', '<div class="tw"><table>', html).replace('</table>', '</table></div>')
css = Path(sys.argv[1]).read_text()
# the intro sits above the hero; the hero is full-bleed, so it closes the first column and the article opens a new one
intro, _, html = html.partition('<p>[[HERO]]</p>')
html = html.replace('<p>[[STRIP]]</p>', strip)
out = css.replace('{{TITLE}}', title).replace('{{SUB}}', sub) + intro + '</article></main>\n' + hero + '\n<main><article>' + html + '</article></main>'
Path(sys.argv[2]).write_text(out); print(len(out)/1e6, 'MB')
