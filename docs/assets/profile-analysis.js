(function(){
'use strict';
let current=null;

const median=values=>{
  const xs=values.map(Number).filter(Number.isFinite).sort((a,b)=>a-b);
  if(!xs.length)return null;
  const m=Math.floor(xs.length/2);
  return xs.length%2?xs[m]:(xs[m-1]+xs[m])/2;
};
const finite=value=>value!==null&&value!==undefined&&value!==''&&Number.isFinite(Number(value));
const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
const signedTime=(seconds,fmt)=>{
  if(!finite(seconds))return '—';
  const value=Math.round(Number(seconds));
  if(Math.abs(value)<1)return '0:00';
  return (value>0?'+':'−')+fmt(Math.abs(value));
};
const pct=value=>finite(value)?Math.round(Number(value))+' %':'—';

function finishedRows(ctx,filter=()=>true){
  return ctx.records().filter(row=>ctx.finish(row)&&finite(row.finish_seconds)&&filter(row));
}
function rankInfo(ctx,record,rows){
  const sorted=rows.slice().sort((a,b)=>a.finish_seconds-b.finish_seconds);
  const index=sorted.findIndex(row=>String(row.id)===String(record.id));
  if(index<0)return {place:null,percentile:null,n:sorted.length};
  return {
    place:index+1,
    percentile:sorted.length?Math.round(100*(sorted.length-index-1)/sorted.length):null,
    n:sorted.length
  };
}
function sexKey(ctx,record){return ctx.analyticalSex(record)}
function groups(ctx,record){
  const sex=sexKey(ctx,record);
  const all=finishedRows(ctx);
  const classRows=record.class_name?finishedRows(ctx,row=>row.class_name===record.class_name):[];
  const sexRows=sex?finishedRows(ctx,row=>ctx.analyticalSex(row)===sex):[];
  return {
    field:{id:'field',label:'Fältet',rows:all,...rankInfo(ctx,record,all)},
    class:{id:'class',label:record.class_name||'Klassen',rows:classRows,...rankInfo(ctx,record,classRows)},
    sex:{id:'sex',label:sex==='F'?'Kvinnor':sex==='M'?'Män':'Kön',rows:sexRows,...rankInfo(ctx,record,sexRows)}
  };
}
function coverage(ctx,record){
  const points=ctx.boundaries().filter(point=>finite(point.km)&&Number(point.km)>0);
  return {observed:points.filter(point=>ctx.observed(record,point)).length,total:points.length};
}
function segmentData(ctx,record,rows){
  const stats=ctx.segmentStats(rows),parts=ctx.pairs(record);
  return parts.map(part=>{
    const stat=stats.find(item=>item.index===part.index);
    const relative=stat&&stat.n>=5&&finite(stat.median)&&part.seconds>0?100*stat.median/part.seconds:null;
    return {...part,stat,relative};
  });
}
function strengthClass(value){
  if(!finite(value))return 'missing';
  if(value>=108)return 'very-strong';
  if(value>=102)return 'strong';
  if(value>=98)return 'level';
  if(value>=92)return 'weak';
  return 'very-weak';
}
function strengthLabel(value){
  if(!finite(value))return ['—','Underlag saknas'];
  if(value>=108)return ['↑↑','Mycket stark'];
  if(value>=102)return ['↑','Stark'];
  if(value>=98)return ['•','I nivå'];
  if(value>=92)return ['↓','Svagare'];
  return ['↓↓','Tydligt svagare'];
}
function story(ctx,record,groupSet,segments){
  const field=groupSet.field,place=record.place??field.place;
  if(record.status==='DNS')return 'Ingen start är registrerad för den här deltagaren i den valda upplagan.';
  if(!ctx.finish(record)){
    const passages=ctx.splitsFor(record.id).filter(item=>finite(item.elapsed_seconds)).sort((a,b)=>a.elapsed_seconds-b.elapsed_seconds);
    const last=passages.at(-1);
    return last?'Senaste publicerade passagen är '+ctx.time(last.elapsed_seconds)+'. Analysen nedan använder bara de kontrolltider som faktiskt finns publicerade.':'Resultatet saknar tillräckliga publicerade passager för en full individuell loppanalys.';
  }
  const strongest=segments.filter(item=>finite(item.relative)).sort((a,b)=>b.relative-a.relative)[0];
  const placement=place?' som #'+place:'';
  let text='Loppet slutade på '+ctx.time(record.finish_seconds)+placement+'.';
  if(finite(field.percentile))text+=' Det var snabbare än '+field.percentile+' % av fullföljarna i samma upplaga.';
  if(strongest)text+=' Starkaste observerade delsträckan relativt fältet var '+strongest.from.name+' → '+strongest.to.name+' ('+Math.round(strongest.relative)+' % av fältmedianens fartindex).';
  return text;
}
function checkpointPoints(ctx,record,rows){
  return ctx.boundaries().filter(point=>finite(point.km)&&Number(point.km)>0).map(point=>{
    const own=ctx.observed(record,point);
    const cohort=rows.map(row=>ctx.observed(row,point)?.elapsed_seconds).filter(finite);
    const reference=cohort.length>=5?median(cohort):null;
    return {
      name:point.name,
      km:Number(point.km),
      own:own&&finite(own.elapsed_seconds)?Number(own.elapsed_seconds):null,
      place:own&&finite(own.place)?Number(own.place):null,
      reference,
      n:cohort.length,
      gap:own&&finite(own.elapsed_seconds)&&finite(reference)?reference-Number(own.elapsed_seconds):null
    };
  });
}
function pathRuns(points,getY,x){
  const runs=[];let run=[];
  points.forEach((point,index)=>{
    const value=getY(point);
    if(!finite(value)){if(run.length)runs.push(run);run=[];return}
    run.push([x(index),Number(value),point]);
  });
  if(run.length)runs.push(run);
  return runs;
}
function gapChart(ctx,points){
  const W=760,H=238,L=62,R=18,T=20,B=58;
  const values=points.map(p=>p.gap).filter(finite);
  if(values.length<2)return '<p class="empty">Minst två verkliga passager med referensunderlag krävs för gapgrafen.</p>';
  const maxAbs=Math.max(60,...values.map(v=>Math.abs(v)));
  const x=index=>L+index*(W-L-R)/Math.max(1,points.length-1);
  const y=value=>T+(maxAbs-Number(value))/(2*maxAbs)*(H-T-B);
  let body='';
  [-1,-.5,0,.5,1].forEach(factor=>{
    const value=maxAbs*factor,yy=y(value);
    body+='<line class="'+(factor===0?'profile-zero':'profile-grid')+'" x1="'+L+'" x2="'+(W-R)+'" y1="'+yy.toFixed(1)+'" y2="'+yy.toFixed(1)+'"/>';
    body+='<text x="'+(L-7)+'" y="'+(yy+4).toFixed(1)+'" text-anchor="end">'+(factor===0?'0:00':signedTime(value,ctx.time))+'</text>';
  });
  const runs=pathRuns(points,p=>p.gap,x);
  runs.forEach(run=>{body+='<path class="profile-line" d="'+run.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+','+y(p[1]).toFixed(1)).join(' ')+'"/>';});
  points.forEach((point,index)=>{
    if(!finite(point.gap))return;
    body+='<circle class="profile-point" cx="'+x(index).toFixed(1)+'" cy="'+y(point.gap).toFixed(1)+'" r="5"><title>'+ctx.html(point.name)+' · '+ctx.html(signedTime(point.gap,ctx.time))+' mot median · n='+point.n+'</title></circle>';
  });
  points.forEach((point,index)=>{
    body+='<text class="profile-axis-label" transform="translate('+x(index).toFixed(1)+' '+(H-33)+') rotate(-28)" text-anchor="end">'+ctx.html(point.name)+'</text>';
  });
  return ctx.svg(W,H,body,'Tidslucka mot vald referens genom loppet');
}
function placementChart(ctx,points){
  const W=760,H=238,L=54,R=18,T=20,B=58;
  const values=points.map(p=>p.place).filter(finite);
  if(values.length<2)return '<p class="empty">Minst två publicerade totalplaceringar krävs för placeringsresan.</p>';
  const lo=Math.max(1,Math.min(...values)-2),hi=Math.max(lo+4,Math.max(...values)+2);
  const x=index=>L+index*(W-L-R)/Math.max(1,points.length-1);
  const y=value=>T+(Number(value)-lo)/(hi-lo)*(H-T-B);
  let body='';
  for(let i=0;i<5;i++){
    const value=lo+(hi-lo)*i/4,yy=y(value);
    body+='<line class="profile-grid" x1="'+L+'" x2="'+(W-R)+'" y1="'+yy.toFixed(1)+'" y2="'+yy.toFixed(1)+'"/>';
    body+='<text x="'+(L-7)+'" y="'+(yy+4).toFixed(1)+'" text-anchor="end">#'+Math.round(value)+'</text>';
  }
  pathRuns(points,p=>p.place,x).forEach(run=>{
    body+='<path class="profile-line" d="'+run.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+','+y(p[1]).toFixed(1)).join(' ')+'"/>';
  });
  points.forEach((point,index)=>{
    if(!finite(point.place))return;
    body+='<circle class="profile-point" cx="'+x(index).toFixed(1)+'" cy="'+y(point.place).toFixed(1)+'" r="5"><title>'+ctx.html(point.name)+' · #'+point.place+'</title></circle>';
  });
  points.forEach((point,index)=>{
    body+='<text class="profile-axis-label" transform="translate('+x(index).toFixed(1)+' '+(H-33)+') rotate(-28)" text-anchor="end">'+ctx.html(point.name)+'</text>';
  });
  return ctx.svg(W,H,body,'Publicerad totalplacering genom loppet');
}
function relativeChart(ctx,segments,label){
  const valid=segments.filter(item=>finite(item.relative));
  if(valid.length<2)return '<p class="empty">Minst två segment med fem referensobservationer krävs för relativ fart.</p>';
  const W=900,H=260,L=55,R=20,T=24,B=62;
  const values=valid.map(item=>item.relative),rawLo=Math.min(100,...values),rawHi=Math.max(100,...values),pad=Math.max(4,(rawHi-rawLo)*.18);
  const lo=Math.floor((rawLo-pad)/5)*5,hi=Math.ceil((rawHi+pad)/5)*5;
  const x=index=>L+index*(W-L-R)/Math.max(1,valid.length-1);
  const y=value=>T+(hi-Number(value))/(hi-lo)*(H-T-B);
  let body='';
  for(let i=0;i<6;i++){
    const value=lo+(hi-lo)*i/5,yy=y(value);
    body+='<line class="'+(Math.abs(value-100)<(hi-lo)/12?'profile-zero':'profile-grid')+'" x1="'+L+'" x2="'+(W-R)+'" y1="'+yy.toFixed(1)+'" y2="'+yy.toFixed(1)+'"/>';
    body+='<text x="'+(L-7)+'" y="'+(yy+4).toFixed(1)+'" text-anchor="end">'+Math.round(value)+' %</text>';
  }
  const d=valid.map((item,index)=>(index?'L':'M')+x(index).toFixed(1)+','+y(item.relative).toFixed(1)).join(' ');
  body+='<path class="profile-line" d="'+d+'"/>';
  valid.forEach((item,index)=>{
    const title=item.from.name+' → '+item.to.name+' · '+Math.round(item.relative)+' % mot '+label+' · n='+(item.stat?.n||0);
    body+='<circle class="profile-point" cx="'+x(index).toFixed(1)+'" cy="'+y(item.relative).toFixed(1)+'" r="5"><title>'+ctx.html(title)+'</title></circle>';
    body+='<text class="profile-axis-label" transform="translate('+x(index).toFixed(1)+' '+(H-35)+') rotate(-28)" text-anchor="end">'+ctx.html(item.to.name)+'</text>';
  });
  return ctx.svg(W,H,body,'Relativ fart segment för segment mot '+label);
}
function pacingRibbon(ctx,segments,label){
  if(!segments.length)return '<p class="empty">Inga kompletta segmentpar finns för löparen.</p>';
  return '<div class="profile-journey-ribbon">'+segments.map(item=>{
    const state=strengthClass(item.relative),words=strengthLabel(item.relative),own=ctx.paceDistanceSupported(item)?ctx.pace(item.seconds,item.km,ctx.S.unit):ctx.time(item.seconds);
    return '<article class="profile-pacing-block '+state+'"><span>'+ctx.html(item.from.name+' → '+item.to.name)+'</span><strong>'+ctx.html(own)+'</strong><em>'+words[0]+' '+(finite(item.relative)?Math.round(item.relative)+' %':'—')+'</em><small>'+ctx.html(words[1]+' mot '+label+(item.stat?' · n='+item.stat.n:''))+'</small></article>';
  }).join('')+'</div>';
}
function passageTable(ctx,record){
  let previous={name:'Start',seconds:0};
  const rows=ctx.S.race.stations.filter(st=>st.is_analysis_boundary&&finite(st.km)&&st.km>0).sort((a,b)=>a.sort-b.sort||a.km-b.km).map(st=>{
    const observation=ctx.observed(record,st),elapsed=observation?.elapsed_seconds;
    const valid=finite(elapsed)&&Number(elapsed)>previous.seconds;
    const split=valid?ctx.time(Number(elapsed)-previous.seconds):'—';
    const from=valid?previous.name:'—';
    if(valid)previous={name:st.name,seconds:Number(elapsed)};
    return '<tr><td>'+ctx.html(st.name)+'</td><td>'+ctx.fmtKm(st.km)+'</td><td>'+ctx.time(elapsed)+'</td><td>'+split+(valid?' <small>från '+ctx.html(from)+'</small>':'')+'</td><td>'+(observation?.place??'—')+'</td><td>'+(observation?'Observerad EQ TIME':'Passage saknas')+'</td></tr>';
  }).join('');
  return '<details class="profile-source-passages"><summary>Verifierade passager och källstatus</summary><div class="table-scroll"><table><thead><tr><th>Kontroll</th><th>km*</th><th>Ack. tid</th><th>Sedan föregående verifierade</th><th>Publicerad plats</th><th>Datakälla</th></tr></thead><tbody><tr><td>Start</td><td>0</td><td>0:00</td><td>—</td><td>—</td><td>Tidsnoll</td></tr>'+rows+'</tbody></table></div></details>';
}
function segmentTable(ctx,record,segments){
  if(!segments.length)return '<p class="empty">Inga kompletta observerade delsträckor finns för löparen.</p>';
  const rows=segments.map(item=>{
    const ack=ctx.observed(record,item.to)?.elapsed_seconds;
    const movement=finite(item.placeFrom)&&finite(item.placeTo)?Number(item.placeFrom)-Number(item.placeTo):null;
    return '<tr><td><strong>'+ctx.html(item.from.name+' → '+item.to.name)+'</strong><small>'+ctx.fmtKm(item.km)+' timing-km</small></td><td>'+ctx.time(ack)+'</td><td>'+ctx.time(item.seconds)+'</td><td>'+(ctx.paceDistanceSupported(item)?ctx.pace(item.seconds,item.km,ctx.S.unit):'Distans ej verifierad')+'</td><td>'+(item.placeTo?'#'+item.placeTo:'—')+'</td><td>'+(finite(movement)?(movement>0?'+':'')+Math.round(movement):'—')+'</td><td>'+ctx.time(item.stat?.median)+'</td><td>'+(finite(item.stat?.median)?signedTime(item.stat.median-item.seconds,ctx.time):'—')+'</td><td>'+(item.stat?.n??0)+'</td></tr>';
  }).join('');
  return '<section class="profile-split-section" id="profile-splits"><div class="profile-section-head"><div><p class="eyebrow">MELLANTIDER · ANALYTISKA DELSTRÄCKOR</p><h3>Från analysgräns till analysgräns</h3></div><span class="profile-pill">exakta ackumulerade tider</span></div><div class="table-scroll"><table class="profile-split-table"><thead><tr><th>Delsträcka</th><th>Ack. tid</th><th>Delsträckstid</th><th>Tempo</th><th>Plats</th><th>Förändring</th><th>Fältmedian*</th><th>Mot median</th><th>n</th></tr></thead><tbody>'+rows+'</tbody></table></div><p class="muted small">* Fältmedianen använder endast fullföljare med två verkliga passager på samma segment och kräver minst fem observationer. Tempo döljs där timingdistansen inte kan användas som fysisk distans.</p></section>';
}
function referenceAnchors(ctx,record,rows){
  const routeEnd=ctx.routePoints().at(-1)?.[0]||Number(ctx.S.race.nominal_km)||1;
  const nominal=Number(ctx.S.race.nominal_km)||routeEnd;
  const points=[{km:0,t:0,name:'Start',n:rows.length}];
  ctx.boundaries().filter(point=>finite(point.km)&&Number(point.km)>0).forEach(point=>{
    const values=rows.map(row=>ctx.observed(row,point)?.elapsed_seconds).filter(finite);
    if(values.length<5)return;
    const km=Math.min(routeEnd,Number(point.km)/nominal*routeEnd),t=median(values),last=points.at(-1);
    if(km>last.km+.0001&&finite(t)&&t>last.t)points.push({km,t,name:point.name,n:values.length});
  });
  if(points.length===1)return null;
  return points;
}
function interpolate(anchors,distance){
  if(!anchors||!anchors.length)return null;
  if(distance<=0)return 0;
  for(let i=1;i<anchors.length;i++){
    const a=anchors[i-1],b=anchors[i];
    if(distance<=b.km){
      const factor=(distance-a.km)/Math.max(.000001,b.km-a.km);
      return a.t+(b.t-a.t)*clamp(factor,0,1);
    }
  }
  return distance<=anchors.at(-1).km+.001?anchors.at(-1).t:null;
}
function replayState(ctx,record,groupSet){
  const routeEnd=ctx.routePoints().at(-1)?.[0]||Number(ctx.S.race.nominal_km)||1;
  const nominal=Number(ctx.S.race.nominal_km)||routeEnd;
  const places=ctx.boundaries().filter(point=>finite(point.km)&&Number(point.km)>0).map(point=>({
    km:Number(point.km)/nominal*routeEnd,
    name:point.name,
    observation:ctx.observed(record,point)
  })).filter(item=>item.observation);
  return {
    refs:{
      field:referenceAnchors(ctx,record,groupSet.field.rows),
      class:referenceAnchors(ctx,record,groupSet.class.rows),
      sex:referenceAnchors(ctx,record,groupSet.sex.rows)
    },
    places
  };
}
function gapText(value,ctx){
  if(!finite(value))return 'Underlag saknas';
  if(Math.abs(Number(value))<1)return 'I nivå med medianen';
  return ctx.time(Math.abs(Number(value)))+' '+(Number(value)>0?'före':'efter')+' medianen';
}
function renderJourney(record){
  if(!current||String(current.record.id)!==String(record.id))return;
  const {ctx,groupSet}=current;
  const options=[
    {id:'field',label:'Fältet',group:groupSet.field},
    {id:'class',label:'Klassen',group:groupSet.class},
    {id:'sex',label:groupSet.sex.label,group:groupSet.sex}
  ];
  if(!options.some(option=>option.id===current.referenceMode&&option.group.rows.length>=5))current.referenceMode='field';
  const selected=options.find(option=>option.id===current.referenceMode)||options[0],points=checkpointPoints(ctx,record,selected.group.rows),segments=segmentData(ctx,record,selected.group.rows);
  const placementValues=points.map(point=>point.place).filter(finite);
  const placementSummary=placementValues.length>=2?'Från #'+placementValues[0]+' till #'+placementValues.at(-1)+' · '+((placementValues[0]-placementValues.at(-1))>=0?'+':'')+(placementValues[0]-placementValues.at(-1))+' platser.':'Publicerade placeringsankare saknas.';
  const host=document.querySelector('#profile-journey');
  if(host)host.innerHTML='<section class="profile-journey"><header class="profile-journey-head"><div><p class="eyebrow">LOPPETS UTVECKLING</p><h3>När förändrades loppet?</h3><p>Se när tidslucka, placering och segmentstyrka förändrades. Saknade passager fylls inte ut i analysen.</p></div><div class="profile-reference" role="group" aria-label="Jämför med"><span>Jämför med</span>'+options.map(option=>'<button type="button" data-profile-reference="'+option.id+'" aria-pressed="'+String(option.id===selected.id)+'" '+(option.group.rows.length>=5?'':'disabled')+'>'+ctx.html(option.label)+' <small>n='+option.group.rows.length+(option.group.rows.length<5?' · för litet underlag':'')+'</small></button>').join('')+'</div></header><div class="profile-journey-grid"><article class="profile-journey-card"><div class="profile-section-head compact"><div><p class="eyebrow">GAPGRAF</p><h4>Tidslucka genom loppet</h4></div><span class="profile-pill">'+ctx.html(selected.label)+' · n='+selected.group.rows.length+'</span></div><p class="muted small">Positivt är före referensmedianen, negativt är efter.</p><div class="profile-chart-scroll">'+gapChart(ctx,points)+'</div><small class="profile-trust">Endast verkliga EQ Timing-passager används som punkter. Referensmedianen kräver minst fem observationer vid kontrollen.</small></article><article class="profile-journey-card"><div class="profile-section-head compact"><div><p class="eyebrow">PLACERINGSRESA</p><h4>Publicerad totalplacering</h4></div></div><div class="profile-chart-scroll">'+placementChart(ctx,points)+'</div><small class="profile-trust">'+ctx.html(placementSummary)+' Saknad publicerad placering bryter linjen.</small></article></div><article class="profile-journey-card profile-journey-pacing"><div class="profile-section-head compact"><div><p class="eyebrow">PACING-FINGERAVTRYCK</p><h4>Segment för segment</h4></div><span class="profile-pill">'+ctx.html(selected.label)+' · n='+selected.group.rows.length+'</span></div>'+pacingRibbon(ctx,segments,selected.label)+'<small class="profile-trust">100 % motsvarar referensgruppens median på exakt samma observerade delsträcka. Över 100 % är snabbare.</small></article><details class="profile-method"><summary>Så räknas det</summary><p>Analysen använder publicerade EQ Timing-passager. Segmentjämförelser kräver två verkliga ändankare för både löparen och referensfältet. Ingen uppskattad Replay-position används som tävlingsresultat.</p></details></section>';
  const relative=document.querySelector('#profile-relative');
  if(relative)relative.innerHTML='<section class="profile-relative-card"><div class="profile-section-head"><div><p class="eyebrow">RELATIV FART</p><h3>Fart mot '+ctx.html(selected.label.toLocaleLowerCase('sv'))+'</h3></div><span class="profile-pill">100 % = median</span></div><div class="profile-chart-scroll">'+relativeChart(ctx,segments,selected.label)+'</div></section>';
  document.querySelectorAll('[data-profile-reference]').forEach(button=>button.addEventListener('click',()=>{
    if(button.disabled)return;
    current.referenceMode=button.dataset.profileReference;
    renderJourney(record);
  }));
}
function bindShell(record){
  const {ctx}=current;
  document.querySelector('#profile-fav')?.addEventListener('click',()=>ctx.toggleFav(record.id));
  document.querySelector('#profile-add-compare')?.addEventListener('click',()=>{ctx.addCompare(record.id);render(record,ctx)});
  document.querySelector('#profile-share')?.addEventListener('click',async event=>{
    const hash=new URLSearchParams();
    hash.set('family',ctx.S.family);hash.set('year',String(ctx.S.year));hash.set('runner',String(record.id));
    const url=new URL(location.href);url.hash=hash.toString();
    const button=event.currentTarget;
    try{
      if(navigator.share)await navigator.share({title:record.name+' · Sätila Splits',text:'Individuell loppanalys',url:url.href});
      else if(navigator.clipboard?.writeText)await navigator.clipboard.writeText(url.href);
      else prompt('Kopiera länken:',url.href);
      button.textContent='✓ Länk kopierad';
      setTimeout(()=>button.textContent='Dela loppet',1600);
    }catch(error){if(error?.name!=='AbortError')prompt('Kopiera länken:',url.href)}
  });
  document.querySelectorAll('[data-profile-section]').forEach(button=>button.addEventListener('click',()=>{
    document.querySelector('#'+button.dataset.profileSection)?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
  }));
}
function render(record,ctx){
  const same=current&&String(current.record.id)===String(record.id);
  const groupSet=groups(ctx,record),fieldSegments=segmentData(ctx,record,groupSet.field.rows),cover=coverage(ctx,record),paceKm=ctx.wholeCoursePaceKm(ctx.S.race),field=groupSet.field,classInfo=groupSet.class,sexInfo=groupSet.sex;
  current={record,ctx,groupSet,referenceMode:same?current.referenceMode:'field',replay:replayState(ctx,record,groupSet)};
  const facts=[
    ['Sluttid',ctx.time(record.finish_seconds),record.status],
    ['Placering',record.place?'#'+record.place:(field.place?'#'+field.place:'—'),'total'],
    ['Klassplats',classInfo.place?'#'+classInfo.place:'—',record.class_name||'saknas'],
    ['Könsplats',sexInfo.place?'#'+sexInfo.place:'—',ctx.sexLabel(record)],
    ['Snittfart',finite(paceKm)?ctx.pace(record.finish_seconds,paceKm,ctx.S.unit):'—',finite(paceKm)?ctx.fmtKm(paceKm)+' km':'fysisk distans ej verifierad'],
    ['Snabbare än fältet',pct(field.percentile),'n='+field.n],
    ['Checkpointtäckning',cover.observed+'/'+cover.total,cover.observed===cover.total?'komplett':'partiell']
  ];
  const summaryStory=story(ctx,record,groupSet,fieldSegments);
  const passage=passageTable(ctx,record),split=segmentTable(ctx,record,fieldSegments);
  const shell='<header class="profile2-hero"><div><p class="eyebrow">DELTAGARANALYS · '+ctx.html((ctx.S.race.family||ctx.S.family).toUpperCase())+'</p><h2>'+ctx.html(record.name)+'</h2><p>'+(record.name==='Anonym löpare'?'':'#'+ctx.html(record.bib)+' · ')+ctx.html(record.class_name||'Klass saknas')+' · '+ctx.html(record.club||'Okänd klubb/ort')+' · '+ctx.html(ctx.sexLabel(record))+'</p></div><div class="profile2-hero-actions"><button type="button" class="btn text-btn" id="profile-fav">'+(ctx.S.favorites.includes(record.id)?'★ Sparad':'☆ Spara')+'</button><span class="profile-status">'+ctx.html(record.status)+'</span></div></header>'+
  '<nav class="profile-quick-nav" aria-label="Profilnavigation"><button type="button" data-profile-section="personal-summary">Sammanfattning</button><button type="button" data-profile-section="profile-replay">Replay</button><button type="button" data-profile-section="profile-journey">Loppets utveckling</button><button type="button" data-profile-section="profile-relative">Relativ fart</button><button type="button" data-profile-section="profile-splits">Mellantider</button></nav>'+
  '<div class="profile2-facts">'+facts.map(item=>'<article><span>'+ctx.html(item[0])+'</span><strong>'+ctx.html(item[1])+'</strong><small>'+ctx.html(item[2]||'')+'</small></article>').join('')+'</div>'+
  '<section class="personal-summary" id="personal-summary"><div class="profile-section-head"><div><p class="eyebrow">LOPPET I KORTHET</p><h3>'+(ctx.finish(record)?'Loppet i korthet':record.status==='DNS'?'Ingen start registrerad':'Loppet fram till sista passage')+'</h3></div><span class="profile-pill">'+ctx.html(record.status)+'</span></div><p class="personal-story">'+ctx.html(summaryStory)+'</p><div class="personal-summary-facts"><article><span>'+(ctx.finish(record)?'Sluttid':'Status')+'</span><strong>'+(ctx.finish(record)?ctx.time(record.finish_seconds):ctx.html(record.status))+'</strong></article><article><span>Placering</span><strong>'+(record.place?'#'+record.place:'—')+'</strong></article><article><span>Snabbare än</span><strong>'+pct(field.percentile)+'</strong><small>fullföljare i fältet</small></article><article><span>Checkpointtäckning</span><strong>'+cover.observed+'/'+cover.total+'</strong></article></div><div class="personal-summary-actions"><button type="button" class="btn green" id="profile-share">Dela loppet</button><button type="button" class="btn text-btn" id="profile-add-compare">'+(ctx.S.mapDuel.includes(record.id)?'Ta bort från jämförelse':'Välj till jämförelse')+'</button></div></section>'+
  '<section class="profile-replay-shell" id="profile-replay"><div class="profile-replay-top"><div><p class="eyebrow">REPLAY</p><h3>Se loppet utvecklas på banan</h3><p class="muted small">Positionen mellan verifierade passager är illustrativ. Resultat, tabeller och jämförelser använder bara källstödda observationer.</p></div><span class="profile-pill">EQ Timing + publicerad rutt</span></div><div class="profile-replay-grid"><aside class="profile-replay-live"><div class="profile-column-head"><p class="eyebrow">LOPPET JUST NU</p><h4>Aktuell position</h4></div><div class="profile-live-kpis"><article><span>Lopptid</span><strong data-profile-live="time">0:00</strong></article><article><span>Position</span><strong data-profile-live="distance">0,0 km</strong></article><article><span>Totalplats</span><strong data-profile-live="place">—</strong><small>senast publicerad</small></article><article><span>Aktuell sträcka</span><strong data-profile-live="segment">Start</strong></article><article><span>Progress</span><strong data-profile-live="progress">0 %</strong></article><article><span>Datastatus</span><strong>Illustrativ rörelse</strong></article></div></aside><div class="profile-replay-map-panel"><div id="profile-replay-stage"></div></div><aside class="profile-replay-analysis"><div class="profile-column-head"><p class="eyebrow">JÄMFÖRELSE</p><h4>Mot medianen</h4></div><div class="profile-gap-grid"><article><span>Fältet</span><strong data-profile-gap="field">—</strong><small>n='+field.rows.length+'</small></article><article><span>Klassen</span><strong data-profile-gap="class">—</strong><small>n='+classInfo.rows.length+'</small></article><article><span>'+ctx.html(sexInfo.label)+'</span><strong data-profile-gap="sex">—</strong><small>n='+sexInfo.rows.length+'</small></article></div><div class="profile-replay-insights">'+(ctx.profileInsights(record).slice(0,3).map(item=>'<article class="insight"><span>'+ctx.html(item.label)+'</span><strong>'+ctx.html(item.value)+'</strong><span>'+ctx.html(item.detail)+'</span><small>'+ctx.html(item.method)+'</small></article>').join('')||'<p class="empty">Fler insikter kräver fler verkliga passager.</p>')+'</div></aside></div></section>'+
  '<div id="profile-journey"></div><div id="profile-relative"></div>'+passage+split;
  document.querySelector('#profile-content').innerHTML=shell;
  bindShell(record);
  renderJourney(record);
  ctx.renderReplay(record);
}
function onReplayPosition(detail){
  if(!current||String(detail.runnerId)!==String(current.record.id))return;
  const {ctx,replay}=current,distance=Number(detail.distance)||0,elapsed=detail.elapsed,maxDistance=Number(detail.maxDistance)||1,anchors=detail.anchors||[];
  const set=(name,value)=>{const node=document.querySelector('[data-profile-live="'+name+'"]');if(node)node.textContent=value};
  set('time',finite(elapsed)?ctx.time(elapsed):'—');
  set('distance',ctx.fmtKm(distance)+' km');
  set('progress',Math.round(100*distance/Math.max(.001,maxDistance))+' %');
  const place=replay.places.filter(point=>point.km<=distance+.001&&finite(point.observation?.place)).at(-1);
  set('place',place?'#'+place.observation.place:'—');
  let segment='Start';
  for(let i=1;i<anchors.length;i++){if(distance<=anchors[i].km+.001){segment=anchors[i-1].name+' → '+anchors[i].name;break}segment=anchors.at(-1).name}
  set('segment',segment);
  ['field','class','sex'].forEach(key=>{
    const node=document.querySelector('[data-profile-gap="'+key+'"]');if(!node)return;
    const refTime=interpolate(replay.refs[key],distance),gap=finite(refTime)&&finite(elapsed)?Number(refTime)-Number(elapsed):null;
    node.textContent=gapText(gap,ctx);
  });
}
window.SatilaProfile={render,onReplayPosition};
})();