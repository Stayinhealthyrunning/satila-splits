#!/usr/bin/env python3
"""Rebuild two normalized participant-derived race-course displays from exact owner originals.

Requires numpy and scipy; keeps all raw originals untouched. No split times generated.
The current reconstruction is NEW and is not falsely represented as byte-identical
to the earlier two missing normalized exports. See research/NORMALIZED_43KM_ROUTES.md.
"""
from pathlib import Path
from math import radians, cos, sin, sqrt, atan2
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
import hashlib,json,sys,base64,zlib

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/participant-gpx'
FILE={year:BASE/f'trail43-{year}.gpx' for year in range(2021,2026)}
if any(not path.is_file() for path in FILE.values()):raise SystemExit('Missing one or more owner GPX: '+str(FILE))
R=6371.0088

def dist(a,b):
 x,y,z,w=map(radians,(a[0],a[1],b[0],b[1])); t=sin((z-x)/2)**2+cos(x)*cos(z)*sin((w-y)/2)**2
 return 2*R*atan2(sqrt(max(0,t)),sqrt(max(0,1-t)))
def chain(p):
 return np.r_[0,np.cumsum([dist(a,b) for a,b in zip(p,p[1:])])]
def load(f):
 root=ET.fromstring(f.read_bytes()); trk=[x for x in root.iter() if x.tag.rsplit('}',1)[-1]=='trkpt'];rte=[x for x in root.iter() if x.tag.rsplit('}',1)[-1]=='rtept']
 pts=trk or rte
 out=[]
 for node in pts:
  lat=float(node.attrib['lat']);lon=float(node.attrib['lon']);e=next((el.text for el in node if el.tag.rsplit('}',1)[-1]=='ele'),None)
  p=(lat,lon,float(e) if e else None)
  if not out or dist(out[-1],p)>.000001:out.append(p)
 return out

def simplify(points,tolerance_m=3):
 latitude=radians(sum(p[0] for p in points)/len(points)); xs=111195*cos(latitude);ys=111195
 xy=[(p[1]*xs,p[0]*ys) for p in points]
 keep={0,len(points)-1}; stack=[(0,len(points)-1)];tol2=tolerance_m*tolerance_m
 while stack:
  a,b=stack.pop()
  if b-a<2:continue
  ax,ay=xy[a];bx,by=xy[b];dx=bx-ax;dy=by-ay;d2=dx*dx+dy*dy
  best=tol2;idx=None
  for i in range(a+1,b):
   px,py=xy[i];t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/d2)) if d2 else 0
   delta=(px-ax-t*dx)**2+(py-ay-t*dy)**2
   if delta>best:best=delta;idx=i
  if idx is not None:keep.add(idx);stack.extend(((a,idx),(idx,b)))
 return [points[i] for i in sorted(keep)]

points={y:load(p) for y,p in FILE.items()}
for y in sorted(points):
 raw=points[y]; p=simplify(raw,3); print(f'{y}: {len(raw)} raw {chain(raw)[-1]:.3f} km, 3m simplified {len(p)} points {chain(p)[-1]:.3f} km')
# Find 2022 self-crossing that removes ~0.66km while rejoin ~1.5m apart, chain around 22km
raw=points[2022]; d=chain(raw);ll=np.array([[x[0],x[1]] for x in raw]); lat=np.radians(ll[:,0].mean());xy=np.column_stack((ll[:,1]*111195*np.cos(lat),ll[:,0]*111195)); tree=cKDTree(xy)
candidates=[]
for i in np.where((d>=20)&(d<=23.5))[0]:
 for j in tree.query_ball_point(xy[i],10):
  length=d[j]-d[i]
  if j<=i+50 or not .65<=length<=.85:continue
  sep=np.linalg.norm(xy[i]-xy[j]);candidates.append((abs(length-.760)*6+abs(sep-1.5),i,j,length,sep,d[i],d[j]))
candidates.sort()
print('2022 excursion candidates:',candidates[:8]); assert candidates
_,i,j,length,sep,d0,d1=candidates[0]
route22=raw[:i+1]+raw[j:]
clean22=simplify(route22,3)
print('2021-22 rebuilt:',len(clean22),chain(clean22)[-1], 'removed',length,'gap',sep)
# 2023-2025 using DTW against 2024 with 3m pre-simplification
p24=simplify(points[2024],3);p23=simplify(points[2023],3);p25=simplify(points[2025],3)
print('input points for medoid',len(p23),len(p24),len(p25))

def meter_xy(pts):
 lat=radians(np.mean([p[0] for p in pts]));return np.array([[p[1]*111195*cos(lat),p[0]*111195] for p in pts])
# memory-conscious DTW within broad corridor, 3 standard transitions

def align(base,other):
 a=meter_xy(base);b=meter_xy(other); N=len(a);M=len(b);width=max(150,int(.18*max(N,M)))
 cost=np.full((N+1,M+1),np.inf); prev=np.zeros((N+1,M+1),dtype=np.uint8);cost[0,0]=0
 for ii in range(1,N+1):
  expected=ii*M/N
  lo=max(1,int(expected-width));hi=min(M,int(expected+width)+1)
  ds=np.sum((b[lo-1:hi]-a[ii-1])**2,axis=1)
  for jj,c in zip(range(lo,hi+1),ds):
   choices=(cost[ii-1,jj-1],cost[ii-1,jj],cost[ii,jj-1])
   k=int(np.argmin(choices)); cost[ii,jj]=c+choices[k]; prev[ii,jj]=k
 if not np.isfinite(cost[N,M]): raise RuntimeError('No DTW path')
 i,j=N,M; matches=[[] for _ in range(N)]
 while i>0 and j>0:
  matches[i-1].append(j-1)
  k=prev[i,j]
  if k==0: i-=1;j-=1
  elif k==1: i-=1
  else:j-=1
 # Empty matches interpolate between closest recorded matches
 non=[i for i,v in enumerate(matches) if v]
 result=[]
 for k,v in enumerate(matches):
  if v: result.append(int(np.median(v)));continue
  before=max((x for x in non if x<k),default=non[0]);after=min((x for x in non if x>k),default=non[-1]);idx=result[before] if before==after else round(np.interp(k,[before,after],[np.median(matches[before]),np.median(matches[after])]))
  result.append(int(idx))
 assert all(a<=b for a,b in zip(result,result[1:])), 'DTW mapping not monotone'
 return result,cost[N,M]
match23,cost23=align(p24,p23);match25,cost25=align(p24,p25);print('dtw',cost23,cost25)
# Medoid at each 2024 point: choose exact observed coordinate with smallest total distance to other two points.
med=[]; choice={2023:0,2024:0,2025:0}
for idx,p in enumerate(p24):
 opts=[p23[match23[idx]],p,p25[match25[idx]]]
 scores=[sum(dist(q,other) for other in opts) for q in opts]
 chosen=int(np.argmin(scores));med.append(opts[chosen]);choice[[2023,2024,2025][chosen]]+=1
# duplicate/zero diff removal then 3m DP
med=list(q for k,q in enumerate(med) if k==0 or dist(q,med[k-1])>.000001)
clean35=simplify(med,3)
print('2023-25 rebuilt:',len(clean35),chain(clean35)[-1],'medoid options',choice)

def route_asset(pts,family,years,method,source_names):
 d=chain(pts); return {'family':family,'edition_references':years,'type':'NORMALIZED_PARTICIPANT','evidence_note':'Owner-accepted normalized analysis corridor from verified Suunto/Sports Tracker race-day GPS; course display only, no fabricated timings, no official-organizer status.','geometry_length_km':round(float(d[-1]),6),'published_polyline_length_km':round(float(d[-1]),6),'geometry_export_method':method,'published_points':len(pts),'source_years':years,'source_original_sha256':{str(y):hashlib.sha256(FILE[y].read_bytes()).hexdigest() for y in years},'points':[[round(float(d[k]),6),round(p[0],6),round(p[1],6),round(p[2],1) if p[2] is not None else None] for k,p in enumerate(pts)]}

out=(ROOT/'data/normalized-gpx');out.mkdir(parents=True,exist_ok=True)
for key,pts,yrs,method in [('trail43-2021-2022',clean22,[2021,2022],'2022-participant-base-remove-confirmed-out-and-back-2022-then-douglas-peucker-3m'),('trail43-2023-2025',clean35,[2023,2024,2025],'2023-2025-three-participant-dtw-monotone-2024-anchor-medoid-consensus-then-douglas-peucker-3m')]:
 asset=route_asset(pts,'trail43',yrs,method,[FILE[y].name for y in yrs]);p=out/(key+'-normalized.json');p.write_text(json.dumps(asset,ensure_ascii=False,separators=(',',':'))+'\n');print('ASSET',p.name,p.stat().st_size,'sha256',hashlib.sha256(p.read_bytes()).hexdigest())

# Additional stable, metadata-free normalized GPX exports for long-term restoration.
for key in ('trail43-2021-2022','trail43-2023-2025'):
    route_file=out/(key+'-normalized.json')
    obj=json.loads(route_file.read_text())
    NS='http://www.topografix.com/GPX/1/1';ET.register_namespace('',NS)
    g=ET.Element('{'+NS+'}gpx',{'version':'1.1','creator':'Sätila Splits – owner-approved reconstructed normalized display route'})
    ET.SubElement(g,'metadata');track=ET.SubElement(g,'trk');ET.SubElement(track,'name').text=key+'-normalized';seg=ET.SubElement(track,'trkseg')
    for p in obj['points']:
        node=ET.SubElement(seg,'trkpt',{'lat':f'{p[1]:.6f}','lon':f'{p[2]:.6f}'})
        if p[3] is not None:ET.SubElement(node,'ele').text=f'{p[3]:.1f}'
    gp=out/(key+'-normalized.gpx');gp.write_bytes(ET.tostring(g,encoding='utf-8',xml_declaration=True))
    print('GPX',gp.name,gp.stat().st_size,hashlib.sha256(gp.read_bytes()).hexdigest())
