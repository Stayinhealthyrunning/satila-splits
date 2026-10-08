(()=>{'use strict';
const $=s=>document.querySelector(s);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const finite=value=>value!==null&&value!==undefined&&value!==''&&Number.isFinite(Number(value));
const formatTime=value=>!finite(value)||Number(value)<0?'—':(()=>{let n=Math.round(Number(value)),h=Math.floor(n/3600),m=Math.floor(n%3600/60),s=String(n%60).padStart(2,'0');return h?`${h}:${String(m).padStart(2,'0')}:${s}`:`${m}:${s}`})();
const median=values=>{const a=(values||[]).filter(finite).map(Number).sort((x,y)=>x-y);if(!a.length)return null;const i=Math.floor(a.length/2);return a.length%2?a[i]:(a[i-1]+a[i])/2};
const tokenFor=(raceKey,id)=>String(raceKey)+'::'+String(id);
const parseToken=token=>{const i=String(token||'').indexOf('::');return i>0?{raceKey:String(token).slice(0,i),id:String(token).slice(i+2)}:null};
const normalized=value=>String(value||'').trim().toLocaleLowerCase('sv').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
const resultMatches=(record,query)=>{const q=normalized(query);return q&&normalized(`${record?.name||''} ${record?.bib||''} ${record?.club||''}`).includes(q)};
const finish=row=>row?.status==='FINISHED'&&finite(row.finish_seconds)&&Number(row.finish_seconds)>0;
function promotedGroup(edition){
  const version=edition?.course_version,status=edition?.route_status;
  if(!version||!['organizer_2025_2026_reuse_assumption','official_verified'].includes(status))return null;
  if(/unverified|candidate|pending/i.test(String(version)))return null;
  return version;
}
function wholeCourseComparable(a,b){const ga=promotedGroup(a),gb=promotedGroup(b);return Boolean(ga&&gb&&ga===gb&&a?.family===b?.family)}
function fieldMetrics(race,record){
  if(!finish(record))return{percentile:null,index:null,median:null,n:0};
  const finishers=(race?.results||[]).filter(finish),times=finishers.map(row=>Number(row.finish_seconds)),med=median(times);
  const slower=finishers.filter(row=>Number(row.finish_seconds)>Number(record.finish_seconds)).length;
  return{percentile:finishers.length?100*slower/finishers.length:null,index:finite(med)&&Number(record.finish_seconds)>0?100*Number(med)/Number(record.finish_seconds):null,median:med,n:finishers.length};
}
function observationMap(race,record){
  const stations=new Map((race?.stations||[]).map(st=>[st.uid,st])),out=new Map();
  for(const split of race?.splits||[])if(String(split.result_id)===String(record.id)){const st=stations.get(split.station_uid);if(st&&finite(split.elapsed_seconds))out.set(normalized(st.name),{station:st,elapsed:Number(split.elapsed_seconds),place:finite(split.place)?Number(split.place):null});}
  return out;
}
function comparableCheckpoints(left,right,enabled){
  if(!enabled)return[];
  const a=observationMap(left.race,left.record),b=observationMap(right.race,right.record),rows=[];
  for(const [key,x] of a){const y=b.get(key);if(!y)continue;const kmA=Number(x.station.km),kmB=Number(y.station.km);if(!finite(kmA)||!finite(kmB)||Math.abs(kmA-kmB)>.25)continue;rows.push({name:x.station.name,km:(kmA+kmB)/2,a:x.elapsed,b:y.elapsed,gap:y.elapsed-x.elapsed,placeA:x.place,placeB:y.place});}
  return rows.sort((x,y)=>x.km-y.km);
}
function model(left,right){
  const comparable=wholeCourseComparable(left.edition,right.edition),sameCourse=Boolean(comparable&&left.edition.course_version===right.edition.course_version),fa=fieldMetrics(left.race,left.record),fb=fieldMetrics(right.race,right.record);
  return{left,right,comparable,sameCourse,finishGap:comparable&&finish(left.record)&&finish(right.record)?Number(right.record.finish_seconds)-Number(left.record.finish_seconds):null,fieldA:fa,fieldB:fb,checkpoints:comparableCheckpoints(left,right,sameCourse)};
}
function pct(value){return finite(value)?Number(value).toFixed(1).replace('.',',')+' %':'—'}
function index(value){return finite(value)?Number(value).toFixed(1).replace('.',','):'—'}
function signed(value){return !finite(value)?'—':Number(value)===0?'0:00':(Number(value)>0?'+':'−')+formatTime(Math.abs(Number(value)))}
function participant(item,field,side){
  const r=item.record,e=item.edition;
  return `<article class="multi-year-person"><span class="multi-year-side">${side}</span><div><p class="eyebrow">${e.year} · #${esc(r.bib||'–')}</p><h3>${esc(r.name)}</h3><dl><div><dt>Sluttid</dt><dd>${formatTime(r.finish_seconds)}</dd></div><div><dt>Totalplats</dt><dd>${finite(r.place)?'#'+esc(r.place):'—'}</dd></div><div><dt>Snabbare än fältet</dt><dd>${pct(field.percentile)}</dd></div><div><dt>Fältindex</dt><dd>${index(field.index)}</dd></div></dl><small>Fältindex 100 = mediantid i ${e.year}; över 100 = snabbare än årets median.</small></div></article>`;
}
function render(model){
  const direct=finite(model.finishGap)?`<strong>${model.finishGap===0?'Samma sluttid':model.finishGap>0?'A snabbare med '+formatTime(model.finishGap):'B snabbare med '+formatTime(Math.abs(model.finishGap))}</strong><span>Direkt tidsjämförelse är tillåten eftersom upplagorna har samma uttryckligen godkända banversion.</span>`:`<strong>Jämför prestation relativt respektive års fält</strong><span>Sluttiderna visas som källvärden men rangordnas inte mot varandra eftersom banorna saknar uttryckligt stöd för direkt helbanetidsjämförelse.</span>`;
  const checkpoints=model.checkpoints.length?`<section class="multi-year-section"><h3>Gemensamma verifierade passager</h3><div class="table-scroll"><table><thead><tr><th>Kontroll</th><th>A</th><th>B</th><th>Lucka B−A</th><th>Plats A/B</th></tr></thead><tbody>${model.checkpoints.map(row=>`<tr><th>${esc(row.name)}</th><td>${formatTime(row.a)}</td><td>${formatTime(row.b)}</td><td>${signed(row.gap)}</td><td>${finite(row.placeA)?'#'+row.placeA:'—'} / ${finite(row.placeB)?'#'+row.placeB:'—'}</td></tr>`).join('')}</tbody></table></div></section>`:`<section class="multi-year-section multi-year-warning"><h3>Passage- och segmentduell är avstängd</h3><p>Sätila använder inte deltagar-GPX eller liknande visningsgeometri som bevis för att två historiska upplagor hade identisk bana. Därför fylls inga kontroll- eller segmentjämförelser ut när sådant stöd saknas.</p></section>`;
  return `<div class="multi-year-comparison"><div class="multi-year-people">${participant(model.left,model.fieldA,'A')}${participant(model.right,model.fieldB,'B')}</div><section class="multi-year-finish"><p class="eyebrow">PRESTATION ÖVER ÅR</p>${direct}</section>${checkpoints}<section class="multi-year-method"><strong>Så läses jämförelsen</strong><p>Fältpercentil och fältindex beräknas separat inom varje upplaga och kan därför användas för att bedöma hur prestationen stod sig mot just det årets startfält. Direkt tidsgap visas endast när banjämförbarheten är uttryckligen verifierad enligt Sätilas kurskontrakt.</p></section></div>`;
}
function create(){
  const root=$('#multi-year-comparison'),year=$('#multi-year-year'),search=$('#multi-year-search'),suggestions=$('#multi-year-suggestions'),chips=$('#multi-year-selected'),button=$('#open-multi-year-comparison'),feedback=$('#multi-year-feedback'),dialog=$('#multi-year-dialog'),body=$('#multi-year-dialog-body');
  if(!root||!year||!search||!suggestions||!chips||!button||!dialog||!body)return null;
  let boot=null,family=null,selected=[],suggestionMap=new Map(),cache=new Map(),searchVersion=0,restoredFamily=null,mapController=null;
  const editions=()=>boot?.editions?.filter(ed=>ed.family===family).slice().sort((a,b)=>b.year-a.year)||[];
  async function loadEdition(ed){
    if(!cache.has(ed.race_key))cache.set(ed.race_key,fetch('data/races/'+encodeURIComponent(ed.race_key)+'.json').then(r=>{if(!r.ok)throw Error('Upplagan kunde inte läsas');return r.json()}).then(race=>({edition:ed,race})).catch(error=>{cache.delete(ed.race_key);throw error;}));
    return cache.get(ed.race_key);
  }
  function hide(){suggestions.hidden=true;suggestions.innerHTML='';search.setAttribute('aria-expanded','false');suggestionMap.clear()}
  function renderSelected(){
    chips.innerHTML=selected.length?selected.map((item,i)=>`<button type="button" data-multi-year-remove="${esc(item.token)}"><i>${i+1}</i><span>${esc(item.record.name)} · ${item.edition.year}${item.record.bib?' · #'+esc(item.record.bib):''}</span><b>×</b></button>`).join(''):'<span class="muted small">Välj exakt två resultat. Samma namn kan väljas från olika år utan att systemet antar att identiteten är verifierad.</span>';
    button.disabled=selected.length!==2;button.textContent=selected.length===2?'Jämför på kartan och mellan år':'Välj två resultat för kartjämförelse';
    feedback.textContent=selected.length===2?(selected[0].edition.year===selected[1].edition.year?'Två resultat från samma år valda.':'Olika år valda · årsbanorna visas var för sig där verifierad geometri finns.'):'';
  }
  async function runSearch(){
    const version=++searchVersion,q=search.value.trim();if(!q){hide();return}
    suggestions.hidden=false;suggestions.innerHTML='<p class="muted small">Laddar historiska resultat…</p>';search.setAttribute('aria-expanded','true');
    const metas=year.value==='all'?editions():editions().filter(ed=>String(ed.year)===year.value),loaded=(await Promise.allSettled(metas.map(loadEdition))).filter(x=>x.status==='fulfilled').map(x=>x.value);if(version!==searchVersion)return;
    const chosen=new Set(selected.map(x=>x.token)),needle=normalized(q),matches=[];
    for(const edition of loaded)for(const record of edition.race.results||[])if(resultMatches(record,q)){const token=tokenFor(edition.edition.race_key,record.id);if(!chosen.has(token))matches.push({...edition,record,token});}
    matches.sort((a,b)=>{const an=normalized(a.record.name),bn=normalized(b.record.name);return (an.startsWith(needle)?0:1)-(bn.startsWith(needle)?0:1)||b.edition.year-a.edition.year||(Number(a.record.place)||99999)-(Number(b.record.place)||99999)||an.localeCompare(bn,'sv')});
    suggestionMap=new Map(matches.slice(0,16).map(item=>[item.token,item]));
    suggestions.innerHTML=suggestionMap.size?[...suggestionMap.values()].map(item=>`<button type="button" class="suggestion" data-multi-year-add="${esc(item.token)}"><span><strong>${esc(item.record.name)}</strong><small>${item.edition.year}${item.record.bib?' · #'+esc(item.record.bib):''}${item.record.club?' · '+esc(item.record.club):''}</small></span><b>${formatTime(item.record.finish_seconds)}</b></button>`).join(''):'<p class="muted small">Ingen löpare hittades i valda år.</p>';
  }
  function shareUrl(){
    const url=new URL(location.href);for(const key of ['myFamily','myA','myB'])url.searchParams.delete(key);
    if(selected.length===2){url.searchParams.set('myFamily',family);url.searchParams.set('myA',selected[0].token);url.searchParams.set('myB',selected[1].token)}return url.href;
  }
  function observedAnchors(item,route){
    const length=Number(route.geometry_length_km)||Number(route.points?.at(-1)?.[0])||0;
    const nominal=Number(item.edition.nominal_km||item.race.nominal_km)||0;
    if(length<=0||nominal<=0||['DNS','UNKNOWN'].includes(item.record.status))return[];
    const stations=new Map((item.race.stations||[]).map(st=>[String(st.uid),st]));
    const rows=(item.race.splits||[]).filter(row=>String(row.result_id)===String(item.record.id)).map(row=>({row,st:stations.get(String(row.station_uid))})).filter(x=>x.st&&finite(x.row.elapsed_seconds)&&finite(x.st.km)&&Number(x.st.km)>0&&Number(x.st.km)<=nominal+.1&&(!x.st.is_finish||finish(item.record))).sort((a,b)=>Number(a.st.km)-Number(b.st.km));
    const anchors=[{time:0,distance:0}];let latest=anchors[0];
    for(const {row,st} of rows){const time=Number(row.elapsed_seconds),distance=Math.min(length,Number(st.km)*length/nominal);if(time>latest.time&&distance>latest.distance){latest={time,distance};anchors.push(latest);}}
    if(finish(item.record)&&Number(item.record.finish_seconds)>latest.time&&length>latest.distance)anchors.push({time:Number(item.record.finish_seconds),distance:length});
    return anchors;
  }
  async function openComparison(){
    if(selected.length!==2)return;
    mapController?.destroy?.();mapController=null;
    body.innerHTML='<section id="multi-year-map-root" class="multi-year-map-card"><p class="muted small">Laddar årsbanor…</p></section>'+render(model(selected[0],selected[1]));
    if(!dialog.open)dialog.showModal();
    const token=selected.map(x=>x.token).join('|');
    const items=await Promise.all(selected.map(async item=>{
      const file=item.edition.route_file;
      if(!file)return{year:item.edition.year,name:item.record.name,provenance:'Rutt saknas för upplagan',points:[],anchors:[]};
      try{
        const response=await fetch('data/'+file);if(!response.ok)throw Error('route missing');const route=await response.json();
        const reference=route.type==='OFFICIAL_ORGANIZER'?'Arrangörs-GPX · återanvändning 2025/2026 enligt dokumenterat antagande':route.type==='VERIFIED_PARTICIPANT'?'Deltagarbaserad GPX · endast visningsgeometri':String(route.type||'Banreferens');
        return {year:item.edition.year,name:item.record.name,provenance:reference,
          points:(route.points||[]).map(point=>[point[1],point[2],point[0]]),
          anchors:observedAnchors(item,route)};
      }catch{return{year:item.edition.year,name:item.record.name,provenance:'Publicerbar rutt saknas',points:[],anchors:[]};}
    }));
    if(!dialog.open||selected.map(x=>x.token).join('|')!==token)return;
    mapController=globalThis.LoppMultiYearRouteMap?.mount(body.querySelector('#multi-year-map-root'),items);
  }
  async function restore(){
    if(restoredFamily===family)return;const params=new URLSearchParams(location.search);if(params.get('myFamily')!==family){restoredFamily=family;return}
    const tokens=[params.get('myA'),params.get('myB')].filter(Boolean);if(tokens.length!==2){restoredFamily=family;return}const rows=[];
    for(const token of tokens){const parsed=parseToken(token),ed=editions().find(x=>x.race_key===parsed?.raceKey);if(!ed)return;const loaded=await loadEdition(ed),record=(loaded.race.results||[]).find(x=>String(x.id)===parsed.id);if(!record)return;rows.push({...loaded,record,token})}
    selected=rows;restoredFamily=family;renderSelected();await openComparison();
  }
  root.addEventListener('click',event=>{const add=event.target.closest('[data-multi-year-add]'),remove=event.target.closest('[data-multi-year-remove]');if(add){const item=suggestionMap.get(add.dataset.multiYearAdd);if(item&&!selected.some(x=>x.token===item.token)){selected=selected.length<2?[...selected,item]:[selected[1],item];renderSelected();search.value='';hide();search.focus()}return}if(remove){selected=selected.filter(x=>x.token!==remove.dataset.multiYearRemove);renderSelected()}});
  function updatePicker(){
    const latest=editions()[0]?.year,current=String(year.value)===String(latest);
    root.hidden=current;
    const regular=$('#duel-current-picker');if(regular)regular.hidden=!current;
    if(!current)search.focus();else $('#map-duel-search')?.focus();
  }
  year.addEventListener('change',()=>{search.value='';hide();updatePicker()});search.addEventListener('input',runSearch);search.addEventListener('focus',runSearch);search.addEventListener('keydown',event=>{if(event.key==='Escape')hide();if(event.key==='Enter'){const first=suggestions.querySelector('[data-multi-year-add]');if(first){event.preventDefault();first.click()}}});
  button.addEventListener('click',openComparison);$('#close-multi-year-dialog')?.addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>{mapController?.destroy?.();mapController=null});$('#multi-year-share')?.addEventListener('click',async event=>{try{await navigator.clipboard.writeText(shareUrl());event.currentTarget.textContent='✓ Länk kopierad';setTimeout(()=>event.currentTarget.textContent='↗ Dela jämförelse',1600)}catch{prompt('Kopiera länken:',shareUrl())}});
  document.addEventListener('pointerdown',event=>{if(!event.target.closest('#multi-year-comparison'))hide()});
  renderSelected();
  return{
    init(payload){boot=payload.boot;},
    setContext(nextFamily){const changed=family!==nextFamily;family=nextFamily;if(changed){selected=[];restoredFamily=null}const latest=editions()[0]?.year,previous=changed?String(latest):year.value;year.innerHTML=editions().map(ed=>`<option value="${ed.year}">${ed.year}</option>`).join('')+'<option value="all">Alla år</option>';const deepLink=new URLSearchParams(location.search).get('myFamily')===family;year.value=deepLink?'all':editions().some(ed=>String(ed.year)===String(previous))?String(previous):String(latest);renderSelected();if(changed)hide();updatePicker();restore().catch(console.error)}
  };
}
const controller=create();
window.SatilaMultiYearComparison={
  init(payload){controller?.init(payload)},
  setContext(family,year){controller?.setContext(family,year)},
  _test:{promotedGroup,wholeCourseComparable,fieldMetrics,model}
};
})();