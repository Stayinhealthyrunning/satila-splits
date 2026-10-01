/* Sätila Splits first draft – observed EQ Timing analysis, capability-driven UI. */
(()=>{'use strict';
const $=(s,root=document)=>root.querySelector(s),$$=(s,root=document)=>Array.from(root.querySelectorAll(s));
const html=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const format=n=>Number(n??0).toLocaleString('sv-SE');
const num=n=>typeof n==='number'&&Number.isFinite(n);
const median=a=>{a=a.filter(num).sort((x,y)=>x-y);let n=a.length;return n?(n%2?a[(n-1)/2]:(a[n/2-1]+a[n/2])/2):null};
const quant=(a,p)=>{a=a.filter(num).sort((x,y)=>x-y);if(!a.length)return null;const v=(a.length-1)*p,i=Math.floor(v),f=v-i;return a[i]+(a[Math.min(a.length-1,i+1)]-a[i])*f};
const time=s=>!num(s)||s<0?'—':(()=>{let n=Math.round(s),h=Math.floor(n/3600),m=Math.floor(n%3600/60),sec=String(n%60).padStart(2,'0');return h?`${h}:${String(m).padStart(2,'0')}:${sec}`:`${m}:${sec}`})();
const signed=s=>!num(s)?'—':(s>0?'+':'−')+time(Math.abs(s));
const pace=(sec,km,unit='pace')=>!num(sec)||!num(km)||km<=0?'—':unit==='speed'?(3600*km/sec).toFixed(2).replace('.',',')+' km/h':time(sec/km)+'/km';
const fmtKm=n=>num(n)?n.toFixed(1).replace('.',','):'—';
const readCache=(key,other=[])=>{try{let j=JSON.parse(localStorage.getItem(key));return Array.isArray(j)?j:other}catch{return other}};
const key='satila-splits-favorites-v1';let S={boot:null,family:'ultra85',year:null,race:null,route:null,routeByFamily:{},filtered:[],page:0,sort:'place',q:'',sex:'all',status:'all',className:'all',club:'',unit:'pace',finishSex:new Set(['F','M']),selectedSegment:0,compare:[],mapDuel:[],favorites:readCache(key),searchIndex:-1,loading:0,courseD:null,duelD:null};
const HELP={finish:'Officiella sluttider för FINISHED. Samma 15-minutersbin används för alla könsserier. DNS, DNF och UNKNOWN ingår inte i histogrammet. Kvinna/man visas endast för källstödd uppgift.',percentiles:'P10, P25, P50, P75 och P90 är kvantiler av giltiga sluttider hos fullföljare i det aktuella fälturvalet. Median visas först vid n ≥ 5. Inga saknade tider blir noll.',podium:'Placering bland kvinnor respektive män bestäms av giltiga officiella målgångar eller positiva segmenttider mellan två exakta observationer. Bilder från sociala medier används inte; initialavatarer visas.',groups:'Kön, klass, ålder och klubb/ort härleds enbart från publicerade EQ Timing-fält. Ett filtrerat urval påverkar fältstatistik men inte sökfunktionen.',status:'FINISHED kräver en giltig, positiv tid vid publicerad målstation. DNF, DNS och DSQ följer källflaggor. Okänd status förblir okänd.',flow:'Visar antal verkliga TIME-registreringar vid varje publik kontroll för urvalets löpare. Trivial Start=100 % utelämnas. En saknad passage innebär inte i sig DNF.',placement:'Endast FINISHED med verklig sluttid och publicerad totalplacering. Klick på en punkt för att öppna löparprofilen.',dnf:'DNF knyts till sin sista exakta publika registrering. En brytare utan säker passering redovisas separat och får ingen antagen brytpunkt.',standouts:'Ovanliga prestationer beräknas inom en edition från två verkliga tidtagningspassager. Minst fem giltiga observationer krävs där en gruppmedian används. Ingen personidentitet mellan år antas.',segments:'En segmenttid kräver två verkliga och tidsmässigt positiva passager. Start=0 används före första observerade kontroll. Delsträckans distans kommer från källans timingaxel, inte från GPS-vägens längd. Median n ≥ 5; Q25–Q75 n ≥ 10.',course:'Arrangörens officiella GPX används som ban-/displaygeometri. 2025 års 21/43 km-rutter antas återanvändas utan ändring 2026. Äldre upplagor lånar inte denna rutt. Kartposition mellan verifierade ändankare är illustrativ; rå D+ är inte officiell höjdmetrik.',plan:'Måltiden fördelas efter medianen av exakta segmenttidsandelar (segmenttid / sluttid) inom vald edition och kohort, minst fem per segment. Saknas historiskt underlag används explicit timingdistans som märkt fallback. Värdena normaliseras till exakt hela måltiden; planen är en pacingreferens, inte prognos.',history:'Deltagarantal, fullföljare och status kan visas för alla källstödda år. Enskilda års mediantider redovisas separat men kopplas inte till en gemensam utvecklingskurva utan verifierad whole-course-jämförbarhet. År 2020 har ingen importkälla i arkivet.'};
const famLabel=id=>({ultra85:'85 km',trail43:'43 km',trail22:'22 km'}[id]||id);
const finish=r=>r.status==='FINISHED'&&num(r.finish_seconds)&&r.finish_seconds>0;
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
function subset(){let list=records().filter(r=>(S.sex==='all'||r.sex===S.sex)&&(S.status==='all'||r.status===S.status)&&(S.className==='all'||r.class_name===S.className)&&(!S.club||String(r.club||'').toLocaleLowerCase('sv').includes(S.club.toLocaleLowerCase('sv'))));S.filtered=list;$('#filter-count').textContent=`${format(list.length)} av ${format(records().length)} resultat i detta urval. Individuell sök och jämförelse använder hela upplagan.`;return list}
function updateQuery(mode='replace'){let hash=new URLSearchParams(location.hash.includes('=')?location.hash.slice(1):'');hash.set('family',S.family);hash.set('year',S.year);let target='#'+hash.toString();if(location.hash===target)return;if(mode==='push')history.pushState(null,'',target);else if(mode==='replace')history.replaceState(null,'',target);}
function parseQuery(){let params=new URLSearchParams(location.hash.slice(1));let family=params.get('family');if(['ultra85','trail43','trail22'].includes(family))S.family=family;let year=Number(params.get('year'));if(year&&S.boot.editions.some(e=>e.family===S.family&&e.year===year))S.year=year;}
async function init(){try{S.boot=await fetch('data/bootstrap.json').then(r=>{if(!r.ok)throw Error('Katalogen kunde inte läsas ('+r.status+')');return r.json()});parseQuery();if(!S.year)S.year=Math.max(...S.boot.editions.filter(e=>e.family===S.family).map(e=>e.year));ensureMapDuelControls();bind();await loadRace();const nextHash=new URLSearchParams(location.hash.slice(1)).get('section');if(nextHash)document.getElementById(nextHash)?.scrollIntoView();else if(!location.hash)scrollTo(0,0);}catch(err){$('#race-title').textContent='Källmaterialet kunde inte laddas';$('#race-subtitle').textContent=err.message;console.error(err);}}
async function loadRace(historyMode='replace'){let id=++S.loading;let ed=S.boot.editions.find(e=>e.family===S.family&&e.year===S.year);if(!ed)return;$('#race-title').textContent=`${famLabel(S.family)} · ${S.year}`;$('#race-subtitle').textContent=ed.label+' · '+ed.date;$('#source-indicator').textContent='Hämtar publicerade EQ-data…';let race;try{let req=await fetch(`data/races/${encodeURIComponent(ed.race_key)}.json`);if(!req.ok)throw Error('Detta lopp saknar datafil ('+req.status+')');race=await req.json();}catch(err){if(id!==S.loading)return;S.race=null;S.route=null;$('#source-indicator').textContent='Kunde inte hämta tävlingsdata: '+err.message;$('#source-indicator').setAttribute('role','alert');$('#race-subtitle').textContent='Upplagan kan inte visas just nu. Välj ett annat år eller försök igen.';$('#segment-table tbody').innerHTML='';$('#results-table tbody').innerHTML='';return;}if(id!==S.loading)return;$('#source-indicator').removeAttribute('role');S.race=race;S._splits=null;S._distanceCapability=null;buildSplitIndex();S.page=0;S.selectedSegment=0;S.courseD=null;S.sex='all';S.status='all';S.className='all';S.club='';S.compare=[];S.mapDuel=[];S.selectedClubs=null;document.querySelectorAll('[data-family]').forEach(b=>{b.classList.toggle('selected',b.dataset.family===S.family);b.setAttribute('aria-pressed',String(b.dataset.family===S.family))});$('#year-select').innerHTML=S.boot.editions.filter(e=>e.family===S.family).map(e=>`<option value="${e.year}" ${e.year===S.year?'selected':''}>${e.year} · ${html(e.nominal_km)} km</option>`).join('');$('#source-indicator').textContent='Verifierat EQ Timing · '+race.stations.length+' stationer';$('#official-source').href=ed.source_url;$('#scope-status').textContent=`${format(ed.results)} resultat · ${format(ed.finishers)} målgångar · ${format(ed.split_observations)} tidspassager`;
$('#sex-filter').value='all';$('#status-filter').value='all';$('#club-filter').value='';$('#class-filter').innerHTML='<option value="all">Alla klasser</option>'+Array.from(new Set(records().map(r=>r.class_name).filter(Boolean))).sort((a,b)=>a.localeCompare(b,'sv')).map(k=>`<option value="${html(k)}">${html(k)}</option>`).join('');S.route=null;const source=ed.route_file;if(source){try{S.route=await fetch('data/'+source).then(r=>r.ok?r.json():null)}catch{S.route=null}}if(id!==S.loading)return;$('#course-source').textContent=S.route?`Officiell arrangörsrutt ${S.route.edition_references.join('–')} · GPX-displaylängd ${fmtKm(S.route.geometry_length_km)} km · 2025/2026 återanvändning som arbetsantagande.`:'Ingen lokal geometri verifierad för denna historiska upplaga. Detaljerad karta och illustrativ Replay visas inte från ett annat års bana.';const target=Math.round((ed.nominal_km||43)*10*60);$('#target-time').value=time(target);if(target<3600)$('#target-time').value='02:30:00';const goalPlacement=$('#goal-placement-time');if(goalPlacement)goalPlacement.value='';updateQuery(historyMode);renderAll();}
function renderAll(){subset();renderKpis();renderOverview();renderCumulativeFinish();renderClassDetails();renderDynamics();renderSegments();renderCourse();renderHistory();renderResults();renderFavorites();renderCompareChips();renderMapDuelChips();renderSearchSuggestions();const version=S.loading;clearTimeout(S._extraTimer);S._extraTimer=setTimeout(()=>{if(version!==S.loading)return;try{window.SatilaExtras?.renderAll?.()}catch(err){console.error('Sätila analytics extension:',err)}},100);}
function rerenderFilter(){S.page=0;subset();renderKpis();renderOverview();renderCumulativeFinish();renderClassDetails();renderDynamics();renderSegments();renderResults();const version=S.loading;clearTimeout(S._extraTimer);S._extraTimer=setTimeout(()=>{if(version!==S.loading)return;try{window.SatilaExtras?.renderFiltered?.()}catch(err){console.error('Sätila analytics filter:',err)}},50);}
function setFamily(v){if(v===S.family)return;S.family=v;S.year=Math.max(...S.boot.editions.filter(e=>e.family===v).map(e=>e.year));loadRace('push').catch(console.error)}
function bind(){$$('[data-family]').forEach(el=>el.addEventListener('click',()=>setFamily(el.dataset.family)));$('#year-select').addEventListener('change',e=>{S.year=+e.target.value;loadRace('push').catch(console.error)});$('#open-picker').addEventListener('click',()=>$('#race-context').scrollIntoView());$('#menu-toggle').addEventListener('click',()=>{let n=$('.primary-nav'),a=n.classList.toggle('open');$('#menu-toggle').setAttribute('aria-expanded',String(a))});$$('.primary-nav a').forEach(a=>a.addEventListener('click',()=>{$('.primary-nav').classList.remove('open');$('#menu-toggle').setAttribute('aria-expanded','false')}));document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('.primary-nav').classList.contains('open')){$('.primary-nav').classList.remove('open');$('#menu-toggle').setAttribute('aria-expanded','false');$('#menu-toggle').focus()}});
for(const [id,k] of [['sex-filter','sex'],['status-filter','status'],['class-filter','className']])$('#'+id).addEventListener('change',e=>{S[k]=e.target.value;rerenderFilter()});$('#club-filter').addEventListener('input',e=>{S.club=e.target.value;rerenderFilter()});$('#speed-unit').addEventListener('change',e=>{S.unit=e.target.value;rerenderFilter();renderProfileIfOpen()});$('#reset-filters').addEventListener('click',()=>{S.sex=S.status=S.className='all';S.club='';for(let k of ['sex','status','class'])$('#'+k+'-filter').value='all';$('#club-filter').value='';rerenderFilter()});$('#results-search').addEventListener('input',e=>{S.q=e.target.value;S.page=0;renderResults()});$('#results-sort').addEventListener('change',e=>{S.sort=e.target.value;S.page=0;renderResults()});$('#page-prev').addEventListener('click',()=>{S.page=Math.max(0,S.page-1);renderResults()});$('#page-next').addEventListener('click',()=>{S.page++;renderResults()});$('#podium-segment').addEventListener('change',e=>{S.selectedSegment=+e.target.value;renderSegmentPodium();renderSegmentTable();renderCourse()});
$('#runner-search').addEventListener('input',renderSearchSuggestions);$('#runner-search').addEventListener('keydown',e=>{let list=$$('.suggestion');if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(!list.length)return;S.searchIndex=(S.searchIndex+(e.key==='ArrowDown'?1:-1)+list.length)%list.length;list.forEach((x,i)=>x.classList.toggle('active',i===S.searchIndex));list[S.searchIndex]?.focus()}else if(e.key==='Enter'&&list.length){e.preventDefault();openProfile(list[Math.max(0,S.searchIndex)].dataset.id)}else if(e.key==='Escape')$('#runner-suggestions').innerHTML=''});$('#clear-compare').addEventListener('click',()=>{S.compare=[];renderCompareChips()});$('#open-compare').addEventListener('click',openCompare);$('#calculate-plan').addEventListener('click',renderPlan);$('#target-time').addEventListener('keydown',e=>{if(e.key==='Enter')renderPlan()});$('#plan-cohort').addEventListener('change',renderPlan);$('#course-fit').addEventListener('click',()=>{S.courseD=null;renderCourseMap()});$$('.info').forEach(el=>el.addEventListener('click',()=>{let id=el.dataset.help;$('#help-title').textContent=el.parentElement?.querySelector('h3')?.textContent||'Metod';$('#help-content').textContent=HELP[id]||'Beskrivning saknas.';$('#help-dialog').showModal()}));$$('[data-close]').forEach(el=>el.addEventListener('click',()=>{const name=el.dataset.close;$('#'+name).close();if(name==='profile-dialog'){const target=S.profileReturnFocus?.isConnected?S.profileReturnFocus:$('#runner-search');target?.focus()}}));$$('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d)d.close()}));$$('.section-nav a').forEach(a=>a.addEventListener('click',()=>{$$('.section-nav a').forEach(x=>x.classList.remove('active'));a.classList.add('active')}));const restoreEditionFromUrl=()=>{let p=new URLSearchParams(location.hash.slice(1));let family=p.get('family'),y=Number(p.get('year'));if(family&&y&&(family!==S.family||y!==S.year)&&S.boot?.editions.some(e=>e.family===family&&e.year===y)){S.family=family;S.year=y;loadRace('none').catch(console.error)}};window.addEventListener('hashchange',restoreEditionFromUrl);window.addEventListener('popstate',restoreEditionFromUrl);}
function renderKpis(){let rows=S.filtered,fs=rows.filter(finish),medianSec=fs.length>=5?median(fs.map(r=>r.finish_seconds)):null,counts=collections(rows.map(r=>r.status)),started=(counts.FINISHED||0)+(counts.DNF||0)+(counts.DSQ||0);let list=[['Publicerade resultat',format(rows.length)],['Startande med känd status',format(started)],['Fullföljare',format(fs.length)],['DNF',format(counts.DNF||0)],['DNS',format(counts.DNS||0)],['DSQ',format(counts.DSQ||0)],['Okänd status',format(counts.UNKNOWN||0)],['Fullföljandegrad',started?(100*fs.length/started).toFixed(1).replace('.',',')+' %':'—'],['Median sluttid',time(medianSec)]];$('#kpis').innerHTML=list.map(([label,v])=>`<article class="kpi"><strong>${html(v)}</strong><span>${html(label)}</span></article>`).join('')+`<p class="small muted kpi-note">Fullföljandegrad: ${fs.length} fullföljare / ${started} med känd startstatus (FINISHED + DNF + DSQ). DNS och okänd status ingår inte i nämnaren. Aktuellt filter: ${rows.length} av ${records().length} publicerade resultat.</p>`;}
function svg(w,h,body,aria){return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${html(aria)}" xmlns="http://www.w3.org/2000/svg">${body}</svg>`}
function empty(why='Tillräckligt källunderlag saknas för denna analys.'){return `<p class="empty">${html(why)}</p>`}
function renderOverview(){let fs=S.filtered.filter(finish);$('#finish-series').innerHTML=[['F','Kvinnor','#507c5b'],['M','Män','#cba055']].map(([key,label,c])=>`<label><input type="checkbox" data-finish-sex="${key}" ${S.finishSex.has(key)?'checked':''}/> <i style="display:inline-block;width:10px;height:10px;background:${c};border-radius:3px"></i>${label}</label>`).join('');$$('[data-finish-sex]').forEach(el=>el.addEventListener('change',e=>{if(e.target.checked)S.finishSex.add(e.target.dataset.finishSex);else S.finishSex.delete(e.target.dataset.finishSex);renderFinishChart()}));renderFinishChart();let xs=fs.map(x=>x.finish_seconds),pcts=[.1,.25,.5,.75,.9];$('#percentile-chart').innerHTML=xs.length>=5?`<div class="bars">${pcts.map((p,i)=>{let v=quant(xs,p);return `<div class="barline" style="grid-template-columns:38px 1fr 64px"><strong>P${p*100}</strong><div class="bar-track"><div class="bar-fill" style="width:${Math.round(p*100)}%;background:${i===2?'#d4a858':'#3e5d3a'}"></div></div><strong>${time(v)}</strong></div>`}).join('')}</div><p class="muted small">n=${fs.length} fullföljare i aktuellt urval.</p>`:empty();$('#overall-podium').innerHTML=podiumPair(fs.filter(r=>r.place!=null).sort((a,b)=>a.place-b.place).map(r=>({r,value:time(r.finish_seconds)})));let counts=collections(fs.map(r=>r.class_name||'Ingen uppgift'));let max=Math.max(1,...Object.values(counts));$('#group-bars').innerHTML=`<div class="bars">${Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,6).map(([label,n])=>`<button class="barline" style="border:0;background:transparent;text-align:left;cursor:pointer" data-class-pick="${html(label)}"><span>${html(label)}</span><span class="bar-track"><span class="bar-fill" style="display:block;width:${n/max*100}%"></span></span><strong>${n}</strong></button>`).join('')}</div>`;$$('[data-class-pick]').forEach(b=>b.addEventListener('click',()=>{let k=b.dataset.classPick;if(![...$('#class-filter').options].some(o=>o.value===k))return;S.className=k;$('#class-filter').value=k;rerenderFilter()}));bindResultLinks($('#overall-podium'));}
function collections(arr){let c={};for(let x of arr)c[x]=(c[x]||0)+1;return c}
function renderFinishChart(){
  const fs=S.filtered.filter(finish),mode=S.finishSex.size===2?'all':S.finishSex.has('F')?'F':'M';
  const controls=$('#finish-series');
  controls.innerHTML=[['all','Alla'],['F','Kvinnor'],['M','Män']].map(([key,label])=>`<button type="button" class="series-button" data-finish-mode="${key}" aria-pressed="${mode===key}">${label}</button>`).join('');
  $$('[data-finish-mode]',controls).forEach(button=>button.addEventListener('click',()=>{S.finishSex=new Set(button.dataset.finishMode==='all'?['F','M']:[button.dataset.finishMode]);renderFinishChart()}));
  if(!fs.length){$('#finish-chart').innerHTML=empty();return}
  const min=Math.floor(Math.min(...fs.map(r=>r.finish_seconds))/900)*900,max=Math.ceil(Math.max(...fs.map(r=>r.finish_seconds))/900)*900;
  if(max-min>900*160){$('#finish-chart').innerHTML=empty('Sluttidsspridningen är mycket stor; välj ett snävare fält.');return}
  const bins=[];for(let start=min;start<=max;start+=900)bins.push({start,women:fs.filter(r=>r.sex==='F'&&r.finish_seconds>=start&&r.finish_seconds<start+900).length,men:fs.filter(r=>r.sex==='M'&&r.finish_seconds>=start&&r.finish_seconds<start+900).length,unk:fs.filter(r=>!['F','M'].includes(r.sex)&&r.finish_seconds>=start&&r.finish_seconds<start+900).length});
  const W=600,H=235,P=34,bw=(W-2*P)/bins.length,peak=Math.max(1,...bins.map(b=>(mode!=='M'?b.women:0)+(mode!=='F'?b.men:0)+(mode==='all'?b.unk:0)));
  const body=`<line class="axis" x1="${P}" y1="205" x2="${W-P}" y2="205"/>`+bins.map((b,i)=>{const x=P+i*bw,w=Math.max(1,bw-1),nw=mode!=='M'?b.women:0,nm=mode!=='F'?b.men:0,nu=mode==='all'?b.unk:0,h1=nw/peak*158,h2=nm/peak*158,h3=nu/peak*158;return `<rect x="${x}" y="${205-h1}" width="${w}" height="${h1}" fill="#507c5b"><title>Kvinnor ${nw} · ${time(b.start)}–${time(b.start+900)}</title></rect><rect x="${x}" y="${205-h1-h2}" width="${w}" height="${h2}" fill="#cba055"><title>Män ${nm} · ${time(b.start)}–${time(b.start+900)}</title></rect><rect x="${x}" y="${205-h1-h2-h3}" width="${w}" height="${h3}" fill="#aab3ad"><title>Kön saknas ${nu}</title></rect>${i%Math.max(1,Math.ceil(bins.length/7))===0?`<text x="${x}" y="222">${time(b.start)}</text>`:''}`}).join('');
  const shown=mode==='all'?fs.length:fs.filter(r=>r.sex===mode).length;
  $('#finish-chart').innerHTML=svg(W,H,body,'Sluttidshistogram, 15-minutersintervall')+`<p class="small muted">${shown} av ${fs.length} fullföljare i aktuellt urval. Alla omfattar även ${fs.filter(r=>!['F','M'].includes(r.sex)).length} med okänt källkön. Fasta 15-minutersintervall mellan vyerna.</p>`;
}
const initial=n=>String(n||'?').split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase();
function podiumPair(objs){return ['F','M'].map(sex=>`<div class="podium-group"><h4>${sex==='F'?'KVINNOR':'MÄN'} <small>n=${objs.filter(x=>x.r.sex===sex).length}</small></h4>${objs.filter(x=>x.r.sex===sex).slice(0,3).map((o,i)=>`<button class="podium-row" type="button" data-open="${html(o.r.id)}"><span class="medal medal-${i+1}">${i+1}</span><span class="avatar" aria-hidden="true">${html(initial(o.r.name))}</span><span><strong>${html(o.r.name)}</strong><small>${html(o.r.class_name||'')} · #${html(o.r.bib)}</small></span><span class="finish">${html(o.value)}</span></button>`).join('')||'<p class="muted small">Ingen verifierad prestation.</p>'}</div>`).join('')}
function renderDynamics(){let rows=S.filtered,counts=collections(rows.map(r=>r.status)),den=Math.max(1,...Object.values(counts));$('#status-chart').innerHTML=`<div class="status-rows">${[['FINISHED','Fullföljt','#507c5b'],['DNF','DNF','#cb9150'],['DNS','DNS','#9caca0'],['DSQ','DSQ','#a56b65'],['UNKNOWN','Okänd','#cbd0c8']].map(([k,n,c])=>`<div class="status-row"><span>${n}</span><div class="bar-track"><div class="bar-fill" style="background:${c};width:${(counts[k]||0)/den*100}%"></div></div><strong>${counts[k]||0}</strong></div>`).join('')}</div>`;
let cps=S.race.stations.filter(st=>st.is_analysis_boundary),flow=cps.map(st=>({name:st.name,km:st.km,count:rows.filter(r=>observed(r,st)).length}));let max=Math.max(1,...flow.map(x=>x.count));$('#flow-chart').innerHTML=flow.length?`<div class="bars">${flow.map(x=>`<div class="barline"><span>${html(x.name)}</span><div class="bar-track"><div class="bar-fill" style="width:${x.count/max*100}%"></div></div><strong>${x.count}</strong></div>`).join('')}</div>`:empty();
let fs=rows.filter(r=>finish(r)&&num(r.place)),W=590,H=265,P=39;if(fs.length>=2){let tmin=Math.min(...fs.map(r=>r.finish_seconds)),tmax=Math.max(...fs.map(r=>r.finish_seconds)),maxPlace=Math.max(...fs.map(r=>r.place)),diff=Math.max(1,tmax-tmin);let body=`<line x1="${P}" y1="${H-P}" x2="${W-P}" y2="${H-P}" class="axis"/><line x1="${P}" y1="${P}" x2="${P}" y2="${H-P}" class="axis"/><text x="${P}" y="${H-12}">${time(tmin)}</text><text x="${W-P-35}" y="${H-12}">${time(tmax)}</text><text x="8" y="${P+5}">#1</text><text x="8" y="${H-P}">#${maxPlace}</text>`+fs.map(r=>{let x=P+(r.finish_seconds-tmin)/diff*(W-2*P),y=P+(r.place-1)/Math.max(1,maxPlace-1)*(H-2*P);return `<circle tabindex="0" role="button" data-open="${html(r.id)}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4.2" fill="${r.sex==='F'?'#507c5b':r.sex==='M'?'#cba055':'#aab3ad'}" aria-label="Öppna ${html(r.name)} ${time(r.finish_seconds)}"><title>${html(r.name)} · ${time(r.finish_seconds)} · #${r.place}</title></circle>`}).join('');$('#placement-chart').innerHTML=svg(W,H,body,'Sluttid mot totalplacering; klicka på en punkt för löparprofil.')}else $('#placement-chart').innerHTML=empty();
let dnf=rows.filter(r=>r.status==='DNF'),last=collections(dnf.map(r=>{let seen=splitsFor(r.id);return seen.length?(S.race.stations.find(st=>st.uid===seen[seen.length-1].station_uid)?.name||'Okänd kontroll'):'Ingen säker passage'}));let peak=Math.max(1,...Object.values(last));$('#dnf-chart').innerHTML=dnf.length?`<div class="dnf-rows">${Object.entries(last).sort((a,b)=>b[1]-a[1]).map(([name,n])=>`<div class="barline"><span>${html(name)}</span><div class="bar-track"><div class="bar-fill" style="width:${n/peak*100}%;background:#b98450"></div></div><strong>${n}</strong></div>`).join('')}</div>`:empty('Ingen DNF-registrering i aktuellt urval.');renderStandouts();bindResultLinks($('#dynamics'))}
function standoutsFor(rows){let profiles=rows.filter(finish).map(r=>({r,parts:pairs(r)})).filter(p=>p.parts.length>=2),all=profiles.flatMap(x=>x.parts.map(s=>({...s,r:x.r,rel:s.seconds/s.km/(x.r.finish_seconds/S.race.nominal_km)})));let physical=all.filter(x=>paceDistanceSupported(x)),categories=[];if(all.length){if(physical.length)categories.push({title:'Snabbast relativt eget snitt',list:physical.filter(x=>num(x.rel)).sort((a,b)=>a.rel-b.rel).map(x=>({r:x.r,value:(100/Math.max(.0001,x.rel)).toFixed(0)+' % · '+x.to.name,score:x.rel}))});let finishList=profiles.map(x=>{let p=x.parts[x.parts.length-1];return p&&num(p.placeFrom)&&num(p.placeTo)?{r:x.r,p,change:p.placeFrom-p.placeTo}:null}).filter(Boolean);categories.push({title:'Starkaste avslutningen',list:finishList.sort((a,b)=>b.change-a.change).map(x=>({r:x.r,value:(x.change>=0?'+':'')+x.change+' platser',score:-x.change}))});let gains=all.filter(x=>num(x.placeFrom)&&num(x.placeTo)).map(x=>({...x,change:x.placeFrom-x.placeTo}));categories.push({title:'Största placeringslyftet',list:gains.sort((a,b)=>b.change-a.change).map(x=>({r:x.r,value:'+'+x.change+' · '+x.to.name,score:-x.change}))});let even=profiles.map(x=>{let z=x.parts.filter(p=>paceDistanceSupported(p)).map(p=>p.seconds/p.km);if(z.length<2)return null;let avg=z.reduce((a,b)=>a+b,0)/z.length;return avg>0?{r:x.r,cv:Math.sqrt(z.reduce((a,b)=>a+(b-avg)**2,0)/z.length)/avg}:null}).filter(x=>x&&num(x.cv));if(even.length)categories.push({title:'Jämnast observerade pacing',list:even.sort((a,b)=>a.cv-b.cv).map(x=>({r:x.r,value:(100*x.cv).toFixed(1)+' % variation',score:x.cv}))});let last=profiles.map(x=>{let p=x.parts.at(-1);return p&&paceDistanceSupported(p)?{r:x.r,sec:p.seconds,km:p.km,name:p.to.name}:null}).filter(Boolean);if(last.length)categories.push({title:'Snabbast på sista verifierade segmentet',list:last.sort((a,b)=>a.sec/a.km-b.sec/b.km).map(x=>({r:x.r,value:pace(x.sec,x.km,S.unit),score:x.sec/x.km}))});}return categories}
function renderStandouts(){let cat=standoutsFor(S.filtered);$('#standouts').innerHTML=cat.length?`<div class="standout-grid">${cat.map(c=>`<div class="standout-card"><h4>${html(c.title)}</h4><div class="podium-pair">${podiumPair(c.list.filter((x,i,a)=>a.findIndex(z=>z.r.id===x.r.id)===i))}</div></div>`).join('')}</div>`:empty('För denna upplaga krävs fler verkliga segmentpar för att hitta ovanliga lopp.');}
function renderSegments(){let segs=segmentStats(S.filtered);if(!segs.length){$('#segment-chart').innerHTML=empty();$('#segment-table tbody').innerHTML='';$('#podium-segment').innerHTML='';$('#segment-podium').innerHTML=empty();return}S.selectedSegment=Math.min(S.selectedSegment,segs.length-1);$('#podium-segment').innerHTML=segs.map((s,i)=>`<option value="${i}" ${i===S.selectedSegment?'selected':''}>${html(s.from.name)} → ${html(s.to.name)}</option>`).join('');renderSegmentGraph(segs);renderSegmentTable();renderSegmentPodium()}
function renderSegmentGraph(segs){let valid=segs.filter(s=>num(s.median));if(!valid.length){$('#segment-chart').innerHTML=empty('Minst fem exakta passager per segment krävs för median.');return}let W=700,H=250,P=40,gap=(W-2*P)/segs.length,max=Math.max(...valid.map(s=>s.q75??s.median));let body=`<line x1="${P}" y1="${H-37}" x2="${W-P}" y2="${H-37}" class="axis"/>`+segs.map((s,i)=>{let x=P+(i+.5)*gap,y=num(s.median)?(H-37)-(s.median/max)*(H-65):H-37,yq1=num(s.q25)?(H-37)-(s.q25/max)*(H-65):null,yq3=num(s.q75)?(H-37)-(s.q75/max)*(H-65):null;return `${num(yq1)&&num(yq3)?`<line x1="${x}" y1="${yq1}" x2="${x}" y2="${yq3}" stroke="#759879" stroke-width="8"/>`:''}<circle cx="${x}" cy="${y}" r="${i===S.selectedSegment?7:5}" fill="${i===S.selectedSegment?'#d4a858':'#3e5d3a'}" tabindex="0" role="button" data-segment="${i}" aria-label="Välj ${html(s.from.name)} till ${html(s.to.name)}" ><title>${html(s.from.name)} → ${html(s.to.name)} · n=${s.n} · median ${time(s.median)}</title></circle><text text-anchor="middle" x="${x}" y="${H-15}" transform="rotate(-25 ${x} ${H-15})">${html(s.to.name.slice(0,12))}</text>`}).join('');$('#segment-chart').innerHTML=svg(W,H,body,'Segmentmedianer och kvartilspann');$$('[data-segment]',$('#segment-chart')).forEach(n=>{const go=()=>{S.selectedSegment=+n.dataset.segment;renderSegmentTable();renderSegmentPodium();renderSegmentGraph(segs);renderCourse()};n.addEventListener('click',go);n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}})});}
function renderSegmentTable(){let segs=segmentStats(S.filtered),finishers=S.filtered.filter(finish),dnf=S.filtered.filter(r=>r.status==='DNF'),dnfTimed=dnf.filter(r=>splitsFor(r.id).some(v=>num(v.elapsed_seconds))),dnfTimedN=dnfTimed.length;$('#segment-table tbody').innerHTML=segs.map((s,i)=>{let atStart=finishers.filter(r=>i===0||observed(r,s.from)).length,paired=atStart?`${s.n}/${atStart}`:'—',moves=s.obs.map(o=>num(o.placeFrom)&&num(o.placeTo)?o.placeFrom-o.placeTo:null).filter(num),movement=moves.length>=5?median(moves):null,lastDnf=dnfTimed.filter(r=>{let seen=splitsFor(r.id).filter(v=>num(v.elapsed_seconds));return seen.length&&seen.at(-1).station_uid===s.from.uid}).length,verifiedDnf=dnfTimedN?String(lastDnf):dnf.length?'Okänt':'—';return `<tr data-select-segment="${i}" tabindex="0" class="${i===S.selectedSegment?'selected':''}"><td>${html(s.from.name)} → ${html(s.to.name)}</td><td>${fmtKm(s.km)}</td><td>${s.n}</td><td>${time(s.median)}</td><td>${num(s.q25)?time(s.q25)+' – '+time(s.q75):'n &lt; 10'}</td><td>${paceDistanceSupported(s)?pace(s.median,s.km,S.unit):'Distans ej verifierad'}</td><td>${paired}</td><td>${num(movement)?(movement>0?'+':'')+movement.toFixed(0):'n < 5'}</td><td title="${dnf.length?'Källkopplad offentlig TIME för '+dnfTimedN+' av '+dnf.length+' DNF i urvalet':'Inga DNF i urvalet'}">${verifiedDnf}</td><td>EQ Timing TIME · ${html(s.from.uid)} → ${html(s.to.uid)}</td></tr>`}).join('');$$('[data-select-segment]',$('#segment-table')).forEach(n=>{let go=()=>{S.selectedSegment=+n.dataset.selectSegment;$('#podium-segment').value=String(S.selectedSegment);renderSegmentTable();renderSegmentPodium();renderSegmentGraph(segs);renderCourse()};n.addEventListener('click',go);n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}})});}
function renderSegmentPodium(){let s=currentSeg();$('#segment-podium').innerHTML=s?podiumPair(s.obs.slice().sort((a,b)=>a.seconds-b.seconds).map(o=>({r:o.r,value:paceDistanceSupported(s)?pace(o.seconds,s.km,S.unit):time(o.seconds)+' · tid endast'}))):empty();bindResultLinks($('#segment-podium'))}
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
  if(cohort==='F'||cohort==='M')rows=rows.filter(r=>r.sex===cohort);
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
    return `<tr><td><button type="button" data-plan-segment="${p.index}" aria-label="Visa ${html(p.from.name)} till ${html(p.to.name)} på banan">${html(p.from.name)} → ${html(p.to.name)} ↗</button></td><td>${fmtKm(p.km)}</td><td>${p.n}</td><td>${html(p.method)}</td><td><strong>${time(allocation)}</strong></td><td>${time(elapsed)}</td><td>${paceDistanceSupported(p)?pace(allocation,p.km,S.unit):'Distans ej verifierad'}</td></tr>`;
  }).join('');
  $$('[data-plan-segment]',out).forEach(button=>button.addEventListener('click',()=>{
    const i=+button.dataset.planSegment;
    $('#segment-table [data-select-segment="'+i+'"]')?.click();
    const segment=allSegments.find(s=>s.index===i);
    const points=routePoints();
    if(segment&&points.length){
      S.courseD=((segment.from.km+segment.to.km)/2)/(S.race.nominal_km||1)*points.at(-1)[0];
      renderCourseMap();
      $('#course-map').scrollIntoView({block:'center',behavior:'smooth'});
    }
  }));
  const sampled=parts.filter(p=>p.method==='Historisk median').length;
  const cohortText=cohort==='near'?' inom ±10 % av måltiden':cohort==='class'?` i klassen ${classSelect.value}`:cohort==='all'?' i hela fältet':` med källkön ${cohort}`;
  const highest=parts.slice().sort((a,b)=>b.w-a.w)[0];
  summary.textContent=`${time(target)} · ${rows.length} fullföljare${cohortText} · ${sampled}/${parts.length} segment med minst fem verkliga tidsandelar. Övriga använder öppet märkt timingdistansfallback. Störst historisk tidsandel: ${highest?highest.from.name+' → '+highest.to.name:'—'}. Planen är en pacingreferens, inte en prognos.`;
}

function renderCourse(){renderCourseMap();renderPlan()}
function routePoints(){return S.route?.points||[]}
function project(points,W,H,pad=17){let lon=points.map(p=>p[2]),lat=points.map(p=>p[1]),xmin=Math.min(...lon),xmax=Math.max(...lon),ymin=Math.min(...lat),ymax=Math.max(...lat),dy=Math.max(1e-6,(ymax-ymin)),dx=Math.max(1e-6,(xmax-xmin)*Math.cos((ymin+ymax)*Math.PI/360)),scale=Math.min((W-pad*2)/dx,(H-pad*2)/dy);return points.map(p=>[W/2+((p[2]-(xmin+xmax)/2)*Math.cos((ymin+ymax)*Math.PI/360))*scale,H/2-((p[1]-(ymin+ymax)/2))*scale]);}
function pointAtDistance(pts,d){if(!pts.length)return null;d=Math.max(pts[0][0],Math.min(pts.at(-1)[0],d));let i=1;while(i<pts.length-1&&pts[i][0]<d)i++;let a=pts[i-1],b=pts[i],f=(d-a[0])/Math.max(.00001,b[0]-a[0]);return [d,a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f,num(a[3])&&num(b[3])?a[3]+(b[3]-a[3])*f:null]}
function nearestSegmentPath(path,p){let best={index:0,fraction:0,dist:Infinity};for(let i=1;i<path.length;i++){let [ax,ay]=path[i-1],[bx,by]=path[i],vx=bx-ax,vy=by-ay,len=vx*vx+vy*vy,f=len?Math.max(0,Math.min(1,((p[0]-ax)*vx+(p[1]-ay)*vy)/len)):0,d=(p[0]-ax-vx*f)**2+(p[1]-ay-vy*f)**2;if(d<best.dist)best={index:i,fraction:f,dist:d}}return best}
function pathFor(path){return path.map((p,i)=>(i?'L':'M')+p[0].toFixed(2)+' '+p[1].toFixed(2)).join(' ')}
function elevationSvg(pts,d,interactive=true){if(!pts.length)return empty();let W=780,H=135,P=17,min=Math.min(...pts.map(p=>num(p[3])?p[3]:0)),max=Math.max(...pts.map(p=>num(p[3])?p[3]:0)),md=pts.at(-1)[0],x=p=>P+p[0]/md*(W-2*P),y=p=>H-P-(num(p[3])?(p[3]-min)/Math.max(1,max-min)*(H-2*P):0);let line=pts.map((p,i)=>(i?'L':'M')+x(p).toFixed(1)+' '+y(p).toFixed(1)).join(' '),dot=pointAtDistance(pts,d??0),xx=dot?x(dot):P,yy=dot?y(dot):H-P;return svg(W,H,`<path class="elev-area" d="${line}L${x(pts.at(-1))} ${H-P}L${P} ${H-P}Z"/><path class="elev-line" d="${line}"/><line class="chart-cursor" x1="${xx}" x2="${xx}" y1="${P}" y2="${H-P}"/><circle class="elev-dot" cx="${xx}" cy="${yy}" r="5"/><text x="${P}" y="12" fill="#526855" font-size="10">${Math.round(min)}–${Math.round(max)} m · GPX-höjd</text><text x="${W-P-80}" y="12" fill="#526855" font-size="10">${fmtKm(md)} km</text>${interactive?`<rect data-elev-hit="1" x="${P}" y="0" width="${W-2*P}" height="${H}" fill="transparent" role="slider" tabindex="0" aria-valuemin="0" aria-valuemax="${md}" aria-valuenow="${d??0}" aria-label="Välj position längs höjdprofilen"/>`:''}`,'Interaktiv höjdprofil')}
function attachElevation(host,pts,callback){let el=$('[data-elev-hit]',host);if(!el)return;let md=pts.at(-1)[0];function seek(e){let box=el.ownerSVGElement.getBoundingClientRect(),x=(e.clientX-box.left)/box.width*780,km=Math.max(0,Math.min(md,(x-17)/(780-34)*md));callback(km)}el.addEventListener('pointerdown',e=>{el.setPointerCapture(e.pointerId);seek(e)});el.addEventListener('pointermove',e=>{if(e.pointerType==='mouse'||e.buttons)seek(e)});el.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();let d=Number(el.getAttribute('aria-valuenow'))||0,d2=e.key==='Home'?0:e.key==='End'?md:d+(e.key==='ArrowLeft'?-md/100:md/100);callback(Math.max(0,Math.min(md,d2)))}})}
function renderCourseMap(){let host=$('#course-map'),height=$('#course-elevation'),pts=routePoints();if(!pts.length){host.innerHTML=empty('Ingen godkänd lokal ruttskiss är registrerad för den historiska upplagan. Resultatanalysen är ändå komplett.');height.innerHTML='';$('#course-scrub-label').textContent='Ingen rutt kopplad till denna upplaga.';return}let W=800,H=340,path=project(pts,W,H,20),d=Number.isFinite(S.courseD)?S.courseD:0,mark=pointAtDistance(pts,d),midx=project(mark?[mark]:[pts[0]],W,H,20)[0]; // mark projected on same immutable bounds below
let idx=1;while(idx<pts.length-1&&pts[idx][0]<d)idx++;let a=pts[idx-1],b=pts[idx],f=(d-a[0])/Math.max(1e-7,b[0]-a[0]),px=path[idx-1][0]+(path[idx][0]-path[idx-1][0])*f,py=path[idx-1][1]+(path[idx][1]-path[idx-1][1])*f;
host.innerHTML=svg(W,H,`<defs><pattern id="map-lines" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M0 40Q26 5 48 40" stroke="#b2d1ac" opacity=".09" fill="none"/></pattern></defs><rect width="${W}" height="${H}" fill="url(#map-lines)"/><path class="route-base" d="${pathFor(path)}"/><path class="route-gold" d="${pathFor(path)}"/><circle class="map-crosshair" cx="${px}" cy="${py}" r="7"/><text class="map-label" x="25" y="27">SÄTILA · OFFICIELL REFERENSGEOMETRI</text><text class="map-label" x="25" y="${H-18}">${fmtKm(d)} / ${fmtKm(pts.at(-1)[0])} km</text><rect data-map-hit="course" x="0" y="0" width="${W}" height="${H}" fill="transparent" role="slider" tabindex="0" aria-label="Välj position på banan" aria-valuemin="0" aria-valuemax="${pts.at(-1)[0]}" aria-valuenow="${d}"/>`,'Interaktiv schematisk banöversikt med faktisk GPX-form');height.innerHTML=elevationSvg(pts,d);let seek=n=>{
  // Keep the current SVG and its captured pointer in place while scrubbing.
  // Rebuilding either SVG during pointerdown detaches the hit target and makes
  // a later mouse click or keyboard activation intermittently fail.
  const maxKm=pts.at(-1)[0];S.courseD=Math.max(0,Math.min(maxKm,Number.isFinite(n)?n:0));
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
};let hit=$('[data-map-hit]',host);function locate(e){let rect=hit.ownerSVGElement.getBoundingClientRect(),xx=(e.clientX-rect.left)/rect.width*W,yy=(e.clientY-rect.top)/rect.height*H,spot=nearestSegmentPath(path,[xx,yy]),i=spot.index;seek(pts[i-1][0]+(pts[i][0]-pts[i-1][0])*spot.fraction)}hit.addEventListener('pointerdown',e=>{hit.setPointerCapture(e.pointerId);locate(e)});hit.addEventListener('pointermove',e=>{if(e.buttons)locate(e)});hit.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();seek(Math.max(0,Math.min(pts.at(-1)[0],(S.courseD??0)+(e.key==='ArrowRight'?1:-1)*pts.at(-1)[0]/80)))}});attachElevation(height,pts,seek);$('#course-scrub-label').textContent=`Illustrativ position ${fmtKm(d)} km längs GPX-displayrutt. Klicka i karta eller höjdprofil.`;}
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
    return `<tr><td><button data-edition="${e.year}" type="button">${e.year} ↗</button></td><td>${html(e.date)}</td><td>${html(e.label)}</td><td>${fmtKm(e.nominal_km)} km</td><td>${format(e.results)}</td><td>${format(knownStarters)}</td><td>${format(e.finishers)}</td><td>${format(e.dnf)}</td><td>${format(e.dns)}</td><td>${format(e.dsq)}</td><td>${format(e.unknown)}</td><td>${time(e.median_seconds)}</td><td>${html(e.whole_course_comparison_group||'Ej verifierad')}</td><td>${html(e.route_status||'none')}</td><td><a href="${html(e.source_url)}" target="_blank" rel="noopener">EQ Timing ↗</a></td></tr>`;
  }).join('');
  $$('[data-edition]',$('#history-table')).forEach(button=>button.addEventListener('click',()=>{S.year=+button.dataset.edition;loadRace().then(()=>$('#race-context').scrollIntoView())}));
}

function resultRows(){let q=S.q.toLocaleLowerCase('sv');let list=S.filtered.filter(r=>!q||[r.name,r.bib,r.club,r.class_name,r.status].some(v=>String(v||'').toLocaleLowerCase('sv').includes(q)));switch(S.sort){case 'name':list.sort((a,b)=>a.name.localeCompare(b.name,'sv'));break;case 'time':list.sort((a,b)=>(a.finish_seconds??Infinity)-(b.finish_seconds??Infinity));break;case 'bib':list.sort((a,b)=>Number(a.bib||Infinity)-Number(b.bib||Infinity));break;default:list.sort((a,b)=>(a.place??Infinity)-(b.place??Infinity)||a.name.localeCompare(b.name,'sv'));}return list}
function renderResults(){let list=resultRows(),per=35,pages=Math.max(1,Math.ceil(list.length/per));S.page=Math.min(S.page,pages-1);$('#results-count').textContent=`${format(list.length)} träffar`;
$('#results-table tbody').innerHTML=list.slice(S.page*per,(S.page+1)*per).map(r=>`<tr><td>${S.year}</td><td>${html(S.race.label)} · ${fmtKm(S.race.nominal_km)} km</td><td>${r.place??'—'}</td><td>${html(r.bib)}</td><td><strong>${html(r.name)}</strong></td><td>${r.sex==='F'?'Kvinna':r.sex==='M'?'Man':'—'}</td><td>${html(r.class_name)}</td><td>${html(r.club)}</td><td>${html(r.status)}</td><td>${time(r.finish_seconds)}</td><td><button type="button" data-open="${html(r.id)}" aria-label="Öppna profilen för ${html(r.name)}">Öppna ↗</button></td></tr>`).join('');$('#page-number').textContent=`Sida ${S.page+1} / ${pages}`;$('#page-prev').disabled=S.page<=0;$('#page-next').disabled=S.page>=pages-1;bindResultLinks($('#results-table'));}
function findRecord(id){return records().find(r=>r.id===id)}
function searchMatches(q){q=String(q||'').trim().toLocaleLowerCase('sv');return q.length<2?[]:records().filter(r=>r.name.toLocaleLowerCase('sv').includes(q)||r.bib===q).slice(0,9)}
function renderSearchSuggestions(){let q=$('#runner-search').value,m=searchMatches(q);S.searchIndex=-1;$('#runner-suggestions').innerHTML=m.map(r=>`<button type="button" class="suggestion" data-id="${html(r.id)}" role="option"><span class="avatar">${html(initial(r.name))}</span><strong>${html(r.name)}</strong><small>#${html(r.bib)} · ${time(r.finish_seconds)}</small></button>`).join('');$$('.suggestion').forEach(b=>b.addEventListener('click',()=>{openProfile(b.dataset.id);$('#runner-suggestions').innerHTML=''}));}
function renderFavorites(){let ids=new Set(records().map(r=>r.id));let stored=S.favorites.filter(id=>ids.has(id));$('#favorites').innerHTML=stored.length?'<p class="muted small" style="width:100%;margin:6px 0">Sparade resultat i denna upplaga</p>'+stored.map(id=>`<button data-favorite="${html(id)}" type="button">★ ${html(findRecord(id)?.name||id)}</button>`).join(''):'';$$('[data-favorite]').forEach(b=>b.addEventListener('click',()=>openProfile(b.dataset.favorite)));}
function toggleFav(id){if(S.favorites.includes(id))S.favorites=S.favorites.filter(k=>k!==id);else S.favorites=[id,...S.favorites].slice(0,40);try{localStorage.setItem(key,JSON.stringify(S.favorites))}catch{}renderFavorites();renderProfileIfOpen();}
function addCompare(id){if(!findRecord(id))return;if(S.compare.includes(id)){S.compare=S.compare.filter(x=>x!==id);renderCompareChips();return}S.compare=[...S.compare.slice(-1),id];renderCompareChips();}
function renderCompareChips(){$('#compare-counter').textContent=`(${S.compare.length}/2)`;$('#open-compare').disabled=S.compare.length!==2;$('#compare-chips').innerHTML=S.compare.map(id=>{let r=findRecord(id);return `<span class="chip">${html(r?.name||id)} <button type="button" data-remove-compare="${html(id)}" aria-label="Ta bort ${html(r?.name||'')} från jämförelsen">×</button></span>`}).join('')||'<p class="small" style="color:#c3d5c7">Lägg till löpare från sökträffar eller deras profiler.</p>';$$('[data-remove-compare]').forEach(b=>b.addEventListener('click',()=>addCompare(b.dataset.removeCompare)))}
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
function openProfile(id){let r=findRecord(id);if(!r)return;S.profileReturnFocus=document.activeElement;openId=id;$('#profile-title').textContent=r.name;renderProfile(r);let d=$('#profile-dialog');if(!d.open)d.showModal();}
function renderProfileIfOpen(){if(openId&&$('#profile-dialog').open){let r=findRecord(openId);if(r)renderProfile(r)}}
function renderProfile(r){
  const segments=pairs(r),passages=splitsFor(r.id),insights=profileInsights(r);
  const head=`<div class="profile-head"><div class="avatar" aria-hidden="true">${html(initial(r.name))}</div><div><h3>${html(r.name)}</h3><p class="muted small">#${html(r.bib)} · ${html(r.class_name||'')} · ${html(r.club||'Okänd klubb/ort')} · ${html(r.status)}</p></div><button class="btn green" type="button" id="profile-add-compare">${S.compare.includes(r.id)?'Ta bort från jämförelse':'Jämför detta resultat →'}</button></div>`;
  const kpis=[['Sluttid',time(r.finish_seconds)],['Totalplacering',r.place??'—'],['Snittfart',pace(r.finish_seconds,S.race.nominal_km,S.unit)],['Registrerade passager',passages.length]]
    .map(([label,value])=>`<article><small>${html(label)}</small><strong>${html(value)}</strong></article>`).join('');
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
  $('#profile-content').innerHTML=head+`<div class="profile-kpis">${kpis}</div><div class="profile-actions"><button type="button" class="btn text-btn" id="profile-fav">${S.favorites.includes(r.id)?'★ Sparad · ta bort':'☆ Spara resultat'}</button><button type="button" class="btn text-btn" id="profile-add-duel">Lägg till i kartduell</button></div><h3>Personliga insikter</h3><div class="insights">${insights.length?insights.map(item=>`<article class="insight"><span>${html(item.label)}</span><strong>${html(item.value)}</strong><span>${html(item.detail)}</span><small>${html(item.method)}</small></article>`).join(''):empty('Fler individuella insikter blir tillgängliga där löparen har tillräckligt många verkliga kontrollpassager.')}</div><h3>Journey · verifierade passager</h3><div class="table-scroll"><table><thead><tr><th>Kontroll</th><th>km*</th><th>Ack. tid</th><th>Sedan föregående verifierade</th><th>Publicerad plats</th><th>Datakälla</th></tr></thead><tbody><tr><td>Start</td><td>0</td><td>0:00</td><td>—</td><td>—</td><td>Tidsnoll</td></tr>${journey}</tbody></table></div>${segments.length?`<h3 style="margin-top:22px">Delsträckor och relativ prestation</h3><div class="table-scroll"><table><thead><tr><th>Segment</th><th>Timing-km</th><th>Segmenttid</th><th>Tempo</th><th>Fältmedian*</th><th>Avvikelse</th><th>n</th></tr></thead><tbody>${segmentRows}</tbody></table></div><p class="muted small">* Median för fullföljare med två exakta segmentpassager i denna upplaga, minst fem observationer.</p>`:''}<div id="profile-replay" style="margin-top:20px"></div>`;
  $('#profile-fav').addEventListener('click',()=>toggleFav(r.id));
  $('#profile-add-compare').addEventListener('click',()=>{addCompare(r.id);renderProfile(r)});
  $('#profile-add-duel').addEventListener('click',()=>{addMapDuel(r.id);renderProfile(r)});
  renderProfileReplay(r);
}

function validRouteComparison(){return !!S.route&&routePoints().length>=2&&S.race.stations.filter(s=>s.is_analysis_boundary).length>=2}
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
  const host=$('#profile-replay');
  if(!validRouteComparison()||splitsFor(r.id).length<2){
    host.innerHTML=`<p class="empty">Ingen Replay för detta resultat: ${S.route?'för få verkliga tidsankare':'denna upplaga saknar separat verifierad publicerbar lokal rutt'}. Profilens publicerade passager påverkas inte.</p>`;
    return;
  }
  const pts=routePoints(),anchors=runnerAnchors(r),maxDistance=anchors.at(-1)?.km||0;
  if(anchors.length<3||maxDistance<=0){
    host.innerHTML=empty('Replay kräver minst två verkliga timingankare efter start och en godkänd lokal rutt.');
    return;
  }
  let d=0,playing=false,startedAt=0,startedKm=0;
  S.profileFollow=false;
  host.innerHTML=`<div class="panel-heading"><div><p class="eyebrow">BERÄKNAD POSITION MELLAN KONTROLLER</p><h3>Personlig Replay · bana och höjd</h3></div></div><div class="course-map" id="profile-mini-map"></div><div class="course-elevation" id="profile-mini-elev"></div><div class="replay-controls"><button type="button" class="btn green" id="profile-replay-play">Spela</button><button type="button" class="btn text-btn" id="profile-replay-reset">Börja om</button><label>Uppspelningstid<select id="profile-replay-duration"><option value="30">30 s</option><option value="60">60 s</option><option value="120" selected>120 s</option><option value="180">180 s</option></select></label><button type="button" class="btn text-btn" id="profile-replay-follow" aria-pressed="false">Följ löpare</button><button type="button" class="btn text-btn" id="profile-replay-fit">Visa hela banan</button></div><label>Position längs visningsrutten<input class="duel-scrubber" id="profile-replay-range" type="range" min="0" max="${maxDistance}" step="0.1" value="0" aria-label="Spola genom löparens lopp"/></label><p class="muted small" id="profile-replay-readout"></p>`;
  const map=$('#profile-mini-map'),elev=$('#profile-mini-elev'),range=$('#profile-replay-range'),playButton=$('#profile-replay-play');
  const stop=()=>{playing=false;cancelAnimationFrame(S._replayFrame);playButton.textContent='Spela'};
  function draw(km){
    d=Math.max(0,Math.min(maxDistance,km));
    range.value=d;
    const elapsed=estimatedAt(anchors,d);
    drawSimpleRoute(map,pts,d);
    updateReplayElevation(elev,pts,d,draw);
    $('#profile-replay-readout').textContent=`${fmtKm(d)} km på visningsrutten · ${num(elapsed)?'Beräknad tävlingstid '+time(elapsed):'Ingen säker interpolation'} · Sista exakta ankare: ${anchors.at(-1).name}. Positionen är illustrativ, inte uppmätt GPS.`;
  }
  function frame(now){
    if(!playing)return;
    const duration=Number($('#profile-replay-duration').value)*1000;
    const next=startedKm+(now-startedAt)/duration*maxDistance;
    draw(next);
    if(next>=maxDistance)stop();
    else S._replayFrame=requestAnimationFrame(frame);
  }
  playButton.addEventListener('click',()=>{
    if(playing){stop();return}
    if(d>=maxDistance)draw(0);
    playing=true;startedKm=d;startedAt=performance.now();playButton.textContent='Pausa';
    S._replayFrame=requestAnimationFrame(frame);
  });
  $('#profile-replay-reset').addEventListener('click',()=>{stop();draw(0)});
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
  $('#profile-dialog').addEventListener('close',stop,{once:true});
  draw(0);
}

function runnerAnchors(r){let arr=[{km:0,t:0,name:'Start'}];let cp=S.race.stations.filter(st=>st.is_analysis_boundary).sort((a,b)=>a.km-b.km);let factor=(routePoints().at(-1)?.[0]||S.race.nominal_km)/S.race.nominal_km;for(let st of cp){let s=observed(r,st);if(s&&num(s.elapsed_seconds)&&num(st.km)&&st.km>0){let last=arr.at(-1);if(s.elapsed_seconds>last.t&&st.km*factor>last.km){arr.push({km:Math.min(st.km*factor,routePoints().at(-1)?.[0]||Infinity),t:s.elapsed_seconds,name:st.name})}}}return arr}
function estimatedAt(anchors,d){if(!anchors?.length)return null;d=Math.max(0,d);if(d>anchors.at(-1).km+1e-6)return null;for(let i=1;i<anchors.length;i++){let a=anchors[i-1],b=anchors[i];if(d>=a.km&&d<=b.km){let f=(d-a.km)/Math.max(1e-6,b.km-a.km);return a.t+(b.t-a.t)*f}}return d===0?0:null}
function drawSimpleRoute(host,pts,d,markers=null){
  const W=760,H=280,path=project(pts,W,H,18);
  const xyAt=km=>{
    let i=1;
    while(i<pts.length-1&&pts[i][0]<km)i++;
    const a=pts[i-1],b=pts[i],f=(km-a[0])/Math.max(.000001,b[0]-a[0]);
    return [path[i-1][0]+(path[i][0]-path[i-1][0])*f,path[i-1][1]+(path[i][1]-path[i-1][1])*f];
  };
  let routeSvg=host.querySelector('svg'),hit=host.querySelector('[data-local-hit]');
  if(!routeSvg){
    const markerSvg=Array.isArray(markers)?markers.map((marker,i)=>`<circle data-runner-marker="${i}" r="6" fill="${marker.color}" stroke="#fff" stroke-width="2"><title>${html(marker.label)}</title></circle>`).join(''):'';
    host.innerHTML=svg(W,H,`<path d="${pathFor(path)}" stroke="#d4a858" stroke-width="3" fill="none"/><circle data-route-cursor r="9" fill="#fff" stroke="#d4a858" stroke-width="3"/>${markerSvg}<rect data-local-hit x="0" y="0" width="${W}" height="${H}" fill="transparent" tabindex="0" role="slider" aria-valuemin="0" aria-valuemax="${pts.at(-1)[0]}" aria-valuenow="${d}" aria-label="Sök i kartan"/>`,'Lokal schematisk GPX-karta');
    routeSvg=host.querySelector('svg');hit=host.querySelector('[data-local-hit]');
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
    if(node){node.setAttribute('cx',point[0]+(i?5:-5));node.setAttribute('cy',point[1])}
  });
  const zoom=host.id==='duel-map'?(S.duelZoom||1):host.id==='profile-mini-map'&&S.profileFollow?2.2:host.id==='map-duel-map'&&S.mapDuelCamera==='leader'?2.2:1,width=W/zoom,height=H/zoom;
  const vx=Math.max(0,Math.min(W-width,x-width/2)),vy=Math.max(0,Math.min(H-height,y-height/2));
  routeSvg.setAttribute('viewBox',`${vx} ${vy} ${width} ${height}`);
  hit.setAttribute('aria-valuenow',d);
}

function openCompare(){if(S.compare.length!==2)return;let [x,y]=S.compare.map(findRecord);if(!x||!y)return;$('#compare-content').innerHTML=renderCompareContent(x,y);let d=$('#compare-dialog');if(!d.open)d.showModal();setupCompareInteractions(x,y);}
function commonStationRows(x,y){let rows=[];for(const st of S.race.stations.filter(s=>s.is_analysis_boundary)){let a=observed(x,st),b=observed(y,st);rows.push({st,a,b,km:st.km,diff:a&&b?a.elapsed_seconds-b.elapsed_seconds:null});}return rows}
function renderCompareContent(x,y){
  const finishGap=finish(x)&&finish(y)?x.finish_seconds-y.finish_seconds:null;
  const rows=commonStationRows(x,y),shared=rows.filter(r=>num(r.diff));
  const xParts=pairs(x),yParts=pairs(y);
  let leadChanges=0,previousLead=0;
  for(const row of shared){
    const lead=Math.sign(row.diff);
    if(lead&&previousLead&&lead!==previousLead)leadChanges++;
    if(lead)previousLead=lead;
  }
  const largest=shared.slice().sort((a,b)=>Math.abs(b.diff)-Math.abs(a.diff))[0];
  const insights=[
    finishGap===null?'Slutlig tidslucka saknas eftersom båda inte har en verifierad målgång.':`Verifierad sluttidsskillnad: ${signed(finishGap)} (A minus B).`,
    `${shared.length} gemensamma exakta kontrollpassager. ${leadChanges} växlingar av vem som låg före vid dessa kontroller.`,
    largest?`Största observerade lucka: ${signed(largest.diff)} vid ${largest.st.name}.`:'Minst en gemensam tidskontroll krävs för observerad lucka.'
  ];
  const routeReady=validRouteComparison();
  return `<div class="compare-profiles"><article><p class="eyebrow">LOPP A</p><span class="avatar" aria-hidden="true">${html(initial(x.name))}</span><h3>${html(x.name)}</h3><p class="muted small">${html(x.class_name)} · #${html(x.bib)}</p><strong>${time(x.finish_seconds)}</strong><p>Placering ${x.place??'—'} · ${html(x.status)}</p></article><div class="versus">VS${finishGap!==null?`<small style="display:block;font-size:12px">${signed(finishGap)}</small>`:''}</div><article><p class="eyebrow">LOPP B</p><span class="avatar" aria-hidden="true">${html(initial(y.name))}</span><h3>${html(y.name)}</h3><p class="muted small">${html(y.class_name)} · #${html(y.bib)}</p><strong>${time(y.finish_seconds)}</strong><p>Placering ${y.place??'—'} · ${html(y.status)}</p></article></div><div class="panel-heading"><h3>Tidslucka genom loppet</h3><button class="info" type="button" id="compare-info" aria-label="Metod för jämförelsen">i</button></div><div id="duel-gap-chart" class="chart-host">${gapSvg(shared)}</div><div class="duel-insights"><h3>Vad hände mellan kontrollerna?</h3><ul>${insights.map(value=>`<li>${html(value)}</li>`).join('')}</ul></div><h3>Verkliga passager och delsträckor</h3><div class="table-scroll"><table><thead><tr><th>Kontroll</th><th>Timing-km</th><th>A ack.</th><th>B ack.</th><th>A segment</th><th>B segment</th><th>A plats</th><th>B plats</th><th>A−B</th><th>Visa</th></tr></thead><tbody>${rows.map(row=>{
    const xa=xParts.find(p=>p.to.uid===row.st.uid),yb=yParts.find(p=>p.to.uid===row.st.uid);
    return `<tr><td>${html(row.st.name)}</td><td>${fmtKm(row.km)}</td><td>${time(row.a?.elapsed_seconds)}</td><td>${time(row.b?.elapsed_seconds)}</td><td>${time(xa?.seconds)}</td><td>${time(yb?.seconds)}</td><td>${row.a?.place??'—'}</td><td>${row.b?.place??'—'}</td><td>${signed(row.diff)}</td><td><button type="button" data-duel-ck="${row.st.uid}">Följ ↗</button></td></tr>`;
  }).join('')}</tbody></table></div><p class="muted small">Lucka visas enbart vid gemensamma exakta passager. Segmenttid visas endast när respektive löpare har två exakta, på varandra följande analysgränser. Saknad data fylls inte ut.</p>${routeReady?`<h3 style="margin-top:18px">Interaktiv jämförelse · karta och höjdkurva</h3><div class="compare-dashboard"><div class="duel-map" id="duel-map"></div><div class="duel-elevation" id="duel-elevation"></div></div><div class="duel-controls"><label>Välj position längs banan<input type="range" class="duel-scrubber" id="duel-range" min="0" max="${routePoints().at(-1)[0]}" value="0" step="0.1"/></label><label>Kartutsnitt<input type="range" id="duel-zoom" min="1" max="3" value="1" step="0.25" aria-label="Zooma jämförelsekartan"/></label><button type="button" class="btn text-btn" id="duel-fit">Visa hela banan</button></div><div class="duel-readout" id="duel-readout"></div><p class="muted small">Gemensam visningsdistans. Löparnas tider mellan verkliga kontroller interpoleras endast för presentation; positionen är inte uppmätt GPS. Klick eller för musen över karta och höjdprofil för att söka.</p>`:empty('Direktjämförelse med officiella tider är tillgänglig, men interaktiv kartduell kräver en godkänd lokal bana för just detta loppår.')}`;
}

function gapSvg(obs){if(obs.length<2)return empty('Minst två gemensamma exakta passager krävs för att rita en luckkurva.');let W=750,H=170,P=27,ys=obs.map(x=>x.diff),mx=Math.max(1,...ys.map(Math.abs)),xmin=Math.min(...obs.map(x=>x.km)),xmax=Math.max(...obs.map(x=>x.km)),p=obs.map(o=>[P+(o.km-xmin)/Math.max(1e-6,xmax-xmin)*(W-2*P),H/2-o.diff/mx*55]);let path=pathFor(p);return svg(W,H,`<line class="baseline" x1="${P}" x2="${W-P}" y1="${H/2}" y2="${H/2}"/><path d="${path}" fill="none" stroke="#b48b44" stroke-width="2.5"/>${obs.map((o,i)=>`<circle cx="${p[i][0]}" cy="${p[i][1]}" r="4.5" fill="#365f40" data-duel-ck="${o.st.uid}" tabindex="0" role="button" aria-label="Visa ${html(o.st.name)} i kartan"><title>${html(o.st.name)} · ${signed(o.diff)}</title></circle>`).join('')}<text x="${P}" y="14">A snabbare ↑ · B snabbare ↓</text>`,'Observerad tidslucka vid gemensamma kontroller');}
function setupCompareInteractions(x,y){
  $('#compare-info')?.addEventListener('click',()=>{
    $('#help-title').textContent='Jämför två lopp';
    $('#help-content').textContent='Två publicerade resultat inom samma RaceEdition jämförs direkt. Segmentdata kräver två exakta passager per löpare. Karta och höjd söker på samma illustrativa displaydistans och skapar aldrig nya källpassager.';
    $('#help-dialog').showModal();
  });
  const pts=routePoints();
  S.duelZoom=1;
  function scrub(distance){
    if(!pts.length)return;
    S.duelD=Math.max(0,Math.min(pts.at(-1)[0],distance));
    $('#duel-range').value=S.duelD;
    drawCompareMap(x,y,S.duelD);
  }
  S._duelSeek=scrub;
  $$('[data-duel-ck]',$('#compare-dialog')).forEach(element=>{
    const go=()=>{
      const station=S.race.stations.find(s=>s.uid===+element.dataset.duelCk);
      if(station&&pts.length)scrub(station.km/(S.race.nominal_km||1)*pts.at(-1)[0]);
    };
    element.addEventListener('click',go);
    element.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();go()}});
  });
  if(pts.length){
    $('#duel-range').addEventListener('input',event=>scrub(+event.target.value));
    $('#duel-zoom').addEventListener('input',event=>{S.duelZoom=+event.target.value;drawCompareMap(x,y,S.duelD??0)});
    $('#duel-fit').addEventListener('click',()=>{S.duelZoom=1;$('#duel-zoom').value='1';drawCompareMap(x,y,S.duelD??0)});
    scrub(0);
  }
}
function drawCompareMap(x,y,d){
  const pts=routePoints(),map=$('#duel-map'),elev=$('#duel-elevation');
  if(!map||!pts.length)return;
  const xAnchors=runnerAnchors(x),yAnchors=runnerAnchors(y);
  drawSimpleRoute(map,pts,d,[{km:Math.min(d,xAnchors.at(-1).km),color:'#315f41',label:'A · illustrativ position fram till sista säkra ankare'},{km:Math.min(d,yAnchors.at(-1).km),color:'#b48b44',label:'B · illustrativ position fram till sista säkra ankare'}]);
  const a=estimatedAt(xAnchors,d),b=estimatedAt(yAnchors,d),gap=num(a)&&num(b)?a-b:null;
  if(!elev.querySelector('svg')){
    elev.innerHTML=elevationSvg(pts,d);
    attachElevation(elev,pts,S._duelSeek);
  }else{
    const P=17,W=780,H=135,md=pts.at(-1)[0],dot=pointAtDistance(pts,d);
    const heights=pts.map(p=>num(p[3])?p[3]:0),min=Math.min(...heights),max=Math.max(...heights);
    const xx=P+d/md*(W-2*P),yy=H-P-((num(dot?.[3])?dot[3]:0)-min)/Math.max(1,max-min)*(H-2*P);
    const cursor=elev.querySelector('.chart-cursor'),point=elev.querySelector('.elev-dot');
    cursor.setAttribute('x1',xx);cursor.setAttribute('x2',xx);
    point.setAttribute('cx',xx);point.setAttribute('cy',yy);
    elev.querySelector('[data-elev-hit]').setAttribute('aria-valuenow',d);
  }
  $('#duel-readout').innerHTML=`<strong>Vald GPX-distans: ${fmtKm(d)} km</strong> · <span style="color:#315f41">A ${html(x.name)}: ${time(a)}</span> · <span style="color:#a47b37">B ${html(y.name)}: ${time(b)}</span> · <strong>Tidslucka A−B: ${signed(gap)}</strong>${!num(a)||!num(b)?'<br>En löpare saknar senare säkerställt timingankare; markören fryser vid sista observerade position och ingen tid extrapoleras.':''}`;
}

function renderCumulativeFinish(){
  const host=$('#percentile-chart'),finishers=S.filtered.filter(finish);
  if(!host||finishers.length<5)return;
  const groups=[{label:'Alla',rows:finishers,color:'#315f41'},{label:'Kvinnor',rows:finishers.filter(r=>r.sex==='F'),color:'#568663'},{label:'Män',rows:finishers.filter(r=>r.sex==='M'),color:'#bb9149'}].filter(g=>g.rows.length>=5);
  const times=finishers.map(r=>r.finish_seconds),min=Math.floor(Math.min(...times)/900)*900,max=Math.ceil(Math.max(...times)/900)*900;
  if(max<=min)return;
  const W=700,H=200,P=37,steps=40;
  const body=`<line class="axis" x1="${P}" x2="${W-P}" y1="${H-P}" y2="${H-P}"/>`+groups.map(group=>{
    const values=group.rows.map(r=>r.finish_seconds);
    const points=Array.from({length:steps+1},(_,i)=>{
      const threshold=min+(max-min)*i/steps,count=values.filter(v=>v<=threshold).length;
      return [P+i/steps*(W-2*P),H-P-count/values.length*(H-2*P)];
    });
    return `<path d="${pathFor(points)}" fill="none" stroke="${group.color}" stroke-width="2.5"><title>${group.label} · n=${values.length}</title></path>`;
  }).join('')+`<text x="${P}" y="${H-8}">${time(min)}</text><text x="${W-P-45}" y="${H-8}">${time(max)}</text><text x="4" y="${P}">100%</text>`;
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
  if($('#map-duel-controls'))return;
  $('#clear-compare').insertAdjacentHTML('afterend',`<div id="map-duel-controls" class="map-duel-picker"><p class="eyebrow">KARTDUELL</p><p class="small">Välj 2–5 resultat i samma upplaga från löparprofilerna.</p><div id="map-duel-chips" class="compare-chips"></div><div class="map-duel-picker-actions"><button type="button" class="btn gold" id="open-map-duel" disabled>Öppna kartduell <span id="map-duel-counter">(0/5)</span> ↗</button><button type="button" class="link-button" id="clear-map-duel">Rensa</button></div></div>`);
  $('#open-map-duel').addEventListener('click',openMapDuel);
  $('#clear-map-duel').addEventListener('click',()=>{S.mapDuel=[];renderMapDuelChips()});
}
function addMapDuel(id){
  if(!findRecord(id))return;
  if(S.mapDuel.includes(id))S.mapDuel=S.mapDuel.filter(value=>value!==id);
  else if(S.mapDuel.length<5)S.mapDuel.push(id);
  renderMapDuelChips();
}
function renderMapDuelChips(){
  if(!$('#map-duel-chips'))return;
  $('#map-duel-counter').textContent=`(${S.mapDuel.length}/5)`;
  $('#open-map-duel').disabled=S.mapDuel.length<2;
  $('#map-duel-chips').innerHTML=S.mapDuel.map(id=>{const runner=findRecord(id);return `<span class="chip">${html(runner?.name||id)} <button type="button" data-remove-map-duel="${html(id)}" aria-label="Ta bort ${html(runner?.name||'')} från kartduellen">×</button></span>`}).join('')||'<p class="small muted">Ingen löpare vald för kartduell.</p>';
  $$('[data-remove-map-duel]').forEach(button=>button.addEventListener('click',()=>addMapDuel(button.dataset.removeMapDuel)));
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
function openMapDuel(){
  const dialog=$('#map-duel-dialog'),host=$('#map-duel-content'),runners=S.mapDuel.map(findRecord).filter(Boolean);
  if(runners.length<2||runners.length>5)return;
  cancelAnimationFrame(S._mapDuelFrame);
  if(!validRouteComparison()){
    host.innerHTML=empty('Kartduell kräver en godkänd lokal rutt för exakt denna tävlingsupplaga. Resultaten kan fortfarande jämföras två och två utan karta.');
    dialog.showModal();return;
  }
  const data=runners.map((runner,i)=>({runner,anchors:runnerAnchors(runner),color:['#d8ad62','#69a07b','#8e9dc4','#d28975','#b58ec4'][i]}));
  const insufficient=data.filter(item=>item.anchors.length<3);
  if(insufficient.length){
    host.innerHTML=empty(`Kartduell kräver två verkliga kontrollankare efter start per löpare. Saknas för: ${insufficient.map(item=>item.runner.name).join(', ')}.`);
    dialog.showModal();return;
  }
  const pts=routePoints(),maxClock=Math.max(...data.map(item=>item.anchors.at(-1).t));
  let clock=0,playing=false,startedAt=0,startedClock=0;
  S.mapDuelCamera='full';
  host.innerHTML=`<p class="muted small">Gemensam tävlingsklocka. Markörerna interpoleras endast mellan varje löpares verkliga EQ-passager och fryser vid sista säkra ankarpunkt. De är inte uppmätta GPS-positioner.</p><div class="compare-dashboard"><div id="map-duel-map" class="duel-map"></div><div id="map-duel-elevation" class="duel-elevation"></div></div><div class="map-duel-playback"><button type="button" class="btn green" id="map-duel-play">Spela</button><button type="button" class="btn text-btn" id="map-duel-reset">Börja om</button><label>Hastighet<select id="map-duel-speed"><option value="0.5">0,5×</option><option value="1" selected>1×</option><option value="2">2×</option><option value="4">4×</option></select></label><label>Kamera<select id="map-duel-camera"><option value="full">Hela banan</option><option value="leader">Följ ledaren</option></select></label><button type="button" class="btn text-btn" id="map-duel-fit">Visa hela banan</button></div><label>Delad tävlingsklocka<input id="map-duel-clock" type="range" min="0" max="${maxClock}" step="1" value="0" aria-label="Sök i kartduellens tävlingsklocka"/></label><p id="map-duel-readout" class="duel-readout"></p><h3>Position och ordning vid vald tid</h3><div id="map-duel-leaderboard"></div>`;
  dialog.showModal();
  const map=$('#map-duel-map'),elev=$('#map-duel-elevation'),play=$('#map-duel-play'),range=$('#map-duel-clock');
  const stop=()=>{playing=false;cancelAnimationFrame(S._mapDuelFrame);play.textContent='Spela'};
  function draw(next){
    clock=Math.max(0,Math.min(maxClock,next));range.value=clock;
    const positions=data.map(item=>({...item,km:distanceAtTime(item.anchors,clock)}));
    const leader=positions.slice().sort((a,b)=>b.km-a.km)[0];
    drawSimpleRoute(map,pts,leader.km,positions.map(item=>({km:item.km,color:item.color,label:`${item.runner.name} · illustrativ position`})));
    updateReplayElevation(elev,pts,leader.km,km=>{
      const target=estimatedAt(data[0].anchors,km);
      if(num(target)){stop();draw(target)}
    });
    $('#map-duel-readout').textContent=`Tävlingsklocka ${time(clock)} · ledare på visningsrutten: ${leader.runner.name} · ${fmtKm(leader.km)} km. Positioner mellan kontroller är beräknade.`;
    $('#map-duel-leaderboard').innerHTML=`<div class="table-scroll"><table><thead><tr><th>Ordning*</th><th>Löpare</th><th>Status</th><th>Illustrativ km</th><th>Sista exakta kontroll</th></tr></thead><tbody>${positions.sort((a,b)=>b.km-a.km).map((item,i)=>`<tr><td>${i+1}</td><td><i class="duel-color" style="background:${item.color}"></i>${html(item.runner.name)}</td><td>${html(item.runner.status)}</td><td>${fmtKm(item.km)}</td><td>${html(item.anchors.at(-1).name)}</td></tr>`).join('')}</tbody></table></div><p class="small muted">* Ordningen är en illustrativ interpolation mellan registrerade kontroller, inte en officiell mellanplacering.</p>`;
  }
  function frame(now){
    if(!playing)return;
    const speed=Number($('#map-duel-speed').value),next=startedClock+(now-startedAt)/120000*maxClock*speed;
    draw(next);
    if(next>=maxClock)stop();else S._mapDuelFrame=requestAnimationFrame(frame);
  }
  S._mapDuelSeek=km=>{const target=estimatedAt(data[0].anchors,km);if(num(target)){stop();draw(target)}};
  play.addEventListener('click',()=>{
    if(playing){stop();return}
    if(clock>=maxClock)draw(0);
    playing=true;startedClock=clock;startedAt=performance.now();play.textContent='Pausa';S._mapDuelFrame=requestAnimationFrame(frame);
  });
  $('#map-duel-reset').addEventListener('click',()=>{stop();draw(0)});
  range.addEventListener('input',()=>{stop();draw(+range.value)});
  $('#map-duel-speed').addEventListener('change',()=>{if(playing){startedClock=clock;startedAt=performance.now()}});
  $('#map-duel-camera').addEventListener('change',event=>{S.mapDuelCamera=event.target.value;draw(clock)});
  $('#map-duel-fit').addEventListener('click',()=>{S.mapDuelCamera='full';$('#map-duel-camera').value='full';draw(clock)});
  dialog.addEventListener('close',stop,{once:true});
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
    </div>`);
    if(!$('#extra-segments')) $('#segments').insertAdjacentHTML('beforeend',`<div id="extra-segments" class="extra-grid segment-extras">
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">FÄLTETS YTTERKANTER</p><h3>Q10–Q90 per delsträcka</h3></div><button class="info" data-help-extra="q1090">i</button></div><div id="segment-q1090"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">RETENTION</p><h3>Hur mycket av fältet syns kvar?</h3></div><button class="info" data-help-extra="retention">i</button></div><div id="segment-retention"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">PACINGINDEX</p><h3>Fart mot eget loppsnitt</h3></div><button class="info" data-help-extra="pacing">i</button></div><div id="segment-pacing"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">KVINNOR / MÄN</p><h3>Vald delsträcka</h3></div><button class="info" data-help-extra="sexpace">i</button></div><div id="segment-sex-extra"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">KLASSER</p><h3>Gruppjämförelse</h3></div><button class="info" data-help-extra="groups">i</button></div><div id="segment-groups"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">TEMPOHEATMAP</p><h3>Var förändras gruppernas relativa tempo?</h3></div><button class="info" data-help-extra="heatmap">i</button></div><div id="segment-heatmap" class="heatmap-scroll"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">FÄLTETS SPRIDNING</p><h3>Q25–Q75 genom kontrollerna</h3></div><button class="info" data-help-extra="spread">i</button></div><div id="checkpoint-spread"></div></article>
    </div>`);
    if(!$('#extra-course')) $('#course').insertAdjacentHTML('beforeend',`<div id="extra-course" class="extra-grid two-up">
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">COURSE INTELLIGENCE</p><h3>Banans dimensioner</h3></div><button class="info" data-help-extra="courseintel">i</button></div><div id="course-intelligence"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">BANVERSIONER</p><h3>Historisk kartjämförelse</h3></div><button class="info" data-help-extra="maphistory">i</button></div><div id="map-history"></div></article>
    </div>`);
    if(!$('#extra-history')) $('#history').insertAdjacentHTML('beforeend',`<div id="extra-history" class="extra-grid history-extra">
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">PRESTATION PER UPPLAGA</p><h3>Medianer utan falsk trendlinje</h3></div><button class="info" data-help-extra="performance">i</button></div><div id="history-performance"></div></article>
      <article class="panel"><div class="panel-heading"><div><p class="eyebrow">KÖNSFÖRDELNING</p><h3>Andel kvinnor och män över tid</h3></div><button class="info" data-help-extra="sexhistory">i</button></div><div id="history-sex"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">ÅRENS FINGERAVTRYCK</p><h3>Fyra oberoende mått – inget syntetiskt betyg</h3></div><button class="info" data-help-extra="fingerprint">i</button></div><div id="history-fingerprint"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">COURSEVERSION & PROVENIENS</p><h3>Vad går att jämföra?</h3></div><button class="info" data-help-extra="provenance">i</button></div><div id="course-provenance"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">GRUPPTABELL</p><h3>Kön och klass i valt fält</h3></div><button class="info" data-help-extra="grouptable">i</button></div><div id="group-table"></div></article>
      <article class="panel extra-wide"><div class="panel-heading"><div><p class="eyebrow">KÄLLTÄCKNING</p><h3>Resultat, passager och rutt per år</h3></div><button class="info" data-help-extra="coverage">i</button></div><div id="coverage-table"></div></article>
    </div>`);
  }
  const extraHelp={sexfinish:'Fullföljandegraden räknas inom källstött kön: FINISHED / (FINISHED + DNF + DSQ). DNS och okänd startstatus ingår inte i nämnaren.',goal:'Simuleringen placerar en angiven måltid i den observerade sluttidsordningen för nuvarande filtrerade fält. Det är inte en prognos över en framtida placering.',age:'Ålder visas endast när EQ Timing publicerar en rimlig numerisk ålder. Saknad ålder infereras aldrig från klassnamn.',club:'Klubb/ort är källfältet som publicerats av EQ Timing; tomma uppgifter förblir saknade.',gain:'Placeringslyft kräver minst två kontroller med publicerad totalplacering. Startplacering gissas inte.',finishprogress:'Sista tredjedelens progression jämför publicerad placering närmast före 2/3 av timingdistansen med sista publicerade placeringen.',q1090:'Q10–Q90 publiceras först vid minst 20 exakta segmentobservationer. Q25–Q75 kräver minst 10 och median minst 5.',retention:'Retention är antal löpare med en faktisk TIME-observation vid kontrollen relativt den första analyserbara kontrollen. Det är inte samma sak som överlevnad/DNF.',sexpace:'Median segmenttid visas separat för kvinnor och män endast vid minst fem exakta observationer i respektive grupp.',groups:'Gruppmedianer baseras på publicerad klass och kräver minst fem exakta segmentobservationer.',heatmap:'Varje cell är gruppens segmentmedian relativt hela fältets segmentmedian. Minst fem observationer krävs för både grupp och totalfält.',spread:'Q25–Q75 för ackumulerad verklig passagetid kräver minst tio fullföljare per kontroll. Saknade passager fylls inte ut.',courseintel:'Dimensionerna redovisas separat. Rå positiv GPX-höjd är en geometrisk filsumma och inte arrangörens officiella D+. Inget sammanslaget svårighetsbetyg skapas.',maphistory:'Kartor jämförs bara där lokal ruttgeometri faktiskt finns. En modern officiell rutt lånas inte bakåt till äldre upplagor.',performance:'Enskilda upplagors medianer kan redovisas sida vid sida. En sammanhängande prestationsutveckling ritas endast inom en uttryckligen verifierad whole-course-grupp.',sexhistory:'Andelar bygger endast på källstött kön. Resultat utan kön ligger utanför nämnaren och redovisas separat i tooltip/tabell.',fingerprint:'Varje upplaga visas med oberoende dimensioner. De vägs aldrig ihop till ett syntetiskt svårighetsindex.',provenance:'CourseVersion, route-status och timingkälla hålls separata. Kartgeometri är inte tidtagningsbevis.',grouptable:'Gruppstatistik visar n och median endast när n är tillräckligt. Namn eller kön infereras inte.',coverage:'Källtäckning beskriver vad analysmotorn faktiskt har: resultat, fullföljare, passager, stationer och lokal rutt.'};
  function barRows(items,valueLabel=x=>x.value){if(!items.length)return empty();const max=Math.max(1,...items.map(x=>x.value));return `<div class="bars">${items.map(x=>`<div class="barline"><span title="${esc(x.label)}">${esc(x.label)}</span><div class="bar-track"><div class="bar-fill" style="width:${100*x.value/max}%"></div></div><strong>${esc(valueLabel(x))}</strong></div>`).join('')}</div>`}
  function renderSexCompletion(){const out=$('#sex-completion');if(!out)return;const rows=S.filtered,items=['F','M'].map(sex=>{const r=rows.filter(x=>x.sex===sex),started=r.filter(x=>['FINISHED','DNF','DSQ'].includes(x.status)),fin=started.filter(finish);return {sex,label:sex==='F'?'Kvinnor':'Män',started:started.length,fin:fin.length,pct:started.length?100*fin.length/started.length:null}});out.innerHTML=items.some(x=>x.started)?`<div class="completion-pair">${items.map(x=>`<article><strong>${esc(x.label)}</strong><span class="big-number">${num(x.pct)?x.pct.toFixed(1).replace('.',',')+' %':'—'}</span><div class="bar-track"><div class="bar-fill" style="width:${x.pct||0}%"></div></div><small>${x.fin}/${x.started} startande med känd startstatus</small></article>`).join('')}</div>`:empty('Kön eller startstatus saknas för detta urval.')}
  function parseClock(s){const p=String(s||'').trim().split(':').map(Number);if(p.some(x=>!Number.isFinite(x))||p.length<2||p.length>3)return null;const n=p.length===2?p[0]*3600+p[1]*60:p[0]*3600+p[1]*60+p[2];return n>0?n:null}
  function renderGoal(){const host=$('#goal-placement');if(!host)return;const fs=S.filtered.filter(finish).sort((a,b)=>a.finish_seconds-b.finish_seconds);if(fs.length<5){host.innerHTML=empty('Minst fem fullföljare krävs.');return}const input=$('#goal-placement-time');if(!input.value){input.value=time(median(fs.map(r=>r.finish_seconds)))}const target=parseClock(input.value);if(!target){host.innerHTML=empty('Ange måltid som HH:MM eller HH:MM:SS.');return}const faster=fs.filter(r=>r.finish_seconds<target).length,place=Math.min(fs.length+1,faster+1),beat=Math.max(0,fs.length-faster),pct=100*beat/fs.length;const near=fs.slice().sort((a,b)=>Math.abs(a.finish_seconds-target)-Math.abs(b.finish_seconds-target)).slice(0,3);host.innerHTML=`<div class="sim-kpis"><span><strong>≈ ${place}</strong><small>placering i observerat fält</small></span><span><strong>${pct.toFixed(0)} %</strong><small>av målgångarna bakom måltiden</small></span></div><p class="small muted">Närmaste observerade sluttider</p>${near.map(r=>`<button class="mini-result" data-open="${esc(r.id)}"><span>${esc(r.name)}</span><strong>${time(r.finish_seconds)}</strong><small>#${r.place??'—'}</small></button>`).join('')}`;bindResultLinks(host)}
  function renderAge(){const h=$('#age-chart');if(!h)return;const ages=S.filtered.filter(r=>num(r.age)&&r.age>=0&&r.age<=120),minimum=ages.length?Math.floor(Math.min(...ages.map(r=>r.age))/5)*5:0,maximum=ages.length?Math.floor(Math.max(...ages.map(r=>r.age))/5)*5:0,bins=[];for(let a=minimum;a<=maximum;a+=5)bins.push({label:`${a}–${a+4}`,value:ages.filter(r=>r.age>=a&&r.age<a+5).length});h.innerHTML=ages.length?barRows(bins)+`<p class="small muted">Exakt ålder känd för ${ages.length}/${S.filtered.length} resultat. Åldersklasser används inte som ersättning för födelseår.</p>`:empty('EQ Timing publicerar ingen numerisk ålder i detta urval.')}
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
    const selected=[...S.selectedClubs].map(name=>{
      const rows=S.filtered.filter(r=>r.club===name),finishers=rows.filter(finish),med=finishers.length>=5?median(finishers.map(r=>r.finish_seconds)):null;
      return `<tr><td>${esc(name)}</td><td>${rows.length}</td><td>${finishers.length}</td><td>${time(med)}</td></tr>`;
    }).join('');
    const full=groups.map(([name,n])=>{
      const finishers=S.filtered.filter(r=>r.club===name&&finish(r)),med=finishers.length>=5?median(finishers.map(r=>r.finish_seconds)):null;
      return `<tr><td>${esc(name)}</td><td>${n}</td><td>${finishers.length}</td><td>${time(med)}</td></tr>`;
    }).join('');
    host.innerHTML=`<p class="small muted">Välj högst fyra källgrupper. Median visas först vid fem fullföljare.</p><div class="club-choices">${choices}</div><div class="table-scroll"><table><thead><tr><th>Vald klubb/ort</th><th>Resultat</th><th>Fullföljare</th><th>Median</th></tr></thead><tbody>${selected}</tbody></table></div><details class="class-details"><summary>Visa alla ${groups.length} källgrupper</summary><div class="table-scroll"><table><thead><tr><th>Klubb/ort</th><th>Resultat</th><th>Fullföljare</th><th>Median</th></tr></thead><tbody>${full}</tbody></table></div></details>`;
    $$('[data-club-choice]',host).forEach(input=>input.addEventListener('change',()=>{
      if(input.checked&&S.selectedClubs.size<4)S.selectedClubs.add(input.dataset.clubChoice);
      else if(!input.checked)S.selectedClubs.delete(input.dataset.clubChoice);
      renderClub();
    }));
  }

  function placements(r){return S.race.stations.filter(s=>s.is_analysis_boundary).map(st=>{const o=observed(r,st);return o&&num(o.place)?{st,place:o.place,t:o.elapsed_seconds}:null}).filter(Boolean)}
  function renderPlacementGain(){const h=$('#placement-gain');if(!h)return;const xs=S.filtered.map(r=>{const a=placements(r);return a.length>=2?{r,from:a[0],to:a.at(-1),delta:a[0].place-a.at(-1).place}:null}).filter(Boolean).sort((a,b)=>b.delta-a.delta);if(!xs.length){h.innerHTML=empty('Minst två publicerade placeringspassager krävs.');return}const top=xs.slice(0,8).map(x=>({label:x.r.name,value:Math.max(0,x.delta),raw:x.delta,r:x.r}));const max=Math.max(1,...top.map(x=>Math.abs(x.raw)));h.innerHTML=`<div class="gain-list">${top.map(x=>`<button data-open="${esc(x.r.id)}" class="gain-row"><span>${esc(x.label)}</span><div class="gain-axis"><i style="width:${Math.abs(x.raw)/max*100}%" class="${x.raw>=0?'positive':'negative'}"></i></div><strong>${x.raw>=0?'+':''}${x.raw}</strong></button>`).join('')}</div><p class="small muted">Första till sista observerade placering. Positivt = netto framåt.</p>`;bindResultLinks(h)}
  function renderFinishProgress(){const h=$('#finish-progression');if(!h)return;const threshold=(S.race.nominal_km||0)*2/3;const vals=S.filtered.filter(finish).map(r=>{const a=placements(r).filter(x=>num(x.st.km));const before=a.filter(x=>x.st.km<=threshold).at(-1);const last=a.at(-1);return before&&last&&before.st.uid!==last.st.uid?{r,delta:before.place-last.place,from:before.st.name,to:last.st.name}:null}).filter(Boolean).sort((a,b)=>b.delta-a.delta);if(!vals.length){h.innerHTML=empty('Tillräckliga placeringsankare i sista tredjedelen saknas.');return}h.innerHTML=`<div class="finish-progress-list">${vals.slice(0,10).map((x,i)=>`<button class="mini-result" data-open="${esc(x.r.id)}"><span><b>${i+1}</b> ${esc(x.r.name)}</span><strong>${x.delta>=0?'+':''}${x.delta} platser</strong><small>${esc(x.from)} → ${esc(x.to)}</small></button>`).join('')}</div>`;bindResultLinks(h)}
  function segmentExtended(){return segmentStats(S.filtered).map(s=>{const xs=s.obs.map(o=>o.seconds);return {...s,q10:xs.length>=20?quant(xs,.1):null,q90:xs.length>=20?quant(xs,.9):null}})}
  function renderQ1090(){const h=$('#segment-q1090');if(!h)return;const segs=segmentExtended().filter(s=>num(s.q10)&&num(s.q90));if(!segs.length){h.innerHTML=empty('Q10–Q90 kräver minst 20 exakta observationer per delsträcka.');return}const W=700,H=250,P=42,max=Math.max(...segs.map(s=>s.q90)),gap=(W-2*P)/segs.length;const body=segs.map((s,i)=>{const x=P+(i+.5)*gap,y1=H-P-s.q10/max*(H-2*P),y9=H-P-s.q90/max*(H-2*P),ym=H-P-s.median/max*(H-2*P);return `<line x1="${x}" x2="${x}" y1="${y1}" y2="${y9}" class="quantile-whisker"/><circle cx="${x}" cy="${ym}" r="4" class="quantile-median"><title>${esc(s.from.name)} → ${esc(s.to.name)} · Q10 ${time(s.q10)} · median ${time(s.median)} · Q90 ${time(s.q90)} · n=${s.n}</title></circle><text x="${x}" y="${H-12}" text-anchor="middle">${esc(s.to.name.slice(0,9))}</text>`}).join('');h.innerHTML=svg(W,H,body,'Q10 till Q90 per segment')}
  function renderRetention(){const h=$('#segment-retention');if(!h)return;const cps=S.race.stations.filter(s=>s.is_analysis_boundary&&num(s.km)).sort((a,b)=>a.sort-b.sort||a.km-b.km);const counts=cps.map(st=>({st,n:S.filtered.filter(r=>observed(r,st)).length}));const base=counts.find(x=>x.n>0)?.n||0;if(!base){h.innerHTML=empty();return}const W=700,H=230,P=40,maxKm=Math.max(...counts.map(x=>x.st.km),1),pts=counts.map(x=>[P+x.st.km/maxKm*(W-2*P),H-P-(x.n/base)*(H-2*P),x]);h.innerHTML=svg(W,H,`<line class="axis" x1="${P}" x2="${W-P}" y1="${H-P}" y2="${H-P}"/><path class="line-dark" d="${pathFor(pts)}"/>${pts.map(p=>`<circle cx="${p[0]}" cy="${p[1]}" r="4" fill="#3e5d3a"><title>${esc(p[2].st.name)} · ${p[2].n}/${base} · ${(100*p[2].n/base).toFixed(1)} %</title></circle>`).join('')}<text x="${P}" y="15">första analyserbara kontroll = 100 %</text>`,'Observerad passageretention')}
  function renderSegmentSex(){const h=$('#segment-sex-extra');if(!h)return;const s=currentSeg();if(!s){h.innerHTML=empty();return}const vals=['F','M'].map(sex=>{const xs=s.obs.filter(o=>o.r.sex===sex).map(o=>o.seconds);return {sex,label:sex==='F'?'Kvinnor':'Män',n:xs.length,med:xs.length>=5?median(xs):null}});h.innerHTML=`<div class="sex-pacing-cards">${vals.map(x=>`<article><span>${x.label}</span><strong>${time(x.med)}</strong><small>n=${x.n}${x.n<5?' · median dold':''}</small></article>`).join('')}</div><p class="small muted">${esc(s.from.name)} → ${esc(s.to.name)} · ${fmtKm(s.km)} km</p>`}
  function renderSegmentGroups(){const h=$('#segment-groups');if(!h)return;const s=currentSeg();if(!s){h.innerHTML=empty();return}const groups=collections(s.obs.map(o=>o.r.class_name||'').filter(Boolean)),items=Object.keys(groups).map(k=>{const xs=s.obs.filter(o=>o.r.class_name===k).map(o=>o.seconds);return {label:k,n:xs.length,med:xs.length>=5?median(xs):null}}).filter(x=>num(x.med)).sort((a,b)=>a.med-b.med).slice(0,10);h.innerHTML=items.length?`<div class="bars">${items.map(x=>`<div class="barline group-time"><span>${esc(x.label)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.min(100,100*items[0].med/x.med)}%"></div></div><strong>${time(x.med)}</strong><small>n=${x.n}</small></div>`).join('')}</div>`:empty('Ingen klass har minst fem exakta segmentobservationer.')}
  function topClasses(){const c=collections(S.filtered.map(r=>r.class_name||'').filter(Boolean));return Object.entries(c).sort((a,b)=>b[1]-a[1]).slice(0,7).map(x=>x[0])}
  function renderHeatmap(){const h=$('#segment-heatmap');if(!h)return;const segs=segmentStats(S.filtered),classes=topClasses();if(!segs.length||!classes.length){h.innerHTML=empty();return}let cells='';for(const cl of classes){cells+=`<div class="heat-label">${esc(cl)}</div>`;for(const s of segs){const xs=s.obs.filter(o=>o.r.class_name===cl).map(o=>o.seconds),med=xs.length>=5?median(xs):null,ratio=num(med)&&num(s.median)?med/s.median:null,c=num(ratio)?Math.max(-.25,Math.min(.25,ratio-1)):null;const op=c===null?0:Math.min(1,Math.abs(c)/.25),cls=c===null?'missing':c<=0?'fast':'slow';cells+=`<div class="heat-cell ${cls}" style="--heat:${op}" title="${esc(cl)} · ${esc(s.from.name)}→${esc(s.to.name)} · ${ratio===null?'n<5 / saknas':((ratio-1)*100).toFixed(1)+' % mot fältmedian'}"><span>${ratio===null?'—':(100*(ratio-1)).toFixed(0)+'%'}</span><small>n=${xs.length}</small></div>`}}h.innerHTML=`<div class="heat-grid" style="--cols:${segs.length}"><div></div>${segs.map(s=>`<div class="heat-head">${esc(s.to.name)}</div>`).join('')}${cells}</div><p class="small muted">Negativt = snabbare segmenttid än fältets median; positivt = långsammare. Minst fem observationer per cell.</p>`}
  function renderCheckpointSpread(){const h=$('#checkpoint-spread');if(!h)return;const cps=S.race.stations.filter(s=>s.is_analysis_boundary&&num(s.km)).sort((a,b)=>a.sort-b.sort||a.km-b.km),vals=cps.map(st=>{const xs=S.filtered.filter(finish).map(r=>observed(r,st)?.elapsed_seconds).filter(num);return {st,n:xs.length,q25:xs.length>=10?quant(xs,.25):null,med:xs.length>=5?median(xs):null,q75:xs.length>=10?quant(xs,.75):null}}).filter(x=>num(x.q25)&&num(x.q75));if(!vals.length){h.innerHTML=empty('Q25–Q75 kräver minst tio fullföljare med verklig passage.');return}const W=760,H=260,P=45,max=Math.max(...vals.map(x=>x.q75)),maxKm=Math.max(...vals.map(x=>x.st.km),1);h.innerHTML=svg(W,H,`<line class="axis" x1="${P}" x2="${W-P}" y1="${H-P}" y2="${H-P}"/>${vals.map(v=>{const x=P+v.st.km/maxKm*(W-2*P),y1=H-P-v.q25/max*(H-2*P),ym=H-P-v.med/max*(H-2*P),y3=H-P-v.q75/max*(H-2*P);return `<line class="quantile-whisker" x1="${x}" x2="${x}" y1="${y1}" y2="${y3}"/><circle class="quantile-median" cx="${x}" cy="${ym}" r="4"><title>${esc(v.st.name)} · Q25 ${time(v.q25)} · median ${time(v.med)} · Q75 ${time(v.q75)} · n=${v.n}</title></circle><text x="${x}" y="${H-15}" text-anchor="middle">${esc(v.st.name.slice(0,9))}</text>`}).join('')}`,'Ackumulerad passagetid Q25–Q75')}
  function syncSegmentOverlay(){if(!S.route||!$('#course-map svg'))return;const seg=currentSeg();if(!seg)return;const pts=routePoints(),total=pts.at(-1)?.[0],nom=S.race.nominal_km||seg.to.km;if(!num(total)||!num(nom))return;const start=Math.max(0,seg.from.km/nom*total),end=Math.min(total,seg.to.km/nom*total),proj=project(pts,800,340,20),picked=proj.filter((p,i)=>pts[i][0]>=start&&pts[i][0]<=end);if(picked.length<2)return;const old=$('.segment-route-overlay',$('#course-map'));old?.remove();const ns='http://www.w3.org/2000/svg',path=document.createElementNS(ns,'path');path.setAttribute('d',pathFor(picked));path.setAttribute('class','segment-route-overlay');path.setAttribute('aria-label',`Vald delsträcka ${seg.from.name} till ${seg.to.name}`);$('#course-map svg').appendChild(path);const mid=(start+end)/2;S.courseD=Number.isFinite(S.courseD)?S.courseD:mid}
  function renderCourseIntel(){const h=$('#course-intelligence');if(!h)return;const fs=S.filtered.filter(finish),dnf=S.filtered.filter(r=>r.status==='DNF').length,started=fs.length+dnf+S.filtered.filter(r=>r.status==='DSQ').length;const dims=[['Timingdistans',fmtKm(S.race.nominal_km)+' km','Officiell resultataxel'],['Publika kontroller',S.race.stations.filter(s=>s.is_analysis_boundary).length,'TIME-ankare för segment'],['Median sluttid',fs.length>=5?time(median(fs.map(r=>r.finish_seconds))):'—',`n=${fs.length}`],['DNF-andel',started?(100*dnf/started).toFixed(1).replace('.',',')+' %':'—','Observerad status'],['Displayrutt',S.route?fmtKm(S.route.geometry_length_km)+' km':'—',S.route?'Arrangörens GPX':'Saknas för upplagan'],['Rå GPX D+',S.route?Math.round(S.route.raw_positive_gain_m_not_official)+' m':'—','Ej officiell höjdmetrik']];h.innerHTML=`<div class="dimension-grid">${dims.map(d=>`<article><span>${esc(d[0])}</span><strong>${esc(d[1])}</strong><small>${esc(d[2])}</small></article>`).join('')}</div><p class="small muted">Dimensionerna redovisas separat och vägs inte ihop till något svårighetsbetyg.</p>`}
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
    host.innerHTML=`<div class="table-scroll"><table><thead><tr><th>Familj/år</th><th>Marknads-km</th><th>GPX-km</th><th>CourseVersion</th><th>Whole-course-grupp</th><th>Ruttstatus</th><th>Källtyp</th><th>Källfil</th><th>SHA-256</th></tr></thead><tbody>${rows.map(e=>`<tr><td>${esc(e.family)} · ${e.year}</td><td>${fmtKm(e.nominal_km)}</td><td>${fmtKm(e.route_geometry_km)}</td><td>${esc(e.course_version||'Ej verifierad')}</td><td>${esc(e.whole_course_comparison_group||'Ej verifierad')}</td><td>${esc(e.route_status||'none')}</td><td>${esc(e.route_source_type||'—')}</td><td>${esc(e.route_source_filename||'—')}</td><td><code>${esc(e.route_sha256||'—')}</code></td></tr>`).join('')}</tbody></table></div><p class="small muted">2025/2026-arrangörsrutten för 21/43 km är ett uttryckligt projektantagande; äldre års geometri och helbaneprestation är inte automatiskt jämförbara. Rå deltagar-GPX publiceras inte.</p>`;
  }

  function renderGroupTable(){
    const h=$('#group-table');if(!h)return;
    const rows=S.filtered,groups=[];
    const add=(kind,name,matching)=>{const rs=rows.filter(matching),fs=rs.filter(finish);groups.push({kind,name,n:rs.length,finish:fs.length,med:fs.length>=5?median(fs.map(r=>r.finish_seconds)):null})};
    for(const sex of ['F','M','other'])add('Kön',sex==='F'?'Kvinnor':sex==='M'?'Män':'Kön saknas',r=>sex==='other'?!['F','M'].includes(r.sex):r.sex===sex);
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

  extraHelp.pacing='Pacingindex = 100 × (egen sluttid / officiell timingdistans) / (egen segmenttid / kontrakterad segmentdistans). Över 100 betyder snabbare än löparens eget hel-loppssnitt. Diagrammet visar median av individuella index från minst fem fullföljare med två exakta segmentpassager.';
  extraHelp.sexpace='Gemensam tidsaxel visar separata segmentmedianer för källstödda kvinnor och män. Varje punkt kräver minst fem exakta observationer i könsgruppen; en saknad punkt bryter linjen.';
  extraHelp.groups='Välj högst fem publicerade klasser. Gruppkurvan är median av individuella pacingindex per segment; minst fem exakta observationer krävs per klass och punkt.';
  function renderPacingIndex(){
    const host=$('#segment-pacing');
    if(!host)return;
    const nominal=S.race.nominal_km;
    const rows=segmentStats(S.filtered).map(s=>{
      const values=s.obs.filter(o=>paceDistanceSupported(s)&&finish(o.r)&&num(o.seconds)&&o.seconds>0&&num(s.km)&&s.km>0&&num(nominal)&&nominal>0)
        .map(o=>100*(o.r.finish_seconds/nominal)/(o.seconds/s.km)).filter(v=>num(v)&&v>0);
      return {...s,paceN:values.length,paceMedian:values.length>=5?median(values):null};
    });
    const valid=rows.filter(s=>num(s.paceMedian));
    if(!valid.length){host.innerHTML=empty('Minst fem fullföljare med två exakta passager och kontrakterad segmentdistans krävs för pacingindex.');return}
    const W=700,H=240,P=42,lo=Math.min(90,...valid.map(s=>s.paceMedian)),hi=Math.max(110,...valid.map(s=>s.paceMedian));
    const y=value=>H-P-(value-lo)/Math.max(1,hi-lo)*(H-2*P),step=(W-2*P)/Math.max(1,rows.length);
    const body=`<line class="axis" x1="${P}" x2="${W-P}" y1="${y(100)}" y2="${y(100)}"/><text x="4" y="${y(100)-5}">100</text>`+
      rows.map((s,i)=>{const x=P+(i+.5)*step;return num(s.paceMedian)?`<circle data-pacing-segment="${s.index}" tabindex="0" role="button" aria-label="Välj ${html(s.from.name)} till ${html(s.to.name)}" cx="${x}" cy="${y(s.paceMedian)}" r="${s.index===S.selectedSegment?7:5}" fill="${s.index===S.selectedSegment?'#d4a858':'#3e5d3a'}"><title>${html(s.from.name)} → ${html(s.to.name)} · median ${s.paceMedian.toFixed(1)} · n=${s.paceN}</title></circle>`:''}).join('');
    host.innerHTML=svg(W,H,body,'Median av löparnas individuella pacingindex per delsträcka')+`<p class="small muted">100 = eget hel-loppssnitt · över 100 = snabbare · n varierar per segment. ${valid.map(s=>`${html(s.to.name)} ${s.paceMedian.toFixed(0)} (n=${s.paceN})`).join(' · ')}</p>`;
    $$('[data-pacing-segment]',host).forEach(node=>{
      const select=()=>$('#segment-table [data-select-segment="'+node.dataset.pacingSegment+'"]')?.click();
      node.addEventListener('click',select);
      node.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();select()}});
    });
  }
  function renderSexSeries(){
    const host=$('#segment-sex-extra'),segments=segmentStats(S.filtered);
    if(!host||!segments.length)return;
    S.extraSexSelection ||= new Set(['F','M']);
    const series=['F','M'].map((sex,i)=>({sex,label:sex==='F'?'Kvinnor':'Män',color:i?'#b48b44':'#3e7250',values:segments.map(s=>{
      const times=s.obs.filter(o=>o.r.sex===sex).map(o=>o.seconds);
      return {n:times.length,value:times.length>=5?median(times):null};
    })}));
    const all=series.flatMap(s=>s.values.map(v=>v.value)).filter(num);
    if(!all.length)return;
    const W=700,H=220,P=40,max=Math.max(...all),step=(W-2*P)/Math.max(1,segments.length);
    const x=i=>P+(i+.5)*step,y=v=>H-P-v/max*(H-2*P);
    const body=`<line class="axis" x1="${P}" x2="${W-P}" y1="${H-P}" y2="${H-P}"/><text x="5" y="${P}">${time(max)}</text>`+series.filter(s=>S.extraSexSelection.has(s.sex)).map(s=>{
      let path='',previous=false;
      const dots=s.values.map((v,i)=>{
        if(!num(v.value)){previous=false;return ''}
        path+=`${previous?'L':'M'}${x(i)},${y(v.value)} `;previous=true;
        return `<circle cx="${x(i)}" cy="${y(v.value)}" r="4" fill="${s.color}"><title>${s.label} · ${html(segments[i].from.name)} → ${html(segments[i].to.name)} · ${time(v.value)} · n=${v.n}</title></circle>`;
      }).join('');
      return `<path d="${path}" fill="none" stroke="${s.color}" stroke-width="2.5"/>${dots}`;
    }).join('');
    host.insertAdjacentHTML('beforeend',`<div class="series-choices">${series.map(s=>`<label><input type="checkbox" data-sex-series="${s.sex}" ${S.extraSexSelection.has(s.sex)?'checked':''}><i style="background:${s.color}"></i>${s.label}</label>`).join('')}</div>${svg(W,H,body,'Kvinna och man: segmentmedianer på gemensam tidsaxel')}<p class="small muted">Samma tidsaxel även när en serie döljs. Varje punkt kräver fem exakta segmentobservationer; saknad punkt bryter linjen.</p>`);
    $$('[data-sex-series]',host).forEach(input=>input.addEventListener('change',()=>{
      if(input.checked)S.extraSexSelection.add(input.dataset.sexSeries);else S.extraSexSelection.delete(input.dataset.sexSeries);
      renderSegmentSex();renderSexSeries();
    }));
  }
  function renderClassSeries(){
    const host=$('#segment-groups'),segments=segmentStats(S.filtered);
    if(!host||!segments.length)return;
    const classes=Object.entries(collections(S.filtered.map(r=>r.class_name).filter(Boolean))).sort((a,b)=>b[1]-a[1]).slice(0,8).map(x=>x[0]);
    if(!classes.length)return;
    if(!S.extraClassSelection||![...S.extraClassSelection].some(name=>classes.includes(name)))S.extraClassSelection=new Set(classes.slice(0,3));
    const colors=['#315f41','#af8740','#6b7f9e','#a86659','#76639a','#638b7c','#9d7186','#697c43'];
    const series=classes.map((name,i)=>({name,color:colors[i],values:segments.map(s=>{
      const indices=s.obs.filter(o=>paceDistanceSupported(s)&&o.r.class_name===name&&finish(o.r)&&num(S.race.nominal_km)&&S.race.nominal_km>0)
        .map(o=>100*(o.r.finish_seconds/S.race.nominal_km)/(o.seconds/s.km)).filter(v=>num(v)&&v>0);
      return {n:indices.length,value:indices.length>=5?median(indices):null};
    })}));
    const all=series.flatMap(s=>s.values.map(v=>v.value)).filter(num);
    if(!all.length)return;
    const W=700,H=230,P=40,lo=Math.min(90,...all),hi=Math.max(110,...all),step=(W-2*P)/Math.max(1,segments.length);
    const x=i=>P+(i+.5)*step,y=v=>H-P-(v-lo)/Math.max(1,hi-lo)*(H-2*P);
    const body=`<line class="axis" x1="${P}" x2="${W-P}" y1="${y(100)}" y2="${y(100)}"/><text x="4" y="${y(100)-5}">100</text>`+series.filter(s=>S.extraClassSelection.has(s.name)).map(s=>{
      let path='',previous=false;
      const dots=s.values.map((v,i)=>{
        if(!num(v.value)){previous=false;return ''}
        path+=`${previous?'L':'M'}${x(i)},${y(v.value)} `;previous=true;
        return `<circle cx="${x(i)}" cy="${y(v.value)}" r="4" fill="${s.color}"><title>${html(s.name)} · ${html(segments[i].to.name)} · ${v.value.toFixed(1)} · n=${v.n}</title></circle>`;
      }).join('');
      return `<path d="${path}" fill="none" stroke="${s.color}" stroke-width="2.5"/>${dots}`;
    }).join('');
    host.insertAdjacentHTML('beforeend',`<p class="small muted">Välj högst fem källklasser. Median av individuellt pacingindex per segment; 100 = eget loppmedel.</p><div class="series-choices">${series.map(s=>`<label><input type="checkbox" data-class-series="${html(s.name)}" ${S.extraClassSelection.has(s.name)?'checked':''} ${S.extraClassSelection.size>=5&&!S.extraClassSelection.has(s.name)?'disabled':''}><i style="background:${s.color}"></i>${html(s.name)}</label>`).join('')}</div>${svg(W,H,body,'Klassers pacingindex på gemensam segmentaxel')}<p class="small muted">Varje punkt kräver fem exakta observationer i klassen; saknad punkt bryter linjen.</p>`);
    $$('[data-class-series]',host).forEach(input=>input.addEventListener('change',()=>{
      if(input.checked&&S.extraClassSelection.size<5)S.extraClassSelection.add(input.dataset.classSeries);
      else if(!input.checked)S.extraClassSelection.delete(input.dataset.classSeries);
      renderSegmentGroups();renderClassSeries();
    }));
  }
  function renderSegments(){renderQ1090();renderRetention();renderPacingIndex();renderSegmentSex();renderSexSeries();renderSegmentGroups();renderClassSeries();renderHeatmap();renderCheckpointSpread();syncSegmentOverlay()}
  function renderFiltered(){renderSexCompletion();renderGoal();renderAge();renderClub();renderPlacementGain();renderFinishProgress();renderSegments();renderCourseIntel();renderGroupTable()}
  function wire(){if(wired)return;wired=true;document.addEventListener('click',e=>{const info=e.target.closest('[data-help-extra]');if(info){$('#help-title').textContent=info.closest('.panel')?.querySelector('h3')?.textContent||'Metod';$('#help-content').textContent=extraHelp[info.dataset.helpExtra]||'';$('#help-dialog').showModal();return}if(e.target.closest('[data-segment],[data-select-segment]'))setTimeout(renderSegments,0)});document.addEventListener('change',e=>{if(e.target.matches('#podium-segment'))setTimeout(renderSegments,0)});document.addEventListener('click',e=>{if(e.target.matches('#goal-placement-run'))renderGoal()});document.addEventListener('keydown',e=>{if(e.target.matches('#goal-placement-time')&&e.key==='Enter')renderGoal()})}
  function renderAll(){ensurePanels();wire();renderFiltered();renderCourseIntel();renderMapHistory();renderHistoryPerformance();renderSexHistory();renderFingerprint();renderProvenance();renderCoverage()}
  return {renderAll,renderFiltered,renderSegments};
})();

init();
})();
