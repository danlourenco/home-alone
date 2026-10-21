#!/usr/bin/env python3
"""test_board.py: one page for every test and comparison sheet (user, Oct 21: one artifact, collapsible sections, what to look at, when).

Reads spec/captures/test-board.json, embeds each image (downscaled), writes ~/.cache/home-alone-board/test-board.html.
Then publish that file to the board URL in the manifest (Artifact tool, url=...). Add a test by adding an entry; newest first.

  uv run --with pillow python -I tools/house/test_board.py            # build the page
  uv run --with pillow python -I tools/house/test_board.py --selftest
"""
import base64, html, io, json, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "spec/captures/test-board.json"
OUT = Path.home() / ".cache/home-alone-board/test-board.html"
ORDER = ["needs-you", "running", "done", "settled", "superseded"]
LABEL = {"needs-you": "Needs you", "running": "In progress", "done": "Ready to look", "settled": "Settled", "superseded": "Superseded"}
MAX_W, MAX_BYTES = 1600, 15_000_000
e = html.escape


def img_uri(src, max_w=None):
    from PIL import Image
    p = Path(src).expanduser()
    p = p if p.is_absolute() else ROOT / p
    if not p.exists():
        return None
    im = Image.open(p).convert("RGB")
    mw = max_w or MAX_W
    if im.width > mw:
        im = im.resize((mw, round(im.height * mw / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=80, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def test_html(t, uri=img_uri):
    s = t.get("status", "done")
    chips = f'<span class="pill {s}">{LABEL.get(s, s)}</span>'
    meta = " · ".join(x for x in (t.get("date"), t.get("app")) if x)
    out = [f'<details class="test" id="{e(t["id"])}"{" open" if s in ("needs-you", "running") else ""}>',
           f'<summary>{chips}<span class="t">{e(t["title"])}</span><span class="meta">{e(meta)}</span></summary><div class="body">']
    if t.get("when"):
        out.append(f'<p class="when"><b>When:</b> {e(t["when"])}</p>')
    if t.get("what"):
        out.append(f'<p>{e(t["what"])}</p>')
    if t.get("look"):
        out.append('<h4>What to look at</h4><ul>' + "".join(f"<li>{e(x)}</li>" for x in t["look"]) + "</ul>")
    for i, c in enumerate(t.get("commands", []), 1):
        out.append(f'<div class="cmd"><span class="n">{i}</span><code>{e(c)}</code><button type="button" class="copy" data-c="{e("! " + c)}">Copy</button></div>')
    if t.get("table"):
        tb = t["table"]
        out.append('<div class="tw"><table><thead><tr>' + "".join(f"<th>{e(h)}</th>" for h in tb["head"]) + "</tr></thead><tbody>"
                   + "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in tb["rows"]) + "</tbody></table></div>")
        if tb.get("note"):
            out.append(f'<p class="note">{e(tb["note"])}</p>')
    for im in t.get("images", []) if s != "superseded" else []:   # the page must stay under 16 MB: superseded tests keep their text only
        u = uri(im["src"], {"settled": 1000, "done": 1600}.get(s, 2600)) if uri is img_uri else uri(im["src"])   # open tests sharper: the lightbox zooms
        out.append(f'<figure><img loading="lazy" tabindex="0" role="button" title="Click to zoom" alt="{e(im.get("caption", ""))}" src="{u}"><figcaption>{e(im.get("caption", ""))}</figcaption></figure>'
                   if u else f'<p class="note">Image missing: {e(im["src"])}</p>')
    out.append("</div></details>")
    return "\n".join(out)


def page(m, uri=img_uri):
    tests = sorted(m["tests"], key=lambda t: ORDER.index(t.get("status", "done")) if t.get("status") in ORDER else 9)
    groups = []
    for s in ORDER:
        g = [t for t in tests if t.get("status") == s]
        if g:
            groups.append(f'<section><h2>{LABEL[s]} <span class="count">{len(g)}</span></h2>' + "\n".join(test_html(t, uri) for t in g) + "</section>")
    dec = "".join(f"<li>{e(d)}</li>" for d in m.get("decisions", []))
    now = datetime.datetime.now().strftime("%b %d, %H:%M")
    return CSS + f"""<main>
<header><h1>Test Board</h1><p class="lede">Every test and comparison for the house, newest first. Open a section for what changed, what to look at, and the sheet. Pinch to zoom on a phone. Updated {now}.</p></header>
{f'<section class="decide"><h2>Your decisions</h2><ul>{dec}</ul></section>' if dec else ''}
{''.join(groups)}
</main>""" + JS


CSS = """<title>Test Board</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400&display=swap">
<style>
/* layout: one reading column of collapsible test cards, grouped by status; needs-you first and open */
:root { --bg:#f2f4f6; --card:#ffffff; --fg:#1d232b; --muted:#5d6773; --line:#d8dde3; --brick:#9a3324;
  --need:#a35c00; --run:#215f9e; --ok:#2e7d4f; --old:#7a828c;
  --display:"Archivo",system-ui,sans-serif; --body:"Source Sans 3",system-ui,sans-serif; --mono:"JetBrains Mono",ui-monospace,monospace; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#13171c; --card:#1b2027; --fg:#e6e9ee; --muted:#9aa4b0; --line:#2c333c; --brick:#d8705a; --need:#e3a14b; --run:#6aa8e6; --ok:#6cc08f; --old:#8b939c; color-scheme:dark } }
:root[data-theme="dark"] { --bg:#13171c; --card:#1b2027; --fg:#e6e9ee; --muted:#9aa4b0; --line:#2c333c; --brick:#d8705a; --need:#e3a14b; --run:#6aa8e6; --ok:#6cc08f; --old:#8b939c; color-scheme:dark }
body { background:var(--bg); color:var(--fg); font:16px/1.5 var(--body); padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); padding-block:24px 48px }
main { max-width:60rem; margin:0 auto; display:grid; gap:28px }
h1 { font:700 2rem/1.1 var(--display); margin:0; letter-spacing:-.01em; text-wrap:balance }
h1::after { content:""; display:block; width:3rem; height:4px; background:var(--brick); margin-top:10px }
.lede { color:var(--muted); max-width:42rem; margin:10px 0 0 }
h2 { font:600 .8rem var(--display); text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin:0 0 10px }
.count { color:var(--fg); margin-left:4px }
section { display:grid; gap:10px }
.decide ul { margin:0; padding:14px 18px 14px 34px; background:var(--card); border:1px solid var(--line); border-left:4px solid var(--need); border-radius:6px; display:grid; gap:6px }
.test { background:var(--card); border:1px solid var(--line); border-radius:6px }
summary { cursor:pointer; list-style:none; display:flex; flex-wrap:wrap; align-items:baseline; gap:6px 12px; padding:14px 16px }
summary::-webkit-details-marker { display:none }
summary::before { content:"▸"; color:var(--muted); transition:transform .15s }
details[open] > summary::before { transform:rotate(90deg) }
summary:focus-visible { outline:2px solid var(--brick); outline-offset:2px }
.t { font:600 1.05rem var(--display); flex:1 1 16rem; min-width:0 }
.meta { color:var(--muted); font:400 .8rem var(--mono) }
.pill { font:600 .7rem var(--body); text-transform:uppercase; letter-spacing:.06em; padding:2px 8px; border-radius:999px; border:1px solid currentColor }
.pill.needs-you { color:var(--need) } .pill.running { color:var(--run) } .pill.done { color:var(--ok) } .pill.settled, .pill.superseded { color:var(--old) }
.body { padding:0 16px 16px; display:grid; gap:12px; min-width:0 }
.body p { margin:0; max-width:65ch }
.when { color:var(--need) }
h4 { margin:4px 0 0; font:600 .85rem var(--display) }
ul { margin:0; padding-left:20px }
.cmd { display:flex; gap:10px; align-items:flex-start; background:var(--bg); border:1px solid var(--line); border-radius:6px; padding:10px; min-width:0 }
.cmd .n { font:600 .8rem var(--mono); color:var(--brick) }
.cmd code { font:400 .78rem/1.45 var(--mono); flex:1; min-width:0; overflow-wrap:anywhere }
.copy { font:600 .8rem var(--body); color:var(--fg); background:var(--card); border:1px solid var(--line); border-radius:4px; padding:4px 10px; cursor:pointer }
.copy:focus-visible { outline:2px solid var(--brick) }
.tw { overflow-x:auto }
table { border-collapse:collapse; font-variant-numeric:tabular-nums; font-size:.9rem }
th, td { text-align:left; padding:6px 12px 6px 0; border-bottom:1px solid var(--line); white-space:nowrap }
th { color:var(--muted); font-weight:600 }
.note { color:var(--muted); font-size:.85rem }
figure { margin:0; display:grid; gap:6px }
figure img { width:100%; height:auto; border-radius:4px; border:1px solid var(--line); cursor:zoom-in }
figure img:focus-visible { outline:2px solid var(--brick); outline-offset:2px }
.lb { position:fixed; inset:0; z-index:50; background:rgba(8,10,12,.94); overflow:hidden; touch-action:none; cursor:grab }
.lb img { position:absolute; left:0; top:0; transform-origin:0 0; max-width:none; user-select:none; -webkit-user-drag:none }
.lb .bar { position:absolute; left:0; right:0; top:0; display:flex; gap:8px; align-items:center; justify-content:flex-end; color:#e6e9ee; font:600 .85rem var(--body);
  padding:calc(10px + env(safe-area-inset-top, 0px)) max(14px, env(safe-area-inset-right, 0px)) 10px max(14px, env(safe-area-inset-left, 0px)); background:linear-gradient(rgba(0,0,0,.6), transparent) }
.lb .bar span { margin-right:auto; opacity:.8; font-weight:400 }
.lb button { font:600 .85rem var(--body); color:#e6e9ee; background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.25); border-radius:4px; padding:6px 12px; cursor:pointer }
figcaption { color:var(--muted); font-size:.85rem }
@media (prefers-reduced-motion: reduce) { summary::before { transition:none } }
</style>
"""

JS = """<script>
// lightbox: click/Enter an image; wheel or pinch zooms at the pointer, drag pans, double-click toggles 1:1, Esc closes
(() => {
  let lb, im, sc = 1, x = 0, y = 0, fit = 1; const pts = new Map(); let last = null, pinch0 = null;
  const apply = () => { im.style.transform = `translate(${x}px,${y}px) scale(${sc})`; };
  const zoomAt = (f, cx, cy) => { const n = Math.min(Math.max(sc * f, fit * 0.5), 8); x = cx - (cx - x) * n / sc; y = cy - (cy - y) * n / sc; sc = n; apply(); };
  const reset = () => { const W = innerWidth, H = innerHeight; fit = Math.min(W / im.naturalWidth, H / im.naturalHeight); sc = fit; x = (W - im.naturalWidth * sc) / 2; y = (H - im.naturalHeight * sc) / 2; apply(); };
  const close = () => { lb?.remove(); lb = null; document.body.style.overflow = ''; last?.focus(); };
  const open = src => {
    lb = document.createElement('div'); lb.className = 'lb'; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-label', 'Zoomed image');
    lb.innerHTML = '<div class="bar"><span>Scroll or pinch to zoom · drag to pan · double-click 1:1</span><button type="button" data-z="in">+</button><button type="button" data-z="out">−</button><button type="button" data-z="fit">Fit</button><button type="button" data-z="x">Close</button></div>';
    im = new Image(); im.src = src; im.alt = ''; lb.prepend(im); document.body.append(lb); document.body.style.overflow = 'hidden';
    im.decode().then(reset, reset); lb.querySelector('[data-z="x"]').focus();
    lb.addEventListener('click', e => { const z = e.target.dataset?.z; if (!z) return; const W = innerWidth / 2, H = innerHeight / 2;
      if (z === 'x') close(); else if (z === 'fit') reset(); else zoomAt(z === 'in' ? 1.5 : 1 / 1.5, W, H); });
    lb.addEventListener('wheel', e => { e.preventDefault(); zoomAt(Math.exp(-e.deltaY * 0.0015), e.clientX, e.clientY); }, { passive: false });
    lb.addEventListener('dblclick', e => { if (e.target.closest('.bar')) return; Math.abs(sc - 1) < 0.01 ? reset() : zoomAt(1 / sc, e.clientX, e.clientY); });
    lb.addEventListener('pointerdown', e => { if (e.target.closest('.bar')) return; lb.setPointerCapture(e.pointerId); pts.set(e.pointerId, [e.clientX, e.clientY]); pinch0 = null; });
    lb.addEventListener('pointermove', e => { if (!pts.has(e.pointerId)) return; const p = pts.get(e.pointerId);
      if (pts.size === 1) { x += e.clientX - p[0]; y += e.clientY - p[1]; apply(); }
      else { const [a, b] = [...pts.values()]; const d = Math.hypot(a[0] - b[0], a[1] - b[1]); if (pinch0) zoomAt(d / pinch0, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2); pinch0 = d; }
      pts.set(e.pointerId, [e.clientX, e.clientY]); });
    const up = e => { pts.delete(e.pointerId); pinch0 = null; }; lb.addEventListener('pointerup', up); lb.addEventListener('pointercancel', up);
  };
  document.addEventListener('click', e => { const t = e.target.closest('figure img'); if (t) { last = t; open(t.src); } });
  document.addEventListener('keydown', e => { if (lb && e.key === 'Escape') close(); else if (!lb && e.key === 'Enter' && e.target.matches?.('figure img')) { last = e.target; open(e.target.src); } });
  addEventListener('resize', () => lb && reset());
})();
document.addEventListener('click', ev => {
  const b = ev.target.closest('.copy'); if (!b) return;
  const done = () => { b.textContent = 'Copied'; setTimeout(() => b.textContent = 'Copy', 1500); };
  const pick = () => { const r = document.createRange(); r.selectNodeContents(b.previousElementSibling); const s = getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = 'Selected'; };
  try { navigator.clipboard.writeText(b.dataset.c).then(done, pick); } catch (_) { pick(); }
});
</script>"""


def selftest():
    m = {"tests": [{"id": "a", "title": "Old", "status": "superseded"}, {"id": "b", "title": "Do <this>", "status": "needs-you", "commands": ["echo hi"], "images": [{"src": "nope.jpg"}]}]}
    h = page(m, uri=lambda s: None)
    assert h.index("Do &lt;this&gt;") < h.index("Old"), "needs-you sorts first"
    assert 'id="b" open' in h and 'id="a" open' not in h
    assert 'data-c="! echo hi"' in h and "Image missing" in h
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit()
    h = page(json.loads(MANIFEST.read_text()))
    assert len(h) < MAX_BYTES, f"page {len(h)/1e6:.1f} MB: too big, drop superseded images"
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(h)
    print(f"{OUT} ({len(h)/1e6:.1f} MB)")
