#!/usr/bin/env python3
"""Reproducible, conservative static export from EQ Timing's public station archive.

Only observed timing values are source splits. No geospatial interpolation enters results.
The browser receives a small catalogue + one race-bundle at a time.
"""
import json,re,math,hashlib,argparse,collections,statistics,sqlite3,unicodedata,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name=='tools' else Path(__file__).resolve().parent
FAMS=('ultra85','trail43','trail22')
def js(path,thing):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(thing,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sec(ms):return round(ms/1000,2) if isinstance(ms,(float,int)) and ms>0 else None
def racefamily(r):
 km=r.get('Km',0) or 0
 if 75<=km<110:return 'ultra85'
 if 39<=km<51:return 'trail43'
 if 19<=km<26:return 'trail22'
 return None

def parse(root,out,source_cat):
 events=load(source_cat)['events'];catalog=[];history=[];samples=[];coverage=[];archive_hashes={};(out/'satila.sqlite').unlink(missing_ok=True);db=sqlite3.connect(str(out/'satila.sqlite'));db.executescript('''
 CREATE TABLE IF NOT EXISTS editions(race_key TEXT PRIMARY KEY,year INT,leg_uid INT,event_id INT,family TEXT,name TEXT,source_distance REAL,source TEXT);
 CREATE TABLE IF NOT EXISTS results(result_id TEXT PRIMARY KEY,race_key TEXT,entrant_uid INT,name TEXT,bib TEXT,sex TEXT,age INT,class TEXT,club TEXT,status TEXT,finish_seconds REAL,place INT,raw_json TEXT,FOREIGN KEY(race_key) REFERENCES editions(race_key));
 CREATE TABLE IF NOT EXISTS splits(result_id TEXT,station_uid INT,station_name TEXT,km REAL,elapsed_seconds REAL,place INT,status TEXT,raw_json TEXT,PRIMARY KEY(result_id,station_uid),FOREIGN KEY(result_id) REFERENCES results(result_id));
 ''');db.execute('PRAGMA foreign_keys=ON'); total_obs=0
 for e in events:
  year=e['year'];d=root/str(year)
  if not d.exists():continue
  evt=load(d/'event.json');raw=(d/'event.json').read_bytes();archive_hashes[str(year)]={'event_id':e['event_id'],'event_json_sha256':hashlib.sha256(raw).hexdigest()}
  contestants=load(d/'contestants.json');byed={}
  for c in contestants.values():
   for ed in (c.get('EtappeDeltaker') or {}).values():
    byed[int(ed['UID'])]=(c,ed)
  manifest=load(d/'manifest.json')
  for rk,rv in (evt.get('Etapper') or {}).items():
   family=racefamily(rv)
   if not family:continue
   leg=int(rv['UID']);racekey=f'{year}-{family}'
   stations=[s for s in manifest['public_stations'] if s['race_uid']==leg]
   if not stations:continue
   db.execute('INSERT OR REPLACE INTO editions VALUES(?,?,?,?,?,?,?,?)',(racekey,year,leg,e['event_id'],family,rv.get('Navn'),rv.get('Km'),e['url']))
   stations.sort(key=lambda s:(s['sort'],float(s.get('km') or 0),s['station_uid']))
   edmap={eduid:(c,ed) for eduid,(c,ed) in byed.items() if int((ed.get('Etappe') or {}).get('UID',-1))==leg}
   observations=collections.defaultdict(dict)
   for st in stations:
    p=d/'results'/str(leg)/str(st['station_uid'])
    for fn in sorted(p.glob('*.json')):
     page=load(fn)
     for row in page.get('Items') or []:
      uid=int(row.get('EtappeDeltakerUID') or 0)
      if uid<=0:continue
      total_obs+=1
      prior=observations[uid].get(st['station_uid'])
      if prior and (prior.get('StatusTekst')=='TIME' and prior.get('AkkumulertTid')>0):continue
      observations[uid][st['station_uid']]=row
   finishstations=[s for s in stations if s.get('is_finish')]
   if not finishstations:raise RuntimeError(f'Missing finish station {racekey}')
   finishst=finishstations[-1];finishid=finishst['station_uid'];alluids=set(edmap)|set(observations)
   rows=[];splits=[]
   for uid in sorted(alluids):
    c,ed=edmap.get(uid,({},{}));ath=c.get('Utover') or {};station_obs=observations.get(uid,{})
    finish=station_obs.get(finishid,{});status_text=str(finish.get('StatusTekst','')).upper()
    isfinish=(not ed.get('DNF') and not ed.get('DNS') and not ed.get('DSQ') and status_text=='TIME' and sec(finish.get('AkkumulertTid')) is not None)
    if ed.get('DSQ') or status_text=='DSQ':status='DSQ'
    elif ed.get('DNS') or status_text=='DNS':status='DNS'
    elif ed.get('DNF') or status_text=='DNF':status='DNF'
    elif isfinish:status='FINISHED'
    else:status='UNKNOWN'
    name=(ath.get('NavnFormatert') or (' '.join(filter(None,[ath.get('Fornavn'),ath.get('Etternavn')])))).strip()
    if not name:name='Ej publicerat namn'
    cl=c.get('Klasse') or {};club=c.get('KlubbTeamFormatert') or c.get('Klubbnavn') or ath.get('Klubbnavn') or ''
    sex={'m':'M','f':'F','male':'M','female':'F'}.get(str(ath.get('Kjonn') or cl.get('Kjonn') or '').lower())
    age=c.get('Alder') if isinstance(c.get('Alder'),int) and 5<=c.get('Alder')<=100 else None
    resultid=f'eq-{year}-{leg}-{uid}';tim=sec(finish.get('AkkumulertTid')) if status=='FINISHED' else None
    pl=(finish.get('Plassering') or {}).get('Total') if status=='FINISHED' else None
    r={'id':resultid,'source_uid':uid,'name':name,'bib':str(c.get('Startnummer') or ed.get('Startnummer') or ''),'sex':sex,'age':age,'class_name':cl.get('Navn') or '', 'club':club,'status':status,'finish_seconds':tim,'place':pl if isinstance(pl,int) and pl>0 else None}
    rows.append(r)
    db.execute('INSERT OR REPLACE INTO results VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(resultid,racekey,uid,name,r['bib'],sex,age,r['class_name'],club,status,tim,r['place'],json.dumps({'contestant':c,'entry':ed},ensure_ascii=False)))
    prev=-1
    for st in stations:
     row=station_obs.get(st['station_uid'])
     if not row or str(row.get('StatusTekst','')).upper()!='TIME':continue
     t=sec(row.get('AkkumulertTid'))
     if t is None or t<=0:continue
     # retain source observations, but never synthesize missing checkpoints or nonmonotone elapsed time
     rank=(row.get('Plassering') or {}).get('Total')
     s={'result_id':resultid,'station_uid':st['station_uid'],'elapsed_seconds':t,'place':rank if isinstance(rank,int) and rank>0 else None}
     splits.append(s)
     db.execute('INSERT OR REPLACE INTO splits VALUES(?,?,?,?,?,?,?,?)',(resultid,st['station_uid'],st['station_name'],st['km'],t,s['place'],'TIME',json.dumps(row,ensure_ascii=False)))
   rows.sort(key=lambda r:((r['place'] is None),r['place'] or 999999,r['finish_seconds'] or 1e9,r['name']))
   station_list=[{'uid':s['station_uid'],'name':s['station_name'],'km':s.get('km'),'sort':s['sort'],'is_finish':bool(s['is_finish']),'is_start':False,'is_analysis_boundary':s['station_name'].upper() not in ('PRE','FV')} for s in stations]
   stats=collections.Counter(r['status'] for r in rows)
   finishers=[r['finish_seconds'] for r in rows if r['status']=='FINISHED']
   edition={'race_key':racekey,'family':family,'year':year,'event_id':e['event_id'],'leg_uid':leg,'name':rv.get('Navn'),'nominal_km':rv.get('Km'),'date':e['date'],'source_url':e['url'],'course_version':f'{family}-{year}-unverified','route_status':'none','stations':station_list,'results':rows,'splits':splits}
   js(out/'races'/f'{racekey}.json',edition)
   db.execute('INSERT OR REPLACE INTO editions VALUES(?,?,?,?,?,?,?,?)',(racekey,year,leg,e['event_id'],family,rv.get('Navn'),rv.get('Km'),e['url']))
   entry={'race_key':racekey,'family':family,'year':year,'label':rv.get('Navn'),'nominal_km':rv.get('Km'),'date':e['date'],'event_id':e['event_id'],'results':len(rows),'finishers':stats['FINISHED'],'dnf':stats['DNF'],'dns':stats['DNS'],'dsq':stats['DSQ'],'unknown':stats['UNKNOWN'],'split_observations':len(splits),'timing_stations':len(stations),'median_seconds':round(statistics.median(finishers),2) if len(finishers)>=5 else None,'source_url':e['url'],'route_status':'none'}
   catalog.append(entry);coverage.append(entry.copy())
  db.commit()
 db.close();catalog.sort(key=lambda r:(-r['year'],FAMS.index(r['family'])))
 meta={'schema':'satila-first-draft-1','contract':'loppanalys-engine-1.0','event':'Sätila Trail Run','families':[{'id':'ultra85','label':'85 km','subtitle':'Ultra','color':'#d8ad62'},{'id':'trail43','label':'43 km','subtitle':'Maraton','color':'#85a18a'},{'id':'trail22','label':'22 km','subtitle':'Halvmaraton','color':'#becfc0'}], 'editions':catalog,'source_archive':'EQ Timing full public-station pagination, workflow run 36818159977','coverage_note':'Public result API Items contains DNS placeholders; split_observations counts only TIME observations; unique results are deduplicated by EtappeDeltakerUID.'}
 js(out/'bootstrap.json',meta);js(out/'coverage.json',coverage);js(out/'source-fingerprints.json',archive_hashes)
 return meta,total_obs

def geodist(a,b):
 lat1,lon1=a;lat2,lon2=b;h=math.sin(math.radians(lat2-lat1)/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(math.radians(lon2-lon1)/2)**2
 return 6371.0088*2*math.atan2(math.sqrt(h),math.sqrt(1-h))

def build_route_asset_from_trackpoints(tr,family,raw=b'',source_filename='synthetic.gpx'):
 """Export every geometrically unique organizer trackpoint with source chainage.

 The five organizer routes contain only 5,483 trackpoints in total. Keeping the
 source geometry avoids shortcutting bends and loops, while the browser still
 fetches only the route used by the selected edition. Consecutive zero-distance
 duplicates are omitted so the public distance axis remains strictly monotone.
 """
 if not tr:raise RuntimeError('Empty official GPX '+source_filename)
 cumulative=[0.];ascent=0
 for a,b in zip(tr,tr[1:]):
  cumulative.append(cumulative[-1]+geodist(a[:2],b[:2]));ascent+=max(0,(b[2] or 0)-(a[2] or 0)) if a[2] is not None and b[2] is not None else 0
 inds=[0]
 for i in range(1,len(tr)):
  if cumulative[i]>cumulative[inds[-1]]+1e-9:inds.append(i)
 points=[[round(cumulative[i],6),round(tr[i][0],6),round(tr[i][1],6),round(tr[i][2],1) if tr[i][2] is not None else None] for i in inds]
 drawn=sum(geodist(a[1:3],b[1:3]) for a,b in zip(points,points[1:]))
 sha=hashlib.sha256(raw).hexdigest()
 refs=[2026] if family=='ultra85' else [2025,2026]
 asset={'family':family,'edition_references':refs,'type':'OFFICIAL_ORGANIZER','evidence_note':'Organizer 2026 download; internal GPX 2025 title reused for unchanged 2025/2026 course on 5, 10, 21 and 43 km as agreed with project owner.','source_sha256':sha,'geometry_length_km':round(cumulative[-1],6),'published_polyline_length_km':round(drawn,6),'raw_positive_gain_m_not_official':round(ascent,1),'geometry_export_method':'all_geometrically_unique_source_trackpoints','points':points}
 inventory={k:v for k,v in asset.items() if k!='points'}|{'source_filename':unicodedata.normalize('NFC',source_filename),'source_points':len(tr),'published_points':len(points)}
 return asset,inventory

def build_route_asset(file,family):
 tree=ET.parse(file);tr=[]
 for p in tree.iter():
  if p.tag.endswith('}trkpt') or p.tag=='trkpt':
   lat=float(p.attrib['lat']);lon=float(p.attrib['lon']);el=next((float(v.text) for v in p if v.tag.endswith('}ele') or v.tag=='ele'),None)
   tr.append((lat,lon,el))
 return build_route_asset_from_trackpoints(tr,family,Path(file).read_bytes(),Path(file).name)

def routes(out,gpxdir):
 mapping={'5':'trail5','10':'trail10','21':'trail22','43':'trail43','85':'ultra85'}; inventory=[]
 for file in sorted(gpxdir.glob('*.gpx')):
  match=re.search(r'Trail\s+(5|10|21|43|85)\s*-\s*2026',file.name,re.I)
  if not match:continue
  family=mapping[match.group(1)];asset,item=build_route_asset(file,family)
  js(out/'routes'/f'{family}-2025-2026.json' if family!='ultra85' else out/'routes'/'ultra85-2026.json',asset)
  inventory.append(item)
 if inventory:js(out/'route-inventory.json',inventory)
 else:inventory=load(out/'route-inventory.json') if (out/'route-inventory.json').exists() else []
 # Link route references to completed 2025 and future 2026 catalogue only; never borrow routes for older years.
 bootstrap=load(out/'bootstrap.json')
 for ed in bootstrap['editions']:
  if ed['year']==2025 and ed['family'] in ('trail22','trail43') and (out/'routes'/f'{ed["family"]}-2025-2026.json').exists():
   ed['route_status']='organizer_2025_2026_reuse_assumption';ed['route_file']=f'routes/{ed["family"]}-2025-2026.json';ed['course_version']=f'{ed["family"]}-2025-2026-organizer-assumed'
 js(out/'bootstrap.json',bootstrap)
 for ed in bootstrap['editions']:
  if ed.get('route_file'):
   f=out/'races'/f'{ed["race_key"]}.json';race=load(f);race['route_status']=ed['route_status'];race['route_file']=ed['route_file'];race['course_version']=ed['course_version'];js(f,race)
 return inventory

def distance_fields(racekey,eq_km,config):
 extra=(config.get('editions') or {}).get(racekey)
 if not extra:return {}
 if float(extra['eq_timing_leg_km'])!=float(eq_km):raise RuntimeError(f'{racekey}: configured EQ distance does not match source nominal_km')
 return dict(extra)

def refresh_distance_metadata(out,config_path=ROOT/'config'/'edition-distance-metadata.json'):
 """Enrich committed bundles without requiring the private EQ source archive."""
 config=load(config_path);bootstrap=load(out/'bootstrap.json')
 for ed in bootstrap['editions']:
  fields=distance_fields(ed['race_key'],ed['nominal_km'],config)
  for key in ('eq_timing_leg_km','organizer_advertised_km','distance_semantics_status','distance_evidence_note','distance_source_urls'):ed.pop(key,None)
  ed.update(fields)
  route_file=ed.get('route_file')
  if route_file:ed['measured_route_geometry_km']=load(out/route_file)['geometry_length_km']
  else:ed.pop('measured_route_geometry_km',None)
  file=out/'races'/f"{ed['race_key']}.json";race=load(file)
  for key in ('eq_timing_leg_km','organizer_advertised_km','distance_semantics_status','distance_evidence_note','distance_source_urls'):race.pop(key,None)
  race.update(fields)
  if route_file:race['measured_route_geometry_km']=ed['measured_route_geometry_km']
  else:race.pop('measured_route_geometry_km',None)
  js(file,race)
 js(out/'bootstrap.json',bootstrap)
 return len(bootstrap['editions'])

def refresh_coverage(out):
 """Derive public field coverage from committed race bundles after course linking."""
 boot=load(out/'bootstrap.json');coverage=[]
 inventory=load(out/'route-inventory.json') if (out/'route-inventory.json').exists() else []
 for ed in boot['editions']:
  race=load(out/'races'/f"{ed['race_key']}.json")
  route=next((item for item in inventory if ed.get('route_file') and item['family']==ed['family'] and ed['year'] in item['edition_references']),None)
  rows=race['results'];sex_f=sum(r.get('sex')=='F' for r in rows);sex_m=sum(r.get('sex')=='M' for r in rows)
  coverage.append(ed|{
   'sex_f':sex_f,'sex_m':sex_m,'sex_known':sex_f+sex_m,
   'age_known':sum(isinstance(r.get('age'),int) for r in rows),
   'class_known':sum(bool(r.get('class_name')) for r in rows),
   'club_known':sum(bool(r.get('club')) for r in rows),
   'status_known':sum(r.get('status')!='UNKNOWN' for r in rows),
   'known_starters':sum(r.get('status') in ('FINISHED','DNF','DSQ') for r in rows),
   'route_status':ed.get('route_status','none'),
   'course_version':ed.get('course_version'),
   'whole_course_comparison_group':ed.get('whole_course_comparison_group'),
   'route_source_type':route.get('type') if route else None,
   'route_source_filename':route.get('source_filename') if route else None,
   'route_sha256':route.get('source_sha256') if route else None,
   'route_geometry_km':route.get('geometry_length_km') if route else None,
   'route_evidence_note':route.get('evidence_note') if route else None
  })
 js(out/'coverage.json',coverage)
 return coverage

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',default=str(ROOT/'data/work/eqtiming-full'));ap.add_argument('--gpix',default=str(ROOT/'data/source/gpx'));ap.add_argument('--events',default=str(ROOT/'config/eqtiming-events.json'));ap.add_argument('--out',default=str(ROOT/'docs/data'));ap.add_argument('--refresh-coverage-only',action='store_true');ap.add_argument('--refresh-distance-metadata-only',action='store_true');arg=ap.parse_args();out=Path(arg.out);out.mkdir(parents=True,exist_ok=True)
 if arg.refresh_coverage_only:
  print('COVERAGE',len(refresh_coverage(out)),'editions refreshed from committed bundles');return
 if arg.refresh_distance_metadata_only:
  print('DISTANCE METADATA',refresh_distance_metadata(out),'editions refreshed');refresh_coverage(out);return
 meta,n=parse(Path(arg.source),out,Path(arg.events));inv=routes(out,Path(arg.gpix));refresh_distance_metadata(out);refresh_coverage(out);print('EQ full observations',n,'EDITION COUNT',len(meta['editions']),'UNIQUE',sum(x['results'] for x in meta['editions']),'FINISHED',sum(x['finishers'] for x in meta['editions']),'SPLITS',sum(x['split_observations'] for x in meta['editions'])); print('BY FAMILY',collections.Counter(x['family'] for x in meta['editions']));print('GPX',[(x['family'],x['geometry_length_km']) for x in inv]);
if __name__=='__main__':main()
