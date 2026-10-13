"""Rebuild diagnostic plates from archived survey data; no model geometry is changed."""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/home_alone/references/reconciliation'
DATA = json.loads((ROOT/'art/home_alone/references/survey/house_survey.json').read_text())
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
BG='#f7f5ef'; INK='#24313b'; BLUE='#2578a9'; RED='#b44b44'; GREEN='#278369'
def font(n): return ImageFont.truetype(FONT,n)
def canvas(title, sub, h=1050):
 im=Image.new('RGB',(1700,h),BG); d=ImageDraw.Draw(im)
 d.text((45,28),title,font=font(32),fill=INK);d.text((45,76),sub,font=font(18),fill=INK)
 return im,d

def grid(d,x,y,w,h,xlim,ylim):
 scale=min(w/(xlim[1]-xlim[0]),h/(ylim[1]-ylim[0]))
 def p(a,b):return (x+(a-xlim[0])*scale,y+h-(b-ylim[0])*scale)
 for a in range(math.ceil(xlim[0]),math.floor(xlim[1])+1):
  d.line([p(a,ylim[0]),p(a,ylim[1])],fill='#e1dfd7');
  if a%5==0:d.text(p(a,ylim[0]),str(a),font=font(13),fill=INK)
 for b in range(math.ceil(ylim[0]),math.floor(ylim[1])+1):
  d.line([p(xlim[0],b),p(xlim[1],b)],fill='#e1dfd7')
  if b%5==0:d.text(p(xlim[0],b),str(b),font=font(13),fill=INK)
 return p

def rect(d,p,r,color,width=2):
 x0,x1,y0,y1=r;d.line([p(x0,y0),p(x0,y1),p(x1,y1),p(x1,y0),p(x0,y0)],fill=color,width=width)
def rooms(d,p,which,color,transform=lambda x,y:(x,y)):
 for name,r in DATA[which]['rooms'].items():
  if name in ('vestibule','closet_off_breakfast','main_stair_well'):continue
  a,b=transform(r['x'][0],r['y'][0]),transform(r['x'][1],r['y'][1])
  rect(d,p,(*sorted([a[0],b[0]]),*sorted([a[1],b[1]])),color)
mesh=np.load(OUT/'exterior-slices.npz')
im,d=canvas('01 / Where the floor plans disagree','Same metres and plot scale in all panels. These are existing candidates, not an adopted floor plan.')
for i,title in enumerate(['Marina upper: translation only','Current Unity upper transform','Older Godot ground floor']):
 x=45+i*550;d.text((x,128),title,font=font(21),fill=INK)
 p=grid(d,x+5,180,510,570,(-1,25),(-1,24))
 rooms(d,p,'ground',BLUE)
 for seg in mesh['1.5']:
  if np.all((seg[:,0]>-1)&(seg[:,0]<25)&(seg[:,1]>-1)&(seg[:,1]<24)):
   d.line([p(*q) for q in seg],fill='#a4aaa5',width=1)
 if i<2:
  fn=(lambda x,y:(x+4.1,y+.08)) if i==0 else (lambda x,y:(4.1+(13.02-x)*14.44/13.02,.36+(y-.28)*16.38/18.62))
  rooms(d,p,'upper',RED,fn)
 else:
  # Translation aligns front door/foyer centre; no scale correction.
  for r in [(-12.1,-7.8,.8,8.3),(-7.8,-2.2,0,9.3),(-2.2,2.2,0,10.6),(2.2,7.6,0,6.8),(7.6,12,.7,6.8),(2.2,8.5,6.8,10),(2.2,6,10,14.2),(6,11.2,10,10+477*.09290304/5.2)]:
   rect(d,p,(r[0]+11.2,r[1]+11.2,r[2]+.2,r[3]+.2),GREEN)
 rect(d,p,(9.12,10.4,3.7,7.9),INK,3)
 d.text((x,875),['X +4.10; rear coordinate +0.08 m.','Mirror X; scale X 1.109, depth 0.880.','X +11.20; rear coordinate +0.20 m.'][i],font=font(16),fill=INK)
 d.text((x,903),['Front aligned; stair/wing mismatch remains.','Shown BEFORE hall replacement/room trimming.','Recovered shape; still estimated dimensions.'][i],font=font(15),fill=INK)
d.text((45,970),'Blue: raw ground survey   Red: upper survey   Green: Godot candidate   Grey: original exterior slice at +1.5 m',font=font(19),fill=INK)
d.text((45,1000),'Black: current Unity main-stair footprint. Grey uses existing shell scale 0.83, not a newly calibrated alignment.',font=font(17),fill=INK)
im.save(OUT/'01-floor-overlays.png')

im,d=canvas('02 / Stair sections reveal the missing connections','Unfolded walking paths: a turn is marked along the path, not drawn as a straight physical flight.',1050)
metrics={}
for i,(title,run,rise,end,label) in enumerate([
 ('Unity main stair',4.2,3.0,3.0,'Single flight: no intermediate landing or turning flight.'),
 ('Godot main stair / candidate to recover',4.8,2.68,3.35,'16 rises to rear landing; four more turning steps to +3.35 m.'),
 ('Unity breakfast stair',2.6,2.2,3.0,'Landing is 2.84 m long; missing 0.80 m rise and onward connection.'),
 ('Godot breakfast stair',3.55,3.35,3.35,'Full-height visible flight, but no upper-floor exit is modelled.')]):
 col=i%2;row=i//2;x=45+col*840;y=135+row*420
 d.text((x,y),title,font=font(23),fill=INK)
 p=grid(d,x+20,y+48,755,265,(-.3,8),(-.2,4.5))
 d.line([p(0,0),p(run,rise)],fill=BLUE,width=5)
 landing=1.2 if i==1 else (2.84 if i==2 else .6)
 d.line([p(run,rise),p(run+landing,rise)],fill=BLUE,width=5)
 if i==1:
  d.line([p(6,2.68),p(7.24,3.35),p(7.7,3.35)],fill=GREEN,width=5)
  d.text(p(5.0,1.3),'turn ->',font=font(17),fill=GREEN)
 if i==2:
  d.line([p(run+landing,rise),p(run+landing,end)],fill=RED,width=4)
  d.text(p(5.5,2.4),'unresolved',font=font(15),fill=RED)
 d.line([p(0,end),p(8,end)],fill='#b7b2a7',width=2)
 pitch=math.degrees(math.atan2(rise,run));metrics[title]={'run_m':run,'rise_m':rise,'pitch_degrees':round(pitch,2),'upper_level_m':end}
 d.text((x,y+325),f'Rise {rise:.2f} m / run {run:.2f} m = {pitch:.1f} degrees',font=font(18),fill=INK)
 d.text((x,y+354),label,font=font(15),fill=INK)
d.text((45,980),'Unity breakfast landing underside: +2.00 m (2.20 minus 0.20 slab). Godot service pitch: 43.3 degrees.',font=font(18),fill=INK)
d.text((45,1008),'Sections compare existing geometry. Final wells, headroom and turn clearances require the coupled plan; no compliance claim.',font=font(17),fill=INK)
im.save(OUT/'02-stair-sections.png')

im,d=canvas('03 / Exterior and floor levels must be fitted together','Original exterior mesh projected at the CURRENT Unity scale/translation. Projection includes rear surfaces.',950)
pts=mesh['points']; q=pts[(pts[:,0]>3.8)&(pts[:,0]<19)&(pts[:,1]>-.5)&(pts[:,1]<11.5)&(pts[:,2]>-.2)]
for i,(title,axis,lim) in enumerate([('Main-block front projection',0,(3,20)),('Main-block side projection',1,(-1,13))]):
 x=45+i*830;d.text((x,130),title,font=font(23),fill=INK);p=grid(d,x+15,190,755,570,lim,(-.5,12))
 edges=mesh['edges']
 keep=np.all((edges[:,:,0]>3.8)&(edges[:,:,0]<19)&(edges[:,:,1]>-.5)&(edges[:,:,1]<11.5)&(edges[:,:,2]>-.2),axis=1)
 for edge in edges[keep]:
  d.line([p(v[axis],v[2]) for v in edge],fill='#b5beb5',width=1)
 for z,name,color in [(0,'Ground 0.00',INK),(3,'Unity upper 3.00',BLUE),(3.35,'Godot upper 3.35',GREEN),(5.85,'Unity attic floor 5.85',BLUE),(8.25,'Unity attic ceiling 8.25',RED)]:
  d.line([p(lim[0],z),p(lim[1],z)],fill=color,width=2)
  d.text((x+20,p(lim[0],z)[1]-22),name,font=font(16),fill=color)
d.text((45,825),'This diagnoses level relationships; it is not a front-visible architectural elevation or proof of roof clearance.',font=font(20),fill=INK)
d.text((45,861),'Next: fit roof sections at the actual attic room and stair positions, with floor structure and occupied headroom.',font=font(19),fill=INK)
im.save(OUT/'03-exterior-levels.png')

# One independent arithmetic check catches transform reversal/scale mistakes in the packet.
assert abs((4.1+(13.02-0)*14.44/13.02)-18.54)<1e-8
assert abs((.36+(18.90-.28)*16.38/18.62)-16.74)<1e-8
assert abs(16*.1675+4*.1675-3.35)<1e-8
assert 40 < metrics['Unity breakfast stair']['pitch_degrees'] < 41
(OUT/'section-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
print('Three diagnostic plates and section metrics generated; arithmetic checks pass.')

im,d=canvas('04 / Visitor plans: an independent stacking check','Ground scale from its 15 ft living-room label; upper scale transfers that corresponding span. These are visitor drawings.',1000)
p=grid(d,60,180,950,720,(-1,24),(-1,20))
# Register facade centre/front line. No independent stretching of X and Y.
for filename,ppm,anchor,color in [('real-house-first-floor.jpg',168/4.572,(379,580),BLUE),('real-house-second-floor.jpg',169/4.572,(400,436),RED)]:
 src=Image.open(ROOT/'art/home_alone/references/survey'/filename).convert('RGB')
 ar=np.asarray(src); mask=(ar.min(2)<170)&(ar.max(2)-ar.min(2)>35)
 # Restrict to wall outlines, excluding grey annotation lines and most furniture.
 if filename.startswith('real-house-first'):mask &= (ar[:,:,1]>ar[:,:,0]*1.2)&(ar[:,:,1]>ar[:,:,2]*1.2)
 else:mask &= (ar[:,:,1]>ar[:,:,0]*1.2)&(ar[:,:,1]>ar[:,:,2]*1.2)
 yy,xx=np.nonzero(mask)
 for px,py in zip(xx,yy):
  X=11.2+(px-anchor[0])/ppm;Y=.2+(anchor[1]-py)/ppm
  d.point(p(X,Y),fill=color)
d.text((1060,200),'Blue: visitor ground floor',font=font(22),fill=BLUE)
d.text((1060,235),'Red: visitor upper floor',font=font(22),fill=RED)
notes=['Ground: 36.745 px/metre','Upper: 36.964 px/metre','Front datum: (11.20, 0.20) m','','Independent check: main rear wall','Ground y = 8.58 m (pixel 272)','Upper y = 8.75 m (pixel 120)','Residual = 0.17 m','','Left main-block facade residual','approximately 0.07 m.','','Residuals describe drawing agreement,','not measurement accuracy.','Upper and lower footprints differ;','their stair cores are useful candidates.']
for j,line in enumerate(notes):d.text((1060,300+j*30),line,font=font(19),fill=INK)
d.text((60,942),'Registering these drawings does not establish that Marina’s independently reconstructed upstairs has the same proportions.',font=font(19),fill=INK)
im.save(OUT/'04-visitor-plan-overlay.png')

im,d=canvas('05 / Preserve the recognizable interior compositions','Source and saved Godot views are similar directions, not calibrated camera matches. Godot remains a blockout.',1120)
pairs=[('Marina / main stair 05:40',OUT/'main-340.jpg'),('Godot / saved foyer',ROOT/'art/home_alone/marina/godot-foyer.png'),('Marina / breakfast 18:34',OUT/'breakfast-1114.jpg'),('Godot / saved breakfast',ROOT/'art/home_alone/marina/godot-breakfast.png')]
for i,(label,path) in enumerate(pairs):
 x=45+(i%2)*835;y=135+(i//2)*470
 d.text((x,y),label,font=font(23),fill=INK)
 pic=Image.open(path);pic.thumbnail((790,410));im.paste(pic,(x,y+40))
im.save(OUT/'05-interior-comparisons.png')
print('Visitor overlay and interior comparisons generated.')

im,d=canvas('06 / Main stair: a concrete fit candidate to test','Proposal only: recover the turning form and test +3.35 m upper level. Dimensions below are authored, not surveyed.',1050)
p=grid(d,65,180,590,710,(8.7,14),(2.8,11.5))
rect(d,p,(9.12,13.23,3.0,11.01),INK,3)
rect(d,p,(9.12,10.40,3.7,8.5),BLUE,4)
for i in range(17):d.line([p(9.12,3.7+i*.3),p(10.4,3.7+i*.3)],fill=BLUE,width=2)
rect(d,p,(9.12,10.4,8.5,11.01),GREEN,4)
rect(d,p,(10.4,11.64,9.0,10.3),GREEN,4)
for i in range(5):d.line([p(10.4+i*.31,9),p(10.4+i*.31,10.3)],fill=GREEN,width=2)
rect(d,p,(11.64,13.23,3.0,11.01),RED,4)
d.text(p(9.18,6.0),'16 rises',font=font(16),fill=BLUE)
d.text(p(9.17,10.7),'landing',font=font(15),fill=GREEN)
d.text(p(11.78,8.7),'gallery',font=font(15),fill=RED)
d.line([p(9.6,11.01),p(11.4,11.01)],fill='#c99837',width=7)
d.text((710,165),'Fit and clearance budget',font=font(26),fill=INK)
lines=['Foyer envelope: 4.11 m wide (current survey).','Lower flight: 1.28 m wide, 4.80 m run, 16 rises.','Riser: 0.1675 m; rear landing at +2.68 m.','Turning flight: 1.24 m run, four rises to +3.35 m.','Gallery available width: 1.59 m before rails/trim.','','Landing slab assumed 0.20 m: underside +2.48 m.','Reserve a 2.10 m clear passage below it.','Main stair sits in an open, double-height foyer;','remove the current slab over its full rise/turn.','','Gold line: current rear-window span, to camera-fit.','At sill +3.30 m it is 0.62 m above this landing.','','This fits the plan envelope arithmetically.','Traversal-tested; source camera fit still open.','Roof, gallery access and both stair arrivals must','be reconciled before adopting the 3.35 m level.']
for j,line in enumerate(lines):d.text((710,215+j*32),line,font=font(20),fill=INK)
d.text((65,945),'Breakfast stair: reserve its own upper arrival near the parents’ area; do not attach it to the main stair by assumption.',font=font(20),fill=INK)
d.text((65,983),'Basement access: retain the breakfast-room door established in Part 2. Exact descent and hidden service turns remain open.',font=font(19),fill=INK)
im.save(OUT/'06-main-stair-fit-candidate.png')
assert 13.23-11.64>1.5 and 2.68-.2>2.1

# Candidate bounds exported from the built Unity scene, rather than another hand-fitted floor plan.
geometry = ROOT/'unity/HomeAlone/Captures/ConnectedStairStudy/geometry.json'
if geometry.exists():
 built = {v['name']:v for v in json.loads(geometry.read_text())}
 im,d=canvas('07 / Connected stair candidate: the cost of making it fit',
             'Traversal-tested hypothesis. Grey is the ORIGINAL exterior at the existing transform; final registration remains open.',1120)
 for col,(title,level) in enumerate([('Ground / visible room sequence','1.5'),('Upper / authored return corridor','4.5')]):
  x=45+col*810;d.text((x,125),title,font=font(23),fill=INK)
  p=grid(d,x,175,760,650,(8,20),(4,17))
  for seg in mesh[level]:
   if np.all((seg[:,0]>8)&(seg[:,0]<20)&(seg[:,1]>4)&(seg[:,1]<17)):
    d.line([p(*v) for v in seg],fill='#a0aaa5',width=2)
  rect(d,p,(9.15,13.28,4,11.05),BLUE,2)
  rect(d,p,(13.44,17.5,6.86,12.64),BLUE,2)
  names=['HutchBase','VisibleServiceFlight','ServiceLanding','HiddenServiceTurn'] if col==0 else ['VisibleServiceFlight','ServiceLanding','HiddenServiceTurn','UpperReturn','UpperLink']
  for name in names:
   b=built[name];a,c=b['min'],b['max'];color=GREEN if name in ('HutchBase','VisibleServiceFlight') else RED
   rect(d,p,(a[0],c[0],a[2],c[2]),color,4)
   labels={'HutchBase':'hutch','VisibleServiceFlight':'12 rises','ServiceLanding':'+2.01','HiddenServiceTurn':'8 rises','UpperReturn':'+3.35','UpperLink':'upper link'}
   d.text(p(a[0]+.06,c[2]-.14),labels[name],font=font(15),fill=color)
  if col==0:
   d.line([p(13.28,9.05),p(13.28,10.4)],fill='#c99837',width=8)
   d.text(p(9.3,9.9),'foyer door ->',font=font(17),fill=INK)
  else:
   rect(d,p,(11.64,13.23,4,11.01),GREEN,3)
   d.text(p(11.8,7.8),'main gallery',font=font(15),fill=GREEN)
 notes=['Green: source-visible grouping; dimensions still authored. Red: hidden connection invented for this study.',
        'Breakfast flight: 12 rises x 0.1675 m, 3.00 m run; landing 1.18 x 1.20 m. East turn: 8 rises, 2.00 m run.',
        'The rear stair bay reaches Z 14.80 m: 2.16 m past the existing breakfast rear wall at Z 12.64 m.',
        'Upper link crosses above the LOW end of the flight (Z 10.40-11.60); the first, deeper crossing blocked headroom.',
        '42 continuous walking checkpoints pass both ways. This does not validate roof containment or historical dimensions.',
        'Keep the original exterior intact while resolving these rear wing / upper corridor conflicts. No front-facade changes adopted.']
 for i,line in enumerate(notes):d.text((45,882+i*33),line,font=font(19),fill=INK)
 im.save(OUT/'07-connected-stair-footprint.png')
 assert abs(built['ServiceLanding']['max'][1]-2.01)<.03
 assert abs(built['UpperLink']['max'][1]-3.35)<.001
 print('Connected stair footprint generated from Unity bounds.')
