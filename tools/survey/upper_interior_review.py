"""Draw the saved Unity upstairs layout over the ground survey; no image fitting implied."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
j = json.loads((ROOT / 'art/home_alone/references/survey/house_survey.json').read_text())
u = json.loads((ROOT / 'unity/HomeAlone/Captures/UpperInterior/layout.json').read_text())
out = ROOT / 'art/home_alone/references/reconciliation/08-upstairs-registration.png'
im = Image.new('RGB', (1500, 1060), '#f7f5ef')
d = ImageDraw.Draw(im, 'RGBA')
font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
f = ImageFont.truetype(font_path, 19)
small = ImageFont.truetype(font_path, 15)
big = ImageFont.truetype(font_path, 29)
def point(x, z): return (45 + x * 43, 970 - z * 43)
def rect(x0,x1,z0,z1): return (*point(x0,z1), *point(x1,z0))
d.text((40,24),'Upstairs aligned to the main staircase',fill='#172d34',font=big)
d.text((40,65),'Working geometry — clockwise rotation, uniform 0.80 scale, local clearance adjustments',fill='#47545b',font=f)
for n in range(24):
    d.line((*point(n,0),*point(n,19)), fill=(50,65,70,25))
    if n%2==0:d.text(point(n,-.4),str(n),fill='#555555',font=small)
for n in range(20): d.line((*point(0,n),*point(23,n)),fill=(50,65,70,25))
for r in j['ground']['rooms'].values():
    d.rectangle(rect(*r['x'],*r['y']),outline=(70,70,70,190),width=2)
# Original image-derived rectangles under the same rigid registration, including known tracing errors.
for name,r in j['upper']['rooms'].items():
    if name=='main_stair_well':continue
    d.rectangle(rect(5.336+.8*r['y'][0],5.336+.8*r['y'][1],11-.8*r['x'][1],11-.8*r['x'][0]),outline=(110,80,165,160),width=2)
colors=['#e9ad67','#e9ad67','#77c3cc','#77c3cc','#9fc98d','#e9ad67','#e9ad67','#e9ad67','#d798b5','#d798b5','#77c3cc','#77c3cc','#f2d279']
labels=['West bedroom','Buzz','Hall bathroom','Bathroom extension','Linen closet','Kevin','Sister','Sister extension',"Parents’ entry",'Parents','Ensuite entry','Ensuite','Hall']
for i,(r,c) in enumerate(zip(u['rooms'],colors),1):
    rgb=tuple(bytes.fromhex(c[1:]))
    d.rectangle(rect(r['x0'],r['x1'],r['y0'],r['y1']),fill=(*rgb,135),outline=(*rgb,255),width=3)
    cx,cy=point((r['x0']+r['x1'])/2,(r['y0']+r['y1'])/2)
    d.text((cx-7,cy-10),str(i),fill='#132f3a',font=f)
d.rectangle(rect(9.15,11.64,5.4,5.76),fill='#f7f5ef',outline='#c14638',width=2)
d.rectangle(rect(9.15,10.4,3.7,8.5),outline='#c14638',width=4)
d.rectangle(rect(9.15,13.28,8.5,11.05),outline='#c14638',width=4)
d.rectangle(rect(11.64,13.28,7.26,8.5),outline='#c14638',width=4)
d.text(point(8.4,11.8),'Rear landing +2.68 m',fill='#9f3329',font=f)
d.text(point(7.8,-1.25),'FRONT / VESTIBULE',fill='#172d34',font=f)
d.text((1070,130),'Room key',fill='#172d34',font=big)
for i,label in enumerate(labels,1):d.text((1070,175+i*30),f'{i:2}. {label}',fill='#172d34',font=f)
for i,line in enumerate(['Grey: downstairs survey','Purple: old upstairs rectangles','Colour: new upstairs rooms','Red: stairs and headroom cut','', 'Room sizes remain provisional.', 'The bathroom overlaps the front', 'foyer / vestibule in this fit.', '', 'Local adjustments:', '• West bedrooms narrowed', '• Hall edge recessed 0.36 m', '• Ensuite entry widened 0.52 m', '• Survey room labels corrected']):
    d.text((1070,620+i*26),line,fill='#47545b',font=small)
im.save(out)
print(out)
