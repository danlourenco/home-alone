import json, cv2, numpy as np
FT2=0.09290304
S='/private/tmp/claude-501/-Users-dlo-Dev-home-alone/1462a0ae-e474-4f69-957a-73ff0f12f2e8/scratchpad'
OUT='/Users/dlo/Dev/home-alone/art/home_alone/references/survey'
# ---------- ground ----------
G_ROOMS={ # wall-top-level inner faces, rectified px (x0,x1,y0,y1); y grows toward the FRONT
 'den':(466,785,749,1345),'living':(800,1170,682,1397),'fireplace_recess':(930,1053,619,671),
 'foyer':(1185,1512,550,1410),'vestibule':(1185,1512,1310,1410),'dining':(1525,1924,919,1393),
 'sunroom':(1934,2248,753,1335),'service_stair_bay':(1525,1606,420,882),'breakfast':(1614,1847,420,882),
 'breakfast_extension':(1847,1934,737,882),'kitchen':(1847,2250,94,737),'closet_off_breakfast':(1890,2000,753,800)}
G_FEATURES={ # px, wall-top frame; floor-level items already corrected (y-103, x about nadir 1286 x1.116)
 'front_door_centre':(1350,1424),'main_stair_foot':(1237,1130),'main_stair_top_landing':(1237,800),
 'foyer_rear_arch_door':(1290,550),'foyer_to_breakfast_opening':(1512,760),
 'kitchen_back_door':(1910,94),'kitchen_rear_window_sink':(2070,94),
 'window_seat_1':(2250,290),'window_seat_2':(2250,470),'fridge':(2215,120),
 'island_long_leg_x':(2038,2094),'island_y':(237,497),'island_L_foot':(1960,2094),'island_L_y':(457,497),
 'service_stair_foot':(1565,700),'service_stair_landing':(1565,450),
 'living_fireplace':(992,671),'dining_table':(1720,1150),'breakfast_table':(1748,670)}
G_OPEN={ # (wall, from px, to px) along the wall
 'den_living_double_door':('x=785..800',1140,1280),'living_foyer_cased':('x=1170..1185',1150,1290),
 'foyer_dining_french':('x=1512..1525',1140,1290),'dining_sunroom_french':('x=1924..1934',1110,1290),
 'foyer_breakfast_arch':('x=1512..1525',690,830),'breakfast_corridor':('x=1607..1613',752,881),
 'service_stair_landing_open':('x=1607..1613',488,559),'kitchen_back_door':('y=82..94',1880,1940),
 'kitchen_rear_window':('y=82..94',2040,2100),'vestibule_inner_door':('y=1300..1309',1305,1400)}
ga=sum((r[1]-r[0])*(r[3]-r[2]) for k,r in G_ROOMS.items() if k not in('vestibule','closet_off_breakfast'))
ppm_g=(ga/(2620*FT2))**0.5; ox,oy=459,1426   # origin: front-left OUTER corner of ground envelope (den left outer wall, living front outer)
def gm(x,y): return round((x-ox)/ppm_g,2), round((oy-y)/ppm_g,2)
ground={'px_per_m':round(ppm_g,3),'origin_px':[ox,oy],'axes':'X east (+right in overhead), Y toward rear (+up in overhead); metres from front-left outer corner','rooms':{},'openings':{},'features':{}}
for k,(x0,x1,y0,y1) in G_ROOMS.items():
    (X0,Y0),(X1,Y1)=gm(x0,y1),gm(x1,y0)
    ground['rooms'][k]={'x':[X0,X1],'y':[Y0,Y1],'w':round(X1-X0,2),'d':round(Y1-Y0,2),'area_m2':round((X1-X0)*(Y1-Y0),1),'area_ft2':round((X1-X0)*(Y1-Y0)/FT2)}
for k,(w,a,b) in G_OPEN.items():
    if w.startswith('x='):
        xw=int(w[2:].split('..')[0]); ground['openings'][k]={'wall':w,'x_m':gm(xw,0)[0],'y_m':[gm(0,b)[1],gm(0,a)[1]],'width_m':round((b-a)/ppm_g,2)}
    else:
        yw=int(w[2:].split('..')[0]); ground['openings'][k]={'wall':w,'y_m':gm(0,yw)[1],'x_m':[gm(a,0)[0],gm(b,0)[0]],'width_m':round((b-a)/ppm_g,2)}
for k,v in G_FEATURES.items():
    if k.endswith('_x') or k.endswith('_foot') and 'island' in k: ground['features'][k]=[gm(v[0],0)[0],gm(v[1],0)[0]]
    elif k.endswith('_y'): ground['features'][k]=[gm(0,v[1])[1],gm(0,v[0])[1]]
    else: ground['features'][k]=list(gm(*v))
ground['interior_area_m2']=round(ga/ppm_g**2,1); ground['kitchen_share']=round(G_ROOMS and ((2250-1847)*(737-94))/ga,4)
ground['envelope_m']={'width':round((2264-459)/ppm_g,2),'depth':round((1426-81)/ppm_g,2)}
ground['wall_thickness_m']=round(13/ppm_g,2)
# ---------- upper ----------
U_ROOMS={'parents_bedroom':(945,1274,79,300),'parents_bedroom_L':(945,1166,300,403),'master_bath':(751,882,125,355),'master_bath_L':(882,930,239,355),
 'girls_room_rear':(755,1078,414,552),'girls_room_rear_notch':(755,930,368,414),'linen_closet':(1095,1166,420,552),'kevin_jeff_room':(1179,1473,325,555),'hall_bathroom':(1198,1470,572,694),
 'upper_hall':(1095,1184,572,1083),'main_stair_well':(1095,1182,830,1000),'girls_room_front':(755,1078,800,1073),'buzz_room':(1203,1430,707,1083)}
ua=sum((r[1]-r[0])*(r[3]-r[2]) for k,r in U_ROOMS.items() if k!='main_stair_well')
ppm_u=(ua/(1900*FT2))**0.5; uox,uoy=742,1098
def um(x,y): return round((x-uox)/ppm_u,2), round((uoy-y)/ppm_u,2)
upper={'px_per_m':round(ppm_u,3),'origin_px':[uox,uoy],'axes':'X east, Y toward rear; metres from the upper block front-left outer corner (separate frame from ground)','rooms':{}}
for k,(x0,x1,y0,y1) in U_ROOMS.items():
    (X0,Y0),(X1,Y1)=um(x0,y1),um(x1,y0)
    upper['rooms'][k]={'x':[X0,X1],'y':[Y0,Y1],'w':round(X1-X0,2),'d':round(Y1-Y0,2),'area_m2':round((X1-X0)*(Y1-Y0),1),'area_ft2':round((X1-X0)*(Y1-Y0)/FT2)}
upper['interior_area_m2']=round(ua/ppm_u**2,1); upper['facade_width_m']=round((1444-742)/ppm_u,2); upper['depth_m']=round((1098-62)/ppm_u,2)
upper['wall_thickness_m']=round(17/ppm_u,2)
# ---------- attic ----------
ax0,ax1,ay0,ay1=670,1248,58,1020; aa=(ax1-ax0)*(ay1-ay0); ppm_a=(aa/(476*FT2))**0.5
attic={'px_per_m':round(ppm_a,3),'source':'Part 2 14:00 orthographic top-down frame (1920x1080)','room':{'w':round((ax1-ax0)/ppm_a,2),'d':round((ay1-ay0)/ppm_a,2)},
 'stair_well':{'x':[round((896-ax0)/ppm_a,2),round((1022-ax0)/ppm_a,2)],'y_from_rear':[round((489-ay0)/ppm_a,2),round((773-ay0)/ppm_a,2)]},
 'chimney':{'x':[round((910-ax0)/ppm_a,2),round((1000-ax0)/ppm_a,2)],'depth_from_rear_wall':round((150-ay0)/ppm_a,2)}}
json.dump({'ground':ground,'upper':upper,'attic':attic,
 'calibration':{'main_floor_ft2':2620,'upstairs_ft2':1900,'attic_ft2':476,'kitchen_ft2':477,'source':'Marina Coates tour onscreen figures: Part 1 13:23 (kitchen), Part 2 11:00 (floor table)'}},
 open(OUT+'/house_survey.json','w'),indent=1)
print(json.dumps(ground,indent=1)); print(json.dumps(upper,indent=1)); print(json.dumps(attic,indent=1))
# ---------- annotated plan images ----------
def draw(src,dst,ppm,ox,oy,rooms,labels_m=True,extra=None):
    im=cv2.imread(src); H,W=im.shape[:2]
    for i in range(0,60):
        x=int(ox+i*ppm); 
        if 0<=x<W: cv2.line(im,(x,0),(x,H),(255,255,0) if i%5==0 else (120,120,0),2 if i%5==0 else 1); cv2.putText(im,f"{i}m",(x+2,18),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,255),1)
        y=int(oy-i*ppm)
        if 0<=y<H: cv2.line(im,(0,y),(W,y),(255,255,0) if i%5==0 else (120,120,0),2 if i%5==0 else 1); cv2.putText(im,f"{i}m",(2,y-3),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,255),1)
    for k,(x0,x1,y0,y1) in rooms.items():
        cv2.rectangle(im,(x0,y0),(x1,y1),(0,0,255),2)
        w=(x1-x0)/ppm; d=(y1-y0)/ppm
        cv2.putText(im,k,(x0+4,y0+16),cv2.FONT_HERSHEY_SIMPLEX,0.45,(255,255,255),2); cv2.putText(im,k,(x0+4,y0+16),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,0,255),1)
        cv2.putText(im,f"{w:.1f}x{d:.1f}m",(x0+4,y0+32),cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,255,255),2); cv2.putText(im,f"{w:.1f}x{d:.1f}m",(x0+4,y0+32),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
    cv2.imwrite(dst,im,[cv2.IMWRITE_JPEG_QUALITY,90])
draw(S+'/ground_rect.png',OUT+'/ground-plan-rectified.jpg',ppm_g,ox,oy,G_ROOMS)
draw(S+'/upper_rect.png',OUT+'/upper-plan-rectified.jpg',ppm_u,uox,uoy,U_ROOMS)
draw(S+'/p2plans/p2_840s.png',OUT+'/attic-plan-ortho.jpg',ppm_a,ax0,ay1,{'attic':(ax0,ax1,ay0,ay1),'stair_well':(896,1022,489,773),'chimney':(910,1000,44,150)})
print('images written')
