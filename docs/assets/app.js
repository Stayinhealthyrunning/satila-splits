/* Sätila Splits first draft – observed EQ Timing analysis, capability-driven UI. */
(()=>{'use strict';
const $=(s,root=document)=>root.querySelector(s),$$=(s,root=document)=>Array.from(root.querySelectorAll(s));
const html=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const format=n=>Number(n??0).toLocaleString('sv-SE');
const num=n=>typeof n==='number'&&Number.isFinite(n);
const median=a=>{a=a.filter(num).sort((x,y)=>x-y);let n=a.length;return n?(n%2?a[(n-1)/2]:(a[n/2-1]+a[n/2])/2):null};
const mean=a=>{a=a.filter(num);return a.length?a.reduce((sum,value)=>sum+value,0)/a.length:null};
const quant=(a,p)=>{a=a.filter(num).sort((x,y)=>x-y);if(!a.length)return null;const v=(a.length-1)*p,i=Math.floor(v),f=v-i;return a[i]+(a[Math.min(a.length-1,i+1)]-a[i])*f};
const time=s=>!num(s)||s<0?'—':(()=>{let n=Math.round(s),h=Math.floor(n/3600),m=Math.floor(n%3600/60),sec=String(n%60).padStart(2,'0');return h?`${h}:${String(m).padStart(2,'0')}:${sec}`:`${m}:${sec}`})();
const signed=s=>!num(s)?'—':(s>0?'+':'−')+time(Math.abs(s));
const pace=(sec,km,unit='pace')=>!num(sec)||!num(km)||km<=0?'—':unit==='speed'?(3600*km/sec).toFixed(2).replace('.',',')+' km/h':time(sec/km)+'/km';
const fmtKm=n=>num(n)?n.toFixed(1).replace('.',','):'—';
const readCache=(key,other=[])=>{try{let j=JSON.parse(localStorage.getItem(key));return Array.isArray(j)?j:other}catch{return other}};

/* One soundtrack shared by the two modal map players. Music is independent
   of the animation clock: it loops at the finish until the dialog closes. */
const replaySoundtrack=(()=>{
  const audio=new Audio('assets/satila-trail.mp3');
  audio.preload='metadata';audio.loop=true;
  const DEFAULT_VOLUME=.30,VOLUME_KEY='satila-music-volume',ENABLED_KEY='satila-music-enabled';
  let enabled=true,volume=DEFAULT_VOLUME,lastAudible=DEFAULT_VOLUME,sessionActive=false,host=null;
  try{
    const saved=localStorage.getItem(VOLUME_KEY);
    if(saved!==null&&Number.isFinite(Number(saved)))volume=Math.max(0,Math.min(1,Number(saved)));
    enabled=localStorage.getItem(ENABLED_KEY)!=='false';
  }catch{}
  if(volume>0)lastAudible=volume;
  audio.volume=volume;
  const note=message=>{const el=host?.querySelector('[data-replay-audio-note]');if(el){el.hidden=false;el.textContent=message}};
  const render=()=>{
    if(!host)return;
    const btn=host.querySelector('[data-replay-music]'),slider=host.querySelector('[data-replay-volume]');
    if(btn){btn.setAttribute('aria-pressed',String(enabled));btn.textContent=enabled?'♫ Musik':'♪ Musik av';btn.title=enabled?'Stäng av musik':'Slå på musik'}
    if(slider)slider.value=String(volume);
  };
  function setVolume(value){
    volume=Math.max(0,Math.min(1,Number.isFinite(value)?value:DEFAULT_VOLUME));
    if(volume>0)lastAudible=volume;
    audio.volume=volume;
    try{localStorage.setItem(VOLUME_KEY,String(volume))}catch{}
  }
  function start(){
    sessionActive=true;
    if(enabled)audio.play().catch(()=>note('Webbläsaren väntar med musiken. Tryck på Spela igen.'));
  }
  function pause(){sessionActive=false;audio.pause()}
  function close(){pause();try{audio.currentTime=0}catch{}host=null}
  function bind(container){
    close();host=container;render();
    container.querySelector('[data-replay-music]')?.addEventListener('click',()=>{
      enabled=!enabled;
      if(enabled&&volume<=0)setVolume(lastAudible||DEFAULT_VOLUME);
      try{localStorage.setItem(ENABLED_KEY,String(enabled))}catch{}
      render();
      if(enabled&&sessionActive)audio.play().catch(()=>note('Tryck på Spela igen för att starta musiken.'));
      else audio.pause();
    });
    container.querySelector('[data-replay-volume]')?.addEventListener('input',event=>setVolume(Number(event.target.value)));
  }
  audio.addEventListener('error',()=>note('Musiken kunde inte laddas. Kartuppspelningen fungerar ändå.'));
  return {bind,start,pause,close};
})();

const key='satila-splits-favorites-v1';let S={boot:null,family:'trail43',year:null,race:null,route:null,routeByFamily:{},filtered:[],page:0,sort:'place',q:'',sex:'all',status:'all',className:'all',club:'',clubExact:false,clubOptions:[],clubSuggestionIndex:-1,unit:'pace',finishSex:new Set(['F','M']),selectedSegment:0,podiumStart:0,podiumEnd:1,standoutTab:'relative',compare:[],mapDuel:[],favorites:readCache(key),searchIndex:-1,mapDuelSearchIndex:-1,loading:0,courseD:null,duelD:null,placementWindow:null,segmentSeriesMode:'all'};
const HELP={finish:'Officiella sluttider för FINISHED. Samma 15-minutersbin används för alla könsserier. DNS, DNF och UNKNOWN ingår inte i histogrammet. Kvinna/man visas endast för källstödd uppgift.',percentiles:'P10, P25, P50, P75 och P90 är kvantiler av giltiga sluttider hos fullföljare i det aktuella fälturvalet. Median visas först vid n ≥ 5. Inga saknade tider blir noll.',podium:'Placering bland kvinnor respektive män bestäms av giltiga officiella målgångar eller positiva segmenttider mellan två valda, exakta observationer. Bilder från sociala medier används inte; initialavatarer visas.',groups:'Kön, klass, ålder och klubb/ort härleds enbart från publicerade EQ Timing-fält. Ett filtrerat urval påverkar fältstatistik men inte sökfunktionen.',status:'Anmälda är alla publicerade resultatrader i urvalet. Startande kräver känd startstatus (FINISHED + DNF + DSQ); en post med okänd status räknas inte som bekräftad start. DNF och Fullföljt visar respektive källstatus; DSQ och okänd status redovisas inte som egna delar här.',flow:'Visar antal verkliga TIME-registreringar vid varje publik kontroll för urvalets löpare. Trivial Start=100 % utelämnas. En saknad passage innebär inte i sig DNF.',placement:'Endast FINISHED med verklig sluttid och publicerad totalplacering. Klick på en punkt för att öppna löparprofilen.',standouts:'Ovanliga prestationer beräknas inom en edition från två verkliga tidtagningspassager. Minst fem giltiga observationer krävs där en gruppmedian används. Ingen personidentitet mellan år antas.',segments:'En segmenttid kräver två verkliga och tidsmässigt positiva passager. Start=0 används före första observerade kontroll. Delsträckans distans kommer från källans timingaxel, inte från GPS-vägens längd. Median n ≥ 5; Q25–Q75 n ≥ 10.',course:'Källbelagd arrangörs- eller deltagargeometri används som displayrutt ovanpå OpenStreetMap med sin redovisade proveniens. Deltagarspår är inte officiell ban- eller tidtagningsevidens. Kartposition mellan verifierade ändankare är illustrativ; rå D+ är inte officiell höjdmetrik.',plan:'Måltiden fördelas efter medianen av exakta segmenttidsandelar (segmenttid / sluttid) inom vald edition och kohort, minst fem per segment. Saknas historiskt underlag används explicit timingdistans som märkt fallback. Värdena normaliseras till exakt hela måltiden; planen är en pacingreferens, inte prognos.',history:'Deltagarantal, fullföljare och status kan visas för alla källstödda år. Enskilda års mediantider redovisas separat men kopplas inte till en gemensam utvecklingskurva utan verifierad whole-course-jämförbarhet. År 2020 har ingen importkälla i arkivet.'};
HELP.placement+=' okänd status räknas inte som bekräftad start.';
function showHelp(title,body){$('#help-title').textContent=title||'Metod';$('#help-content').textContent=`${body||'Beskrivning saknas.'} Visningen utgår alltid från det aktuella urvalet och publicerade källfält. Saknade värden visas som saknade och ersätts aldrig med antaganden.`;$('#help-dialog').showModal()}
const famLabel=id=>({ultra85:'85 km',trail43:'43 km',trail22:'22 km'}[id]||id);
const eqTimingKm=r=>num(r?.eq_timing_leg_km)?r.eq_timing_leg_km:r?.nominal_km;
const advertisedKm=r=>num(r?.organizer_advertised_km)?r.organizer_advertised_km:eqTimingKm(r);
const wholeCoursePaceKm=r=>r?.distance_semantics_status==='organizer_eq_discrepancy'?(num(r?.measured_route_geometry_km)?r.measured_route_geometry_km:null):eqTimingKm(r);
const editionDistanceLabel=r=>num(r?.organizer_advertised_km)&&r.organizer_advertised_km!==eqTimingKm(r)?`${fmtKm(r.organizer_advertised_km)} km annonserat · EQ Timing ${fmtKm(eqTimingKm(r))} km`:`${fmtKm(eqTimingKm(r))} km`;
const finish=r=>r.status==='FINISHED'&&num(r.finish_seconds)&&r.finish_seconds>0;
const explicitClassSex=r=>{const value=String(r?.class_name||'').trim().toLocaleLowerCase('sv');return /^(kvinna|kvinnor|dam)(\b|\s|$)/.test(value)?'F':/^(man|män|herr)(\b|\s|$)/.test(value)?'M':null};
const analyticalSex=r=>{const source=r?.sex==='F'||r?.sex==='M'?r.sex:null,fromClass=explicitClassSex(r);return source&&fromClass&&source!==fromClass?null:source};
const sexLabel=r=>analyticalSex(r)==='F'?'Kvinna':analyticalSex(r)==='M'?'Man':'Okänt/inkonsekvent';
function records(){return S.race?.results||[]}
function splitsFor(id){return (S._splits||(S._splits=new Map())).get(id)||[]}
function buildSplitIndex(){S._splits=new Map();S._observedStations=new Set();for(const v of S.race.splits){S._observedStations.add(v.station_uid);if(!S._splits.has(v.result_id))S._splits.set(v.result_id,[]);S._splits.get(v.result_id).push(v)}const order=new Map(S.race.stations.map((v,i)=>[v.uid,i]));for(const values of S._splits.values())values.sort((a,b)=>(order.get(a.station_uid)??999)-(order.get(b.station_uid)??999));}
function observed(r,station){return splitsFor(r.id).find(s=>s.station_uid===station.uid)||null}
function boundaries(){// Preserve metadata-only stations in the source table; do not make them an observed segment endpoint.
let cp=S.race.stations.filter(s=>s.is_analysis_boundary&&num(s.km)&&s.km>0&&S._observedStations?.has(s.uid)).sort((a,b)=>a.sort-b.sort||a.km-b.km);return [{uid:'start',name:'Start',km:0},...cp]}
function pairs(r){let c=boundaries(),out=[];for(let i=1;i<c.length;i++){let a=c[i-1],b=c[i];if(!num(a.km)||!num(b.km)||b.km<=a.km)continue;let sa=i===1?{elapsed_seconds:0,place:null}:observed(r,a),sb=observed(r,b);if(!sa||!sb||!num(sb.elapsed_seconds)||!num(sa.elapsed_seconds)||sb.elapsed_seconds<=sa.elapsed_seconds)continue;out.push({index:i-1,from:a,to:b,seconds:sb.elapsed_seconds-sa.elapsed_seconds,placeFrom:sa.place,placeTo:sb.place,km:b.km-a.km});}return out;}
function segmentStats(rows){let cp=boundaries(),segs=[];for(let i=1;i<cp.length;i++){let a=cp[i-1],b=cp[i],km=b.km-a.km;if(!num(km)||km<=0)continue;let obs=[];for(const r of rows.filter(finish)){let s=pairs(r).find(p=>p.index===i-1);if(s)obs.push({...s,r});}let xs=obs.map(x=>x.seconds),n=xs.length;segs.push({index:i-1,from:a,to:b,km,n,median:n>=5?median(xs):null,q25:n>=10?quant(xs,.25):null,q75:n>=10?quant(xs,.75):null,obs});}return segs;}
/* A valid TIME pair does not certify that its public timing-km metadata is
   physical course distance. Assess pace against the UNFILTERED source field,
   never a narrow cohort whose slower median could conceal an axis mismatch. */
function paceDistanceSupported(s){
 if(!num(s.km)||s.km<=0)return false;
 if(!S._distanceCapability){
  S._distanceCapability=new Map();
  segmentStats(records()).forEach(x=>{
   const implied=x.n>=5&&num(x.median)&&x.median>0?x.km/(x.median/3600):null;
   const knownUnverified=S.race?.family==='trail43'&&[2023,2024].includes(S.race.year)&&x.from.name==='Torrås'&&x.to.name==='Almered';
   S._distanceCapability.set(String(x.from.uid)+':'+String(x.to.uid),
      !(knownUnverified||(x.km>=3&&num(implied)&&implied>20)));
  });
 }
 return S._distanceCapability.get(String(s.from.uid)+':'+String(s.to.uid))!==false;
}
const currentSeg=()=>segmentStats(S.filtered)[S.selectedSegment]||null;
// Club/ort suggestions are derived from the selected edition's actual EQ Timing club field.
const clubKey=value=>String(value||'').trim().normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('sv');
function prepareClubOptions(){
  const clubs=new Map();
  for(const row of records()){
    const name=String(row.club||'').trim(),key=clubKey(name);
    if(!key)continue;
    const existing=clubs.get(key);
    if(existing)existing.count++;
    else clubs.set(key,{name,count:1,key});
  }
  S.clubOptions=[...clubs.values()].sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name,'sv'));
  hideClubSuggestions();
}
function hideClubSuggestions(){
  const input=$('#club-filter'),host=$('#club-suggestions');
  if(!input||!host)return;
  host.hidden=true;
  input.setAttribute('aria-expanded','false');
  input.removeAttribute('aria-activedescendant');
  S.clubSuggestionIndex=-1;
}
function renderClubSuggestions(showAll=false){
  const input=$('#club-filter'),host=$('#club-suggestions');
  if(!input||!host)return;
  const q=clubKey(input.value);
  if(!q&&!showAll){hideClubSuggestions();return}
  const matches=S.clubOptions.filter(item=>!q||item.key.includes(q)).sort((a,b)=>{
    const ap=q&&a.key.startsWith(q)?0:1,bp=q&&b.key.startsWith(q)?0:1;
    return ap-bp||b.count-a.count||a.name.localeCompare(b.name,'sv');
  }).slice(0,8);
  S.clubSuggestionIndex=-1;
  input.removeAttribute('aria-activedescendant');
  host.innerHTML=matches.length?matches.map((item,i)=>
    '<button type="button" id="club-choice-'+i+'" class="club-suggestion" role="option" aria-selected="false" tabindex="-1" data-club-option="'+html(item.name)+'"><span>'+html(item.name)+'</span><small>'+item.count+' deltagare</small></button>'
  ).join(''):'<p class="club-suggestion-empty">Inga klubbar eller orter matchar. Du kan fortfarande filtrera på texten.</p>';
  host.hidden=false;
  input.setAttribute('aria-expanded','true');
  Array.from(host.querySelectorAll('[data-club-option]')).forEach(button=>button.addEventListener('click',()=>selectClubSuggestion(button.dataset.clubOption)));
}
function activateClubSuggestion(index){
  const options=Array.from($('#club-suggestions').querySelectorAll('[data-club-option]'));
  if(!options.length)return;
  S.clubSuggestionIndex=(index+options.length)%options.length;
  const input=$('#club-filter');
  options.forEach((button,i)=>{
    const active=i===S.clubSuggestionIndex;
    button.classList.toggle('active',active);
    button.setAttribute('aria-selected',String(active));
  });
  input.setAttribute('aria-activedescendant',options[S.clubSuggestionIndex].id);
  options[S.clubSuggestionIndex].scrollIntoView({block:'nearest'});
}
function selectClubSuggestion(name){
  S.club=String(name||'');
  S.clubExact=true;
  $('#club-filter').value=S.club;
  rerenderFilter();
  $('#club-filter').focus();
  hideClubSuggestions();
}

function subset(){let list=records().filter(r=>(S.sex==='all'||analyticalSex(r)===S.sex)&&(S.status==='all'||r.status===S.status)&&(S.className==='all'||r.class_name===S.className)&&(!S.club||(S.clubExact?clubKey(r.club)===clubKey(S.club):clubKey(r.club).includes(clubKey(S.club)))));S.filtered=list;$('#filter-count').textContent=`${format(list.length)} av ${format(records().length)} resultat i detta urval. Individuell sök och jämförelse använder hela upplagan.`;return list}
function updateQuery(mode='replace'){let hash=new URLSearchParams(location.hash.includes('=')?location.hash.slice(1):'');hash.set('family',S.family);hash.set('year',S.year);if(mode==='push')for(const key of ['compareA','compareB','compareTime','compareSegment'])hash.delete(key);let target='#'+hash.toString();if(location.hash===target)return;if(mode==='push')history.pushState(null,'',target);else if(mode==='replace')history.replaceState(null,'',target);}
function requestedEdition(){const query=new URLSearchParams(location.search),hash=new URLSearchParams(location.hash.slice(1));return {family:hash.get('family')||query.get('family'),year:Number(hash.get('year')||query.get('year'))||null}}
function parseQuery(){const requested=requestedEdition(),family=requested.family;if(['ultra85','trail43','trail22'].includes(family))S.family=family;const year=requested.year;if(year&&S.boot.editions.some(e=>e.family===S.family&&e.year===year))S.year=year;}
async function init(){try{S.boot=await fetch('data/bootstrap.json').then(r=>{if(!r.ok)throw Error('Katalogen kunde inte läsas ('+r.status+')');return r.json()});window.SatilaMultiYearComparison?.init?.({boot:S.boot});parseQuery();if(!S.year)S.year=Math.max(...S.boot.editions.filter(e=>e.family===S.family).map(e=>e.year));ensureMapDuelControls();bind();await loadRace();const initialHash=new URLSearchParams(location.hash.slice(1)),requestedRunner=initialHash.get('runner')||new URLSearchParams(location.search).get('runner');if(requestedRunner){const runner=findRecord(requestedRunner)||records().find(row=>String(row.bib)===String(requestedRunner));if(runner)openProfile(runner.id)}else restoreComparisonFromUrl(initialHash);const nextHash=initialHash.get('section');if(nextHash)document.getElementById(nextHash)?.scrollIntoView();else if(!location.hash)scrollTo(0,0);}catch(err){$('#race-title').textContent='Källmaterialet kunde inte laddas';$('#race-subtitle').textContent=err.message;console.error(err);}}
async function loadRace(historyMode='replace'){let id=++S.loading;let ed=S.boot.editions.find(e=>e.family===S.family&&e.year===S.year);if(!ed)return;$('#race-title').textContent=`${famLabel(S.family)} · ${S.year}`;$('#race-subtitle').textContent=ed.label+' · '+ed.date;$('#source-indicator').textContent='Hämtar publicerade EQ-data…';let race;try{let req=await fetch(`data/races/${encodeURIComponent(ed.race_key)}.json`);if(!req.ok)throw Error('Detta lopp saknar datafil ('+req.status+')');race=await req.json();}catch(err){if(id!==S.loading)return;S.race=null;S.route=null;$('#source-indicator').textContent='Kunde inte hämta tävlingsdata: '+err.message;$('#source-indicator').setAttribute('role','alert');$('#race-subtitle').textContent='Upplagan kan inte visas just nu. Välj ett annat år eller försök igen.';$('#segment-table tbody').innerHTML='';$('#results-table tbody').innerHTML='';return;}if(id!==S.loading)return;$('#source-indicator').removeAttribute('role');S.race=race;S._splits=null;S._distanceCapability=null;buildSplitIndex();S.page=0;S.selectedSegment=0;S.podiumStart=0;S.podiumEnd=1;S.placementZoom=0;S.placementWindow=null;S.segmentSeriesMode='all';S.courseD=null;S.courseFromSegment=false;S.sex='all';S.status='all';S.className='all';S.club='';S.clubExact=false;S.compare=[];S.mapDuel=[];S.duelClock=0;S.compareSegment=null;S.duelCamera='both';S.duelManualZoom=false;S.selectedClubs=null;S.extraClassSelection=null;document.querySelectorAll('[data-family]').forEach(b=>{b.classList.toggle('selected',b.dataset.family===S.family);b.setAttribute('aria-pressed',String(b.dataset.family===S.family))});$('#year-select').innerHTML=S.boot.editions.filter(e=>e.family===S.family).map(e=>`<option value="${e.year}" ${e.year===S.year?'selected':''}>${e.year} · ${html(advertisedKm(e))} km</option>`).join('');$('#source-indicator').textContent='Verifierat EQ Timing · '+race.stations.length+' stationer';$('#official-source').href=ed.source_url;$('#scope-status').textContent=`${format(ed.results)} resultat · ${format(ed.finishers)} målgångar · ${format(ed.split_observations)} tidspassager`;
$('#sex-filter').value='all';$('#status-filter').value='all';$('#club-filter').value='';prepareClubOptions();$('#class-filter').innerHTML='<option value="all">Alla klasser</option>'+Array.from(new Set(records().map(r=>r.class_name).filter(Boolean))).sort((a,b)=>a.localeCompare(b,'sv')).map(k=>`<option value="${html(k)}">${html(k)}</option>`).join('');S.route=null;const source=ed.route_file;if(source){try{S.route=await fetch('data/'+source).then(r=>r.ok?r.json():null)}catch{S.route=null}}if(id!==S.loading)return;$('#course-source').textContent=S.route?(S.route.type==='VERIFIED_PARTICIPANT'?(S.route.normalized_source_group?`Normaliserad deltagarbaserad bana för ${S.race.year} · ${fmtKm(S.route.geometry_length_km)} km. Korrigerad visningsgeometri, inte officiell arrangörsbana eller löparens uppmätta positioner. Beräkningarna använder endast registrerade EQ Timing-passager.`:`Verifierat deltagar-GPX för ${S.race.year} · ${fmtKm(S.route.geometry_length_km)} km. Banans GPS-geometri är separat från EQ Timings kontrollavstånd; beräkningar använder endast registrerade TIME-passager.`):`Arrangörsrutt ${S.route.edition_references.join('–')} · GPX-displaylängd ${fmtKm(S.route.geometry_length_km)} km · 2025/2026 återanvändning som arbetsantagande.`):'Ingen publicerbar GPX-geometri kopplad till denna upplaga ännu. Kontrolltiderna påverkas inte.';if(S.route?.elevation_provenance?.type==='SPATIALLY_TRANSFERRED_PARTICIPANT_GPX')$('#course-source').textContent+=' Höjdprofil: geografiskt överförd från 2024 års deltagar-GPX, inte uppmätt 2023-höjd eller officiella höjdmeter.';const editionFinishTimes=records().filter(finish).map(r=>r.finish_seconds),target=median(editionFinishTimes);$('#target-time').value=num(target)?time(target):'';$('#target-time').dataset.defaultSource='edition-median';$('#target-time').dataset.defaultN=String(editionFinishTimes.length);$('#target-time').dataset.defaultSeconds=num(target)?String(target):'';const goalPlacement=$('#goal-placement-time');if(goalPlacement)goalPlacement.value='';updateQuery(historyMode);renderAll();window.SatilaMultiYearComparison?.setContext?.(S.family,S.year);}
function renderAll(){subset();renderKpis();renderOverview();renderCumulativeFinish();renderClassDetails();renderDynamics();renderSegments();renderCourse();renderHistory();renderResults();renderFavorites();renderCompareChips();renderMapDuelChips();renderSearchSuggestions();const version=S.loading;clearTimeout(S._extraTimer);S._extraTimer=setTimeout(()=>{if(version!==S.loading)return;try{window.SatilaExtras?.renderAll?.()}catch(err){console.error('Sätila analytics extension:',err)}},100);}
function rerenderFilter(){S.page=0;subset();renderKpis();renderOverview();renderCumulativeFinish();renderClassDetails();renderDynamics();renderSegments();renderResults();const version=S.loading;clearTimeout(S._extraTimer);S._extraTimer=setTimeout(()=>{if(version!==S.loading)return;try{window.SatilaExtras?.renderFiltered?.()}catch(err){console.error('Sätila analytics filter:',err)}},50);}
function setFamily(v){if(v===S.family)return;S.family=v;S.year=Math.max(...S.boot.editions.filter(e=>e.family===v).map(e=>e.year));loadRace('push').catch(console.error)}
function bind(){$$('[data-family]').forEach(el=>el.addEventListener('click',()=>setFamily(el.dataset.family)));$('#year-select').addEventListener('change',e=>{S.year=+e.target.value;loadRace('push').catch(console.error)});$('#open-picker').addEventListener('click',()=>$('#race-context').scrollIntoView());$('#menu-toggle').addEventListener('click',()=>{let n=$('.primary-nav'),a=n.classList.toggle('open');$('#menu-toggle').setAttribute('aria-expanded',String(a))});$$('.primary-nav a').forEach(a=>a.addEventListener('click',()=>{$('.primary-nav').classList.remove('open');$('#menu-toggle').setAttribute('aria-expanded','false')}));document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('.primary-nav').classList.contains('open')){$('.primary-nav').classList.remove('open');$('#menu-toggle').setAttribute('aria-expanded','false');$('#menu-toggle').focus()}});
for(const [id,k] of [['sex-filter','sex'],['status-filter','status'],['class-filter','className']])$('#'+id).addEventListener('change',e=>{S[k]=e.target.value;rerenderFilter()});$('#club-filter').addEventListener('input',e=>{S.club=e.target.value;S.clubExact=false;rerenderFilter();renderClubSuggestions()});
$('#club-filter').addEventListener('focus',()=>renderClubSuggestions(true));
$('#club-filter').addEventListener('keydown',e=>{
  const host=$('#club-suggestions');
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){
    e.preventDefault();
    if(host.hidden)renderClubSuggestions(true);
    const count=host.querySelectorAll('[data-club-option]').length;
    if(!count)return;
    activateClubSuggestion(S.clubSuggestionIndex<0?(e.key==='ArrowDown'?0:count-1):S.clubSuggestionIndex+(e.key==='ArrowDown'?1:-1));
  }else if(e.key==='Enter'&&!host.hidden&&S.clubSuggestionIndex>=0){
    e.preventDefault();
    const item=host.querySelectorAll('[data-club-option]')[S.clubSuggestionIndex];
    if(item)selectClubSuggestion(item.dataset.clubOption);
  }else if(e.key==='Escape'||e.key==='Tab'){
    hideClubSuggestions();
  }
});
document.addEventListener('pointerdown',e=>{if(!e.target.closest('.club-filter-field'))hideClubSuggestions()});
document.addEventListener('focusin',e=>{if(!e.target.closest('.club-filter-field'))hideClubSuggestions()});$('#speed-unit').addEventListener('change',e=>{S.unit=e.target.value;rerenderFilter();renderProfileIfOpen()});$('#reset-filters').addEventListener('click',()=>{S.sex=S.status=S.className='all';S.club='';S.clubExact=false;S.selectedClubs=null;hideClubSuggestions();for(let k of ['sex','status','class'])$('#'+k+'-filter').value='all';$('#club-filter').value='';rerenderFilter()});$('#results-search').addEventListener('input',e=>{S.q=e.target.value;S.page=0;renderResults()});$('#results-sort').addEventListener('change',e=>{S.sort=e.target.value;S.page=0;renderResults()});$('#page-prev').addEventListener('click',()=>{S.page=Math.max(0,S.page-1);renderResults()});$('#page-next').addEventListener('click',()=>{S.page++;renderResults()});$('#podium-segment-start').addEventListener('change',e=>{S.podiumStart=+e.target.value;if(S.podiumEnd<=S.podiumStart)S.podiumEnd=S.podiumStart+1;S.selectedSegment=S.podiumStart;renderSegmentSelectors();focusSelectedSegmentOnCourse();renderSegmentPodium();renderSegmentTable();renderSegmentGraph(segmentStats(S.filtered));renderCourse()});$('#podium-segment-end').addEventListener('change',e=>{S.podiumEnd=+e.target.value;renderSegmentPodium()});
$('#runner-search').addEventListener('input',renderSearchSuggestions);$('#runner-search').addEventListener('keydown',e=>{let list=$$('.suggestion',$('#runner-suggestions'));if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(!list.length)return;S.searchIndex=(S.searchIndex+(e.key==='ArrowDown'?1:-1)+list.length)%list.length;list.forEach((x,i)=>x.classList.toggle('active',i===S.searchIndex));list[S.searchIndex]?.focus()}else if(e.key==='Enter'&&list.length){e.preventDefault();openProfile(list[Math.max(0,S.searchIndex)].dataset.id)}else if(e.key==='Escape')$('#runner-suggestions').innerHTML=''});$('#map-duel-search').addEventListener('input',renderMapDuelSuggestions);$('#map-duel-search').addEventListener('keydown',e=>{const list=$$('.suggestion',$('#map-duel-suggestions'));if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(!list.length)return;S.mapDuelSearchIndex=(S.mapDuelSearchIndex+(e.key==='ArrowDown'?1:-1)+list.length)%list.length;list.forEach((x,i)=>x.classList.toggle('active',i===S.mapDuelSearchIndex));list[S.mapDuelSearchIndex]?.focus()}else if(e.key==='Enter'&&list.length){e.preventDefault();addMapDuel(list[Math.max(0,S.mapDuelSearchIndex)].dataset.mapDuelId)}else if(e.key==='Escape')$('#map-duel-suggestions').innerHTML=''});$('#open-compare').addEventListener('click',openCompare);$('#calculate-plan').addEventListener('click',renderPlan);$('#target-time').addEventListener('keydown',e=>{if(e.key==='Enter')renderPlan()});$('#plan-cohort').addEventListener('change',renderPlan);$('#course-fit').addEventListener('click',()=>{S.courseD=null;renderCourseMap()});$$('.info').forEach(el=>el.addEventListener('click',()=>{let id=el.dataset.help;showHelp(el.parentElement?.querySelector('h3')?.textContent,HELP[id])}));$$('[data-close]').forEach(el=>el.addEventListener('click',()=>{const name=el.dataset.close;$('#'+name).close();if(name==='profile-dialog'){const target=S.profileReturnFocus?.isConnected?S.profileReturnFocus:$('#runner-search');target?.focus()}}));$$('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d)d.close()}));$$('.section-nav a').forEach(a=>a.addEventListener('click',()=>{$$('.section-nav a').forEach(x=>x.classList.remove('active'));a.classList.add('active')}));const restoreEditionFromUrl=()=>{const fragment=new URLSearchParams(location.hash.slice(1)); // Section anchors are not requests to change the selected edition.
 if(location.hash&&!fragment.has('family')&&!fragment.has('year'))return;
 const requested=requestedEdition(),family=['ultra85','trail43','trail22'].includes(requested.family)?requested.family:S.family,years=S.boot?.editions.filter(e=>e.family===family).map(e=>e.year)||[],year=requested.year&&years.includes(requested.year)?requested.year:(family===S.family&&years.includes(S.year)?S.year:Math.max(...years));
 if(years.length&&(family!==S.family||year!==S.year)){S.family=family;S.year=year;loadRace('none').catch(console.error)}};window.addEventListener('hashchange',restoreEditionFromUrl);window.addEventListener('popstate',restoreEditionFromUrl);}
function renderKpis(){const rows=S.filtered,counts=collections(rows.map(r=>r.status)),started=(counts.FINISHED||0)+(counts.DNF||0)+(counts.DSQ||0),statuses=[['Anmälda',rows.length,'#244e38'],['Startande',started,'#4d7454'],['DNF',counts.DNF||0,'#cb9150'],['Fullföljt',counts.FINISHED||0,'#34795c']],completion=started?100*(counts.FINISHED||0)/started:null;$('#kpis').innerHTML=`<div id="status-chart"><div class="status-summary kpi-status-summary">${statuses.map(([label,value,color])=>`<article style="--status-color:${color}"><span>${label}</span><strong>${format(value)}</strong><div class="status-meter" aria-hidden="true"><i style="width:${rows.length?100*value/rows.length:0}%"></i></div></article>`).join('')}</div></div><p class="small muted kpi-note">Fullföljandegrad: ${completion===null?'—':completion.toFixed(1).replace('.',',')+' %'}. Startande = FINISHED + DNF + DSQ med känd startstatus. DNS och okänd status finns kvar i källdatan men visas inte som egna dashboardkort. Aktuellt filter: ${rows.length} av ${records().length} publicerade resultat.</p>`;}
function svg(w,h,body,aria){return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${html(aria)}" xmlns="http://www.w3.org/2000/svg">${body}</svg>`}
function empty(why='Tillräckligt källunderlag saknas för denna analys.'){return `<p class="empty">${html(why)}</p>`}
function renderOverview(){let fs=S.filtered.filter(finish);$('#finish-series').innerHTML=[['F','Kvinnor',SEX_COLORS.F],['M','Män',SEX_COLORS.M]].map(([key,label,c])=>`<label><input type="checkbox" data-finish-sex="${key}" ${S.finishSex.has(key)?'checked':''}/> <i style="display:inline-block;width:10px;height:10px;background:${c};border-radius:3px"></i>${label}</label>`).join('');$$('[data-finish-sex]').forEach(el=>el.addEventListener('change',e=>{if(e.target.checked)S.finishSex.add(e.target.dataset.finishSex);else S.finishSex.delete(e.target.dataset.finishSex);renderFinishChart()}));renderFinishChart();let pcts=[.1,.25,.5,.75,.9];
  const groups=[{label:'Kvinnor',color:SEX_COLORS.F,rows:fs.filter(r=>analyticalSex(r)==='F')},{label:'Män',color:SEX_COLORS.M,rows:fs.filter(r=>analyticalSex(r)==='M')}];
  const unknown=fs.filter(r=>!analyticalSex(r)).length;
  $('#percentile-chart').innerHTML=fs.length>=5?`<div class="sex-percentile-grid">${groups.map(g=>`<section class="sex-percentile-card"><h4><i style="background:${g.color}"></i>${g.label} <small>n=${g.rows.length}</small></h4>${g.rows.length>=5?`<div class="bars">${pcts.map(p=>{const v=quant(g.rows.map(r=>r.finish_seconds),p);return `<div class="barline" style="grid-template-columns:38px 1fr 64px"><strong>P${p*100}</strong><div class="bar-track"><div class="bar-fill" style="width:${p*100}%;background:${g.color}"></div></div><strong>${time(v)}</strong></div>`}).join('')}</div>`:'<p class="small muted">Minst fem fullföljare krävs för percentiler.</p>'}</section>`).join('')}</div><p class="muted small">Könsuppdelade sluttidspercentiler i aktuellt urval · ${unknown} med saknad könsuppgift redovisas inte i delserierna.</p>`:empty();
  $('#overall-podium').innerHTML=podiumPair(fs.filter(r=>r.place!=null).sort((a,b)=>a.place-b.place).map(r=>({r,value:time(r.finish_seconds)})));let counts=collections(fs.map(r=>r.class_name||'Ingen uppgift'));let max=Math.max(1,...Object.values(counts));$('#group-bars').innerHTML=`<div class="bars">${Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,6).map(([label,n])=>{const rows=fs.filter(r=>(r.class_name||'Ingen uppgift')===label),women=rows.filter(r=>analyticalSex(r)==='F').length,men=rows.filter(r=>analyticalSex(r)==='M').length,unknown=rows.length-women-men;return `<button class="barline" style="border:0;background:transparent;text-align:left;cursor:pointer" data-class-pick="${html(label)}"><span>${html(label)}</span><span class="bar-track" style="display:flex;overflow:hidden"><span style="display:block;width:${women/max*100}%;background:${SEX_COLORS.F}" title="Kvinnor: ${women}"></span><span style="display:block;width:${men/max*100}%;background:${SEX_COLORS.M}" title="Män: ${men}"></span><span style="display:block;width:${unknown/max*100}%;background:${SEX_COLORS.unknown}" title="Okänt/inkonsekvent: ${unknown}"></span></span><strong>${n} <small style="display:block;font-weight:500">K ${women} · M ${men}${unknown?' · ? '+unknown:''}</small></strong></button>`}).join('')}</div><p class="small muted">Kvinnor (rosa) · män (blått) · okänt eller källinkonsekvent kön (grått). Antal fullföljare per klass.</p>`;$$('[data-class-pick]').forEach(b=>b.addEventListener('click',()=>{let k=b.dataset.classPick;if(![...$('#class-filter').options].some(o=>o.value===k))return;S.className=k;$('#class-filter').value=k;rerenderFilter()}));bindResultLinks($('#overall-podium'));}
function collections(arr){let c={};for(let x of arr)c[x]=(c[x]||0)+1;return c}
// Shared analytical palette: women pink, men blue; neutral/unknown remains grey.
const SEX_COLORS={F:'#d65a91',M:'#3479c5',unknown:'#aab3ad'};
function chartYTicks(left,right,top,bottom,min,max,format,steps=4){
  return Array.from({length:steps+1},(_,i)=>{
    const value=min+(max-min)*i/steps,y=bottom-(bottom-top)*i/steps;
    return `<line x1="${left}" x2="${right}" y1="${y}" y2="${y}" stroke="currentColor" opacity="${i===0 ? .27 : .12}"/><text x="${left-6}" y="${y+3}" text-anchor="end">${format(value)}</text>`;
  }).join('');
}
function chartXTicks(left,right,y,min,max,format,steps=6){
  return Array.from({length:steps+1},(_,i)=>{
    const value=min+(max-min)*i/steps,x=left+(right-left)*i/steps;
    return `<line x1="${x}" x2="${x}" y1="${y}" y2="${y+4}" stroke="currentColor" opacity=".4"/><text x="${x}" y="${y+16}" text-anchor="middle">${format(value)}</text>`;
  }).join('');
}
function renderFinishChart(){
  const fs=S.filtered.filter(finish),mode=S.finishSex.size===2?'all':S.finishSex.has('F')?'F':'M';
  const controls=$('#finish-series');
  controls.innerHTML=[['all','Alla'],['F','Kvinnor'],['M','Män']].map(([key,label])=>`<button type="button" class="series-button" data-finish-mode="${key}" aria-pressed="${mode===key}">${label}</button>`).join('');
  $$('[data-finish-mode]',controls).forEach(button=>button.addEventListener('click',()=>{S.finishSex=new Set(button.dataset.finishMode==='all'?['F','M']:[button.dataset.finishMode]);renderFinishChart()}));
  if(!fs.length){$('#finish-chart').innerHTML=empty();return}
  const min=Math.floor(Math.min(...fs.map(r=>r.finish_seconds))/900)*900,max=Math.ceil(Math.max(...fs.map(r=>r.finish_seconds))/900)*900;
  if(max-min>900*160){$('#finish-chart').innerHTML=empty('Sluttidsspridningen är mycket stor; välj ett snävare fält.');return}
  const bins=[];for(let start=min;start<=max;start+=900)bins.push({start,women:fs.filter(r=>analyticalSex(r)==='F'&&r.finish_seconds>=start&&r.finish_seconds<start+900).length,men:fs.filter(r=>analyticalSex(r)==='M'&&r.finish_seconds>=start&&r.finish_seconds<start+900).length,unk:fs.filter(r=>!analyticalSex(r)&&r.finish_seconds>=start&&r.finish_seconds<start+900).length});
  const W=600,H=235,P=42,bw=(W-2*P)/bins.length,peak=Math.max(1,...bins.map(b=>(mode!=='M'?b.women:0)+(mode!=='F'?b.men:0)+(mode==='all'?b.unk:0)));
  const body=chartYTicks(P,W-P,47,205,0,peak,v=>String(Math.round(v)))+chartXTicks(P,W-P,205,min,max,v=>time(v),Math.min(6,Math.max(2,Math.floor(bins.length/3))))+bins.map((b,i)=>{const x=P+i*bw,w=Math.max(1,bw-1),nw=mode!=='M'?b.women:0,nm=mode!=='F'?b.men:0,nu=mode==='all'?b.unk:0,h1=nw/peak*158,h2=nm/peak*158,h3=nu/peak*158;return `<rect x="${x}" y="${205-h1}" width="${w}" height="${h1}" fill="${SEX_COLORS.F}"><title>Kvinnor ${nw} · ${time(b.start)}–${time(b.start+900)}</title></rect><rect x="${x}" y="${205-h1-h2}" width="${w}" height="${h2}" fill="${SEX_COLORS.M}"><title>Män ${nm} · ${time(b.start)}–${time(b.start+900)}</title></rect><rect x="${x}" y="${205-h1-h2-h3}" width="${w}" height="${h3}" fill="#aab3ad"><title>Kön saknas ${nu}</title></rect>`}).join('');
  const shown=mode==='all'?fs.length:fs.filter(r=>analyticalSex(r)===mode).length;
  $('#finish-chart').innerHTML=svg(W,H,body,'Sluttidshistogram, 15-minutersintervall')+`<p class="small muted">${shown} av ${fs.length} fullföljare i aktuellt urval. Alla omfattar även ${fs.filter(r=>!analyticalSex(r)).length} med okänt eller källinkonsekvent kön. Fasta 15-minutersintervall mellan vyerna.</p>`;
}
const initial=n=>String(n||'?').split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase();
function podiumPair(objs,limit=3){return ['F','M'].map(sex=>`<div class="podium-group"><h4>${sex==='F'?'KVINNOR':'MÄN'} <small>n=${objs.filter(x=>analyticalSex(x.r)===sex).length}</small></h4>${objs.filter(x=>analyticalSex(x.r)===sex).slice(0,limit).map((o,i)=>`<button class="podium-row" type="button" data-open="${html(o.r.id)}"><span class="medal medal-${i+1}">${i+1}</span><span class="avatar" aria-hidden="true">${html(initial(o.r.name))}</span><span><strong>${html(o.r.name)}</strong><small>${html(o.r.class_name||'')} · #${html(o.r.bib)}</small></span><span class="finish">${html(o.value)}</span></button>`).join('')||'<p class="muted small">Ingen verifierad prestation.</p>'}</div>`).join('')}
function renderDynamics(){
 const rows=S.filtered,host=$('#placement-chart'),original=rows.filter(r=>finish(r)&&num(r.place));let fs=original.slice(),zoom=S.placementZoom||0;
 if(S.placementWindow){const w=S.placementWindow,visible=fs.filter(r=>r.finish_seconds>=w.t0&&r.finish_seconds<=w.t1&&r.place>=w.p0&&r.place<=w.p1);if(visible.length>=2)fs=visible;else S.placementWindow=null}
 if(!S.placementWindow&&zoom){const ordered=fs.map(r=>r.finish_seconds).sort((a,b)=>a-b),lo=quant(ordered,zoom===1 ? .10 : .25),hi=quant(ordered,zoom===1 ? .90 : .75),visible=fs.filter(r=>r.finish_seconds>=lo&&r.finish_seconds<=hi);if(visible.length>=2)fs=visible;else{zoom=0;S.placementZoom=0}}
 if(fs.length<2){host.innerHTML=empty();renderStandouts();return}
 const W=760,H=310,L=62,R=24,T=28,B=48,tmin=Math.min(...fs.map(r=>r.finish_seconds)),tmax=Math.max(...fs.map(r=>r.finish_seconds)),minPlace=Math.min(...fs.map(r=>r.place)),maxPlace=Math.max(...fs.map(r=>r.place)),tdiff=Math.max(1,tmax-tmin),pdiff=Math.max(1,maxPlace-minPlace),x=value=>L+(value-tmin)/tdiff*(W-L-R),y=value=>T+(value-minPlace)/pdiff*(H-T-B);
 const axes=Array.from({length:6},(_,i)=>{const value=minPlace+pdiff*i/5,yy=y(value);return `<line x1="${L}" x2="${W-R}" y1="${yy}" y2="${yy}" stroke="currentColor" opacity="${i===5 ? .27 : .12}"/><text x="${L-7}" y="${yy+4}" text-anchor="end">#${Math.round(value)}</text>`}).join('')+chartXTicks(L,W-R,H-B,tmin,tmax,v=>time(v),6);
 const points=fs.map(r=>`<circle tabindex="0" role="button" data-open="${html(r.id)}" cx="${x(r.finish_seconds).toFixed(1)}" cy="${y(r.place).toFixed(1)}" r="4.5" fill="${analyticalSex(r)==='F'?SEX_COLORS.F:analyticalSex(r)==='M'?SEX_COLORS.M:SEX_COLORS.unknown}" aria-label="Öppna ${html(r.name)} ${time(r.finish_seconds)}"><title>${html(r.name)} · ${html(sexLabel(r))} · ${html(r.class_name||'Klass saknas')} · ${time(r.finish_seconds)} · #${r.place}</title></circle>`).join('');
 const controls=`<div class="placement-zoom-controls"><button type="button" class="btn text-btn" id="placement-zoom-in" ${zoom>=2||S.placementWindow?'disabled':''}>Tangentbordszoom</button><button type="button" class="btn text-btn" id="placement-zoom-reset" ${!zoom&&!S.placementWindow?'disabled':''}>Återställ utsnitt</button><span role="status" aria-live="polite">${fs.length} av ${original.length} placerade fullföljare · ${S.placementWindow?'Eget draget utsnitt':zoom===0?'Hela fältet':zoom===1?'P10–P90':'P25–P75'}</span></div>`;
 host.innerHTML=controls+`<svg class="placement-scatter" viewBox="0 0 ${W} ${H}" role="img" aria-label="Sluttid mot totalplacering. Dra över bakgrunden för att zooma och öppna en punkt med klick eller Enter."><rect data-placement-brush x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}" fill="transparent"/><g class="chart-grid">${axes}</g><line x1="${L}" y1="${H-B}" x2="${W-R}" y2="${H-B}" class="axis"/><line x1="${L}" y1="${T}" x2="${L}" y2="${H-B}" class="axis"/><g class="placement-points">${points}</g><rect data-placement-selection class="placement-brush-selection" hidden/></svg><div class="map-legend"><span><i style="background:${SEX_COLORS.F}"></i>Kvinnor</span><span><i style="background:${SEX_COLORS.M}"></i>Män</span><span><i style="background:${SEX_COLORS.unknown}"></i>Okänt/inkonsekvent</span></div>`;
 const svgNode=$('svg',host),brush=$('[data-placement-brush]',host),selection=$('[data-placement-selection]',host);let start=null;
 const point=event=>{const rect=svgNode.getBoundingClientRect();return{x:Math.max(L,Math.min(W-R,(event.clientX-rect.left)*W/(rect.width||1))),y:Math.max(T,Math.min(H-B,(event.clientY-rect.top)*H/(rect.height||1)))}};
 const finishBrush=event=>{if(!start)return;const end=point(event),x0=Math.min(start.x,end.x),x1=Math.max(start.x,end.x),y0=Math.min(start.y,end.y),y1=Math.max(start.y,end.y);start=null;selection.hidden=true;if(x1-x0<26||y1-y0<22)return;S.placementZoom=0;S.placementWindow={t0:tmin+(x0-L)/(W-L-R)*tdiff,t1:tmin+(x1-L)/(W-L-R)*tdiff,p0:minPlace+(y0-T)/(H-T-B)*pdiff,p1:minPlace+(y1-T)/(H-T-B)*pdiff};renderDynamics()};
 svgNode.addEventListener('pointerdown',event=>{if(event.target.closest?.('[data-open]'))return;start=point(event);svgNode.setPointerCapture?.(event.pointerId);selection.hidden=false;selection.setAttribute('x',start.x);selection.setAttribute('y',start.y);selection.setAttribute('width',0);selection.setAttribute('height',0)});svgNode.addEventListener('pointermove',event=>{if(!start)return;const current=point(event),x0=Math.min(start.x,current.x),y0=Math.min(start.y,current.y);selection.setAttribute('x',x0);selection.setAttribute('y',y0);selection.setAttribute('width',Math.abs(current.x-start.x));selection.setAttribute('height',Math.abs(current.y-start.y))});svgNode.addEventListener('pointerup',finishBrush);svgNode.addEventListener('pointercancel',()=>{start=null;selection.hidden=true});
 $('#placement-zoom-in').addEventListener('click',()=>{S.placementWindow=null;S.placementZoom=Math.min(2,zoom+1);renderDynamics();$('#placement-zoom-in')?.focus()});$('#placement-zoom-reset').addEventListener('click',()=>{S.placementWindow=null;S.placementZoom=0;renderDynamics();$('#placement-zoom-in')?.focus()});
 renderStandouts();bindResultLinks($('#dynamics'))
}

/* Every standout uses source-supported adjacent TIME observations. Physical
   pacing categories never include a segment whose timing distance is gated. */
function standoutFinishStrength(profiles){
 const cps=boundaries(),goal=cps.at(-1);
 if(cps.length<4||goal?.name!=='Mål'||!num(goal.km)||goal.km<=0)return[];
 const breakpoint=cps.slice(1,-1).filter(p=>p.km>=goal.km*.55&&p.km<=goal.km*.80)
  .sort((a,b)=>Math.abs(a.km/goal.km-2/3)-Math.abs(b.km/goal.km-2/3))[0];
 if(!breakpoint)return[];
 return profiles.map(({r,parts})=>{
  // Require a continuous observed Start→Mål series and usable physical pacing
  // on every leg, rather than treating missing passings as if they were zero.
  if(parts.length!==cps.length-1||parts.some((part,i)=>part.index!==i||!paceDistanceSupported(part)))return null;
  const midway=observed(r,breakpoint),finishObs=observed(r,goal);
  const t0=midway?.elapsed_seconds,t1=finishObs?.elapsed_seconds;
  if(!num(t0)||!num(t1)||t0<=0||t1<=t0)return null;
  const before=breakpoint.km/t0,after=(goal.km-breakpoint.km)/(t1-t0);
  const ratio=after/before;
  return num(ratio)&&ratio>0?{r,ratio,from:breakpoint.name,to:goal.name}:null;
 }).filter(Boolean);
}
const STANDOUT_EXPLANATIONS={
 relative:'Löparens snabbaste verifierade delsträcka jämförs med den egna genomsnittshastigheten över hela loppet. 140 % betyder att hastigheten på just denna delsträcka var 40 % högre än löparens loppsnitt, inte att hela loppet gick 40 % snabbare. Terräng och lutning påverkar.',
 finish:'Fartbevarandet från kontrollen närmast två tredjedelar av banan fram till mål jämförs med farten före kontrollen. Resultatet jämförs med medianen för fullföljare av samma kön i urvalet: 112 % betyder 12 % starkare fartbevarande än gruppmedianen. Det betyder inte nödvändigtvis att löparen ökade farten – även den som saktar ned mindre än andra kan ligga över 100 %. Minst fem jämförbara löpare och sammanhängande verkliga TIME-passager krävs.',
 gain:'Största verkliga förbättring i totalplacering mellan två intilliggande kontroller. +23 platser betyder att löparen passerade 23 placeringar på den delsträckan. Bara positiva förbättringar rangordnas; en saknad placering antas aldrig vara noll.',
 even:'Lägst variation i tempo (sekunder per kilometer) mellan minst två verifierade delsträckor. 5 % variation är en variationskoefficient på 5 % (standardavvikelse delad med genomsnittstempo). Låg variation innebär jämnare tempo, men kupering och olika långa delsträckor påverkar jämförelsen.',
 last:'Snabbast registrerade tempo på den sista observerade delsträckan ända fram till mål, uttryckt i min/km eller km/h enligt ditt enhetsval. Endast verkliga TIME-par och delsträckor med tillförlitligt distansunderlag används. Detta är absolut fart, inte ett mått på vunna placeringar.'
};
function standoutsFor(rows){
 const paceKm=wholeCoursePaceKm(S.race);
 const profiles=rows.filter(finish).map(r=>({r,parts:pairs(r)})).filter(x=>x.parts.length>=2);
 const all=profiles.flatMap(x=>x.parts.map(s=>({...s,r:x.r,rel:num(paceKm)&&paceKm>0?s.seconds/s.km/(x.r.finish_seconds/paceKm):null})));
 if(!all.length)return[];
 const physical=all.filter(x=>paceDistanceSupported(x)&&num(x.rel)&&x.rel>0);
 const gain=all.filter(x=>num(x.placeFrom)&&num(x.placeTo)).map(x=>({...x,change:x.placeFrom-x.placeTo})).filter(x=>x.change>0);
 const finishEntries=standoutFinishStrength(profiles);
 const finishList=finishEntries.flatMap(x=>{
  const sex=analyticalSex(x.r),cohort=finishEntries.filter(y=>analyticalSex(y.r)===sex);
  if(!sex||cohort.length<5)return[];
  const groupMedian=median(cohort.map(y=>y.ratio));
  if(!num(groupMedian)||groupMedian<=0)return[];
  const index=100*x.ratio/groupMedian;
  return [{...x,index}];
 });
 const even=profiles.map(x=>{
  const z=x.parts.filter(p=>paceDistanceSupported(p)).map(p=>p.seconds/p.km);
  if(z.length<2)return null;
  const avg=z.reduce((a,b)=>a+b,0)/z.length;
  return avg>0?{r:x.r,cv:Math.sqrt(z.reduce((a,b)=>a+(b-avg)**2,0)/z.length)/avg}:null;
 }).filter(x=>x&&num(x.cv));
 const goal=boundaries().at(-1);
 const last=profiles.map(x=>{
  const p=x.parts.at(-1);
  return p&&p.to.uid===goal?.uid&&paceDistanceSupported(p)?{r:x.r,sec:p.seconds,km:p.km,name:p.to.name}:null;
 }).filter(Boolean);
 return [
  {id:'relative',title:'Relativt eget snitt',list:physical.sort((a,b)=>a.rel-b.rel).map(x=>({r:x.r,value:(100/x.rel).toFixed(0)+' % · '+x.to.name,score:x.rel}))},
  {id:'finish',title:'Starkaste avslutningen',list:finishList.sort((a,b)=>b.index-a.index).map(x=>({r:x.r,value:x.index.toFixed(0)+' % · '+x.from+' → '+x.to,score:-x.index}))},
  {id:'gain',title:'Största placeringslyftet',list:gain.sort((a,b)=>b.change-a.change).map(x=>({r:x.r,value:'+'+x.change+' · '+x.to.name,score:-x.change}))},
  {id:'even',title:'Jämnast pacing',list:even.sort((a,b)=>a.cv-b.cv).map(x=>({r:x.r,value:(100*x.cv).toFixed(1)+' % variation',score:x.cv}))},
  {id:'last',title:'Snabbast sista segment',list:last.sort((a,b)=>a.sec/a.km-b.sec/b.km).map(x=>({r:x.r,value:pace(x.sec,x.km,S.unit),score:x.sec/x.km}))}
 ];
}
function renderStandouts(){
 const categories=standoutsFor(S.filtered),host=$('#standouts');
 if(!categories.length){host.innerHTML=empty('För denna upplaga krävs fler verkliga segmentpar för att hitta ovanliga lopp.');return}
 if(!categories.some(c=>c.id===S.standoutTab))S.standoutTab=categories[0].id;
 const active=categories.find(c=>c.id===S.standoutTab);
 const unique=active.list.filter((x,i,a)=>a.findIndex(z=>z.r.id===x.r.id)===i);
 host.innerHTML=
  '<div class="standout-tabs" role="tablist" aria-label="Välj topplista">'+
    categories.map(c=>'<button type="button" role="tab" data-standout-tab="'+c.id+'" aria-controls="standout-active-panel" aria-selected="'+(c.id===active.id)+'">'+html(c.title)+'</button>').join('')+
  '</div>'+
  '<div class="standout-explanation" role="note" aria-live="polite"><strong>Så ska resultatet tolkas</strong><p>'+html(STANDOUT_EXPLANATIONS[active.id])+'</p></div>'+
  '<div class="standout-active" id="standout-active-panel" role="tabpanel"><h4>'+html(active.title)+'</h4><div class="podium-pair">'+podiumPair(unique,5)+'</div></div>';
 $$('[data-standout-tab]',host).forEach(button=>button.addEventListener('click',()=>{
  S.standoutTab=button.dataset.standoutTab;renderStandouts();bindResultLinks(host)
 }));
}
function renderSegmentSelectors(){const cp=boundaries(),start=$('#podium-segment-start'),end=$('#podium-segment-end');if(!start||!end)return;if(cp.length<2){start.innerHTML='';end.innerHTML='';return}S.podiumStart=Math.max(0,Math.min(S.podiumStart,cp.length-2));S.podiumEnd=Math.max(S.podiumStart+1,Math.min(S.podiumEnd,cp.length-1));start.innerHTML=cp.slice(0,-1).map((point,i)=>`<option value="${i}" ${i===S.podiumStart?'selected':''}>${html(point.name)}</option>`).join('');end.innerHTML=cp.map((point,i)=>i>S.podiumStart?`<option value="${i}" ${i===S.podiumEnd?'selected':''}>${html(point.name)}</option>`:'').join('')}
function renderSegments(){let segs=segmentStats(S.filtered);if(!segs.length){$('#segment-chart').innerHTML=empty();$('#segment-table tbody').innerHTML='';$('#podium-segment-start').innerHTML='';$('#podium-segment-end').innerHTML='';$('#segment-podium').innerHTML=empty();return}S.selectedSegment=Math.min(S.selectedSegment,segs.length-1);S.podiumStart=Math.min(S.podiumStart,segs.length-1);S.podiumEnd=Math.max(S.podiumStart+1,Math.min(S.podiumEnd,segs.length));renderSegmentSelectors();renderSegmentGraph(segs);renderSegmentTable();renderSegmentPodium()}
function selectAdjacentSegment(index){S.selectedSegment=index;S.podiumStart=index;S.podiumEnd=index+1;renderSegmentSelectors()}
function segmentModeRows(rows=S.filtered){return S.segmentSeriesMode==='all'?rows:rows.filter(r=>analyticalSex(r)===S.segmentSeriesMode)}
function distribution(values){return {n:values.length,median:values.length>=5?median(values):null,q25:values.length>=10?quant(values,.25):null,q75:values.length>=10?quant(values,.75):null}}
function modeDistributionSegments(segs){return segs.map(s=>{const obs=s.obs.filter(o=>S.segmentSeriesMode==='all'||analyticalSex(o.r)===S.segmentSeriesMode),d=distribution(obs.map(o=>o.seconds));return {...s,...d,obs}})}
function segmentModeControls(){return `<div class="segment-series-toggle" role="radiogroup" aria-label="Grupp för segmentdiagram">${[['all','Alla'],['F','Kvinnor'],['M','Män']].map(([value,label])=>`<button type="button" role="radio" aria-checked="${S.segmentSeriesMode===value}" data-segment-series-mode="${value}">${label}</button>`).join('')}</div>`}
function bandChart(host,points,{label='Segmentmedianer och kvartilband',valueLabel=time,dataAttribute='data-extra-segment',legacyDataAttribute='',labelClass='',minValue=0,domainPoints=points,note='',referenceValue=null,referenceLabel='',showStart=false,startValue=null,startExplanation='' }={}){
  const valid=points.filter(p=>num(p.median));if(!valid.length){host.innerHTML=segmentModeControls()+empty('Minst fem exakta observationer krävs för median i vald grupp.');bindModeControls(host);return}
  const W=760,H=270,L=62,R=22,T=28,B=58,domain=(domainPoints||points).flatMap(p=>[p.q25,p.median,p.q75]).filter(num),lo=Math.min(minValue,Number.isFinite(referenceValue)?referenceValue:Infinity,...domain),hi=Math.max(lo+1,Number.isFinite(referenceValue)?referenceValue:-Infinity,...domain),step=(W-L-R)/Math.max(1,points.length+(showStart?1:0)),x=i=>L+(i+(showStart?1.5:.5))*step,startX=L+.5*step,y=v=>H-B-(v-lo)/(hi-lo)*(H-T-B);
  const lineRuns=[],bandRuns=[];let line=[],band=[];const flush=()=>{if(line.length)lineRuns.push(line),line=[];if(band.length)bandRuns.push(band),band=[]};
  points.forEach((p,i)=>{if(!num(p.median)){flush();return}line.push([x(i),y(p.median)]);if(num(p.q25)&&num(p.q75))band.push([x(i),y(p.q25),y(p.q75)]);else{if(band.length)bandRuns.push(band);band=[]}});flush();
  const color=S.segmentSeriesMode==='F'?SEX_COLORS.F:S.segmentSeriesMode==='M'?SEX_COLORS.M:'#3e5d3a';
  const bandColor=S.segmentSeriesMode==='F'?'rgba(214,90,145,.18)':S.segmentSeriesMode==='M'?'rgba(52,121,197,.18)':'rgba(76,114,83,.18)';
  const bands=bandRuns.filter(run=>run.length>1).map(run=>`<path class="distribution-band" style="fill:${bandColor}" d="M${run.map(p=>`${p[0]},${p[2]}`).join('L')}L${run.slice().reverse().map(p=>`${p[0]},${p[1]}`).join('L')}Z"/>`).join('');
  const lines=lineRuns.map(run=>`<path class="distribution-median-line" style="stroke:${color}" d="M${run.map(p=>`${p[0]},${p[1]}`).join('L')}"/>`).join('');
  const marks=points.map((p,i)=>num(p.median)?`<circle ${dataAttribute}="${p.index??i}" ${legacyDataAttribute?`${legacyDataAttribute}="${p.index??i}"`:''} tabindex="0" role="button" aria-pressed="${(p.index??i)===S.selectedSegment}" aria-label="Välj ${html(p.label||p.to?.name||'punkt')}" cx="${x(i)}" cy="${y(p.median)}" r="${(p.index??i)===S.selectedSegment?7:4}" fill="${(p.index??i)===S.selectedSegment?'#d4a858':color}"><title>${html(p.title||p.label||p.to?.name||'Punkt')} · median ${valueLabel(p.median)} · Q25 ${valueLabel(p.q25)} · Q75 ${valueLabel(p.q75)} · n=${p.n}</title></circle><text${labelClass?` class="${labelClass}"`:''} x="${x(i)}" y="${H-18}" text-anchor="middle" transform="rotate(-25 ${x(i)} ${H-18})">${html(String(p.label||p.to?.name||'').slice(0,11))}</text>`:'').join('');
  // Start is a separate origin/reference marker, never a fabricated segment median.
  const origin=showStart&&num(startValue)?
    '<g class="chart-start-origin"><circle class="chart-start-marker" cx="'+startX+'" cy="'+y(startValue)+'" r="5"><title>Start · '+html(startExplanation||valueLabel(startValue))+'</title></circle><text class="chart-start-label" x="'+startX+'" y="'+(H-18)+'" text-anchor="middle" transform="rotate(-25 '+startX+' '+(H-18)+')">Start</text></g>':'';
  // The highlighted 100% tick takes precedence over any nearby generic tick.
  const axisTicks=Number.isFinite(referenceValue)?Array.from({length:5},(_,i)=>{
    const value=lo+(hi-lo)*i/4,yy=y(value);
    if(Math.abs(yy-y(referenceValue))<14)return '';
    return '<line x1="'+L+'" x2="'+(W-R)+'" y1="'+yy+'" y2="'+yy+'" stroke="currentColor" opacity="'+(i===0?.27:.12)+'"/><text x="'+(L-6)+'" y="'+(yy+3)+'" text-anchor="end">'+valueLabel(value)+'</text>';
  }).join(''):chartYTicks(L,W-R,T,H-B,lo,hi,valueLabel);
  const referenceTick=Number.isFinite(referenceValue)?
    '<text class="chart-reference-y-label" x="'+(L-6)+'" y="'+(y(referenceValue)+3)+'" text-anchor="end">'+html(valueLabel(referenceValue))+'</text>':'';
  const reference=Number.isFinite(referenceValue)?`<line class="chart-reference-line" x1="${L}" x2="${W-R}" y1="${y(referenceValue)}" y2="${y(referenceValue)}"/><text class="chart-reference-label" x="${W-R}" y="${y(referenceValue)-5}" text-anchor="end">${html(referenceLabel||valueLabel(referenceValue))}</text>`:'';
  host.innerHTML=segmentModeControls()+svg(W,H,axisTicks+bands+reference+referenceTick+lines+marks+origin,label)+`<p class="small muted">Median kräver n≥5. Bandet visar Q25–Q75 och kräver n≥10; luckor lämnas öppna. ${note}</p>`;
  bindModeControls(host)
}
function bindModeControls(host){$$('[data-segment-series-mode]',host).forEach(button=>button.addEventListener('click',()=>{S.segmentSeriesMode=button.dataset.segmentSeriesMode;renderSegments();window.SatilaExtras?.renderSegments?.()}))}
function renderSegmentGraph(segs){const host=$('#segment-chart'),shown=modeDistributionSegments(segs);bandChart(host,shown,{dataAttribute:'data-segment',domainPoints:segs,note:'Alla tre lägen använder samma diagramtyp och gemensamma min-n-regler.'});$$('[data-segment]',host).forEach(n=>{const go=()=>activateSegment(+n.dataset.segment);n.addEventListener('click',go);n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}})})}
function renderSegmentTable(){let segs=segmentStats(S.filtered);$('#segment-table tbody').innerHTML=segs.map((s,i)=>`<tr data-select-segment="${i}" tabindex="0" class="${i===S.selectedSegment?'selected':''}"><td>${html(s.from.name)} → ${html(s.to.name)}</td><td>${fmtKm(s.km)}</td><td>${s.n}</td><td>${time(s.median)}</td><td>${num(s.q25)?time(s.q25)+' – '+time(s.q75):'n &lt; 10'}</td><td>${paceDistanceSupported(s)?pace(s.median,s.km,S.unit):'Distans ej verifierad'}</td></tr>`).join('');$$('[data-select-segment]',$('#segment-table')).forEach(n=>{let go=()=>activateSegment(+n.dataset.selectSegment);n.addEventListener('click',go);n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}})});}
function selectedRange(){const cp=boundaries(),from=cp[S.podiumStart],to=cp[S.podiumEnd];if(!from||!to||to.km<=from.km)return null;const obs=S.filtered.filter(finish).map(r=>{const a=S.podiumStart===0?{elapsed_seconds:0}:observed(r,from),b=observed(r,to);return a&&b&&num(a.elapsed_seconds)&&num(b.elapsed_seconds)&&b.elapsed_seconds>a.elapsed_seconds?{r,seconds:b.elapsed_seconds-a.elapsed_seconds}:null}).filter(Boolean),adjacent=segmentStats(records()).slice(S.podiumStart,S.podiumEnd),distanceSupported=adjacent.length===S.podiumEnd-S.podiumStart&&adjacent.every(paceDistanceSupported);return {from,to,km:to.km-from.km,obs,distanceSupported}}
function renderSegmentPodium(){let range=selectedRange();$('#segment-podium').innerHTML=range?`<p class="segment-range-summary">${html(range.from.name)} → ${html(range.to.name)} · ${fmtKm(range.km)} timing-km · ${range.obs.length} giltiga tidspar</p><div class="podium-pair">${podiumPair(range.obs.slice().sort((a,b)=>a.seconds-b.seconds).map(o=>({r:o.r,value:range.distanceSupported?pace(o.seconds,range.km,S.unit):time(o.seconds)+' · tid endast'})))}</div>`:empty();bindResultLinks($('#segment-podium'))}
function parseTarget(){let s=$('#target-time').value.trim(),p=s.split(':').map(Number);if(p.some(x=>!Number.isFinite(x)||x<0)||p.length<2||p.length>3||p.slice(1).some(x=>x>59))return null;let n=p.length===2?p[0]*3600+p[1]*60:p[0]*3600+p[1]*60+p[2];return n>0?n:null}
function renderPlan(){
  if(!S.race)return;
  const cohortSelect=$('#plan-cohort');
  if(!cohortSelect.querySelector('[value="class"]'))cohortSelect.add(new Option('Vald klass','class'));
  cohortSelect.querySelector('[value="near"]').textContent='Nära min måltid (±10 %)';
  let classSelect=$('#plan-class');
  if(!classSelect){
    const label=document.createElement('label');
    label.id='plan-class-label';
    label.textContent='Klass för referens';
    classSelect=document.createElement('select');
    classSelect.id='plan-class';
    classSelect.addEventListener('change',renderPlan);
    label.appendChild(classSelect);
    cohortSelect.closest('label').after(label);
  }
  const oldClass=classSelect.value;
  const classes=[...new Set(records().map(r=>r.class_name).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'sv'));
  classSelect.replaceChildren(...classes.map(name=>new Option(name,name)));
  if(classes.includes(oldClass))classSelect.value=oldClass;
  classSelect.closest('label').hidden=cohortSelect.value!=='class';
  const target=parseTarget(),out=$('#plan-table tbody'),summary=$('#plan-summary');
  if(!target){summary.textContent='Ange en giltig måltid som HH:MM eller HH:MM:SS.';out.innerHTML='';return}
  const cohort=cohortSelect.value;
  let rows=records().filter(finish);
  if(cohort==='F'||cohort==='M')rows=rows.filter(r=>analyticalSex(r)===cohort);
  if(cohort==='class')rows=rows.filter(r=>r.class_name===classSelect.value);
  if(cohort==='near')rows=rows.filter(r=>Math.abs(r.finish_seconds-target)<=target*.10);
  if(rows.length<5){
    out.innerHTML='';
    summary.textContent=`Den valda referenskohorten har ${rows.length} fullföljare. Minst fem behövs; välj en bredare grupp eller annan måltid.`;
    return;
  }
  const allSegments=segmentStats(rows);
  const distanceTotal=allSegments.reduce((sum,s)=>sum+(num(s.km)&&s.km>0?s.km:0),0);
  const parts=allSegments.map(s=>{
    const ratios=s.obs.map(o=>o.seconds/o.r.finish_seconds).filter(x=>num(x)&&x>0);
    const n=ratios.length;
    const observedWeight=n>=5?median(ratios):null;
    const fallbackWeight=paceDistanceSupported(s)&&distanceTotal>0&&num(s.km)&&s.km>0?s.km/distanceTotal:null;
    return {...s,n,w:observedWeight??fallbackWeight,method:observedWeight!==null?'Historisk median':fallbackWeight!==null?'Distansfallback':'Saknas'};
  });
  const sum=parts.reduce((value,p)=>value+(p.w||0),0);
  if(!sum||parts.some(p=>p.w===null)){
    out.innerHTML='';
    summary.textContent='Loppplanen är ofullständig: en eller flera delsträckor saknar både historisk andel och kontrakterad distans.';
    return;
  }
  let elapsed=0;
  out.innerHTML=parts.map(p=>{
    const allocation=target*p.w/sum;
    elapsed+=allocation;
    return `<tr><td><button type="button" data-plan-segment="${p.index}" aria-label="Visa ${html(p.from.name)} till ${html(p.to.name)} på banan">${html(p.from.name)} → ${html(p.to.name)} ↗</button></td><td>${fmtKm(p.km)}</td><td>${p.n}</td><td>${html(p.method)}</td><td><strong>${time(allocation)}</strong></td><td>${time(elapsed)}</td><td>${paceDistanceSupported(p)?pace(allocation,p.km,S.unit):'Distans ej verifierad'}</td><td title="Ingen verifierad fysisk kontrollankring längs GPX">Ej verifierat</td><td>EQ Timing TIME-par · n=${p.n} · ${p.method==='Historisk median'?'observerad tidsandel':'öppet märkt timing-km-fallback'}</td></tr>`;
  }).join('');
  $$('[data-plan-segment]',out).forEach(button=>button.addEventListener('click',()=>{
    const i=+button.dataset.planSegment;
    $('#segment-table [data-select-segment="'+i+'"]')?.click();
    const segment=allSegments.find(s=>s.index===i);
    const points=routePoints();
    if(segment&&points.length){
      S.courseD=timingToRouteKm((segment.from.km+segment.to.km)/2,points);
      renderCourseMap();
      $('#course-map').scrollIntoView({block:'center',behavior:'smooth'});
    }
  }));
  const sampled=parts.filter(p=>p.method==='Historisk median').length;
  const cohortText=cohort==='near'?' inom ±10 % av måltiden':cohort==='class'?` i klassen ${classSelect.value}`:cohort==='all'?' i hela fältet':` med källkön ${cohort}`;
  const highest=parts.slice().sort((a,b)=>b.w-a.w)[0];
  const defaultSeconds=Number($('#target-time').dataset.defaultSeconds),usesEditionMedian=num(defaultSeconds)&&Math.abs(target-defaultSeconds)<1;summary.textContent=`${usesEditionMedian?'Grundvärde: upplagans mediantid · ':''}${time(target)} · ${rows.length} fullföljare${cohortText} · ${sampled}/${parts.length} segment med minst fem verkliga tidsandelar. Övriga använder öppet märkt timingdistansfallback. Störst historisk tidsandel: ${highest?highest.from.name+' → '+highest.to.name:'—'}. Planen är en pacingreferens, inte en prognos.`;
}

function focusSelectedSegmentOnCourse(){
 const seg=currentSeg(),points=routePoints(),nominal=S.race?.nominal_km,total=points.at(-1)?.[0];
 if(!seg||!num(nominal)||nominal<=0||!num(total)||total<=0)return;
 // This is an explicitly ILLUSTRATIVE proportional timing-km projection,
 // never a claimed GPS coordinate for an observed timing station.
 S.courseD=timingToRouteKm((seg.from.km+seg.to.km)/2,points);
 S.courseFromSegment=true;
}
function renderCourse(){renderCourseMap();renderPlan()}
function routePoints(){return S.route?.points||[]}
function timingToRouteKm(timingKm,points=routePoints()){const total=points.at(-1)?.[0],timingTotal=S.race?.nominal_km;if(!num(total)||!num(timingTotal)||timingTotal<=0)return 0;return Math.max(0,Math.min(total,Number(timingKm)/timingTotal*total))}
function elevationSegmentRanges(points=routePoints()){const bs=boundaries();return bs.slice(1).map((to,index)=>{const from=bs[index],start=timingToRouteKm(from.km,points),end=timingToRouteKm(to.km,points);return {index,from,to,start,end,label:`${from.name} → ${to.name}`}}).filter(s=>s.end>s.start)}
function mapProjection(points,W,H,pad=17){
 const radians=value=>Number(value)*Math.PI/180,merc=lat=>Math.log(Math.tan(Math.PI/4+radians(Math.max(-85,Math.min(85,lat)))/2)),xs=points.map(p=>radians(p[2])),ys=points.map(p=>merc(p[1])),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys),scale=Math.min((W-pad*2)/Math.max(1e-9,xmax-xmin),(H-pad*2)/Math.max(1e-9,ymax-ymin)),ox=(W-(xmax-xmin)*scale)/2,oy=(H-(ymax-ymin)*scale)/2;
 const projectCoord=(lat,lon)=>[ox+(radians(lon)-xmin)*scale,H-(oy+(merc(lat)-ymin)*scale)];
 const inverseCoord=(x,y)=>{const m=ymin+(H-y-oy)/scale;return [(2*Math.atan(Math.exp(m))-Math.PI/2)*180/Math.PI,(xmin+(x-ox)/scale)*180/Math.PI]};
 return {project:point=>projectCoord(point[1],point[2]),projectCoord,inverseCoord}
}
function mapViewport(host,H){
 // Match the geographic SVG viewBox to the actual visible map panel ratio.
 // Unlike scaling the SVG arbitrarily, this preserves correct GPX geography.
 const bounds=host.getBoundingClientRect(),w=bounds.width||host.clientWidth||760,h=bounds.height||host.clientHeight||H;
 return {W:Math.max(160,Math.round(H*w/Math.max(1,h))),H};
}
function project(points,W,H,pad=17){const projection=mapProjection(points,W,H,pad);return points.map(projection.project)}
function osmTiles(points,W,H,pad=17){
 if(!points.length)return'';
 const projection=mapProjection(points,W,H,pad);
 // Cover the ENTIRE SVG viewBox, including map letterboxing around long, thin
 // trails: route-bounds-only tiles left 125–210 px grey side strips at 800 px.
 const [north,west]=projection.inverseCoord(0,0),[south,east]=projection.inverseCoord(W,H);
 const tileRange=zoom=>{
  const n=2**zoom,lonToX=lon=>(Number(lon)+180)/360*n,latToY=lat=>{const r=Number(lat)*Math.PI/180;return (1-Math.asinh(Math.tan(r))/Math.PI)/2*n};
  const minX=Math.max(0,Math.min(n-1,Math.floor(lonToX(west)))),maxX=Math.max(0,Math.min(n-1,Math.floor(lonToX(east)))),minY=Math.max(0,Math.min(n-1,Math.floor(latToY(north)))),maxY=Math.max(0,Math.min(n-1,Math.floor(latToY(south))));
  return {zoom,n,minX,maxX,minY,maxY,columns:maxX-minX+1,rows:maxY-minY+1}
 };
 // Adapt zoom to the visible geographic extent: avoid 55 tile requests for
 // one ultra map, but do not stretch a single low-resolution tile over 5 km.
 let tiles;
 for(let zoom=15;zoom>=8;zoom--){
  const candidate=tileRange(zoom);
  if(candidate.columns<=7&&candidate.rows<=6&&candidate.columns*candidate.rows<=24){tiles=candidate;break}
 }
 tiles=tiles||tileRange(8);
 const {zoom,n,minX,maxX,minY,maxY}=tiles,tileLon=x=>x/n*360-180,tileLat=y=>Math.atan(Math.sinh(Math.PI*(1-2*y/n)))*180/Math.PI;
 let images='';
 for(let y=minY;y<=maxY;y++)for(let x=minX;x<=maxX;x++){
  const [left,top]=projection.projectCoord(tileLat(y),tileLon(x)),[right,bottom]=projection.projectCoord(tileLat(y+1),tileLon(x+1));
  images+=`<image href="https://tile.openstreetmap.org/${zoom}/${x}/${y}.png" x="${left.toFixed(2)}" y="${top.toFixed(2)}" width="${(right-left).toFixed(2)}" height="${(bottom-top).toFixed(2)}" preserveAspectRatio="none"/>`
 }
 return `<rect class="osm-map-fallback" width="${W}" height="${H}"/><g class="osm-tile-layer" data-zoom="${zoom}" aria-hidden="true">${images}</g>`
}
const osmAttribution=()=>'<a class="osm-attribution" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">© OpenStreetMap contributors</a>';
function pointAtDistance(pts,d){if(!pts.length)return null;d=Math.max(pts[0][0],Math.min(pts.at(-1)[0],d));let i=1;while(i<pts.length-1&&pts[i][0]<d)i++;let a=pts[i-1],b=pts[i],f=(d-a[0])/Math.max(.00001,b[0]-a[0]);return [d,a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f,num(a[3])&&num(b[3])?a[3]+(b[3]-a[3])*f:null]}
function nearestSegmentPath(path,p){let best={index:0,fraction:0,dist:Infinity};for(let i=1;i<path.length;i++){let [ax,ay]=path[i-1],[bx,by]=path[i],vx=bx-ax,vy=by-ay,len=vx*vx+vy*vy,f=len?Math.max(0,Math.min(1,((p[0]-ax)*vx+(p[1]-ay)*vy)/len)):0,d=(p[0]-ax-vx*f)**2+(p[1]-ay-vy*f)**2;if(d<best.dist)best={index:i,fraction:f,dist:d}}return best}
function pathFor(path){return path.map((p,i)=>(i?'L':'M')+p[0].toFixed(2)+' '+p[1].toFixed(2)).join(' ')}
function elevationSvg(pts,d,interactive=true){const isDsm=S.route?.elevation_provenance?.type==='DSM_RECONSTRUCTED_SURFACE',isTransferred=S.route?.elevation_provenance?.type==='SPATIALLY_TRANSFERRED_PARTICIPANT_GPX';if(!pts.length)return empty();if(!pts.some(p=>Number.isFinite(p[3])))return '<p class="muted small">Höjddata saknas i detta historiska deltagarspår. Kartan och distanspositioneringen fungerar ändå.</p>';let W=780,H=135,P=17,min=Math.min(...pts.map(p=>num(p[3])?p[3]:0)),max=Math.max(...pts.map(p=>num(p[3])?p[3]:0)),md=pts.at(-1)[0],x=p=>P+p[0]/md*(W-2*P),y=p=>H-P-(num(p[3])?(p[3]-min)/Math.max(1,max-min)*(H-2*P):0),line=pts.map((p,i)=>(i?'L':'M')+x(p).toFixed(1)+' '+y(p).toFixed(1)).join(' '),dot=pointAtDistance(pts,d??0),xx=dot?x(dot):P,yy=dot?y(dot):H-P,ranges=elevationSegmentRanges(pts);const bands=interactive?ranges.map(s=>{const left=x([s.start]),right=x([s.end]),mid=(left+right)/2;return `<rect data-elev-segment="${s.index}" class="elevation-segment ${s.index===S.selectedSegment?'selected':''}" x="${left}" y="18" width="${Math.max(1,right-left)}" height="${H-18}" tabindex="0" role="button" aria-pressed="${s.index===S.selectedSegment}" aria-label="Välj timingsegment ${html(s.label)} på höjdprofilen" style="pointer-events:none"><title>${html(s.label)} · proportionellt projicerat från EQ Timing-axeln till visningsrutt</title></rect>${right-left>46?`<text class="elevation-segment-label" x="${mid}" y="${H-4}" text-anchor="middle">${html(s.to.name.slice(0,10))}</text>`:''}`}).join(''):'';return svg(W,H,`<path class="elev-area" d="${line}L${x(pts.at(-1))} ${H-P}L${P} ${H-P}Z" opacity=".18"/><g class="elev-line" aria-label="Färgkodade höjdsegment">${pts.slice(1).map((p,i)=>{const prev=pts[i],delta=num(p[3])&&num(prev[3])?p[3]-prev[3]:0;return `<line x1="${x(prev)}" y1="${y(prev)}" x2="${x(p)}" y2="${y(p)}" stroke="${delta>0.5?'#c08737':delta<-.5?'#337f63':'#8b968a'}" stroke-width="2.4"><title>${delta>0.5?'Uppför':delta<-.5?'Nedför':'Flackt'} · ${fmtKm(p[0])} km</title></line>`}).join('')}</g>${bands}${interactive?`<rect data-elev-hit="1" x="${P}" y="0" width="${W-2*P}" height="${H}" fill="transparent" role="slider" tabindex="0" aria-valuemin="0" aria-valuemax="${md}" aria-valuenow="${d??0}" aria-label="Välj position längs höjdprofilen"/>`:''}<line class="chart-cursor" x1="${xx}" x2="${xx}" y1="${P}" y2="${H-P}"/><circle class="elev-dot" cx="${xx}" cy="${yy}" r="5"/><text x="${P}" y="12" fill="#526855" font-size="10">${Math.round(min)}–${Math.round(max)} m · ${isDsm?'Copernicus DSM · rekonstruerad ythöjd':S.route?.elevation_provenance?.type==='DEM_RECONSTRUCTED_TERRAIN'?'Rekonstruerad DEM-terränghöjd':isTransferred?'Överförd GPX-höjd (2024)':'GPX-höjd'}</text><text x="${W-P-80}" y="12" fill="#526855" font-size="10">${fmtKm(md)} km</text>`,'Interaktiv höjdprofil')+(isDsm?'<p class="muted small elevation-source-note">Rekonstruerad ythöjd från Copernicus GLO-30 (digital ytmodell, cirka 30 m, EGM2008; skog och byggnader kan påverka). Inte uppmätt löparhöjd eller officiella höjdmeter.</p>':isTransferred?'<p class="muted small elevation-source-note">Illustrativ höjdprofil överförd geografiskt från 2024 års deltagar-GPX. Inte originalhöjd från 2023 och inte officiella höjdmeter.</p>':'')}
// Copernicus WorldDEM-30 attribution is retained in elevationSvg for reconstructed profiles.
function activateSegment(index){selectAdjacentSegment(index);focusSelectedSegmentOnCourse();renderSegmentTable();renderSegmentPodium();renderSegmentGraph(segmentStats(S.filtered));renderCourse();window.SatilaExtras?.renderSegments?.()}
function attachElevation(host,pts,callback){if(S.route?.elevation_provenance?.type==='DSM_RECONSTRUCTED_SURFACE'&&!$('.worlddem-attribution',host))host.insertAdjacentHTML('beforeend','<p class="muted small elevation-source-note worlddem-attribution">Copernicus WorldDEM-30 · rekonstruerad ythöjd; inte uppmätt löparhöjd eller officiella höjdmeter.</p>');let el=$('[data-elev-hit]',host);if(!el)return;const svg=el.ownerSVGElement,md=pts.at(-1)[0];function kmAt(e){const box=svg.getBoundingClientRect(),view=svg.viewBox.baseVal,width=view?.width||780,height=view?.height||135,left=view?.x||0,scale=Math.min(box.width/width,box.height/height),insetX=(box.width-width*scale)/2,x=left+(e.clientX-box.left-insetX)/Math.max(.0001,scale),hitLeft=Number(el.getAttribute('x'))||17,hitWidth=Number(el.getAttribute('width'))||(width-34);return Math.max(0,Math.min(md,(x-hitLeft)/hitWidth*md))}function seek(e){callback(kmAt(e))}el.addEventListener('pointerdown',e=>{el.setPointerCapture(e.pointerId);seek(e)});svg.addEventListener('pointermove',seek);el.addEventListener('click',e=>{if(!e.detail)return;const hit=elevationSegmentRanges(pts).find(s=>kmAt(e)>=s.start&&kmAt(e)<=s.end);if(hit)activateSegment(hit.index)});el.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();let d=Number(el.getAttribute('aria-valuenow'))||0,d2=e.key==='Home'?0:e.key==='End'?md:d+(e.key==='ArrowLeft'?-md/100:md/100);callback(Math.max(0,Math.min(md,d2)))}});$$('[data-elev-segment]',host).forEach(node=>{const go=e=>{e.preventDefault();e.stopPropagation();activateSegment(+node.dataset.elevSegment)};node.addEventListener('pointerdown',go);node.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){go(e)}})})}
function renderCourseMap(){let host=$('#course-map'),height=$('#course-elevation'),pts=routePoints();if(!pts.length){host.innerHTML=empty('Ingen godkänd lokal ruttskiss är registrerad för den historiska upplagan. Resultatanalysen är ändå komplett.');height.innerHTML='';$('#course-scrub-label').textContent='Ingen rutt kopplad till denna upplaga.';return}let {W,H}=mapViewport(host,340),path=project(pts,W,H,20),d=Number.isFinite(S.courseD)?S.courseD:0,mark=pointAtDistance(pts,d),midx=project(mark?[mark]:[pts[0]],W,H,20)[0]; // mark projected on same immutable bounds below
let idx=1;while(idx<pts.length-1&&pts[idx][0]<d)idx++;let a=pts[idx-1],b=pts[idx],f=(d-a[0])/Math.max(1e-7,b[0]-a[0]),px=path[idx-1][0]+(path[idx][0]-path[idx-1][0])*f,py=path[idx-1][1]+(path[idx][1]-path[idx-1][1])*f;
host.innerHTML=svg(W,H,`${osmTiles(pts,W,H,20)}<path class="route-base" d="${pathFor(path)}"/><path class="route-gold" d="${pathFor(path)}"/><circle class="map-crosshair" cx="${px}" cy="${py}" r="7"/><text class="map-label" x="25" y="27">SÄTILA · ${S.route?.normalized_source_group?'NORMALISERAD DELTAGARBANA':S.route?.type==='VERIFIED_PARTICIPANT'?'DELTAGARSPÅR':'ARRANGÖRSRUTT'}</text><text class="map-label" x="25" y="${H-18}">${fmtKm(d)} / ${fmtKm(pts.at(-1)[0])} km</text><rect data-map-hit="course" x="0" y="0" width="${W}" height="${H}" fill="transparent" role="slider" tabindex="0" aria-label="Välj position på banan" aria-valuemin="0" aria-valuemax="${pts.at(-1)[0]}" aria-valuenow="${d}"/>`,'Interaktiv OpenStreetMap-bakgrund med faktisk GPX-form')+osmAttribution();height.innerHTML=elevationSvg(pts,d);let seek=n=>{
  // Keep the current SVG and its captured pointer in place while scrubbing.
  // Rebuilding either SVG during pointerdown detaches the hit target and makes
  // a later mouse click or keyboard activation intermittently fail.
  const maxKm=pts.at(-1)[0];S.courseD=Math.max(0,Math.min(maxKm,Number.isFinite(n)?n:0));S.courseFromSegment=false;
  let k=1;while(k<pts.length-1&&pts[k][0]<S.courseD)k++;
  const p0=pts[k-1],p1=pts[k],fraction=(S.courseD-p0[0])/Math.max(1e-7,p1[0]-p0[0]);
  const cx=path[k-1][0]+(path[k][0]-path[k-1][0])*fraction,cy=path[k-1][1]+(path[k][1]-path[k-1][1])*fraction;
  const mapCursor=host.querySelector('.map-crosshair');
  if(mapCursor){mapCursor.setAttribute('cx',cx);mapCursor.setAttribute('cy',cy)}
  const mapLabels=host.querySelectorAll('.map-label');
  if(mapLabels.length>1)mapLabels[1].textContent=fmtKm(S.courseD)+' / '+fmtKm(maxKm)+' km';
  host.querySelector('[data-map-hit]')?.setAttribute('aria-valuenow',S.courseD);
  const elev=height.querySelector('[data-elev-hit]');
  if(elev){
    const heights=pts.map(p=>num(p[3])?p[3]:0),lo=Math.min(...heights),hi=Math.max(...heights);
    const dot=pointAtDistance(pts,S.courseD),P=17,W=780,H=135;
    const ex=P+S.courseD/maxKm*(W-2*P),ey=H-P-((num(dot?.[3])?dot[3]:0)-lo)/Math.max(1,hi-lo)*(H-2*P);
    const cursor=height.querySelector('.chart-cursor'),point=height.querySelector('.elev-dot');
    if(cursor){cursor.setAttribute('x1',ex);cursor.setAttribute('x2',ex)}
    if(point){point.setAttribute('cx',ex);point.setAttribute('cy',ey)}
    elev.setAttribute('aria-valuenow',S.courseD);
  }
  $('#course-scrub-label').textContent='Illustrativ position '+fmtKm(S.courseD)+' km längs GPX-displayrutt. Klicka i karta eller höjdprofil.';
};let hit=$('[data-map-hit]',host);function locate(e){let rect=hit.ownerSVGElement.getBoundingClientRect(),xx=(e.clientX-rect.left)/rect.width*W,yy=(e.clientY-rect.top)/rect.height*H,spot=nearestSegmentPath(path,[xx,yy]),i=spot.index;seek(pts[i-1][0]+(pts[i][0]-pts[i-1][0])*spot.fraction)}hit.addEventListener('pointerdown',e=>{hit.setPointerCapture(e.pointerId);locate(e)});hit.addEventListener('pointermove',e=>{if(e.buttons)locate(e)});hit.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();seek(Math.max(0,Math.min(pts.at(-1)[0],(S.courseD??0)+(e.key==='ArrowRight'?1:-1)*pts.at(-1)[0]/80)))}});attachElevation(height,pts,seek);$('#course-scrub-label').textContent=`Illustrativ position ${fmtKm(d)} km längs GPX-displayrutt.${S.courseFromSegment?' Segmentmitt proportionellt uppskattad från timing-km; ej verifierad kontrollposition.':''} Klicka i karta eller höjdprofil.`;}
function renderHistory(){
  const editions=S.boot.editions.filter(e=>e.family===S.family).sort((a,b)=>a.year-b.year);
  const first=editions[0]?.year||2016,last=editions.at(-1)?.year||2025;
  const W=700,H=250,P=42,step=(W-2*P)/(last-first+1),peak=Math.max(1,...editions.map(e=>e.results));
  const body=`<line class="axis" x1="${P}" x2="${W-P}" y1="210" y2="210"/>`+editions.map(e=>{
    const x=P+(e.year-first)*step+4,bar=e.results/peak*160,finished=e.finishers/peak*160,dnf=e.dnf/peak*160,width=Math.max(5,step-12);
    return `<rect x="${x}" y="${210-bar}" width="${width}" height="${bar}" fill="#c5d6c6"><title>${e.year} · ${e.results} publicerade resultat</title></rect><rect x="${x}" y="${210-finished}" width="${width*.7}" height="${finished}" fill="#426d4b"><title>${e.year} · ${e.finishers} fullföljare</title></rect><rect x="${x+width*.72}" y="${210-dnf}" width="${width*.28}" height="${dnf}" fill="#b88c4e"><title>${e.year} · ${e.dnf} DNF</title></rect><text x="${x}" y="227">${e.year}</text>`;
  }).join('');
  $('#history-chart').innerHTML=svg(W,H,body,'Källstödda resultat, fullföljare och DNF per år; luckan 2020 är inget nollår')+`<div class="map-legend"><span><i style="background:#c5d6c6"></i>Resultat</span><span><i style="background:#426d4b"></i>Fullföljare</span><span><i style="background:#b88c4e"></i>DNF</span></div><p class="muted small">2020 saknar verifierad upplaga i källarkivet och visas därför som en lucka, inte noll deltagare.</p>`;
  $('#history-course-notes').innerHTML=S.family==='trail43'?`<p><strong>2021–2022:</strong> deltagarspår ger en sammanhängande preliminär kursfamilj. <strong>2023–2025:</strong> en andra korridor med stor förändring mot 2022. Arrangörens GPX med intern 2025-titel används som arbetsreferens för 2025/2026.</p><p class="muted small">Fleråriga helbanetider binds inte ihop som prestationsserie innan jämförbarheten har godkänts.</p>`:S.family==='trail22'?`<p><strong>2025–2026:</strong> gemensam arrangörsgeometri enligt projektägarens återanvändningsbeslut. Äldre banor kräver egen evidens.</p>`:`<p><strong>2026:</strong> egen officiell GPX om cirka 87,9 km. 2021–2025 hanteras som separata historiska upplagor tills jämförbarhet har verifierats.</p>`;
  $('#history-table tbody').innerHTML=editions.slice().reverse().map(e=>{
    const knownStarters=e.results-e.dns-e.unknown;
    return `<tr><td><button data-edition="${e.year}" type="button">${e.year} ↗</button></td><td>${html(e.date)}</td><td>${html(e.label)}</td><td>${html(editionDistanceLabel(e))}</td><td>${format(e.results)}</td><td>${format(knownStarters)}</td><td>${format(e.finishers)}</td><td>${format(e.dnf)}</td><td>${format(e.dns)}</td><td>${format(e.dsq)}</td><td>${format(e.unknown)}</td><td>${time(e.median_seconds)}</td><td>${html(e.whole_course_comparison_group||'Ej verifierad')}</td><td>${html(e.route_status||'none')}</td><td><a href="${html(e.source_url)}" target="_blank" rel="noopener">EQ Timing ↗</a></td></tr>`;
  }).join('');
  $$('[data-edition]',$('#history-table')).forEach(button=>button.addEventListener('click',()=>{S.year=+button.dataset.edition;loadRace().then(()=>$('#race-context').scrollIntoView())}));
}

function resultRows(){
  const q=S.q.toLocaleLowerCase('sv');
  const list=S.filtered.filter(r=>!q||[r.name,r.bib,r.club,r.class_name,r.status].some(v=>String(v||'').toLocaleLowerCase('sv').includes(q)));
  // Missing values remain last in both directions. Stable source/placing ties
  // make pagination deterministic; edition year and race family are constant here.
  const cmpText=(x,y)=>{const a=String(x??'').trim(),b=String(y??'').trim();if(!a||!b)return a? -1:b?1:0;return a.localeCompare(b,'sv',{numeric:true,sensitivity:'base'})};
  const cmpNum=(a,b,sign=1)=>num(a)&&num(b)?sign*(a-b):num(a)?-1:num(b)?1:0;
  const sourceTie=(a,b)=>cmpNum(a.place,b.place)||cmpText(a.bib,b.bib)||cmpText(a.name,b.name)||cmpText(a.id,b.id);
  const statusOrder={FINISHED:0,DNF:1,DNS:2,DSQ:3,UNKNOWN:4};
  list.sort((a,b)=>{
    let cmp=0;
    switch(S.sort){
      case 'place_desc':cmp=cmpNum(a.place,b.place,-1);break;
      case 'name':cmp=cmpText(a.name,b.name);break;
      case 'name_desc':cmp=-cmpText(a.name,b.name);break;
      case 'time':cmp=cmpNum(a.finish_seconds,b.finish_seconds);break;
      case 'time_desc':cmp=cmpNum(a.finish_seconds,b.finish_seconds,-1);break;
      case 'bib':cmp=cmpText(a.bib,b.bib);break;
      case 'sex':cmp=cmpText(analyticalSex(a),analyticalSex(b));break;
      case 'class':cmp=cmpText(a.class_name,b.class_name);break;
      case 'club':cmp=cmpText(a.club,b.club);break;
      case 'status':cmp=(statusOrder[a.status]??9)-(statusOrder[b.status]??9);break;
      default:cmp=cmpNum(a.place,b.place);
    }
    return cmp||sourceTie(a,b);
  });
  return list;
}
function renderResults(){let list=resultRows(),per=35,pages=Math.max(1,Math.ceil(list.length/per));S.page=Math.min(S.page,pages-1);$('#results-count').textContent=`${format(list.length)} träffar`;
$('#results-table tbody').innerHTML=list.slice(S.page*per,(S.page+1)*per).map(r=>`<tr><td>${S.year}</td><td>${html(S.race.label)} · ${html(editionDistanceLabel(S.race))}</td><td>${r.place??'—'}</td><td>${html(r.bib)}</td><td><strong>${html(r.name)}</strong></td><td>${html(sexLabel(r))}</td><td>${html(r.class_name)}</td><td>${html(r.club)}</td><td>${html(r.status)}</td><td>${time(r.finish_seconds)}</td><td><button type="button" data-open="${html(r.id)}" aria-label="Öppna profilen för ${html(r.name)}">Öppna ↗</button></td></tr>`).join('');$('#page-number').textContent=`Sida ${S.page+1} / ${pages}`;$('#page-prev').disabled=S.page<=0;$('#page-next').disabled=S.page>=pages-1;bindResultLinks($('#results-table'));}
function findRecord(id){return records().find(r=>r.id===id)}
function searchMatches(q){q=String(q||'').trim().toLocaleLowerCase('sv');return q.length<2?[]:records().filter(r=>r.name.toLocaleLowerCase('sv').includes(q)||r.bib===q).slice(0,9)}
function renderSearchSuggestions(){let q=$('#runner-search').value,m=searchMatches(q);S.searchIndex=-1;const host=$('#runner-suggestions');host.innerHTML=m.map(r=>`<button type="button" class="suggestion" data-id="${html(r.id)}" role="option"><span class="avatar">${html(initial(r.name))}</span><strong>${html(r.name)}</strong><small>#${html(r.bib)} · ${time(r.finish_seconds)}</small></button>`).join('');$$('.suggestion',host).forEach(b=>b.addEventListener('click',()=>{openProfile(b.dataset.id);host.innerHTML=''}));}
function renderMapDuelSuggestions(){const input=$('#map-duel-search'),host=$('#map-duel-suggestions');if(!input||!host)return;const matches=searchMatches(input.value).filter(r=>!S.mapDuel.includes(r.id));S.mapDuelSearchIndex=-1;host.innerHTML=matches.map(r=>`<button type="button" class="suggestion" data-map-duel-id="${html(r.id)}" role="option" ${S.mapDuel.length>=5?'disabled':''}><span class="avatar">${html(initial(r.name))}</span><strong>${html(r.name)}</strong><small>#${html(r.bib)} · ${html(r.class_name||'Klass saknas')} · ${time(r.finish_seconds)}</small></button>`).join('');$$('[data-map-duel-id]',host).forEach(button=>button.addEventListener('click',()=>addMapDuel(button.dataset.mapDuelId)))}
function renderFavorites(){let ids=new Set(records().map(r=>r.id));let stored=S.favorites.filter(id=>ids.has(id));$('#favorites').innerHTML=stored.length?'<p class="muted small" style="width:100%;margin:6px 0">Sparade resultat i denna upplaga</p>'+stored.map(id=>`<button data-favorite="${html(id)}" type="button">★ ${html(findRecord(id)?.name||id)}</button>`).join(''):'';$$('[data-favorite]').forEach(b=>b.addEventListener('click',()=>openProfile(b.dataset.favorite)));}
function toggleFav(id){if(S.favorites.includes(id))S.favorites=S.favorites.filter(k=>k!==id);else S.favorites=[id,...S.favorites].slice(0,40);try{localStorage.setItem(key,JSON.stringify(S.favorites))}catch{}renderFavorites();renderProfileIfOpen();}
function addCompare(id){addMapDuel(id)}
function renderCompareChips(){const host=$('#compare-chips');if(host)host.innerHTML=''}
function bindResultLinks(host=document){$$('[data-open]',host).forEach(el=>{const go=()=>openProfile(el.dataset.open);el.addEventListener('click',go);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}})});}
function profileInsights(r){
  const parts=pairs(r).filter(p=>p.km>0),physicalParts=parts.filter(p=>paceDistanceSupported(p)),out=[];
  if(!parts.length)return out;
  if(physicalParts.length){
  const fastest=physicalParts.reduce((a,b)=>a.seconds/a.km<b.seconds/b.km?a:b);
  const slowest=physicalParts.reduce((a,b)=>a.seconds/a.km>b.seconds/b.km?a:b);
  out.push({label:'Snabbast delsträcka',value:`${fastest.from.name} → ${fastest.to.name}`,detail:pace(fastest.seconds,fastest.km,S.unit),method:'Två exakta passager; tempot kräver godkänd timingdistans.'});
  out.push({label:'Långsammast delsträcka',value:`${slowest.from.name} → ${slowest.to.name}`,detail:pace(slowest.seconds,slowest.km,S.unit),method:'Två exakta passager; tempot kräver godkänd timingdistans.'});
  }
  const ranked=parts.filter(p=>num(p.placeFrom)&&num(p.placeTo)).map(p=>({...p,delta:p.placeFrom-p.placeTo}));
  if(ranked.length){
    const up=ranked.reduce((a,b)=>a.delta>b.delta?a:b),down=ranked.reduce((a,b)=>a.delta<b.delta?a:b);
    out.push({label:'Största avancemang',value:`${up.delta>=0?'+':''}${up.delta} placeringar`,detail:`${up.from.name} → ${up.to.name}`,method:'Publicerad plats vid startkontroll minus plats vid slutkontroll.'});
    out.push({label:'Största placeringstapp',value:`${down.delta} placeringar`,detail:`${down.from.name} → ${down.to.name}`,method:'Publicerad plats vid startkontroll minus plats vid slutkontroll.'});
  }
  const last=parts.at(-1);
  out.push({label:'Sista verifierade segmentet',value:paceDistanceSupported(last)?pace(last.seconds,last.km,S.unit):time(last.seconds)+' · distans ej verifierad',detail:`${last.from.name} → ${last.to.name}`,method:'Verklig tid från två exakta passager; farten visas bara med rimligt säker timingdistans.'});
  const field=segmentStats(records());
  const relative=parts.map(p=>{const stat=field.find(s=>s.index===p.index);return stat&&num(stat.median)?{p,delta:p.seconds-stat.median,n:stat.n}:null}).filter(Boolean);
  if(relative.length){
    const best=relative.reduce((a,b)=>a.delta<b.delta?a:b),worst=relative.reduce((a,b)=>a.delta>b.delta?a:b);
    out.push({label:'Starkast relativt fältmedian',value:signed(best.delta),detail:best.p.to.name,method:`Egen segmenttid minus median för fullföljare med exakt segmentpar; n=${best.n}.`});
    out.push({label:'Största relativt tapp',value:signed(worst.delta),detail:worst.p.to.name,method:`Egen segmenttid minus median för fullföljare med exakt segmentpar; n=${worst.n}.`});
  }
  const speeds=physicalParts.map(p=>p.seconds/p.km);
  if(speeds.length>=3){
    const mean=speeds.reduce((a,b)=>a+b,0)/speeds.length;
    const cv=Math.sqrt(speeds.reduce((a,b)=>a+(b-mean)**2,0)/speeds.length)/mean;
    out.push({label:'Variation i observerat tempo',value:`${(cv*100).toFixed(1).replace('.',',')} %`,detail:`${speeds.length} segment`,method:'Standardavvikelse / medeltempo på egna exakta segmentpar.'});
  }
  return out.slice(0,8);
}

let openId=null;
function openProfile(id){let r=findRecord(id);if(!r)return;S.profileReturnFocus=document.activeElement;openId=id;$('#profile-title').textContent=r.name;renderProfile(r);let d=$('#profile-dialog');if(!d.open)d.showModal();requestAnimationFrame(()=>{$('#profile-replay-range')?.dispatchEvent(new Event('input'))});}
function renderProfileIfOpen(){if(openId&&$('#profile-dialog').open){let r=findRecord(openId);if(r)renderProfile(r)}}
function renderProfile(r){
  if(window.SatilaProfile?.render){
    return window.SatilaProfile.render(r,{S,html,num,time,pace,signed,fmtKm,sexLabel,analyticalSex,records,finish,observed,splitsFor,pairs,segmentStats,paceDistanceSupported,boundaries,wholeCoursePaceKm,eqTimingKm,toggleFav,addCompare,renderReplay:renderProfileReplay,routePoints,svg,profileInsights});
  }
  return renderProfileLegacy(r);
}
function renderProfileLegacy(r){
  const segments=pairs(r),passages=splitsFor(r.id),insights=profileInsights(r);
  const head=`<div class="profile-head"><div class="avatar" aria-hidden="true">${html(initial(r.name))}</div><div><h3>${html(r.name)}</h3><p class="muted small">#${html(r.bib)} · ${html(r.class_name||'')} · ${html(r.club||'Okänd klubb/ort')} · ${html(r.status)} · ${html(sexLabel(r))}</p></div><button class="btn green" type="button" id="profile-add-compare">${S.mapDuel.includes(r.id)?'Ta bort från jämförelse':'Jämför detta resultat →'}</button></div>`;
  const paceKm=wholeCoursePaceKm(S.race);
  const kpis=[['Sluttid',time(r.finish_seconds)],['Totalplacering',r.place??'—'],['Snittfart',num(paceKm)?pace(r.finish_seconds,paceKm,S.unit):'Distanskonflikt'],['Registrerade passager',passages.length]]
    .map(([label,value])=>`<article><small>${html(label)}</small><strong>${html(value)}</strong></article>`).join('');
  const distanceNote=num(paceKm)?'':`<p class="muted small">Helbanetempo visas inte: EQ Timing anger ${fmtKm(eqTimingKm(S.race))} km medan arrangörskällan anger ${fmtKm(S.race.organizer_advertised_km)} km, och ingen årsspecifik godkänd GPX-längd finns.</p>`;
  let previous={name:'Start',seconds:0};
  const journey=S.race.stations.filter(st=>st.is_analysis_boundary&&num(st.km)&&st.km>0).sort((a,b)=>a.sort-b.sort||a.km-b.km).map(st=>{
    const observation=observed(r,st),elapsed=observation?.elapsed_seconds;
    const valid=num(elapsed)&&elapsed>previous.seconds;
    const split=valid?time(elapsed-previous.seconds):'—';
    const from=valid?previous.name:'—';
    if(valid)previous={name:st.name,seconds:elapsed};
    return `<tr><td>${html(st.name)}</td><td>${fmtKm(st.km)}</td><td>${time(elapsed)}</td><td>${split}${valid?` <small>från ${html(from)}</small>`:''}</td><td>${observation?.place??'—'}</td><td>${observation?'Observerad EQ TIME':'Passage saknas'}</td></tr>`;
  }).join('');
  const field=segmentStats(records());
  const segmentRows=segments.map(p=>{
    const stat=field.find(s=>s.index===p.index);
    return `<tr><td>${html(p.from.name)} → ${html(p.to.name)}</td><td>${fmtKm(p.km)}</td><td>${time(p.seconds)}</td><td>${paceDistanceSupported(p)?pace(p.seconds,p.km,S.unit):'Distans ej verifierad'}</td><td>${time(stat?.median)}</td><td>${num(stat?.median)?signed(p.seconds-stat.median):'—'}</td><td>${stat?.n??0}</td></tr>`;
  }).join('');
  $('#profile-content').innerHTML=head+`<div class="profile-kpis">${kpis}</div>${distanceNote}<div class="profile-actions"><button type="button" class="btn text-btn" id="profile-fav">${S.favorites.includes(r.id)?'★ Sparad · ta bort':'☆ Spara resultat'}</button></div><h3>Personliga insikter</h3><div class="insights">${insights.length?insights.map(item=>`<article class="insight"><span>${html(item.label)}</span><strong>${html(item.value)}</strong><span>${html(item.detail)}</span><small>${html(item.method)}</small></article>`).join(''):empty('Fler individuella insikter blir tillgängliga där löparen har tillräckligt många verkliga kontrollpassager.')}</div><h3>Journey · verifierade passager</h3><div class="table-scroll"><table><thead><tr><th>Kontroll</th><th>km*</th><th>Ack. tid</th><th>Sedan föregående verifierade</th><th>Publicerad plats</th><th>Datakälla</th></tr></thead><tbody><tr><td>Start</td><td>0</td><td>0:00</td><td>—</td><td>—</td><td>Tidsnoll</td></tr>${journey}</tbody></table></div>${segments.length?`<h3 style="margin-top:22px">Delsträckor och relativ prestation</h3><div class="table-scroll"><table><thead><tr><th>Segment</th><th>Timing-km</th><th>Segmenttid</th><th>Tempo</th><th>Fältmedian*</th><th>Avvikelse</th><th>n</th></tr></thead><tbody>${segmentRows}</tbody></table></div><p class="muted small">* Median för fullföljare med två exakta segmentpassager i denna upplaga, minst fem observationer.</p>`:''}<div id="profile-replay" style="margin-top:20px"></div>`;
  $('#profile-fav').addEventListener('click',()=>toggleFav(r.id));
  $('#profile-add-compare').addEventListener('click',()=>{addCompare(r.id);renderProfile(r)});
  renderProfileReplay(r);
}

function validRouteComparison(){return !!S.route&&routePoints().length>=2} // Map availability must not depend on checkpoint coverage.
function updateReplayElevation(host,pts,d,callback){
  if(!host.querySelector('svg')){
    host.innerHTML=elevationSvg(pts,d);
    attachElevation(host,pts,callback);
    return;
  }
  const P=17,W=780,H=135,md=pts.at(-1)[0],dot=pointAtDistance(pts,d);
  const heights=pts.map(p=>num(p[3])?p[3]:0),min=Math.min(...heights),max=Math.max(...heights);
  const xx=P+d/md*(W-2*P),yy=H-P-((num(dot?.[3])?dot[3]:0)-min)/Math.max(1,max-min)*(H-2*P);
  const cursor=host.querySelector('.chart-cursor'),point=host.querySelector('.elev-dot');
  cursor.setAttribute('x1',xx);cursor.setAttribute('x2',xx);
  point.setAttribute('cx',xx);point.setAttribute('cy',yy);
  host.querySelector('[data-elev-hit]').setAttribute('aria-valuenow',d);
}
function renderProfileReplay(r){
  cancelAnimationFrame(S._replayFrame);
  replaySoundtrack.close();
  const host=$('#profile-replay-stage')||$('#profile-replay');
  if(!validRouteComparison()){
    host.innerHTML=`<p class="empty">Ingen Replay för detta resultat: ${S.route?'för få verkliga tidsankare':'denna upplaga saknar separat verifierad publicerbar lokal rutt'}. Profilens publicerade passager påverkas inte.</p>`;
    return;
  }
  const pts=routePoints(),anchors=runnerAnchors(r),maxDistance=anchors.at(-1)?.km||0;
  if(anchors.length<2||maxDistance<=0){
    // Source geometry still belongs in the personal popup. Only the runner
    // animation is disabled where the participant has no usable TIME after Start.
    host.innerHTML='<h3>Bana och höjd · tillgänglig GPX</h3><div class="course-map" id="profile-mini-map"></div><div class="course-elevation" id="profile-mini-elev"></div><p class="muted small">Banan finns, men denna löpare saknar en senare registrerad TIME-passage. Replay-rörelse kan därför inte beräknas utan att hitta på data.</p>';
    const map=$('#profile-mini-map'),{W,H}=mapViewport(map,280),path=project(pts,W,H,18);
    map.innerHTML=svg(W,H,`${osmTiles(pts,W,H,18)}<path class="simple-route-base" d="${pathFor(path)}"/><path class="simple-route-line" d="${pathFor(path)}"/>`,'Statisk verifierad GPX-rutt över OpenStreetMap')+osmAttribution();
    $('#profile-mini-elev').innerHTML=elevationSvg(pts,0,false);
    return;
  }
  let d=0,playing=false,startedAt=0,startedKm=0;
  S.profileFollow=false;
  host.innerHTML=`<div class="panel-heading"><div><p class="eyebrow">BERÄKNAD POSITION MELLAN KONTROLLER</p><h3>Personlig Replay · bana och höjd</h3></div></div><div class="course-map" id="profile-mini-map"></div><div class="course-elevation" id="profile-mini-elev"></div><div class="replay-controls"><button type="button" class="btn green" id="profile-replay-play">Spela</button><button type="button" class="btn text-btn" id="profile-replay-reset">Börja om</button><label>Uppspelningstid<select id="profile-replay-duration"><option value="30">30 s</option><option value="60">60 s</option><option value="120" selected>120 s</option><option value="180">180 s</option></select></label><button type="button" class="btn text-btn" id="profile-replay-follow" aria-pressed="false">Följ löpare</button><button type="button" class="btn text-btn" id="profile-replay-fit">Visa hela banan</button><button type="button" class="btn text-btn replay-music-toggle" data-replay-music aria-label="Slå av eller på musik" aria-pressed="true">♫ Musik</button><label class="replay-music-volume">Volym <input data-replay-volume type="range" min="0" max="1" step="0.05" value="0.3" aria-label="Musikvolym"></label><span data-replay-audio-note class="muted small" role="status" hidden></span></div><label>Position längs visningsrutten<input class="duel-scrubber" id="profile-replay-range" type="range" min="0" max="${maxDistance}" step="0.1" value="0" aria-label="Spola genom löparens lopp"/></label><p class="muted small" id="profile-replay-readout"></p>`;
  const map=$('#profile-mini-map'),elev=$('#profile-mini-elev'),range=$('#profile-replay-range'),playButton=$('#profile-replay-play');
  replaySoundtrack.bind(host);
  const stop=(pauseMusic=true)=>{playing=false;cancelAnimationFrame(S._replayFrame);playButton.textContent='Spela';if(pauseMusic)replaySoundtrack.pause()};
  function draw(km){
    d=Math.max(0,Math.min(maxDistance,km));
    range.value=d;
    const elapsed=estimatedAt(anchors,d);
    drawSimpleRoute(map,pts,d);
    updateReplayElevation(elev,pts,d,draw);
    $('#profile-replay-readout').textContent=`${fmtKm(d)} km på visningsrutten · ${num(elapsed)?'Beräknad tävlingstid '+time(elapsed):'Ingen säker interpolation'} · Sista exakta ankare: ${anchors.at(-1).name}. Positionen är illustrativ, inte uppmätt GPS.`;
    window.SatilaProfile?.onReplayPosition?.({runnerId:r.id,distance:d,elapsed,anchors,maxDistance});
  }
  function frame(now){
    if(!playing)return;
    const duration=Number($('#profile-replay-duration').value)*1000;
    const next=startedKm+(now-startedAt)/duration*maxDistance;
    draw(next);
    if(next>=maxDistance)stop(false); // Keep soundtrack looping until the popup closes.
    else S._replayFrame=requestAnimationFrame(frame);
  }
  playButton.addEventListener('click',()=>{
    if(playing){stop();return}
    if(d>=maxDistance)draw(0);
    playing=true;startedKm=d;startedAt=performance.now();playButton.textContent='Pausa';
    replaySoundtrack.start();
    S._replayFrame=requestAnimationFrame(frame);
  });
  $('#profile-replay-reset').addEventListener('click',()=>{stop();replaySoundtrack.close();replaySoundtrack.bind(host);draw(0)});
  range.addEventListener('input',()=>{if(playing)stop();draw(+range.value)});
  $('#profile-replay-duration').addEventListener('change',()=>{if(playing){startedKm=d;startedAt=performance.now()}});
  $('#profile-replay-follow').addEventListener('click',event=>{
    S.profileFollow=!S.profileFollow;
    event.currentTarget.setAttribute('aria-pressed',String(S.profileFollow));
    draw(d);
  });
  $('#profile-replay-fit').addEventListener('click',()=>{
    S.profileFollow=false;$('#profile-replay-follow').setAttribute('aria-pressed','false');draw(d);
  });
  $('#profile-dialog').addEventListener('close',()=>{stop();replaySoundtrack.close()},{once:true});
  draw(0);
}

// Replay-only model. All returned synthetic anchors remain local to animation;
 // they are never written to EQ observations, results, journey or segment statistics.
function runnerAnchors(r){
  const endKm=routePoints().at(-1)?.[0]||S.race.nominal_km;
  const factor=endKm/S.race.nominal_km;
  const stations=S.race.stations.filter(st=>st.is_analysis_boundary&&num(st.km)&&st.km>0&&st.km<=S.race.nominal_km).sort((a,b)=>a.km-b.km);
  const raw=[{km:0,t:0,name:'Start',mode:'observed',station:null}];
  for(const st of stations){
    const obs=observed(r,st),last=raw.at(-1),km=Math.min(endKm,st.km*factor);
    if(obs&&num(obs.elapsed_seconds)&&obs.elapsed_seconds>last.t&&km>last.km+1e-6)
      raw.push({km,t:obs.elapsed_seconds,name:st.name,mode:'observed',station:st});
  }
  // An official FINISHED result supplies the observed terminal TIME even if the
  // source bundle has no separately linked public finish passage.
  if(finish(r)&&num(r.finish_seconds)&&r.finish_seconds>raw.at(-1).t)
    raw.push({km:endKm,t:r.finish_seconds,name:'Mål',mode:'observed',station:null});
  if(raw.length<2)return raw;
  const all=[raw[0]];
  for(let i=1;i<raw.length;i++){
    const from=raw[i-1],to=raw[i];
    const missing=stations.filter(st=>st.km*factor>from.km+1e-5&&st.km*factor<to.km-1e-5);
    if(!missing.length){all.push(to);continue}
    const boundaries=[from,...missing.map(st=>({km:st.km*factor,station:st,name:st.name})),to];
    const peers=[];
    for(const peer of records().filter(finish)){
      if(peer.id===r.id)continue;
      const times=boundaries.map((p,j)=>j===0&&p.station===null?0:observed(peer,p.station)?.elapsed_seconds);
      if(times.some(t=>!num(t)))continue;
      const durations=times.slice(1).map((t,j)=>t-times[j]);
      if(durations.some(t=>t<=0))continue;
      const span=times.at(-1)-times[0];
      // Select peers by observed elapsed duration over this same bounding interval,
      // not by an unrelated split or the participant's nominal pace.
      peers.push({durations,span,closeness:Math.abs(Math.log(span/(to.t-from.t)))});
    }
    peers.sort((a,b)=>a.closeness-b.closeness);
    const cohort=peers.slice(0,30);
    if(cohort.length<5){all.push(to);continue} // explicit linear fallback
    const median=values=>{const v=values.slice().sort((a,b)=>a-b);return (v[Math.floor((v.length-1)/2)]+v[Math.floor(v.length/2)])/2};
    const shares=missing.map((_,j)=>median(cohort.map(p=>p.durations[j]/p.span)));
    shares.push(median(cohort.map(p=>p.durations[missing.length]/p.span)));
    const total=shares.reduce((a,b)=>a+b,0);
    if(!(total>0)||shares.some(v=>!(v>0))){all.push(to);continue}
    let elapsed=from.t;
    for(let j=0;j<missing.length;j++){
      elapsed+=(to.t-from.t)*shares[j]/total;
      all.push({km:missing[j].km*factor,t:elapsed,name:missing[j].name,mode:'cohort_estimate',referenceCount:cohort.length});
    }
    all.push(to); // exact observed endpoint preserved, with no drift
  }
  return all;
}
function estimatedAt(anchors,d){if(!anchors?.length)return null;d=Math.max(0,d);if(d>anchors.at(-1).km+1e-6)return null;for(let i=1;i<anchors.length;i++){let a=anchors[i-1],b=anchors[i];if(d>=a.km&&d<=b.km){let f=(d-a.km)/Math.max(1e-6,b.km-a.km);return a.t+(b.t-a.t)*f}}return d===0?0:null}
function drawSimpleRoute(host,pts,d,markers=null,cameraDistance=d){
  const {W,H}=mapViewport(host,280),path=project(pts,W,H,18);
  const xyAt=km=>{
    let i=1;
    while(i<pts.length-1&&pts[i][0]<km)i++;
    const a=pts[i-1],b=pts[i],f=(km-a[0])/Math.max(.000001,b[0]-a[0]);
    return [path[i-1][0]+(path[i][0]-path[i-1][0])*f,path[i-1][1]+(path[i][1]-path[i-1][1])*f];
  };
  let routeSvg=host.querySelector('svg'),hit=host.querySelector('[data-local-hit]');
  if(routeSvg&&Math.abs(Number(routeSvg.dataset.fullMapWidth||W)-W)>2){routeSvg.remove();host.querySelectorAll('.osm-attribution').forEach(node=>node.remove());routeSvg=null;hit=null}
  if(!routeSvg){
    const markerSvg=Array.isArray(markers)?markers.map((marker,i)=>`<circle data-runner-marker="${i}" r="6" fill="${marker.color}" fill-opacity=".72" stroke="#173b2a" stroke-width="1.5" stroke-opacity=".82"><title>${html(marker.label)}</title></circle>`).join(''):'';
    host.insertAdjacentHTML('beforeend',svg(W,H,`${osmTiles(pts,W,H,18)}<path class="simple-route-base" d="${pathFor(path)}"/><path class="simple-route-line" d="${pathFor(path)}"/><circle data-route-cursor r="5" fill="#d4a858" stroke="#173b2a" stroke-width="1" opacity=".65"/>${markerSvg}<rect data-local-hit x="0" y="0" width="${W}" height="${H}" fill="transparent" tabindex="0" role="slider" aria-valuemin="0" aria-valuemax="${pts.at(-1)[0]}" aria-valuenow="${d}" aria-label="Sök i kartan"/>`,'Interaktiv GPX-rutt över OpenStreetMap')+osmAttribution());
    routeSvg=host.querySelector('svg');routeSvg.dataset.fullMapWidth=String(W);hit=host.querySelector('[data-local-hit]');
    const seek=event=>{
      const rect=routeSvg.getBoundingClientRect(),box=routeSvg.viewBox.baseVal;
      const point=[box.x+(event.clientX-rect.left)/rect.width*box.width,box.y+(event.clientY-rect.top)/rect.height*box.height];
      const spot=nearestSegmentPath(path,point),i=spot.index;
      const km=pts[i-1][0]+(pts[i][0]-pts[i-1][0])*spot.fraction;
      if(host.closest('#profile-replay')){
        const range=$('#profile-replay-range');range.value=km;range.dispatchEvent(new Event('input'));
      }else if(host.id==='map-duel-map')S._mapDuelSeek?.(km);
      else S._duelSeek?.(km);
    };
    hit.addEventListener('pointerdown',event=>{hit.setPointerCapture(event.pointerId);seek(event)});
    hit.addEventListener('pointermove',event=>{if(event.pointerType==='mouse'||event.buttons)seek(event)});
    hit.addEventListener('keydown',event=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();
      const current=Number(hit.getAttribute('aria-valuenow'))||0,delta=pts.at(-1)[0]/80;
      const km=event.key==='Home'?0:event.key==='End'?pts.at(-1)[0]:Math.max(0,Math.min(pts.at(-1)[0],current+(event.key==='ArrowRight'?delta:-delta)));
      if(host.closest('#profile-replay')){
        const range=$('#profile-replay-range');range.value=km;range.dispatchEvent(new Event('input'));
      }else if(host.id==='map-duel-map')S._mapDuelSeek?.(km);
      else S._duelSeek?.(km);
    });
  }
  const [x,y]=xyAt(d),cursor=host.querySelector('[data-route-cursor]');
  cursor.setAttribute('cx',x);cursor.setAttribute('cy',y);
  if(Array.isArray(markers))markers.forEach((marker,i)=>{
    const point=xyAt(marker.km),node=host.querySelector('[data-runner-marker="'+i+'"]');
    // Identical route positions share one exact projected coordinate. A visual
    // offset would imply a positional gap; translucent fills show the overlap.
    if(node){node.setAttribute('cx',point[0]);node.setAttribute('cy',point[1])}
  });
  const zoom=host.id==='duel-map'?(S.duelZoom||1):host.id==='profile-mini-map'&&S.profileFollow?2.2:host.id==='map-duel-map'&&S.mapDuelCamera==='leader'?2.2:1,width=W/zoom,height=H/zoom,[cameraX,cameraY]=xyAt(cameraDistance);
  const vx=Math.max(0,Math.min(W-width,cameraX-width/2)),vy=Math.max(0,Math.min(H-height,cameraY-height/2));
  routeSvg.setAttribute('viewBox',`${vx} ${vy} ${width} ${height}`);
  hit.setAttribute('aria-valuenow',d);
}

function comparisonParams(){return new URLSearchParams(location.hash.includes('=')?location.hash.slice(1):'')}
function clearComparisonStateFromUrl(){const hash=comparisonParams();let changed=false;for(const key of ['compareA','compareB','compareTime','compareSegment']){if(hash.has(key)){hash.delete(key);changed=true}}if(changed)history.replaceState(null,'','#'+hash.toString())}
function writeComparisonState(x,y,mode='replace'){
  const hash=comparisonParams();hash.set('family',S.family);hash.set('year',S.year);hash.set('compareA',x.id);hash.set('compareB',y.id);
  if(num(S.duelClock)&&S.duelClock>0)hash.set('compareTime',String(Math.round(S.duelClock)));else hash.delete('compareTime');
  if(Number.isInteger(S.compareSegment))hash.set('compareSegment',String(S.compareSegment));else hash.delete('compareSegment');
  const target='#'+hash.toString();if(location.hash!==target)history[mode==='push'?'pushState':'replaceState'](null,'',target);
}
function restoreComparisonFromUrl(params=comparisonParams()){
  const ids=[params.get('compareA'),params.get('compareB')].filter(Boolean),clockRaw=params.get('compareTime'),segmentRaw=params.get('compareSegment'),clock=clockRaw===null?null:Number(clockRaw),segment=segmentRaw===null?null:Number(segmentRaw);
  if(ids.length!==2||ids[0]===ids[1]||!ids.every(findRecord))return false;
  S.mapDuel=[...ids];S.compare=[...ids];S.duelClock=num(clock)&&clock>=0?clock:0;S.compareSegment=segmentRaw!==null&&Number.isInteger(segment)&&segment>=0?segment:null;renderMapDuelChips();openCompare({updateUrl:false});return true;
}
function openCompare(options={}){const ids=S.mapDuel.length===2?S.mapDuel:S.compare;if(ids.length!==2)return;let [x,y]=ids.map(findRecord);if(!x||!y)return;replaySoundtrack.close();const model=comparisonViewModel(x,y);$('#compare-content').innerHTML=renderCompareContent(model);let d=$('#compare-dialog');if(!d.open)d.showModal();setupCompareInteractions(model);}
function commonStationRows(x,y){let rows=[];for(const st of S.race.stations.filter(s=>s.is_analysis_boundary)){let a=observed(x,st),b=observed(y,st);rows.push({st,a,b,km:st.km,diff:a&&b?b.elapsed_seconds-a.elapsed_seconds:null});}return rows}
function comparisonViewModel(x,y){
  const rows=commonStationRows(x,y),shared=rows.filter(r=>num(r.diff)),xParts=pairs(x),yParts=pairs(y),field=segmentStats(records());
  const segments=boundaries().slice(1).map((to,index)=>{const a=xParts.find(p=>p.to.uid===to.uid),b=yParts.find(p=>p.to.uid===to.uid),stat=field.find(s=>s.to.uid===to.uid),physical=stat?paceDistanceSupported(stat):false,delta=a&&b?b.seconds-a.seconds:null,medianSeconds=stat&&stat.n>=5?stat.median:null,gapAtEnd=rows.find(row=>row.st.uid===to.uid)?.diff??null;return {index,to,from:boundaries()[index],a,b,stat,physical,delta,gapAtEnd,medianSeconds,aRelative:a&&medianSeconds?100*(medianSeconds/a.seconds-1):null,bRelative:b&&medianSeconds?100*(medianSeconds/b.seconds-1):null}});
  let leadChanges=0,previousLead=0;for(const row of shared){const lead=Math.sign(row.diff);if(lead&&previousLead&&lead!==previousLead)leadChanges++;if(lead)previousLead=lead}
  const largest=shared.slice().sort((a,b)=>Math.abs(b.diff)-Math.abs(a.diff))[0]||null,nearest=shared.slice().sort((a,b)=>Math.abs(a.diff)-Math.abs(b.diff))[0]||null;
  const aBest=segments.filter(s=>num(s.delta)&&s.delta>0).sort((a,b)=>b.delta-a.delta)[0]||null,bBest=segments.filter(s=>num(s.delta)&&s.delta<0).sort((a,b)=>a.delta-b.delta)[0]||null;
  const routeReady=validRouteComparison(),intermediate=shared.filter(r=>!r.st.is_finish).length,sparse=intermediate<2;
  return {x,y,rows,shared,segments,finishGap:finish(x)&&finish(y)?y.finish_seconds-x.finish_seconds:null,leadChanges,largest,nearest,aBest,bBest,routeReady,sparse,capabilities:{finish_comparison:finish(x)&&finish(y),checkpoint_gap:shared.length>0,placement_journey:rows.some(r=>num(r.a?.place)||num(r.b?.place)),segment_comparison:segments.some(s=>s.a&&s.b),edition_field_normalization:segments.some(s=>num(s.aRelative)||num(s.bRelative)),shared_course_context:routeReady,animated_two_result_comparison:routeReady,elevation_seek:routeReady,shareable_comparison_state:true,cross_edition_comparison:false,sparse_comparison_fallback:sparse,team_entity:false,audio:routeReady}};
}
function comparisonKpis(m){
  const leader=row=>!row?'—':row.diff===0?`Lika vid ${row.st.name}`:`${row.diff>0?'A':'B'} före ${time(Math.abs(row.diff))} · ${row.st.name}`;
  const gain=(s,who)=>s?`${time(Math.abs(s.delta))} · ${s.from.name} → ${s.to.name}`:`Ingen observerad segmentvinst för ${who}`;
  return [{label:'Slutlig verifierad skillnad',value:m.finishGap===null?'—':`${m.finishGap===0?'Lika':m.finishGap>0?'A före':'B före'} ${m.finishGap===0?'':time(Math.abs(m.finishGap))}`},{label:'A före vid passager',value:String(m.shared.filter(r=>r.diff>0).length)},{label:'B före vid passager',value:String(m.shared.filter(r=>r.diff<0).length)},{label:'Lika vid passager',value:String(m.shared.filter(r=>r.diff===0).length)},{label:'Ledningsväxlingar',value:String(m.leadChanges)},{label:'A vann mest tid',value:gain(m.aBest,'A')},{label:'B vann mest tid',value:gain(m.bBest,'B')},{label:'Närmast varandra',value:leader(m.nearest)},{label:'Största observerade lucka',value:leader(m.largest)}];
}
function renderCompareContent(m){
  const {x,y,rows,segments,finishGap,routeReady}=m,displaySegments=m.sparse?segments.filter(s=>s.a&&s.b):segments,compareMaxClock=Math.ceil(Math.max(runnerAnchors(x).at(-1).t,runnerAnchors(y).at(-1).t)),selected=Number.isInteger(S.compareSegment)?S.compareSegment:null;
  const sparse=m.sparse?`<aside class="comparison-sparse" role="note"><strong>Förenklad verklig resa</strong><span>Upplagan har färre än två gemensamma mellanpassager. Endast de faktiska ankare som finns visas; inga kontroller fylls ut.</span></aside>`:'';
  const participant=`<section aria-labelledby="comparison-participants"><h3 id="comparison-participants" class="sr-only">Deltagare</h3><div class="compare-profiles"><article><p class="eyebrow">LOPP A</p><span class="avatar" aria-hidden="true">${html(initial(x.name))}</span><h3>${html(x.name)}</h3><p class="muted small">${html(x.class_name)} · #${html(x.bib)}</p><strong>${time(x.finish_seconds)}</strong><p>Placering ${x.place??'—'} · ${html(x.status)}</p></article><div class="versus">VS${finishGap!==null?`<small>${finishGap===0?'Lika':finishGap>0?'A före '+time(finishGap):'B före '+time(-finishGap)}</small>`:''}</div><article><p class="eyebrow">LOPP B</p><span class="avatar" aria-hidden="true">${html(initial(y.name))}</span><h3>${html(y.name)}</h3><p class="muted small">${html(y.class_name)} · #${html(y.bib)}</p><strong>${time(y.finish_seconds)}</strong><p>Placering ${y.place??'—'} · ${html(y.status)}</p></article></div><div class="comparison-actions"><button type="button" class="link-button" id="duel-share">Kopiera delbar länk</button><span id="duel-share-status" class="muted small" role="status"></span></div></section>`;
  const kpis=`<section class="comparison-section" aria-labelledby="comparison-kpis"><div class="comparison-heading"><div><p class="eyebrow">DUELLENS NYCKELTAL</p><h3 id="comparison-kpis">Vad avgjorde?</h3></div><button class="info" type="button" id="compare-info" aria-label="Metod för jämförelsen">i</button></div><div class="comparison-kpis">${comparisonKpis(m).map(k=>`<article><span>${html(k.label)}</span><strong>${html(k.value)}</strong></article>`).join('')}</div></section>`;
  const segmentRows=displaySegments.map(s=>`<tr data-comparison-segment-row="${s.index}" class="${selected===s.index?'selected':''}"><td>${html(s.from.name)} → ${html(s.to.name)}</td><td>${time(s.a?.seconds)}</td><td>${time(s.b?.seconds)}</td><td>${!num(s.delta)?'—':s.delta===0?'Lika':`${s.delta>0?'A':'B'} vann ${time(Math.abs(s.delta))}`}</td><td>${!num(s.gapAtEnd)?'—':s.gapAtEnd===0?'Lika':`${s.gapAtEnd>0?'A':'B'} före ${time(Math.abs(s.gapAtEnd))}`}</td><td>${s.physical?`${pace(s.a?.seconds,s.a?.km)} / ${pace(s.b?.seconds,s.b?.km)}`:'Dold · fysisk distans ej verifierad'}</td><td><button type="button" data-duel-segment="${s.index}" data-duel-ck="${s.to.uid}" aria-pressed="${selected===s.index}">Visa ↗</button></td></tr>`).join('');
  const course=routeReady?`<section class="comparison-section" aria-labelledby="comparison-course"><p class="eyebrow">INTERAKTIV BANA</p><h3 id="comparison-course">Karta, höjd och gemensam tävlingsklocka</h3><div id="duel-progress-chart" class="chart-host">${progressSvg(x,y)}</div><p class="muted small">Grön = A, guld = B. Distanslinjerna och kartpositionerna mellan verkliga EQ Timing-passager är rekonstruktion, inte uppmätta passager.</p><div class="compare-dashboard"><div class="duel-map" id="duel-map"><div class="duel-map-toolbar" role="group" aria-label="Kartzoom"><button type="button" id="duel-zoom-in" aria-label="Zooma in">+</button><button type="button" id="duel-zoom-out" aria-label="Zooma ut">−</button><button type="button" id="duel-fit">Hela banan</button></div></div><div class="duel-elevation" id="duel-elevation"></div></div><div class="comparison-playback"><button type="button" class="btn green" id="duel-play">Spela</button><button type="button" class="btn text-btn" id="duel-reset">Börja om</button><label>Uppspelningstid<select id="duel-duration"><option value="30">30 sekunder</option><option value="60">1 minut</option><option value="120" selected>2 minuter</option><option value="180">3 minuter</option></select></label><label>Kamera<select id="duel-camera"><option value="full">Hela banan</option><option value="both" selected>Följ båda</option><option value="leader">Följ ledaren</option></select></label><button type="button" class="btn text-btn replay-music-toggle" data-replay-music aria-label="Slå av eller på musik" aria-pressed="true">♫ Musik</button><label class="replay-music-volume">Volym <input data-replay-volume type="range" min="0" max="1" step="0.05" value="0.3" aria-label="Musikvolym"></label><span data-replay-audio-note class="muted small" role="status" hidden></span></div><label>Gemensam tävlingsklocka <input type="range" id="duel-clock" min="0" max="${compareMaxClock}" step="1" value="${Math.min(S.duelClock||0,compareMaxClock)}" aria-label="Gemensam tävlingsklocka för båda löparna"/></label><div class="duel-clock-row"><strong id="duel-clock-label">${time(S.duelClock||0)}</strong></div><div class="duel-controls"><label>Sök A:s passage längs banan<input type="range" class="duel-scrubber" id="duel-range" min="0" max="${routePoints().at(-1)[0]}" value="0" step="0.1"/></label></div><div class="duel-readout" id="duel-readout"></div></section>`:empty('Direktjämförelsens tabeller är tillgängliga, men karta/höjd kräver en godkänd lokal bana för denna upplaga.');
  return `${participant}${sparse}${kpis}<section class="comparison-section" aria-labelledby="comparison-gap"><p class="eyebrow">TIDSLUCKA GENOM LOPPET</p><h3 id="comparison-gap">Observerad lucka · positiv = A före</h3><div id="duel-gap-chart" class="chart-host">${gapSvg(m.shared)}</div><p class="muted small">Punkterna är verkliga gemensamma passager. Linjen visar endast sambandet mellan observationerna och är inte en uppmätt kontinuerlig lucka.</p></section>${m.capabilities.placement_journey?`<section class="comparison-section" aria-labelledby="comparison-placement"><p class="eyebrow">OFFICIELL PLACERINGSRESA</p><h3 id="comparison-placement">Publicerad placering vid kontroll</h3><div id="duel-placement-chart" class="chart-host">${placementSvg(rows,x,y)}</div><p class="muted small">Plats 1 visas högst. Saknad publicerad placering bryter serien; ingen placering interpoleras.</p></section>`:''}<section class="comparison-section" aria-labelledby="comparison-segments"><p class="eyebrow">SEGMENTDUELL</p><h3 id="comparison-segments">Verkliga delsträckor</h3><div class="table-scroll"><table class="comparison-segment-table"><thead><tr><th>Segment</th><th>A segmenttid</th><th>B segmenttid</th><th>Vann tid</th><th>Ack. läge</th><th>Tempo A / B</th><th>Synka</th></tr></thead><tbody>${segmentRows}</tbody></table></div><p class="muted small">Exakt segmenttid kräver två verkliga, positiva observationer. Ackumulerat läge kräver en gemensam exakt passage. Tempo visas bara där Sätilas distance-evidence-gate godkänner fysisk timingdistans.</p></section>${m.capabilities.edition_field_normalization?`<section class="comparison-section" aria-labelledby="comparison-field"><p class="eyebrow">RELATIV PRESTATION MOT FÄLTET</p><h3 id="comparison-field">Mot upplagans segmentmedian</h3><div id="duel-field-chart" class="chart-host">${fieldComparisonSvg(segments,x,y)}</div><p class="muted small">Positivt = snabbare än medianen bland fullföljare med exakta segmentpassager, minst n=5. Där fysisk distans är spärrad gäller måttet exakt segmenttid, inte min/km.</p></section>`:''}${course}<section class="comparison-section comparison-method" aria-labelledby="comparison-method"><p class="eyebrow">METOD OCH DATAKVALITET</p><h3 id="comparison-method">Vad är observerat och vad är rekonstruerat?</h3><p>Sluttid, kontrolltid, kontrollplats och segmenttid kommer från publicerade EQ Timing-observationer. Lucka = B:s ackumulerade tid minus A:s; positivt betyder att A ligger före. Kartposition mellan tidtagningsankare är endast en illustrativ rekonstruktion och skapar aldrig en officiell passage.</p><p class="muted small">Aktiva capabilities: ${Object.entries(m.capabilities).filter(([,v])=>v===true).map(([k])=>k).join(', ')}. Medvetet av: cross_edition_comparison och team_entity.</p></section>`;
}

function gapSvg(obs){
  if(!obs.length)return empty('Ingen gemensam exakt kontrollpassage finns för en observerad lucka.');
  const W=750,H=205,L=43,R=18,T=29,B=37,ys=obs.map(o=>o.diff/60);
  const mx=Math.max(1,...ys.map(Math.abs)),scale=Math.ceil(mx/5)*5;
  const xmin=0,xmax=Math.max(1,S.race.nominal_km,...obs.map(o=>o.km));
  const xx=km=>L+km/xmax*(W-L-R),yy=minutes=>T+(scale-minutes)/(2*scale)*(H-T-B);
  const ticks=[-scale,-scale/2,0,scale/2,scale];
  const grid=ticks.map(v=>`<line x1="${L}" x2="${W-R}" y1="${yy(v)}" y2="${yy(v)}" stroke="${v===0?'#69786b':'#dce2d9'}" stroke-width="${v===0?1.5:1}" stroke-dasharray="${v===0?'5 4':'2 4'}"/><text x="${L-6}" y="${yy(v)+4}" font-size="11" text-anchor="end" fill="#526456">${Number(v.toFixed(1))}</text>`).join('');
  const xticks=Array.from({length:5},(_,i)=>{const km=xmax*i/4;return `<line x1="${xx(km)}" x2="${xx(km)}" y1="${H-B}" y2="${H-B+4}" stroke="#526456"/><text x="${xx(km)}" y="${H-B+17}" text-anchor="middle" font-size="11" fill="#526456">${Number(km.toFixed(1))}</text>`}).join('');
  const points=obs.map(o=>[xx(o.km),yy(o.diff/60)]);
  return svg(W,H,`<text x="${L}" y="14" font-size="11" fill="#526456">Lucka B−A (min) · positiv = A före · negativ = B före</text>${grid}<line class="axis" x1="${L}" x2="${L}" y1="${T}" y2="${H-B}"/><line class="axis" x1="${L}" x2="${W-R}" y1="${H-B}" y2="${H-B}"/>${xticks}${obs.length>1?`<path d="${pathFor(points)}" fill="none" stroke="#b48b44" stroke-width="2.5"/>`:''}${obs.map((o,i)=>`<circle cx="${points[i][0]}" cy="${points[i][1]}" r="4.5" fill="#365f40" data-duel-ck="${o.st.uid}" tabindex="0" role="button" aria-label="Visa ${html(o.st.name)} i kartan"><title>${html(o.st.name)} · B−A ${signed(o.diff)} · ${o.diff===0?'lika':o.diff>0?'A före':'B före'} · ${fmtKm(o.km)} km</title></circle>`).join('')}<text x="${(L+W-R)/2}" y="${H-4}" text-anchor="middle" font-size="11">Kontrollens timingdistans (km)</text>`,'Observerad tidslucka B minus A i minuter vid gemensamma kontroller');
}
function placementSvg(rows,x,y){
  const observed=rows.filter(r=>num(r.a?.place)||num(r.b?.place));if(!observed.length)return empty('Publicerade kontrollplaceringar saknas.');
  const W=750,H=220,L=48,R=18,T=32,B=43,maxPlace=Math.max(2,...observed.flatMap(r=>[r.a?.place,r.b?.place]).filter(num)),xmax=Math.max(1,S.race.nominal_km,...observed.map(r=>r.km)),xx=km=>L+km/xmax*(W-L-R),yy=place=>T+(place-1)/Math.max(1,maxPlace-1)*(H-T-B);
  const series=(key,color)=>{let paths=[],run=[];for(const row of rows){const place=row[key]?.place;if(!num(place)){if(run.length>1)paths.push(run);run=[];continue}run.push([xx(row.km),yy(place),row,place])}if(run.length>1)paths.push(run);return paths.map(points=>`<path d="${pathFor(points)}" fill="none" stroke="${color}" stroke-width="2.5"/>`).join('')+rows.map(row=>num(row[key]?.place)?`<circle cx="${xx(row.km)}" cy="${yy(row[key].place)}" r="4.5" fill="${color}" data-duel-ck="${row.st.uid}" tabindex="0" role="button"><title>${key==='a'?'A '+x.name:'B '+y.name} · ${row.st.name} · plats ${row[key].place}</title></circle>`:'').join('')};
  return svg(W,H,`<text x="${L}" y="15" fill="#315f41" font-size="11">● A ${html(x.name)}</text><text x="${W/2}" y="15" fill="#a47b37" font-size="11">● B ${html(y.name)}</text>${chartYTicks(L,W-R,T,H-B,maxPlace,1,v=>String(Math.round(v)))}<line class="axis" x1="${L}" x2="${L}" y1="${T}" y2="${H-B}"/><line class="axis" x1="${L}" x2="${W-R}" y1="${H-B}" y2="${H-B}"/>${series('a','#315f41')}${series('b','#b48b44')}<text x="${(L+W-R)/2}" y="${H-5}" text-anchor="middle" font-size="11">Officiell checkpointplacering</text>`,'Officiell placeringsresa för A och B; plats ett högst');
}
function fieldComparisonSvg(segments,x,y){
  const W=750,H=235,L=55,R=18,T=35,B=58,values=segments.flatMap(s=>[s.aRelative,s.bRelative]).filter(num);if(!values.length)return empty('Minst fem exakta fältobservationer krävs.');
  const lo=Math.min(-5,...values),hi=Math.max(5,...values),step=(W-L-R)/Math.max(1,segments.length),xx=i=>L+(i+.5)*step,yy=v=>H-B-(v-lo)/Math.max(1,hi-lo)*(H-T-B);
  const line=key=>{let out='',active=false;for(const s of segments){const v=s[key];if(!num(v)){active=false;continue}out+=`${active?'L':'M'}${xx(s.index)},${yy(v)} `;active=true}return out};
  const dots=(key,color,label)=>segments.map(s=>num(s[key])?`<circle cx="${xx(s.index)}" cy="${yy(s[key])}" r="4.5" fill="${color}" data-duel-segment="${s.index}" data-duel-ck="${s.to.uid}" tabindex="0" role="button"><title>${label} · ${s.from.name} → ${s.to.name} · ${s[key].toFixed(1)} % · ${s.physical?'pace mot fältmedian':'segmenttid mot fältmedian'} · n=${s.stat.n}</title></circle>`:'').join('');
  return svg(W,H,`${chartYTicks(L,W-R,T,H-B,lo,hi,v=>v.toFixed(0)+' %')}<line x1="${L}" x2="${W-R}" y1="${yy(0)}" y2="${yy(0)}" stroke="#59675c" stroke-dasharray="5 4"/><text x="${W-R}" y="${yy(0)-5}" text-anchor="end" font-size="11">0 % · fältmedian</text><text x="${L}" y="15" fill="#315f41" font-size="11">● A ${html(x.name)}</text><text x="${W/2}" y="15" fill="#a47b37" font-size="11">● B ${html(y.name)}</text><path d="${line('aRelative')}" fill="none" stroke="#315f41" stroke-width="2.5"/><path d="${line('bRelative')}" fill="none" stroke="#b48b44" stroke-width="2.5"/>${dots('aRelative','#315f41','A')}${dots('bRelative','#b48b44','B')}${segments.map(s=>`<text x="${xx(s.index)}" y="${H-22}" text-anchor="middle" transform="rotate(-25 ${xx(s.index)} ${H-22})" font-size="10">${html(s.to.name.slice(0,11))}</text>`).join('')}`,'Relativ segmentprestation mot upplagans fältmedian');
}
function progressSvg(x,y){
  const xa=runnerAnchors(x),ya=runnerAnchors(y),W=750,H=215,P=32,B=39,T=35,maxClock=Math.max(1,xa.at(-1).t,ya.at(-1).t),maxKm=Math.max(1,routePoints().at(-1)?.[0]||S.race.nominal_km);
  const xx=t=>P+t/maxClock*(W-2*P),yy=km=>H-B-km/maxKm*(H-B-T);
  const coord=p=>[xx(p.t),yy(p.km)];
  const series=(anchors,color)=>{
    const path=pathFor(anchors.map(coord)),last=anchors.at(-1),lastXY=coord(last);
    return `<path d="${path}" stroke="${color}" stroke-width="3" fill="none"/><circle cx="${lastXY[0]}" cy="${lastXY[1]}" r="4" fill="${color}"><title>${fmtKm(last.km)} km vid ${time(last.t)}</title></circle>${last.t<maxClock?`<path d="M${lastXY[0]} ${lastXY[1]}L${W-P} ${lastXY[1]}" stroke="${color}" stroke-dasharray="4 5" fill="none"/>`:''}`;
  };
  const grid=Array.from({length:5},(_,i)=>{const km=maxKm*i/4;return `<line x1="${P}" x2="${W-P}" y1="${yy(km)}" y2="${yy(km)}" stroke="#dce2d9" stroke-dasharray="2 4"/><text x="${P-5}" y="${yy(km)+4}" font-size="11" text-anchor="end" fill="#526456">${Number(km.toFixed(1))}</text>`}).join('');
  const xticks=Array.from({length:5},(_,i)=>{const t=maxClock*i/4;return `<line x1="${xx(t)}" x2="${xx(t)}" y1="${H-B}" y2="${H-B+4}" stroke="#526456"/><text x="${xx(t)}" y="${H-B+17}" text-anchor="middle" font-size="11" fill="#526456">${Math.floor(t/3600)}:${String(Math.floor(t%3600/60)).padStart(2,'0')}</text>`}).join('');
  const chart=`<text x="${P}" y="14" fill="#315f41" font-size="11">● A ${html(x.name)}</text><text x="${W/2}" y="14" fill="#a47b37" font-size="11">● B ${html(y.name)}</text><text x="${P}" y="29" font-size="11" fill="#526456">Distans (km)</text>${grid}<line class="axis" x1="${P}" x2="${P}" y1="${T}" y2="${H-B}"/><line class="axis" x1="${P}" x2="${W-P}" y1="${H-B}" y2="${H-B}"/>${xticks}${series(xa,'#315f41')}${series(ya,'#b48b44')}<line data-compare-clock-cursor x1="${P}" x2="${P}" y1="${T}" y2="${H-B}" stroke="#59675c" stroke-dasharray="4 3"/><text x="${W/2}" y="${H-4}" text-anchor="middle" font-size="11">Gemensam tävlingsklocka (h:mm)</text>`;
  return svg(W,H,chart,'Två beräknade distanskurvor med graderad distans- och tävlingsklockaxel');
}
function setupCompareInteractions(model){
  const {x,y}=model;
  $('#compare-info')?.addEventListener('click',()=>{
    showHelp('Jämför två lopp','Comparison 2.0 använder lucka = B:s ackumulerade tid minus A:s. Positiv lucka betyder därför att A ligger före. Slut-, passage-, plats- och segmentvärden är verkliga EQ Timing-observationer. De två löparna har en gemensam tävlingsklocka men varsin rekonstruerad position mellan faktiska passager. Rekonstruktionen används bara för animationen och skapar aldrig en ny kontrollpassage.');
  });
  const pts=routePoints(),xa=runnerAnchors(x),ya=runnerAnchors(y),maxClock=Math.max(xa.at(-1).t,ya.at(-1).t);
  let clock=Math.max(0,Math.min(maxClock,S.duelClock||0)),playing=false,startedAt=0,startedClock=0;
  S.duelCamera='both';S.duelZoom=1;S.duelManualZoom=false;
  replaySoundtrack.bind($('#compare-content'));
  const stop=(pauseMusic=true)=>{playing=false;cancelAnimationFrame(S._compareFrame);const play=$('#duel-play');if(play)play.textContent='Spela';if(pauseMusic)replaySoundtrack.pause();};
  function atClock(t){
    clock=Math.max(0,Math.min(maxClock,t));S.duelClock=clock;
    S.duelD=distanceAtTime(xa,clock);
    $('#duel-clock').value=String(clock);$('#duel-clock-label').textContent=time(clock);$('#duel-range').value=String(S.duelD);
    drawCompareMap(x,y,S.duelD,clock);
  }
  function scrub(distance){
    if(!pts.length)return;
    const d=Math.max(0,Math.min(pts.at(-1)[0],distance));
    const t=estimatedAt(xa,d);stop();atClock(num(t)?t:xa.at(-1).t);
  }
  S._duelSeek=scrub;
  $$('[data-duel-ck]',$('#compare-dialog')).forEach(element=>{
    const go=()=>{
      const station=S.race.stations.find(st=>st.uid===+element.dataset.duelCk);
       const segment=Number(element.dataset.duelSegment);if(Number.isInteger(segment)&&segment>=0){S.compareSegment=segment;$$('[data-comparison-segment-row]',$('#compare-dialog')).forEach(row=>row.classList.toggle('selected',+row.dataset.comparisonSegmentRow===segment));$$('[data-duel-segment]',$('#compare-dialog')).forEach(node=>node.setAttribute('aria-pressed',String(+node.dataset.duelSegment===segment)))}
       if(station&&pts.length)scrub(station.km/(S.race.nominal_km||1)*pts.at(-1)[0]);
    };
    element.addEventListener('click',go);
    element.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();go()}});
  });
  $('#duel-share')?.addEventListener('click',async()=>{writeComparisonState(x,y);const url=location.href;try{await navigator.clipboard.writeText(url);$('#duel-share-status').textContent='Länken är kopierad.'}catch{$('#duel-share-status').textContent='Länken finns nu i adressfältet.'}});
  if(pts.length){
    $('#duel-range').addEventListener('input',event=>scrub(+event.target.value));
    $('#duel-clock').addEventListener('input',event=>{stop();atClock(+event.target.value)});
    $('#duel-zoom-in').addEventListener('click',()=>{S.duelManualZoom=true;S.duelZoom=Math.min(4,S.duelZoom+.5);drawCompareMap(x,y,S.duelD??0,clock)});$('#duel-zoom-out').addEventListener('click',()=>{S.duelManualZoom=true;S.duelZoom=Math.max(1,S.duelZoom-.5);drawCompareMap(x,y,S.duelD??0,clock)});
    $('#duel-fit').addEventListener('click',()=>{S.duelCamera='full';S.duelManualZoom=false;S.duelZoom=1;$('#duel-camera').value='full';drawCompareMap(x,y,S.duelD??0,clock)});
    $('#duel-camera').addEventListener('change',event=>{S.duelCamera=event.target.value;S.duelManualZoom=false;drawCompareMap(x,y,S.duelD??0,clock)});
    $('#duel-reset').addEventListener('click',()=>{stop();replaySoundtrack.close();replaySoundtrack.bind($('#compare-content'));atClock(0)});
    function frame(now){
      if(!playing)return;
      const duration=Number($('#duel-duration').value||120)*1000,next=startedClock+(now-startedAt)/duration*maxClock;
      atClock(next);if(next>=maxClock)stop(false);else S._compareFrame=requestAnimationFrame(frame);
    }
    $('#duel-play').addEventListener('click',()=>{
      if(playing){stop();return}
      if(clock>=maxClock)atClock(0);
      playing=true;startedClock=clock;startedAt=performance.now();$('#duel-play').textContent='Pausa';replaySoundtrack.start();
      S._compareFrame=requestAnimationFrame(frame);
    });
    $('#duel-duration').addEventListener('change',()=>{if(playing){startedClock=clock;startedAt=performance.now()}});
    $('#compare-dialog').addEventListener('close',()=>{stop();replaySoundtrack.close()},{once:true});
    atClock(clock);
  }
}
function drawCompareMap(x,y,d,clock){
  const pts=routePoints(),map=$('#duel-map'),elev=$('#duel-elevation');
  if(!map||!pts.length)return;
  const xa=runnerAnchors(x),ya=runnerAnchors(y),t=Number.isFinite(clock)?clock:0,routeEnd=pts.at(-1)[0];
  const aKm=displayDistanceAtTime(xa,t,routeEnd),bKm=displayDistanceAtTime(ya,t,routeEnd);
  const leaderKm=Math.max(aKm,bKm),focusKm=S.duelCamera==='leader'?leaderKm:S.duelCamera==='both'?(aKm+bKm)/2:aKm;
  if(!S.duelManualZoom){if(S.duelCamera==='full')S.duelZoom=1;else if(S.duelCamera==='leader')S.duelZoom=2.2;else if(S.duelCamera==='both')S.duelZoom=Math.max(1.2,Math.min(3.2,routeEnd/Math.max(routeEnd/3,Math.abs(aKm-bKm)*3)));}
  drawSimpleRoute(map,pts,aKm,[{km:aKm,color:'#315f41',label:'A · beräknad position vid gemensam tid'},{km:bKm,color:'#b48b44',label:'B · beräknad position vid gemensam tid'}],focusKm);
  const a=estimatedAt(xa,aKm),b=estimatedAt(ya,aKm),gap=num(a)&&num(b)?b-a:null;
  if(!elev.querySelector('svg')){
    elev.innerHTML=elevationSvg(pts,aKm);
    attachElevation(elev,pts,S._duelSeek);
  }else{
    const P=17,W=780,H=135,md=pts.at(-1)[0],dot=pointAtDistance(pts,aKm);
    const heights=pts.map(p=>num(p[3])?p[3]:0),min=Math.min(...heights),max=Math.max(...heights);
    const xx=P+aKm/md*(W-2*P),yy=H-P-((num(dot?.[3])?dot[3]:0)-min)/Math.max(1,max-min)*(H-2*P);
    const cursor=elev.querySelector('.chart-cursor'),point=elev.querySelector('.elev-dot');
    if(cursor&&point){cursor.setAttribute('x1',xx);cursor.setAttribute('x2',xx);point.setAttribute('cx',xx);point.setAttribute('cy',yy)}
    elev.querySelector('[data-elev-hit]')?.setAttribute('aria-valuenow',aKm);
  }
  const indicator=$('#duel-progress-chart [data-compare-clock-cursor]');
  if(indicator){const cx=32+t/Math.max(1,xa.at(-1).t,ya.at(-1).t)*(750-64);indicator.setAttribute('x1',cx);indicator.setAttribute('x2',cx)}
  const lead=aKm-bKm;
  $('#duel-readout').innerHTML=`<strong>Gemensam tävlingsklocka ${time(t)}</strong> · <span style="color:#315f41">A ${html(x.name)} är cirka ${fmtKm(aKm)} km in i loppet</span> · <span style="color:#a47b37">B ${html(y.name)} befinner sig vid cirka ${fmtKm(bKm)} km på banan</span> · <strong>Positionsskillnad A−B: ${lead>=0?'+':''}${lead.toFixed(1)} km</strong><br>Vid A:s position cirka ${fmtKm(aKm)} km in på visningsrutten: beräknad passagetid A ${time(a)}, B ${time(b)} · Lucka B−A: ${signed(gap)} (${!num(gap)||gap===0?'lika':gap>0?'A före':'B före'}). Mellan exakta kontroller är båda positionerna illustrativa. ${t>xa.at(-1).t||t>ya.at(-1).t?'Löpare utan senare TIME-ankare fryser vid sista observerade position.':''}`;
}
function renderCumulativeFinish(){
  const host=$('#percentile-chart'),finishers=S.filtered.filter(finish);
  if(!host||finishers.length<5)return;
  const groups=[{label:'Alla',rows:finishers,color:'#315f41'},{label:'Kvinnor',rows:finishers.filter(r=>analyticalSex(r)==='F'),color:SEX_COLORS.F},{label:'Män',rows:finishers.filter(r=>analyticalSex(r)==='M'),color:SEX_COLORS.M}].filter(g=>g.rows.length>=5);
  const times=finishers.map(r=>r.finish_seconds),min=Math.floor(Math.min(...times)/900)*900,max=Math.ceil(Math.max(...times)/900)*900;
  if(max<=min)return;
  const W=700,H=200,P=48,steps=40;
  const body=chartYTicks(P,W-P,P,H-P,0,100,v=>Math.round(v)+' %')+chartXTicks(P,W-P,H-P,min,max,v=>time(v),5)+groups.map(group=>{
    const values=group.rows.map(r=>r.finish_seconds);
    const points=Array.from({length:steps+1},(_,i)=>{
      const threshold=min+(max-min)*i/steps,count=values.filter(v=>v<=threshold).length;
      return [P+i/steps*(W-2*P),H-P-count/values.length*(H-2*P)];
    });
    return `<path d="${pathFor(points)}" fill="none" stroke="${group.color}" stroke-width="2.5"><title>${group.label} · n=${values.length}</title></path>`;
  }).join('');
  host.insertAdjacentHTML('beforeend',`<h4 class="subchart-title">Kumulativ målgång i samma tidsfönster</h4>${svg(W,H,body,'Kumulativ andel fullföljare över officiell sluttid')}<div class="map-legend">${groups.map(g=>`<span><i style="background:${g.color}"></i>${g.label} · n=${g.rows.length}</span>`).join('')}</div><p class="muted small">Nämnare: fullföljare med positiv officiell sluttid inom aktuellt urval. Varje könsserie har sin egen källstödda nämnare.</p>`);
}
function renderClassDetails(){
  const host=$('#group-bars'),finishers=S.filtered.filter(finish);
  if(!host)return;
  const counts=Object.entries(collections(finishers.map(r=>r.class_name||'Ingen uppgift'))).sort((a,b)=>b[1]-a[1]);
  if(counts.length<=6)return;
  host.insertAdjacentHTML('beforeend',`<details class="class-details"><summary>Visa alla ${counts.length} klasser</summary><div class="table-scroll"><table><thead><tr><th>Klass</th><th>Fullföljare</th><th>Filter</th></tr></thead><tbody>${counts.map(([name,n])=>`<tr><td>${html(name)}</td><td>${n}</td><td><button type="button" data-class-full="${html(name)}">Välj</button></td></tr>`).join('')}</tbody></table></div></details>`);
  $$('[data-class-full]',host).forEach(button=>button.addEventListener('click',()=>{
    const selected=button.dataset.classFull;
    if(![...$('#class-filter').options].some(option=>option.value===selected))return;
    S.className=selected;$('#class-filter').value=selected;rerenderFilter();
  }));
}
function ensureMapDuelControls(){
  if(!$('#map-duel-builder'))return;
  $('#open-map-duel').addEventListener('click',openMapDuel);
  $('#clear-map-duel').addEventListener('click',()=>{S.mapDuel=[];S.compare=[];S.duelClock=0;S.compareSegment=null;S.duelCamera='both';S.duelManualZoom=false;clearComparisonStateFromUrl();$('#map-duel-search').value='';$('#map-duel-suggestions').innerHTML='';$('#map-duel-feedback').textContent='Välj minst två deltagare.';renderMapDuelChips()});
}
function addMapDuel(id){
  if(!findRecord(id))return;
  S.duelClock=0;S.compareSegment=null;S.duelCamera='both';S.duelManualZoom=false;clearComparisonStateFromUrl();
  if(S.mapDuel.includes(id))S.mapDuel=S.mapDuel.filter(value=>value!==id);
  else if(S.mapDuel.length<5)S.mapDuel.push(id);
  else{$('#map-duel-feedback').textContent='Max fem deltagare kan väljas.';return}
  S.compare=S.mapDuel.length<=2?[...S.mapDuel]:[];
  $('#map-duel-search').value='';$('#map-duel-suggestions').innerHTML='';$('#map-duel-feedback').textContent=S.mapDuel.length<2?'Välj minst två deltagare.':S.mapDuel.length===2?'Två deltagare valda: direktjämförelse och Kartduell är redo.':`${S.mapDuel.length} deltagare valda för Kartduell.`;
  renderMapDuelChips();
}
function renderMapDuelChips(){
  if(!$('#map-duel-chips'))return;
  $('#map-duel-counter').textContent=String(S.mapDuel.length);
  $('#open-map-duel').disabled=S.mapDuel.length<2;
  $('#open-compare').disabled=S.mapDuel.length!==2;
  $('#compare-counter').textContent=`(${S.mapDuel.length}/2)`;
  $('#map-duel-chips').innerHTML=S.mapDuel.map(id=>{const runner=findRecord(id);return `<span class="chip">${html(runner?.name||id)} <button type="button" data-remove-map-duel="${html(id)}" aria-label="Ta bort ${html(runner?.name||'')} från kartduellen">×</button></span>`}).join('')||'<p class="small muted">Ingen löpare vald för kartduell.</p>';
  $$('[data-remove-map-duel]').forEach(button=>button.addEventListener('click',()=>addMapDuel(button.dataset.removeMapDuel)));
  renderMapDuelSuggestions();
}
function distanceAtTime(anchors,elapsed){
  if(!anchors.length)return 0;
  if(elapsed<=0)return 0;
  for(let i=1;i<anchors.length;i++){
    const a=anchors[i-1],b=anchors[i];
    if(elapsed<=b.t)return a.km+(b.km-a.km)*(elapsed-a.t)/Math.max(1e-6,b.t-a.t);
  }
  return anchors.at(-1).km;
}
function displayDistanceAtTime(anchors,elapsed,routeEnd){
  const km=distanceAtTime(anchors,elapsed),last=anchors.at(-1);
  // Finish anchors may differ by tiny source-axis rounding. Once a runner is
  // actually at the route endpoint, use that one canonical endpoint.
  return last&&elapsed>=last.t&&Math.abs(last.km-routeEnd)<.05?routeEnd:km;
}
function openMapDuel(){
  replaySoundtrack.close();
  const dialog=$('#map-duel-dialog'),host=$('#map-duel-content'),runners=S.mapDuel.map(findRecord).filter(Boolean);
  if(runners.length<2||runners.length>5)return;
  cancelAnimationFrame(S._mapDuelFrame);
  if(!validRouteComparison()){
    host.innerHTML=empty('Kartduell kräver en godkänd lokal rutt för exakt denna tävlingsupplaga. Resultaten kan fortfarande jämföras två och två utan karta.');
    dialog.showModal();return;
  }
  const data=runners.map((runner,i)=>({runner,anchors:runnerAnchors(runner),color:['#d8ad62','#69a07b','#8e9dc4','#d28975','#b58ec4'][i]}));
  // The map remains available when timing coverage is sparse. Each runner
  // freezes at their last actual TIME; without one they stay at Start.
  const pts=routePoints(),maxClock=Math.ceil(Math.max(0,...data.map(item=>item.anchors.at(-1).t)));
  let clock=0,playing=false,startedAt=0,startedClock=0;
  S.mapDuelCamera='full';
  host.innerHTML=`<p class="muted small">Gemensam tävlingsklocka. Markörerna följer verifierade EQ-passager. Vid saknade mellankontroller används en robust fartprofil från minst fem närliggande löpare med kompletta passager; annars jämn medelfart mellan de verifierade punkterna. Uppskattningarna används enbart för animeringen, visas inte som resultat och markörerna fryser efter sista säkra ankarpunkt. De är inte uppmätta GPS-positioner.</p><div class="compare-dashboard"><div id="map-duel-map" class="duel-map"></div><div id="map-duel-elevation" class="duel-elevation"></div></div><div class="map-duel-playback"><button type="button" class="btn green" id="map-duel-play">Spela</button><button type="button" class="btn text-btn" id="map-duel-reset">Börja om</button><label>Hastighet<select id="map-duel-speed"><option value="0.5">0,5×</option><option value="1" selected>1×</option><option value="2">2×</option><option value="4">4×</option></select></label><label>Kamera<select id="map-duel-camera"><option value="full">Hela banan</option><option value="leader">Följ ledaren</option></select></label><button type="button" class="btn text-btn" id="map-duel-fit">Visa hela banan</button><button type="button" class="btn text-btn replay-music-toggle" data-replay-music aria-label="Slå av eller på musik" aria-pressed="true">♫ Musik</button><label class="replay-music-volume">Volym <input data-replay-volume type="range" min="0" max="1" step="0.05" value="0.3" aria-label="Musikvolym"></label><span data-replay-audio-note class="muted small" role="status" hidden></span></div><label>Delad tävlingsklocka<input id="map-duel-clock" type="range" min="0" max="${maxClock}" step="1" value="0" aria-label="Sök i kartduellens tävlingsklocka"/></label><p id="map-duel-readout" class="duel-readout"></p><h3>Position och ordning vid vald tid</h3><div id="map-duel-leaderboard"></div>`;
  dialog.showModal();
  const map=$('#map-duel-map'),elev=$('#map-duel-elevation'),play=$('#map-duel-play'),range=$('#map-duel-clock');
  replaySoundtrack.bind(host);
  const stop=(pauseMusic=true)=>{playing=false;cancelAnimationFrame(S._mapDuelFrame);play.textContent='Spela';if(pauseMusic)replaySoundtrack.pause()};
  function draw(next){
    clock=Math.max(0,Math.min(maxClock,next));range.value=clock;
    const positions=data.map(item=>({...item,km:displayDistanceAtTime(item.anchors,clock,pts.at(-1)[0])}));
    const leader=positions.slice().sort((a,b)=>b.km-a.km)[0];
    drawSimpleRoute(map,pts,leader.km,positions.map(item=>({km:item.km,color:item.color,label:`${item.runner.name} · cirka ${fmtKm(item.km)} km in på visningsrutten`})));
    updateReplayElevation(elev,pts,leader.km,km=>{
      const target=estimatedAt(data[0].anchors,km);
      if(num(target)){stop();draw(target)}
    });
    $('#map-duel-readout').textContent=`Tävlingsklocka ${time(clock)} · längst fram just nu: ${leader.runner.name}, som är cirka ${fmtKm(leader.km)} km in på visningsrutten. Positioner mellan kontroller är beräknade.`;
    $('#map-duel-leaderboard').innerHTML=`<div class="table-scroll"><table><thead><tr><th>Ordning*</th><th>Löpare</th><th>Status</th><th>Position på visningsrutt</th><th>Sista exakta kontroll</th></tr></thead><tbody>${positions.sort((a,b)=>b.km-a.km).map((item,i)=>`<tr><td>${i+1}</td><td><i class="duel-color" style="background:${item.color}"></i>${html(item.runner.name)}</td><td>${html(item.runner.status)}</td><td>Cirka ${fmtKm(item.km)} km in</td><td>${html(item.anchors.at(-1).name)}</td></tr>`).join('')}</tbody></table></div><p class="small muted">* Ordningen är en illustrativ interpolation mellan registrerade kontroller, inte en officiell mellanplacering.</p>`;
  }
  function frame(now){
    if(!playing)return;
    const speed=Number($('#map-duel-speed').value),next=startedClock+(now-startedAt)/120000*maxClock*speed;
    draw(next);
    if(next>=maxClock)stop(false); // Keep soundtrack looping at the finish until the popup closes.
    else S._mapDuelFrame=requestAnimationFrame(frame);
  }
  S._mapDuelSeek=km=>{const target=estimatedAt(data[0].anchors,km);if(num(target)){stop();draw(target)}};
  play.addEventListener('click',()=>{
    if(playing){stop();return}
    if(clock>=maxClock)draw(0);
    playing=true;startedClock=clock;startedAt=performance.now();play.textContent='Pausa';replaySoundtrack.start();S._mapDuelFrame=requestAnimationFrame(frame);
  });
  $('#map-duel-reset').addEventListener('click',()=>{stop();replaySoundtrack.close();replaySoundtrack.bind(host);draw(0)});
  range.addEventListener('input',()=>{stop();draw(+range.value)});
  $('#map-duel-speed').addEventListener('change',()=>{if(playing){startedClock=clock;startedAt=performance.now()}});
  $('#map-duel-camera').addEventListener('change',event=>{S.mapDuelCamera=event.target.value;draw(clock)});
  $('#map-duel-fit').addEventListener('click',()=>{S.mapDuelCamera='full';$('#map-duel-camera').value='full';draw(clock)});
  dialog.addEventListener('close',()=>{stop();replaySoundtrack.close()},{once:true});
  draw(0);
}
function renderPage(){renderAll();}
/* Sätila Splits – blueprint completion layer. Uses the shared Engine 1.0 runtime above. */
'use strict';
window.SatilaExtras=(()=>{
  let wired=false;
  const esc=html;
  function ins(afterId,markup){const a=$(afterId);if(a&&!document.querySelector(markup.match(/id="([^"]+)/)?.[1]?`#${markup.match(/id="([^"]+)/)[1]}`:'#__never'))a.insertAdjacentHTML('beforeend',markup)}
  function ensurePanels(){
    if(!$('#extra-overview')) $('#overview').insertAdjacentHTML('beforeend',`<div id="extra-overview" class="extra-grid four-up">
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">KÖN × FULLFÖLJANDE</p><h3>Start till mål</h3></div><button class="info" data-help-extra="sexfinish">i</button></div><div id="sex-completion"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">VAD KRÄVS?</p><h3>Måltid → placering</h3></div><button class="info" data-help-extra="goal">i</button></div><div class="goal-inline"><input id="goal-placement-time" aria-label="Måltid för placeringssimulator" placeholder="06:00:00"><button id="goal-placement-run" class="btn green" type="button">Beräkna</button></div><div id="goal-placement"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">ÅLDER</p><h3>Vilka springer?</h3></div><button class="info" data-help-extra="age">i</button></div><div id="age-chart"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">KLUBB / ORT</p><h3>Största grupperna</h3></div><button class="info" data-help-extra="club">i</button></div><div id="club-chart"></div></article>
    </div>`);
    if(!$('#extra-dynamics')) $('#dynamics').insertAdjacentHTML('beforeend',`<div id="extra-dynamics" class="extra-grid two-up">
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">PLACERINGSFÖRÄNDRING</p><h3>Vem arbetade sig framåt?</h3></div><button class="info" data-help-extra="gain">i</button></div><div id="placement-gain"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">SISTA TREDJEDELEN</p><h3>Avslutningens progression</h3></div><button class="info" data-help-extra="finishprogress">i</button></div><div id="finish-progression"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">SNABBASTE AVSLUTNINGEN</p><h3>Spurten mot mål</h3></div><button class="info" data-help-extra="laststrength">i</button></div><div id="last-segment-strength"></div></article>
    </div>`);
    if(!$('#extra-segments')) $('#segments').insertAdjacentHTML('beforeend',`<div id="extra-segments" class="extra-grid segment-extras">
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">PACINGINDEX</p><h3>Fart per delsträcka i förhållande till hela loppet</h3></div><button class="info" data-help-extra="pacing">i</button></div><div id="segment-pacing"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">KVINNOR / MÄN</p><h3>Tidsåtgång per delsträcka</h3></div><button class="info" data-help-extra="sexpace">i</button></div><div id="segment-sex-extra"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">FÄLTETS SPRIDNING</p><h3>Q25–Q75 genom kontrollerna</h3></div><button class="info" data-help-extra="spread">i</button></div><div id="checkpoint-spread"></div></article>
    </div>`);
    if(!$('#extra-course')) $('#course').insertAdjacentHTML('beforeend',`<div id="extra-course" class="extra-grid course-intelligence-row"><div id="course-intelligence" class="course-intelligence-split"></div></div>`);
    if(!$('#extra-history')) $('#history').insertAdjacentHTML('beforeend',`<div id="extra-history" class="extra-grid history-extra">
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">PRESTATION PER UPPLAGA</p><h3>Medianer utan falsk trendlinje</h3></div><button class="info" data-help-extra="performance">i</button></div><div id="history-performance"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">KÖNSFÖRDELNING</p><h3>Andel kvinnor och män över tid</h3></div><button class="info" data-help-extra="sexhistory">i</button></div><div id="history-sex"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">ÅRENS FINGERAVTRYCK</p><h3>Fyra oberoende mått – inget syntetiskt betyg</h3></div><button class="info" data-help-extra="fingerprint">i</button></div><div id="history-fingerprint"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">COURSEVERSION & PROVENIENS</p><h3>Vad går att jämföra?</h3></div><button class="info" data-help-extra="provenance">i</button></div><div id="course-provenance"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">GRUPPTABELL</p><h3>Kön och klass i valt fält</h3></div><button class="info" data-help-extra="grouptable">i</button></div><div id="group-table"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">KÄLLTÄCKNING</p><h3>Resultat, passager och rutt per år</h3></div><button class="info" data-help-extra="coverage">i</button></div><div id="coverage-table"></div></article>
    </div>`);
  }
  const extraHelp={sexfinish:'Fullföljandegraden räknas inom källstött kön: FINISHED / (FINISHED + DNF + DSQ). DNS och okänd status räknas inte som bekräftad start.',goal:'Simuleringen placerar en angiven måltid i den observerade sluttidsordningen för nuvarande filtrerade fält. Det är inte en prognos över en framtida placering.',age:'Ålder visas endast när EQ Timing publicerar en rimlig numerisk ålder. Saknad ålder infereras aldrig från klassnamn.',club:'Klubb/ort är källfältet som publicerats av EQ Timing; tomma uppgifter förblir saknade.',gain:'Okänd status räknas inte som bekräftad start. Placeringslyft kräver minst två kontroller med publicerad totalplacering. Startplacering gissas inte.',finishprogress:'Sista tredjedelens progression jämför publicerad placering närmast före 2/3 av timingdistansen med sista publicerade placeringen.',laststrength:'Relativ styrka jämför löparens sista verkliga positiva TIME-par med medianen för exakt samma segment. Ingen GPS-fart eller passageimputering används.',q1090:'Median kräver minst fem exakta segmentobservationer. Q25–Q75-bandet kräver minst tio. Luckor fylls aldrig ut.',retention:'Passagetäckning är antal löpare med offentlig TIME-observation vid kontrollen relativt första faktiskt observerade kontrollen. Metadata-only-stationer utan TIME ritas inte som ett konstlat tapp. Det är inte överlevnad eller DNF.',sexpace:'Samma trelägesväljare används i segmentdiagrammen. Median kräver minst fem och Q25–Q75 minst tio exakta observationer i vald grupp.',groups:'Gruppmedianer baseras på publicerad klass och kräver minst fem exakta segmentobservationer.',heatmap:'Varje cell är gruppens segmentmedian relativt hela fältets segmentmedian. Minst fem observationer krävs för både grupp och totalfält.',spread:'Q25–Q75 för ackumulerad verklig passagetid kräver minst tio fullföljare per kontroll. Saknade passager fylls inte ut.',courseintel:'Dimensionerna redovisas separat. Rå positiv GPX-höjd är en geometrisk filsumma och inte arrangörens officiella D+. Inget sammanslaget svårighetsbetyg skapas.',maphistory:'Kartor jämförs bara där lokal ruttgeometri faktiskt finns. En modern officiell rutt lånas inte bakåt till äldre upplagor.',performance:'Enskilda upplagors medianer kan redovisas sida vid sida. En sammanhängande prestationsutveckling ritas endast inom en uttryckligen verifierad whole-course-grupp.',sexhistory:'Andelar bygger endast på källstött kön. Resultat utan kön ligger utanför nämnaren och redovisas separat i tooltip/tabell.',fingerprint:'Varje upplaga visas med oberoende dimensioner. De vägs aldrig ihop till ett syntetiskt svårighetsindex.',provenance:'CourseVersion, route-status och timingkälla hålls separata. Kartgeometri är inte tidtagningsbevis.',grouptable:'Gruppstatistik visar n och median endast när n är tillräckligt. Namn eller kön infereras inte.',coverage:'Källtäckning beskriver vad analysmotorn faktiskt har: resultat, fullföljare, passager, stationer och lokal rutt.'};
  function barRows(items,valueLabel=x=>x.value){if(!items.length)return empty();const max=Math.max(1,...items.map(x=>x.value));return `<div class="bars">${items.map(x=>`<div class="barline"><span title="${esc(x.label)}">${esc(x.label)}</span><div class="bar-track"><div class="bar-fill" style="width:${100*x.value/max}%"></div></div><strong>${esc(valueLabel(x))}</strong></div>`).join('')}</div>`}
  function renderSexCompletion(){const out=$('#sex-completion');if(!out)return;const rows=S.filtered,items=['F','M'].map(sex=>{const r=rows.filter(x=>analyticalSex(x)===sex),started=r.filter(x=>['FINISHED','DNF','DSQ'].includes(x.status)),fin=started.filter(finish);return {sex,label:sex==='F'?'Kvinnor':'Män',started:started.length,fin:fin.length,pct:started.length?100*fin.length/started.length:null}});out.innerHTML=items.some(x=>x.started)?`<div class="completion-pair">${items.map(x=>`<article><strong>${esc(x.label)}</strong><span class="big-number">${num(x.pct)?x.pct.toFixed(1).replace('.',',')+' %':'—'}</span><div class="bar-track"><div class="bar-fill" style="width:${x.pct||0}%;background:${x.sex==='F'?SEX_COLORS.F:SEX_COLORS.M}"></div></div><small>${x.fin}/${x.started} startande med känd startstatus</small></article>`).join('')}</div>`:empty('Kön eller startstatus saknas för detta urval.')}
  function parseClock(s){const p=String(s||'').trim().split(':').map(Number);if(p.some(x=>!Number.isFinite(x))||p.length<2||p.length>3)return null;const n=p.length===2?p[0]*3600+p[1]*60:p[0]*3600+p[1]*60+p[2];return n>0?n:null}
  function renderGoal(){const host=$('#goal-placement');if(!host)return;const fs=S.filtered.filter(finish).sort((a,b)=>a.finish_seconds-b.finish_seconds),editionFinish=records().filter(finish),input=$('#goal-placement-time'),average=mean(editionFinish.map(r=>r.finish_seconds)),fallback=Math.max(3600,Math.round((advertisedKm(S.race)||43)*10*60));if(!input.value){input.value=time(num(average)?average:fallback);input.dataset.defaultSource=num(average)?'finished-mean':'distance-fallback'}if(!fs.length){host.innerHTML=empty(`Ingen giltig FINISHED-tid finns i urvalet. Standardfältet använder ${num(average)?'fortfarande upplagans faktiska medeltid '+time(average):'den tydligt märkta reservtiden '+time(fallback)+' (10 min/km på annonserad distans)'}.`);return}const target=parseClock(input.value);if(!target){host.innerHTML=empty('Ange måltid som HH:MM eller HH:MM:SS.');return}const faster=fs.filter(r=>r.finish_seconds<target).length,place=Math.min(fs.length+1,faster+1),beat=Math.max(0,fs.length-faster),pct=100*beat/fs.length;const near=fs.slice().sort((a,b)=>Math.abs(a.finish_seconds-target)-Math.abs(b.finish_seconds-target)).slice(0,3);host.innerHTML=`<p class="goal-default-note small muted">Standardtid: aritmetiskt medel för ${editionFinish.length} FINISHED i vald upplaga (${time(average)}).</p><div class="sim-kpis"><span><strong>≈ ${place}</strong><small>placering i observerat fält</small></span><span><strong>${pct.toFixed(0)} %</strong><small>av målgångarna bakom måltiden</small></span></div><p class="small muted">Närmaste observerade sluttider</p>${near.map(r=>`<button class="mini-result" data-open="${esc(r.id)}"><span>${esc(r.name)}</span><strong>${time(r.finish_seconds)}</strong><small>#${r.place??'—'}</small></button>`).join('')}`;bindResultLinks(host)}
  function renderAge(){
    const h=$('#age-chart');if(!h)return;
    const ages=S.filtered.filter(r=>num(r.age)&&r.age>=0&&r.age<=120),minimum=ages.length?Math.floor(Math.min(...ages.map(r=>r.age))/5)*5:0,maximum=ages.length?Math.floor(Math.max(...ages.map(r=>r.age))/5)*5:0,bins=[];
    for(let a=minimum;a<=maximum;a+=5){const rows=ages.filter(r=>r.age>=a&&r.age<a+5);bins.push({label:`${a}–${a+4}`,women:rows.filter(r=>analyticalSex(r)==='F').length,men:rows.filter(r=>analyticalSex(r)==='M').length,unknown:rows.filter(r=>!analyticalSex(r)).length})}
    const peak=Math.max(1,...bins.flatMap(b=>[b.women,b.men,b.unknown]));
    h.innerHTML=ages.length?`<div class="age-sex-chart">${bins.map(b=>`<div class="age-sex-row"><strong>${b.label}</strong><div><i class="sex-f" style="width:${100*b.women/peak}%"></i><span>K ${b.women}</span></div><div><i class="sex-m" style="width:${100*b.men/peak}%"></i><span>M ${b.men}</span></div>${b.unknown?`<div><i class="sex-u" style="width:${100*b.unknown/peak}%"></i><span>Okänt ${b.unknown}</span></div>`:''}</div>`).join('')}</div><p class="small muted">Exakt ålder känd för ${ages.length}/${S.filtered.length} resultat. Staplarna använder analytiskt källkön; konflikter redovisas som okänt.</p>`:empty('EQ Timing publicerar ingen numerisk ålder i detta urval.')
  }
  function renderClub(){
    const host=$('#club-chart');
    if(!host)return;
    const groups=Object.entries(collections(S.filtered.map(r=>String(r.club||'').trim()).filter(Boolean))).sort((a,b)=>b[1]-a[1]);
    if(!groups.length){host.innerHTML=empty('Klubb/ort saknas som källfält i detta urval.');return}
    const names=new Set(groups.map(g=>g[0]));
    if(!S.selectedClubs||![...S.selectedClubs].some(name=>names.has(name)))S.selectedClubs=new Set(groups.slice(0,Math.min(3,groups.length)).map(g=>g[0]));
    S.selectedClubs=new Set([...S.selectedClubs].filter(name=>names.has(name)));
    const peak=groups[0][1];
    const visibleGroups=groups.slice(0,10),shownNames=new Set(visibleGroups.map(([name])=>name));for(const item of groups){if(S.selectedClubs.has(item[0])&&!shownNames.has(item[0]))visibleGroups.push(item)}
    const choices=visibleGroups.map(([name,n])=>`<label class="club-choice"><input type="checkbox" data-club-choice="${esc(name)}" ${S.selectedClubs.has(name)?'checked':''} ${S.selectedClubs.size>=4&&!S.selectedClubs.has(name)?'disabled':''}><span>${esc(name)}</span><i class="bar-track"><i class="bar-fill" style="display:block;width:${100*n/peak}%"></i></i><strong>${n}</strong></label>`).join('');
    const selectedAudit=[...S.selectedClubs].map(name=>{const rows=S.filtered.filter(r=>r.club===name),finishers=rows.filter(finish),med=finishers.length>=5?median(finishers.map(r=>r.finish_seconds)):null;return `<tr><td>${esc(name)}</td><td>${rows.length}</td><td>${finishers.length}</td><td>${time(med)}</td></tr>`}).join('');
    const selected=[...S.selectedClubs].map(name=>{
      const rows=S.filtered.filter(r=>r.club===name),finishers=rows.filter(finish),med=finishers.length>=5?median(finishers.map(r=>r.finish_seconds)):null,women=rows.filter(r=>analyticalSex(r)==='F').length,men=rows.filter(r=>analyticalSex(r)==='M').length,unknown=rows.length-women-men;
      return `<article class="club-sex-card"><h4>${esc(name)}</h4><div class="club-sex-bars"><span><i class="sex-f" style="width:${rows.length?100*women/rows.length:0}%"></i><b>Kvinnor ${women}</b></span><span><i class="sex-m" style="width:${rows.length?100*men/rows.length:0}%"></i><b>Män ${men}</b></span>${unknown?`<span><i class="sex-u" style="width:${100*unknown/rows.length}%"></i><b>Okänt ${unknown}</b></span>`:''}</div><dl><div><dt>Resultat</dt><dd>${rows.length}</dd></div><div><dt>Fullföljare</dt><dd>${finishers.length}</dd></div><div><dt>Median</dt><dd>${time(med)}</dd></div></dl></article>`;
    }).join('');
    const full=groups.map(([name,n])=>{
      const finishers=S.filtered.filter(r=>r.club===name&&finish(r)),med=finishers.length>=5?median(finishers.map(r=>r.finish_seconds)):null;
      return `<tr><td>${esc(name)}</td><td>${n}</td><td>${finishers.length}</td><td>${time(med)}</td></tr>`;
    }).join('');
    host.innerHTML=`<p class="small muted">Välj högst fyra källgrupper. Kön visas separat; median visas först vid fem fullföljare.</p><div class="club-choices">${choices}</div><div class="table-scroll club-selection-audit" aria-hidden="true"><table><tbody>${selectedAudit}</tbody></table></div><div class="club-sex-grid">${selected}</div><details class="class-details"><summary>Visa alla ${groups.length} källgrupper</summary><div class="table-scroll"><table><thead><tr><th>Klubb/ort</th><th>Resultat</th><th>Fullföljare</th><th>Median</th></tr></thead><tbody>${full}</tbody></table></div></details>`;
    $$('[data-club-choice]',host).forEach(input=>input.addEventListener('change',()=>{
      if(input.checked&&S.selectedClubs.size<4)S.selectedClubs.add(input.dataset.clubChoice);
      else if(!input.checked)S.selectedClubs.delete(input.dataset.clubChoice);
      renderClub();
    }));
  }

  function placements(r){return S.race.stations.filter(s=>s.is_analysis_boundary).map(st=>{const o=observed(r,st);return o&&num(o.place)?{st,place:o.place,t:o.elapsed_seconds}:null}).filter(Boolean)}
  function renderPlacementGain(){const h=$('#placement-gain');if(!h)return;const xs=S.filtered.map(r=>{const a=placements(r);return a.length>=2?{r,from:a[0],to:a.at(-1),delta:a[0].place-a.at(-1).place}:null}).filter(Boolean).sort((a,b)=>b.delta-a.delta);if(!xs.length){h.innerHTML=empty('Minst två publicerade placeringspassager krävs.');return}const top=xs.slice(0,10).map(x=>({label:x.r.name,value:Math.max(0,x.delta),raw:x.delta,r:x.r}));const max=Math.max(1,...top.map(x=>Math.abs(x.raw)));h.innerHTML=`<div class="gain-list">${top.map(x=>`<button data-open="${esc(x.r.id)}" class="gain-row"><span>${esc(x.label)}</span><div class="gain-axis"><i style="width:${Math.abs(x.raw)/max*100}%" class="${x.raw>=0?'positive':'negative'}"></i></div><strong>${x.raw>=0?'+':''}${x.raw}</strong></button>`).join('')}</div><p class="small muted">Första till sista observerade placering. Positivt = netto framåt.</p>`;bindResultLinks(h)}
  function renderFinishProgress(){
    const h=$('#finish-progression');if(!h)return;
    const threshold=(S.race.nominal_km||0)*2/3;
    const vals=S.filtered.filter(finish).map(r=>{
      const a=placements(r).filter(x=>num(x.st.km));
      const before=a.filter(x=>x.st.km<=threshold).at(-1),last=a.at(-1);
      return before&&last&&before.st.uid!==last.st.uid?{r,delta:before.place-last.place,from:before.st.name,to:last.st.name}:null;
    }).filter(Boolean).sort((a,b)=>b.delta-a.delta);
    const progression=vals.length?
      `<div class="finish-progress-list">${vals.slice(0,10).map((x,i)=>`<button class="mini-result" data-open="${esc(x.r.id)}"><span><b>${i+1}</b> ${esc(x.r.name)}</span><strong>${x.delta>=0?'+':''}${x.delta} platser</strong><small>${esc(x.from)} → ${esc(x.to)}</small></button>`).join('')}</div>`
      :empty('Tillräckliga placeringsankare i sista tredjedelen saknas.');
    h.innerHTML=progression+`<p class="small muted">Snabbaste avslutningen visas separat i nästa kort.</p>`;
    bindResultLinks(h);
  }
  function renderLastSegmentStrength(){
    const h=$('#last-segment-strength');if(!h)return;
    // D11 is based on a runner's last real positive TIME pair and the median
    // for precisely that segment; no unverified physical distance is required.
    const refs=segmentStats(S.filtered),lastStrength=[];
    for(const r of S.filtered.filter(finish)){
      const p=pairs(r).at(-1);if(!p||p.seconds<=0)continue;
      const stat=refs.find(x=>x.index===p.index);
      if(!stat||stat.n<5||!num(stat.median))continue;
      lastStrength.push({r,p,n:stat.n,reference:stat.median,relative:100*stat.median/p.seconds});
    }
    lastStrength.sort((a,b)=>b.relative-a.relative);
    const columns=['F','M'].map(sex=>{const rows=lastStrength.filter(x=>analyticalSex(x.r)===sex).slice(0,5);return `<section><h4>${sex==='F'?'Kvinnor':'Män'}</h4>${rows.length?`<div class="finish-progress-list">${rows.map((x,i)=>`<button class="mini-result" data-open="${esc(x.r.id)}"><span><b>${i+1}</b> ${esc(x.r.name)}</span><strong>${x.relative.toFixed(0)} %</strong><small>${esc(x.p.from.name)} → ${esc(x.p.to.name)} · ${time(x.p.seconds)} · median ${time(x.reference)} · n=${x.n}</small></button>`).join('')}</div>`:empty('Inga källsäkra observationer.')}</section>`}).join('');
    h.innerHTML=lastStrength.length?`<p class="small muted">100 = median för samma observerade segment i aktuellt urval. Över 100 = snabbare. Ingen GPS-fart eller imputerad passage används.</p><div class="strength-pair">${columns}</div>`:empty('Minst fem verkliga segmentpar på respektive löpares sista verifierade delsträcka krävs för relativ styrka.');
    bindResultLinks(h);
  }
  function renderSegmentSex(){const h=$('#segment-sex-extra');if(!h)return;const s=currentSeg();if(!s){h.innerHTML=empty();return}const all=segmentStats(S.filtered),shown=modeDistributionSegments(all),label=S.segmentSeriesMode==='F'?'Kvinnor':S.segmentSeriesMode==='M'?'Män':'Alla';bandChart(h,shown,{dataAttribute:'data-extra-segment',domainPoints:all,showStart:true,startValue:0,startExplanation:'0:00 – ingen tid har förflutit vid start',note:`Start visar 0:00 innan första delsträckan, inte en beräknad median. ${label}; vald delsträcka ${s.from.name} → ${s.to.name}. Median visas från n≥5, Q25–Q75 från n≥10.`})}
  function renderCheckpointSpread(){
    const h=$('#checkpoint-spread');if(!h)return;
    const cps=S.race.stations.filter(s=>s.is_analysis_boundary&&num(s.km)).sort((a,b)=>a.sort-b.sort||a.km-b.km).slice(1),rows=segmentModeRows(S.filtered).filter(finish),allRows=S.filtered.filter(finish);
    const make=(source)=>cps.map((st,i)=>{const d=distribution(source.map(r=>observed(r,st)?.elapsed_seconds).filter(num));return {...d,index:Math.max(0,i-1),label:st.name,title:st.name}});
    bandChart(h,make(rows),{domainPoints:make(allRows),labelClass:'checkpoint-axis-label',note:'Varje kontroll använder sitt eget observerade n; samma personer behöver inte ingå i alla punkter.'})
  }
  function syncSegmentOverlay(){const host=$('#course-map');if(!S.route||!$('svg',host))return;const seg=currentSeg();if(!seg)return;const pts=routePoints(),start=timingToRouteKm(seg.from.km,pts),end=timingToRouteKm(seg.to.km,pts),viewport=mapViewport(host,340),proj=project(pts,viewport.W,viewport.H,20),picked=proj.filter((p,i)=>pts[i][0]>=start&&pts[i][0]<=end);if(picked.length<2)return;const old=$('.segment-route-overlay',host);old?.remove();const ns='http://www.w3.org/2000/svg',path=document.createElementNS(ns,'path');path.setAttribute('d',pathFor(picked));path.setAttribute('class','segment-route-overlay');path.setAttribute('aria-label',`Illustrativ proportionell segmentmarkering ${seg.from.name} till ${seg.to.name}, ingen verifierad kontrollprojektion`);$('svg',host).appendChild(path)}
  function renderCourseIntel(){
    const h=$('#course-intelligence');if(!h)return;
    const fs=S.filtered.filter(finish),dnfs=S.filtered.filter(r=>r.status==='DNF');
    const started=fs.length+dnfs.length+S.filtered.filter(r=>r.status==='DSQ').length;
    const dims=[
      ['EQ Timing-distans',fmtKm(eqTimingKm(S.race))+' km','Originalfält för resultat- och kontrollaxeln'],
      ['Arrangörsdistans',num(S.race.organizer_advertised_km)?fmtKm(S.race.organizer_advertised_km)+' km':'—',num(S.race.organizer_advertised_km)?'Separat källbelagd annonserad distans':'Ingen separat källbelagd uppgift'],
      ['Publika kontroller',S.race.stations.filter(s=>s.is_analysis_boundary).length,'Stationsmetadata, även utan TIME'],
      ['Median sluttid',fs.length>=5?time(median(fs.map(r=>r.finish_seconds))):'—','n='+fs.length],
      ['DNF-andel',started?(100*dnfs.length/started).toFixed(1).replace('.',',')+' %':'—','FINISHED + DNF + DSQ som startnämnare'],
      ['Displayrutt',S.route?fmtKm(S.route.geometry_length_km)+' km':'—',S.route?(S.race.route_status==='participant_track_display_only'?'Verifierat deltagarspår · endast display':'Arrangörens GPX'):'Saknas för upplagan'],
      ['Rå GPX D+',S.route&&num(S.route.raw_positive_gain_m_not_official)?Math.round(S.route.raw_positive_gain_m_not_official)+' m':'—',S.route&&!num(S.route.raw_positive_gain_m_not_official)?'Höjddata saknas i källspåret':'Ej officiell höjdmetrik']
    ];
    const seg=currentSeg();
    let segmentBody=empty('Välj en delsträcka i tabellen för segmentdetaljer.');
    let segmentTitle='Vald delsträcka';
    if(seg){
      const moves=seg.obs.filter(o=>num(o.placeFrom)&&num(o.placeTo)).map(o=>o.placeFrom-o.placeTo);
      const paceKm=wholeCoursePaceKm(S.race);
      const paceValues=paceDistanceSupported(seg)&&num(paceKm)&&paceKm>0
        ?seg.obs.filter(o=>finish(o.r)&&o.seconds>0&&seg.km>0)
          .map(o=>100*(o.r.finish_seconds/paceKm)/(o.seconds/seg.km)).filter(v=>num(v)&&v>0):[];
      const paceMedian=paceValues.length>=5?median(paceValues):null;
      const dnfTimed=dnfs.filter(r=>splitsFor(r.id).some(v=>num(v.elapsed_seconds))).length;
      const details=[
        ['Verkliga tidspar',String(seg.n),'EQ Timing TIME, båda ändankare'],
        ['Segmentmedian',seg.n>=5?time(seg.median):'—','n ≥ 5, endast observerade par'],
        ['Q25–Q75',seg.n>=10?time(seg.q25)+' – '+time(seg.q75):'—','n ≥ 10, inga imputerade passager'],
        ['Pacingindex',num(paceMedian)?paceMedian.toFixed(0):'—',!num(paceKm)?'Helbanedistans skiljer sig mellan källor; index dolt':!paceDistanceSupported(seg)?'Distans ej verifierad; tidsdata behålls':'100 = eget hel-loppssnitt · n='+paceValues.length],
        ['Median placeringsrörelse',moves.length>=5?(median(moves)>0?'+':'')+median(moves).toFixed(0):'—','Kräver minst fem verkliga placeringspar · n='+moves.length],
        ['DNF: sista kontroll',dnfs.length?(dnfTimed?'Se observerade passager':'Okänt'):'—',dnfs.length?dnfTimed+' av '+dnfs.length+' DNF med offentlig TIME; ej faktisk avbrottsplats':'Inga DNF i urvalet'],
        ['Segmentets D+/D−','Ej verifierad','Timingkontroller är inte GPX-höjdankare']
      ];
      segmentTitle=`Vald delsträcka: ${esc(seg.from.name)} → ${esc(seg.to.name)}`;
      segmentBody=`<div class="dimension-grid">${details.map(d=>`<article><span>${esc(d[0])}</span><strong>${esc(d[1])}</strong><small>${esc(d[2])}</small></article>`).join('')}</div><p class="small muted">Segmentanalysen följer tabellens val. Kartans markering är en illustrativ projektion på godkänd GPX, inte en uppmätt checkpointposition.</p>`;
    }
    h.innerHTML=`<article class="panel course-intel-card"><div class="panel-heading"><div><p class="eyebrow">COURSE INTELLIGENCE</p><h3>Banans dimensioner</h3></div><button class="info" data-help-extra="courseintel">i</button></div><div class="dimension-grid">${dims.map(d=>`<article><span>${esc(d[0])}</span><strong>${esc(d[1])}</strong><small>${esc(d[2])}</small></article>`).join('')}</div><p class="small muted">Dimensionerna redovisas separat och vägs inte ihop till något svårighetsbetyg.</p></article><article class="panel course-intel-card"><div class="panel-heading"><div><p class="eyebrow">DELSTRÄCKA</p><h3>${segmentTitle}</h3></div><button class="info" data-help-extra="courseintel">i</button></div>${segmentBody}<p class="small muted">Inga avbrottsplatser eller höjdmeter per segment uppskattas utan källa.</p></article>`;
  }
  function renderMapHistory(){const h=$('#map-history');if(!h)return;if(S.route){h.innerHTML=`<div class="route-version-card"><strong>${S.family==='ultra85'?'2026':'2025–2026'}</strong><span>${esc(S.route.type||'OFFICIAL_ORGANIZER')}</span><b>${fmtKm(S.route.geometry_length_km)} km</b><small>${esc(S.route.evidence_note||'Officiell arrangörsgeometri')}</small></div><p class="small muted">Äldre år överlagras inte eftersom en lokal publicerbar ruttfil saknas eller ännu inte är promoted till jämförbar CourseVersion.</p>`}else h.innerHTML=empty('Den valda upplagan saknar verifierad lokal rutt. En modern rutt lånas inte bakåt.')}
  function historyEditions(){return S.boot.editions.filter(e=>e.family===S.family).sort((a,b)=>a.year-b.year)}
  function renderHistoryPerformance(){const h=$('#history-performance');if(!h)return;const ed=historyEditions().filter(e=>num(e.median_seconds));if(!ed.length){h.innerHTML=empty();return}const min=Math.min(...ed.map(e=>e.median_seconds)),max=Math.max(...ed.map(e=>e.median_seconds)),span=Math.max(1,max-min);h.innerHTML=`<div class="edition-dotplot">${ed.map(e=>`<button type="button" data-year-extra="${e.year}" style="--pos:${100*(e.median_seconds-min)/span}%"><span>${e.year}</span><i></i><strong>${time(e.median_seconds)}</strong></button>`).join('')}</div><p class="small muted">Punkterna är separata upplagemedianer. Ingen linje dras mellan år utan verifierad whole-course-grupp.</p>`;$$('[data-year-extra]',h).forEach(b=>b.addEventListener('click',()=>{S.year=+b.dataset.yearExtra;loadRace().then(()=>$('#race-context').scrollIntoView())}))}
  async function loadRaceMini(ed){try{return await fetch(`data/races/${encodeURIComponent(ed.race_key)}.json`).then(r=>r.ok?r.json():null)}catch{return null}}
  let coveragePromise=null;
  function loadCoverage(){
    if(!coveragePromise)coveragePromise=fetch('data/coverage.json').then(response=>{
      if(!response.ok)throw Error('Källtäckningen kunde inte läsas');
      return response.json();
    }).catch(()=>null);
    return coveragePromise;
  }
  async function renderSexHistory(){
    const host=$('#history-sex');
    if(!host)return;
    const family=S.family;
    host.innerHTML='<p class="muted small">Laddar källstödd könsfördelning…</p>';
    const coverage=await loadCoverage();
    if(S.family!==family)return;
    if(!coverage){host.innerHTML=empty('Källtäckningsfilen kunde inte läsas.');return}
    const rows=coverage.filter(e=>e.family===family).sort((a,b)=>a.year-b.year).map(e=>{
      const known=e.sex_known,coverageRate=e.results?known/e.results:0;
      return {...e,coverageRate,pf:known&&coverageRate>=.8?100*e.sex_f/known:null};
    });
    host.innerHTML=rows.some(e=>num(e.pf))?`<div class="sex-history-bars">${rows.map(e=>`<div><span>${e.year}</span><div class="stack">${num(e.pf)?`<i class="women" style="width:${e.pf}%"></i><i class="men" style="width:${100-e.pf}%"></i>`:''}</div><strong>${num(e.pf)?e.pf.toFixed(0)+' % K':'—'}</strong><small>${e.sex_f} K · ${e.sex_m} M · ${e.results-e.sex_known} utan kön · täckning ${(100*e.coverageRate).toFixed(0)} %${e.coverageRate<.8?' (trend dold under 80 %)':''}</small></div>`).join('')}</div>`:empty('Inget år når minst 80 % källstödd könstäckning.');
  }

  function renderFingerprint(){const h=$('#history-fingerprint');if(!h)return;const ed=historyEditions(),maxR=Math.max(1,...ed.map(e=>e.results)),maxT=Math.max(1,...ed.map(e=>e.timing_stations||0)),maxM=Math.max(1,...ed.map(e=>e.median_seconds||0)),maxD=Math.max(1,...ed.map(e=>e.results?100*e.dnf/e.results:0));h.innerHTML=`<div class="finger-table"><div class="finger-head"><b>År</b><b>Volym</b><b>Stationer</b><b>Median</b><b>DNF</b></div>${ed.map(e=>{const d=e.results?100*e.dnf/e.results:0;return `<div><b>${e.year}</b>${[[e.results/maxR,e.results],[ (e.timing_stations||0)/maxT,e.timing_stations||0],[ (e.median_seconds||0)/maxM,time(e.median_seconds)],[d/maxD,d.toFixed(1)+' %']].map(([p,v])=>`<span><i style="--v:${Math.max(0,p)*100}%"></i><em>${esc(v)}</em></span>`).join('')}</div>`}).join('')}</div>`}
  async function renderProvenance(){
    const host=$('#course-provenance');
    if(!host)return;
    const family=S.family;
    host.innerHTML='<p class="muted small">Laddar banversioner och källor…</p>';
    const coverage=await loadCoverage();
    if(S.family!==family)return;
    if(!coverage){host.innerHTML=empty('Proveniensfilen kunde inte läsas.');return}
    const rows=coverage.filter(e=>e.family===family).sort((a,b)=>b.year-a.year);
    host.innerHTML=`<p class="small muted">Svep tabellen i sidled på smala skärmar för distanskällor, källfil, SHA-256 och verifieringsreservation.</p><div class="table-scroll"><table><thead><tr><th>Familj/år</th><th>Arrangör-km</th><th>EQ Timing-km</th><th>GPX-km</th><th>CourseVersion</th><th>Whole-course-grupp</th><th>Ruttstatus</th><th>Källtyp</th><th>Källfil</th><th>SHA-256</th><th>Publik displayrutt</th><th>Verifieringsreservation</th></tr></thead><tbody>${rows.map(e=>`<tr><td>${esc(e.family)} · ${e.year}</td><td>${fmtKm(e.organizer_advertised_km)}</td><td>${fmtKm(eqTimingKm(e))}</td><td>${fmtKm(e.route_geometry_km)}</td><td>${esc(e.course_version||'Ej verifierad')}</td><td>${esc(e.whole_course_comparison_group||'Ej verifierad')}</td><td>${esc(e.route_status||'none')}</td><td>${esc(e.route_source_type||'—')}</td><td>${esc(e.route_source_filename||'—')}</td><td><code>${esc(e.route_sha256||'—')}</code></td><td>${e.route_file?'Sanerad GPX-displayrutt · '+esc(e.route_file):'Ingen publicerad historisk GPX'}</td><td>${esc(e.distance_evidence_note||e.route_evidence_note||'Ruttens geometri är inte verifierad för denna upplaga.')}${!e.whole_course_comparison_group?' · Helbaneprestation kan inte seriejämföras.':''}</td></tr>`).join('')}</tbody></table></div><p class="small muted">EQ Timing-distans, källbelagd arrangörsdistans och GPX-geometri redovisas separat. 2025/2026-arrangörsrutten för 21/43 km är ett uttryckligt projektantagande; äldre års geometri och helbaneprestation är inte automatiskt jämförbara. Rå deltagar-GPX publiceras inte.</p>`;
  }

  function renderGroupTable(){
    const h=$('#group-table');if(!h)return;
    const rows=S.filtered,groups=[];
    const add=(kind,name,matching)=>{const rs=rows.filter(matching),fs=rs.filter(finish);groups.push({kind,name,n:rs.length,finish:fs.length,med:fs.length>=5?median(fs.map(r=>r.finish_seconds)):null})};
    for(const sex of ['F','M','other'])add('Kön',sex==='F'?'Kvinnor':sex==='M'?'Män':'Kön saknas',r=>sex==='other'?!['F','M'].includes(analyticalSex(r)):analyticalSex(r)===sex);
    for(const name of Object.keys(collections(rows.map(r=>r.class_name).filter(Boolean))).sort((a,b)=>a.localeCompare(b,'sv')))add('Klass',name,r=>r.class_name===name);
    const ages=rows.map(r=>r.age).filter(a=>num(a)&&a>=0&&a<=120);
    if(ages.length)for(let a=Math.floor(Math.min(...ages)/5)*5;a<=Math.max(...ages);a+=5)add('Exakt ålder',`${a}–${a+4}`,r=>num(r.age)&&r.age>=a&&r.age<a+5);
    for(const name of Object.keys(collections(rows.map(r=>r.club).filter(Boolean))).sort((a,b)=>a.localeCompare(b,'sv')))add('Klubb/ort',name,r=>r.club===name);
    const per=25,pages=Math.max(1,Math.ceil(groups.length/per));S.groupPage=Math.max(0,Math.min(S.groupPage||0,pages-1));
    h.innerHTML=`<div class="table-scroll"><table><thead><tr><th>Typ</th><th>Grupp</th><th>Resultat</th><th>Fullföljare</th><th>Median*</th></tr></thead><tbody>${groups.slice(S.groupPage*per,(S.groupPage+1)*per).map(g=>`<tr><td>${esc(g.kind)}</td><td>${esc(g.name)}</td><td>${g.n}</td><td>${g.finish}</td><td>${time(g.med)}</td></tr>`).join('')}</tbody></table></div><div class="pagination"><button type="button" id="group-prev" ${S.groupPage===0?'disabled':''}>← Föregående</button><span>Sida ${S.groupPage+1} / ${pages} · ${groups.length} grupper</span><button type="button" id="group-next" ${S.groupPage===pages-1?'disabled':''}>Nästa →</button></div><p class="small muted">* Median visas först vid minst fem fullföljare. Åldersgrupper innehåller endast publicerad exakt ålder.</p>`;
    $('#group-prev').addEventListener('click',()=>{S.groupPage--;renderGroupTable()});
    $('#group-next').addEventListener('click',()=>{S.groupPage++;renderGroupTable()});
  }
  async function renderCoverage(){
    const host=$('#coverage-table');
    if(!host)return;
    const family=S.family;
    host.innerHTML='<p class="muted small">Laddar täckningsinventering…</p>';
    const coverage=await loadCoverage();
    if(S.family!==family)return;
    if(!coverage){host.innerHTML=empty('Källtäckningsfilen kunde inte läsas.');return}
    const rows=coverage.filter(e=>e.family===family).sort((a,b)=>b.year-a.year);
    const pct=(count,total)=>total?(100*count/total).toFixed(0)+' %':'—';
    host.innerHTML=`<p class="small muted">Maskinläsbar export: <a href="data/coverage.json" download>coverage.json ↗</a>. Täckning räknas på källfält, inte på antaganden.</p><div class="table-scroll"><table><thead><tr><th>År</th><th>Resultat</th><th>Fullföljare</th><th>TIME</th><th>Stationer</th><th>Status</th><th>Kön</th><th>Ålder</th><th>Klass</th><th>Klubb</th><th>Rutt</th><th>CourseVersion</th></tr></thead><tbody>${rows.map(e=>`<tr><td>${e.year}</td><td>${format(e.results)}</td><td>${format(e.finishers)}</td><td>${format(e.split_observations)}</td><td>${e.timing_stations}</td><td>${pct(e.status_known,e.results)}</td><td>${pct(e.sex_known,e.results)}</td><td>${pct(e.age_known,e.results)}</td><td>${pct(e.class_known,e.results)}</td><td>${pct(e.club_known,e.results)}</td><td>${e.route_file?'Ja · '+esc(e.route_status):'Nej'}</td><td>${esc(e.course_version||'ej verifierad')}</td></tr>`).join('')}</tbody></table></div>`;
  }

  extraHelp.pacing='Pacingindex = 100 × (egen sluttid / källsäker helbanedistans) / (egen segmenttid / kontrakterad segmentdistans). Över 100 betyder snabbare än löparens eget hel-loppssnitt. Indexet döljs när källorna anger olika helbanedistans och årsspecifik ruttgeometri saknas.';
  extraHelp.sexpace='Gemensam tidsaxel visar separata segmentmedianer för källstödda kvinnor och män. Varje punkt kräver minst fem exakta observationer i könsgruppen; en saknad punkt bryter linjen.';
  extraHelp.groups='Välj högst fem publicerade klasser. Gruppkurvan är median av individuella pacingindex per segment; minst fem exakta observationer krävs per klass och punkt.';
  function renderPacingIndex(){
    const host=$('#segment-pacing');
    if(!host)return;
    const nominal=wholeCoursePaceKm(S.race);
    if(!num(nominal)){host.innerHTML=empty('Pacingindex visas inte eftersom EQ Timing och arrangörskällan anger olika helbanedistans utan godkänd årsspecifik GPX. Observerade segmenttider är fortsatt tillgängliga.');return}
    const base=segmentStats(S.filtered),rows=base.map(s=>{
      const values=s.obs.filter(o=>(S.segmentSeriesMode==='all'||analyticalSex(o.r)===S.segmentSeriesMode)&&paceDistanceSupported(s)&&finish(o.r)&&num(o.seconds)&&o.seconds>0&&num(s.km)&&s.km>0)
        .map(o=>100*(o.r.finish_seconds/nominal)/(o.seconds/s.km)).filter(v=>num(v)&&v>0),d=distribution(values);
      return {...s,n:d.n,median:d.median,q25:d.q25,q75:d.q75,label:s.to.name};
    });
    const domain=base.map(s=>{const values=s.obs.filter(o=>paceDistanceSupported(s)&&finish(o.r)&&num(o.seconds)&&o.seconds>0&&num(s.km)&&s.km>0).map(o=>100*(o.r.finish_seconds/nominal)/(o.seconds/s.km)).filter(v=>num(v)&&v>0),d=distribution(values);return {...s,...d,label:s.to.name}});
    bandChart(host,rows,{domainPoints:domain,legacyDataAttribute:'data-pacing-segment',valueLabel:v=>num(v)?v.toFixed(0)+' %':'—',minValue:Math.min(90,...domain.map(s=>s.q25??s.median).filter(num)),referenceValue:100,referenceLabel:'100 % · hela loppet',showStart:true,startValue:100,startExplanation:'referensnivå för hela loppet, inte en uppmätt segmentfart',note:'Startpunkten visar bara referensnivån, inte en uppmätt segmenttid. Den streckade 100 %-linjen markerar löparens eget hel-loppssnitt; över 100 % betyder högre fart på delsträckan än det snittet.'});
  }
  function renderSexSeries(){
    /* Vald delsträcka använder samma radioväljare i renderSegmentSex. */
  }
  function renderClassSeries(){
    const host=$('#segment-groups'),segments=segmentStats(S.filtered);
    if(!host||!segments.length)return;
    const classes=Object.entries(collections(S.filtered.map(r=>r.class_name).filter(Boolean))).sort((a,b)=>b[1]-a[1]).slice(0,8).map(x=>x[0]);
    if(!classes.length)return;
    if(!S.extraClassSelection||![...S.extraClassSelection].some(name=>classes.includes(name)))S.extraClassSelection=new Set(classes.slice(0,3));
    const colors=['#315f41','#af8740','#6b7f9e','#a86659','#76639a','#638b7c','#9d7186','#697c43'];
    const series=classes.map((name,i)=>({name,color:colors[i],values:segments.map(s=>{
      const paceKm=wholeCoursePaceKm(S.race);
      const indices=s.obs.filter(o=>paceDistanceSupported(s)&&o.r.class_name===name&&finish(o.r)&&num(paceKm)&&paceKm>0)
        .map(o=>100*(o.r.finish_seconds/paceKm)/(o.seconds/s.km)).filter(v=>num(v)&&v>0);
      return {n:indices.length,value:indices.length>=5?median(indices):null};
    })}));
    const all=series.flatMap(s=>s.values.map(v=>v.value)).filter(num);
    if(!all.length)return;
    const W=700,H=230,P=52,lo=Math.min(90,...all),hi=Math.max(110,...all),step=(W-2*P)/Math.max(1,segments.length);
    const x=i=>P+(i+.5)*step,y=v=>H-P-(v-lo)/Math.max(1,hi-lo)*(H-2*P);
    const body=chartYTicks(P,W-P,P,H-P,lo,hi,v=>v.toFixed(0)+' %')+`<line class="axis" x1="${P}" x2="${W-P}" y1="${y(100)}" y2="${y(100)}" stroke-dasharray="4 3"/>`+series.filter(s=>S.extraClassSelection.has(s.name)).map(s=>{
      let path='',previous=false;
      const dots=s.values.map((v,i)=>{
        if(!num(v.value)){previous=false;return ''}
        path+=`${previous?'L':'M'}${x(i)},${y(v.value)} `;previous=true;
        return `<circle data-extra-segment="${segments[i].index}" tabindex="0" role="button" aria-pressed="${segments[i].index===S.selectedSegment}" aria-label="Välj ${html(segments[i].from.name)} till ${html(segments[i].to.name)}" cx="${x(i)}" cy="${y(v.value)}" r="${segments[i].index===S.selectedSegment?6:4}" fill="${s.color}"><title>${html(s.name)} · ${html(segments[i].to.name)} · ${v.value.toFixed(1)} · n=${v.n}</title></circle>`;
      }).join('');
      return `<path d="${path}" fill="none" stroke="${s.color}" stroke-width="2.5"/>${dots}`;
    }).join('');
    host.innerHTML=`<p class="small muted">Välj två till fem publicerade klasser. Urvalet styr exakt vilka klassnamn som ritas; varje kurva är medianen av individuellt pacingindex per segment.</p><div class="series-choices" role="group" aria-label="Välj klasser att jämföra">${series.map(s=>`<label><input type="checkbox" data-class-series="${html(s.name)}" ${S.extraClassSelection.has(s.name)?'checked':''} ${S.extraClassSelection.size>=5&&!S.extraClassSelection.has(s.name)?'disabled':''}><i style="background:${s.color}"></i>${html(s.name)}</label>`).join('')}</div>${svg(W,H,body,'Klassers pacingindex på gemensam segmentaxel')}<p class="small muted">Streckad 100 %-linje = eget loppmedel. Varje punkt kräver fem exakta observationer i klassen; saknad punkt bryter linjen.</p>`;
    $$('[data-class-series]',host).forEach(input=>input.addEventListener('change',()=>{
      if(input.checked&&S.extraClassSelection.size<5)S.extraClassSelection.add(input.dataset.classSeries);
      else if(!input.checked)S.extraClassSelection.delete(input.dataset.classSeries);
      renderClassSeries();
    }));
  }
  function renderSegments(){renderPacingIndex();renderSegmentSex();renderSexSeries();renderClassSeries();renderCheckpointSpread();syncSegmentOverlay();renderCourseIntel()}
  function renderFiltered(){renderSexCompletion();renderGoal();renderAge();renderClub();renderPlacementGain();renderFinishProgress();renderLastSegmentStrength();renderSegments();renderCourseIntel();renderGroupTable()}
  function wire(){if(wired)return;wired=true;document.addEventListener('click',e=>{const info=e.target.closest('[data-help-extra]');if(info){showHelp(info.closest('.panel')?.querySelector('h3')?.textContent,extraHelp[info.dataset.helpExtra]);return}const linked=e.target.closest('[data-extra-segment]');if(linked){$('#segment-table [data-select-segment="'+linked.dataset.extraSegment+'"]')?.click();return}if(e.target.closest('[data-segment],[data-select-segment]'))setTimeout(renderSegments,0)});document.addEventListener('change',e=>{if(e.target.matches('#podium-segment-start'))setTimeout(renderSegments,0)});document.addEventListener('click',e=>{if(e.target.matches('#goal-placement-run'))renderGoal()});document.addEventListener('keydown',e=>{if(e.target.matches('[data-extra-segment]')&&(e.key==='Enter'||e.key===' ')){e.preventDefault();$('#segment-table [data-select-segment="'+e.target.dataset.extraSegment+'"]')?.click();return}if(e.target.matches('#goal-placement-time')&&e.key==='Enter')renderGoal()})}
  function renderAll(){ensurePanels();wire();renderFiltered();renderCourseIntel();renderMapHistory();renderHistoryPerformance();renderSexHistory();renderFingerprint();renderProvenance();renderCoverage()}
  return {renderAll,renderFiltered,renderSegments};
})();

init();
})();
