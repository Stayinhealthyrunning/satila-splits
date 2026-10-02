#!/usr/bin/env python3
"""Import exactly seven checksum-pinned sanitized historical ultra85 tracks.

The encoded geometry contains no participant name, GPS timestamp or raw GPX.
Real race results and split observations are read but never altered.
"""
from __future__ import annotations
import base64,hashlib,json,math,zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'docs'/'data'
ENCODED=ROOT/'data'/'derived'/'ultra85-2018-2025-sanitized.zlib.b64'
EXPECTED_B64_SHA='a565fe9209450c06e7407ead0c9414507b35783fe23f5a2a855b428aec9dcb46'
EXPECTED_PAYLOAD_SHA='f376db183f0c4db80bab2ef33d60e09dd7c47737c1f0b7bfa3f9efab22065d69'
SHA={
2018:'5f0864fba534b23d48ac2adde73240bd58d48946d4a2cb092757a9b4304175ec',
2019:'4b508c9071480feea7823ca8df371cf39030b74d62370851df8de485fbce9510',
2021:'13c033f0e4a336334f9030ea322f4df3df226415c850896fd511e980e36ed294',
2022:'0b6cd4a39ecce9fe6262f03b8c9be15c59c6428277c0b67497402d95d95207b0',
2023:'e363954507767a4a06f74f4547d4e5b7216849452317f4359c368ecd28636e81',
2024:'042ddbb7d32862fbcc415f284577f3dad8225adec47f1240e9dd9caa7f7f18c6',
2025:'d54db03d752dd1e6679492f595aa6121c4396d94ed13c9903f5a974b11380d47',
}
EXPECTED_PTS={2018:1618,2019:1345,2021:964,2022:1607,2023:796,2024:1158,2025:856}
EXPECTED_KM={2018:84.148,2019:81.152,2021:82.775,2022:84.211,2023:81.049,2024:83.364,2025:81.414}
R=6371.0088

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def dump(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
def digest(x):return hashlib.sha256(x).hexdigest()
def hav(a,b):
 lat1,lon1,lat2,lon2=map(math.radians,(a[0],a[1],b[0],b[1]))
 x=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
 return 2*R*math.asin(min(1,math.sqrt(x)))
def decode_polyline(encoded):
 nums=[];i=0
 while i<len(encoded):
  v=0;shift=0
  while True:
   if i>=len(encoded):raise ValueError('Incomplete polyline varint')
   n=ord(encoded[i])-63;i+=1
   if not 0<=n<=63:raise ValueError('Invalid polyline codepoint')
   v|=(n&31)<<shift;shift+=5
   if shift>45:raise ValueError('Oversize varint')
   if n<32:break
  nums.append((~(v>>1)) if (v&1) else (v>>1))
 if len(nums)%2:raise ValueError('Uneven coordinate pairs')
 lat=lon=0;out=[]
 for i in range(0,len(nums),2):
  lat+=nums[i];lon+=nums[i+1]
  p=(lat/1000000,lon/1000000)
  if not (56<=p[0]<=59 and 11<=p[1]<=14):raise ValueError('Coordinate outside verified region')
  if out and hav(out[-1],p)<.000001:raise ValueError('Degenerate polyline point')
  out.append(p)
 return out

def main():
 encoded=ENCODED.read_bytes()
 assert digest(encoded)==EXPECTED_B64_SHA,'Sanitized coordinate payload SHA mismatch'
 raw=zlib.decompress(base64.b64decode(encoded,validate=True))
 assert digest(raw)==EXPECTED_PAYLOAD_SHA,'Uncompressed coordinate payload SHA mismatch'
 payload=json.loads(raw)
 assert payload['schema']==1 and payload['purpose']=='SANITIZED_ULTRA85_ROUTES_2018_2025' and payload['quantization']==1000000
 assert set(map(int,payload['routes']))==set(SHA),'Expected exactly seven original year-scoped routes'
 bootstrap=read(DATA/'bootstrap.json');bykey={ed['race_key']:ed for ed in bootstrap['editions']}
 inventory=read(DATA/'route-inventory.json');coverage=read(DATA/'coverage.json');cov={ed['race_key']:ed for ed in coverage}
 registry=read(ROOT/'config/source-registry.json');reg=registry.setdefault('historical_ultra85_gpx',{})
 pre={(ed['race_key']):(len(read(DATA/'races'/(ed['race_key']+'.json'))['results']),len(read(DATA/'races'/(ed['race_key']+'.json'))['splits'])) for ed in bootstrap['editions']}
 for year,sha in SHA.items():
  src=payload['routes'][str(year)]
  assert src['original_sha256']==sha,(year,'source fingerprint mismatch')
  pts=decode_polyline(src['encoded_polyline_1e6'])
  assert len(pts)==EXPECTED_PTS[year]==src['published_points'],(year,'unexpected point count')
  assert src['source_geometry_length_km']>=src['expected_published_geometry_length_km']
  assert src['expected_published_geometry_length_km']/src['source_geometry_length_km']>=.995
  chain=0.;routepts=[]
  for i,p in enumerate(pts):
   if i:chain+=hav(pts[i-1],p)
   routepts.append([round(chain,6),p[0],p[1],None])
  assert abs(chain-EXPECTED_KM[year])<.025,(year,chain,EXPECTED_KM[year])
  assert abs(chain-src['expected_published_geometry_length_km'])<.025,(year,'unexpected encoded geometry')
  key=f'{year}-ultra85';ed=bykey[key];racepath=DATA/'races'/f'{key}.json';race=read(racepath)
  assert race['race_key']==key and race['year']==year and ed['year']==year
  if ed.get('route_file') and ed.get('route_file')!=f'routes/{key}-participant.json':raise ValueError(f'Existing route must not be overridden silently: {key}')
  typ='TRACE_DE_TRAIL' if year==2022 else 'VERIFIED_PARTICIPANT'
  origin='Trace de Trail third-party historic route export' if year==2022 else 'RouteGadget3 recorded participant GPS from the edition date'
  evidence=f'{origin}, individually supplied by owner and SHA-256 pinned to {year}. Simplified map-only GPX geometry; no official organizer equivalence, no source elevation, no runner-position timing extrapolation; only observed EQ Timing splits may be used for analysis.'
  rel=f'routes/{key}-participant.json'
  meta=dict(family='ultra85',edition_references=[year],race_key=key,type=typ,evidence_note=evidence,source_sha256=sha,
            source_class='TRACE_DE_TRAIL_HISTORIC_ROUTE' if year==2022 else 'ROUTEGADGET3_PARTICIPANT',
            geometry_length_km=round(chain,6),published_polyline_length_km=round(chain,6),
            source_geometry_length_km=src['source_geometry_length_km'],geometry_export_method='source-GPX-consecutive-deduplication-3m-Douglas-Peucker-1e6-coordinate-encoding',
            raw_source_points=src['source_points'],published_points=len(routepts),elevation_status='not_in_source')
  dump(DATA/rel,{**meta,'points':routepts})
  inv={**meta,'source_filename':f'ultra85-{year}-private-source.gpx'}
  inventory=[row for row in inventory if row.get('race_key')!=key]
  inventory.append(inv)
  upd={'route_file':rel,'route_status':'participant_track_display_only','route_source_sha256':sha,
       'measured_route_geometry_km':meta['geometry_length_km'], 'course_version':f'ultra85-{year}-year-specific-participant-display-not-canonical'}
  for obj in (ed,race):obj.update(upd)
  # Existing nominal km, official/organizer citations, results and TIME observations are immutable.
  if ed.get('distance_evidence_note'):
   ed['distance_evidence_note']=ed['distance_evidence_note'].replace('No accepted year-specific GPX geometry is assigned.','Year-specific non-organizer GPS display geometry now available; timing/nominal distance remains unchanged.')
  cov[key].update(upd)
  cov[key].update(route_sha256=sha,route_source_type=typ,route_source_filename=inv['source_filename'],route_geometry_km=meta['geometry_length_km'],route_evidence_note=evidence)
  reg[str(year)]={'status':'VERIFIED_YEAR_SCOPED_NON_ORGANIZER_DISPLAY','source_sha256':sha,'source_class':meta['source_class'],'original_privately_archived':True,'sanitized_geometry_payload':str(ENCODED.relative_to(ROOT)),'display_route':rel,'display_only':True}
  dump(racepath,race)
  print(f'ROUTE {key}: {len(routepts)} map points, {chain:.3f} km (source {src["source_geometry_length_km"]:.3f} km) [{typ}]',flush=True)
 inventory.sort(key=lambda v:(v['family'],v['edition_references'][0],v.get('race_key','')))
 dump(DATA/'route-inventory.json',inventory)
 dump(DATA/'bootstrap.json',bootstrap)
 dump(DATA/'coverage.json',coverage)
 dump(ROOT/'config/source-registry.json',registry)
 post={(ed['race_key']):(len(read(DATA/'races'/(ed['race_key']+'.json'))['results']),len(read(DATA/'races'/(ed['race_key']+'.json'))['splits'])) for ed in bootstrap['editions']}
 assert pre==post,'Result/split population was changed by route-only import'
 assert sum(a for a,b in post.values())==3272 and sum(b for a,b in post.values())==16525
 for y in SHA:assert bykey[f'{y}-ultra85']['route_file']==f'routes/{y}-ultra85-participant.json'
 for y in (2016,2017):assert not bykey[f'{y}-ultra85'].get('route_file'),'Do not borrow route for unverified historical year'
 print('PASS: seven historical ultra85 editions linked, 2016–17 untouched, 3272 results and 16525 observed TIME rows preserved',flush=True)
if __name__=='__main__':main()