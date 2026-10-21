# build_post.py HEAD OUT: docs/blog/show-and-tell.md -> one self-contained HTML page (images embedded). Publish OUT to https://claude.ai/artifact/U88DkFDMdj4v2coLFrtVLL
import re, io, base64, sys
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
html = markdown.markdown(rest, extensions=['tables', 'fenced_code'])
html = re.sub(r'<table>', '<div class="tw"><table>', html).replace('</table>', '</table></div>')
css = Path(sys.argv[1]).read_text()
out = css.replace('{{TITLE}}', title).replace('{{SUB}}', sub) + html + '</article></main>'
Path(sys.argv[2]).write_text(out); print(len(out)/1e6, 'MB')
