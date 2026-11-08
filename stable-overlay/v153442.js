(()=>{
const d=document,$=id=>d.getElementById(id),all=()=>[...d.querySelectorAll('*')];
const DB_NAME='mingpai-free-v1',STORE='records',WEATHER_KEY='mingpai-field-weather-v2',OLD_WEATHER_KEY='mingpai-field-weather-v1';
let currentWeather=null,baselineIds=new Set(),envDrafts=new Map(),started=false;
function openDb(){return new Promise((res,rej)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{const db=r.result;if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE,{keyPath:'id'})};r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)})}
async function getRecord(id){const db=await openDb();return new Promise((res,rej)=>{const q=db.transaction(STORE,'readonly').objectStore(STORE).get(id);q.onsuccess=()=>res(q.result||null);q.onerror=()=>rej(q.error)})}
async function putRecord(rec){const db=await openDb();return new Promise((res,rej)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put(rec);tx.oncomplete=()=>res();tx.onerror=()=>rej(tx.error)})}
async function allRecords(){const db=await openDb();return new Promise((res,rej)=>{const q=db.transaction(STORE,'readonly').objectStore(STORE).getAll();q.onsuccess=()=>res(q.result||[]);q.onerror=()=>rej(q.error)})}
function dateKey(){return $('workdate')?.value||new Date().toISOString().slice(0,10)}
function loadWeather(){try{currentWeather=JSON.parse(localStorage.getItem(WEATHER_KEY)||'null');if(!currentWeather){const old=JSON.parse(localStorage.getItem(OLD_WEATHER_KEY)||'null');if(old){currentWeather={...old,dateKey:dateKey()};localStorage.setItem(WEATHER_KEY,JSON.stringify(currentWeather))}}}catch{currentWeather=null}}
function installWeather(){
 const brand=d.querySelector('.brand-inner');if(!brand)return;
 let w=brand.querySelector('.field-weather-wrap');
 if(!w){w=d.createElement('div');w.className='field-weather-wrap';
  const inline=d.createElement('div');inline.className='weather-inline';inline.innerHTML='<span class="temp-line"><input class="temp" inputmode="decimal" aria-label="顶部温度">℃</span><span class="hum-line"><input class="hum" inputmode="numeric" aria-label="顶部湿度">%RH</span>';
  const rf=d.createElement('button');rf.type='button';rf.className='field-weather-refresh';rf.textContent='↻';rf.title='刷新定位温湿度';
  w.append(inline,rf);brand.insertBefore(w,brand.querySelector('.field-settings-btn')||null);
  const save=()=>{const t=inline.querySelector('.temp').value.trim(),h=inline.querySelector('.hum').value.trim();currentWeather={...(currentWeather||{}),temperature:Number(t),humidity:Number(h),savedAt:Date.now(),manual:true,dateKey:dateKey()};localStorage.setItem(WEATHER_KEY,JSON.stringify(currentWeather))};
  inline.querySelectorAll('input').forEach(inp=>{['click','pointerdown','touchstart'].forEach(ev=>inp.addEventListener(ev,e=>e.stopPropagation()));inp.addEventListener('change',save);inp.addEventListener('blur',save)});
  rf.addEventListener('click',()=>refreshWeather(true));
 }
 const ti=w.querySelector('.temp'),hi=w.querySelector('.hum');
 if(d.activeElement!==ti)ti.value=currentWeather&&Number.isFinite(+currentWeather.temperature)?Number(currentWeather.temperature).toFixed(1):'';
 if(d.activeElement!==hi)hi.value=currentWeather&&Number.isFinite(+currentWeather.humidity)?String(Math.round(+currentWeather.humidity)):'';
}
async function refreshWeather(force=false){
 installWeather();const dk=dateKey();
 if(!force&&currentWeather&&currentWeather.dateKey===dk&&Number.isFinite(+currentWeather.temperature)&&Number.isFinite(+currentWeather.humidity)){decorateCards();return}
 if(!navigator.geolocation)return;
 navigator.geolocation.getCurrentPosition(async pos=>{try{
  const {latitude,longitude}=pos.coords,u='https://api.open-meteo.com/v1/forecast?latitude='+encodeURIComponent(latitude)+'&longitude='+encodeURIComponent(longitude)+'&current=temperature_2m,relative_humidity_2m&timezone=auto';
  const resp=await fetch(u,{cache:'no-store'});if(!resp.ok)throw new Error('weather HTTP '+resp.status);const j=await resp.json();
  currentWeather={temperature:Number(j?.current?.temperature_2m),humidity:Number(j?.current?.relative_humidity_2m),savedAt:Date.now(),latitude,longitude,manual:false,dateKey:dk};
  localStorage.setItem(WEATHER_KEY,JSON.stringify(currentWeather));installWeather();decorateCards();
 }catch(e){console.warn('weather fetch failed',e)}},e=>console.warn('geolocation failed',e),{enableHighAccuracy:false,timeout:10000,maximumAge:3600000});
}
function syncLabel(rec){const s=rec?.syncStatus;return s==='synced'?'已同步':s==='syncing'?'同步中':s==='error'?'失败待重试':s==='pending'?'有修改待同步':s==='local-only'?'仅本机保存':rec?.status==='confirmed'?'尚未同步':'待确认'}
function setField(card,field,value){
 const el=card.querySelector('[data-field="'+field+'"]');if(!el||el.value===value)return false;
 el.value=value;el.dispatchEvent(new Event('change',{bubbles:true}));return true;
}
function applyRecognitionFix(card){
 const raw=card.querySelector('textarea[data-field="raw"]')?.value||'';
 if(/POWER[-–—]?420FX/i.test(raw)&&/高频电刀/.test(raw)){
  setField(card,'name','高频电刀');setField(card,'model','POWER-420FX');
  if(/常州市延陵电子设备有限公司/.test(raw))setField(card,'manufacturer','常州市延陵电子设备有限公司');
  if(/18FX020/i.test(raw))setField(card,'code','18FX020');
 }
 if(/PM-9000\s*Express/i.test(raw)&&/病人监护仪|MINDRAY|迈瑞/i.test(raw))setField(card,'name','多参数监护仪');
}
async function decorateCard(card){
 if(card.dataset.v153442Busy==='1')return;card.dataset.v153442Busy='1';
 try{
  applyRecognitionFix(card);
  const id=card.querySelector('[data-select-id]')?.getAttribute('data-select-id')||card.querySelector('[data-id]')?.getAttribute('data-id');if(!id)return;
  let rec=await getRecord(id);if(!rec)return;
  if(!baselineIds.has(id)&&(rec.temperature==null||rec.temperature==='')&&(rec.humidity==null||rec.humidity==='')){
   rec.temperature=currentWeather&&Number.isFinite(+currentWeather.temperature)?Number(currentWeather.temperature).toFixed(1):'';
   rec.humidity=currentWeather&&Number.isFinite(+currentWeather.humidity)?String(Math.round(+currentWeather.humidity)):'';
   rec.envCapturedAt=Date.now();await putRecord(rec);baselineIds.add(id);
  }
  const title=card.querySelector('.cardtitle'),head=card.querySelector('.cardhead');if(!title)return;
  const small=title.querySelector('small');if(small)small.remove();
  let env=title.querySelector('.env-inline');
  if(!env){env=d.createElement('div');env.className='env-inline';env.innerHTML='<input class="temp" inputmode="decimal" aria-label="记录温度">℃ / <input class="hum" inputmode="numeric" aria-label="记录湿度">%RH';
   const ti=env.querySelector('.temp'),hi=env.querySelector('.hum'),keep=e=>{e.stopPropagation();envDrafts.set(id,{temperature:ti.value,humidity:hi.value})};
   ['input','change','keydown','keyup','click','pointerdown','touchstart'].forEach(ev=>{ti.addEventListener(ev,keep);hi.addEventListener(ev,keep)});
   const persist=async e=>{e.stopPropagation();const draft=envDrafts.get(id)||{temperature:ti.value,humidity:hi.value},r=await getRecord(id);if(!r)return;r.temperature=String(draft.temperature??'').trim();r.humidity=String(draft.humidity??'').trim();r.envCapturedAt=r.envCapturedAt||Date.now();await putRecord(r);envDrafts.delete(id)};
   ti.addEventListener('blur',persist);hi.addEventListener('blur',persist);
  }
  const ti=env.querySelector('.temp'),hi=env.querySelector('.hum'),draft=envDrafts.get(id);
  if(d.activeElement!==ti)ti.value=draft?draft.temperature:(rec.temperature??'');if(d.activeElement!==hi)hi.value=draft?draft.humidity:(rec.humidity??'');
  let sync=title.querySelector('.sync-mini');if(!sync){sync=d.createElement('div');sync.className='sync-mini'}sync.textContent='飞书：'+syncLabel(rec);
  let meta=title.querySelector('.card-meta-row');if(!meta){meta=d.createElement('div');meta.className='card-meta-row';title.appendChild(meta)}
  if(env.parentElement!==meta)meta.appendChild(env);if(sync.parentElement!==meta)meta.appendChild(sync);
  const badge=head?.querySelector('.badge');if(badge){let stack=head.querySelector('.card-status-stack');if(!stack){stack=d.createElement('div');stack.className='card-status-stack';badge.replaceWith(stack);stack.appendChild(badge)}}
  card.querySelectorAll('button').forEach(btn=>{if((btn.textContent||'').trim()==='取消确认')btn.remove()});
 }catch(e){console.warn('v1.153.4.4.2 card patch failed',e)}finally{card.dataset.v153442Busy='0'}
}
function decorateCards(){d.querySelectorAll('#recordList .card').forEach(decorateCard)}
function num(el){const m=(el?.textContent||'').match(/\d+/g);return m?Math.max(...m.map(Number)):0}
function paint(){
 const q=$('queuePill');if(q){const m=(q.textContent||'').match(/识别(?:中)?\s*(\d+)\s*\/\s*等待\s*(\d+)/);if(m){const t='识别'+m[1]+'/等待'+m[2];if(q.textContent!==t)q.textContent=t}}
 const sem={countAll:'field-total',countPending:'field-pending',countOk:'field-confirmed',countSyncPending:'field-sync',selectedCount:'field-selected',queuePill:'field-queue',queueFailedPill:'field-failed'};
 for(const [id,cl] of Object.entries(sem)){const el=$(id);if(!el)continue;el.classList.add(cl);const n=num(el);el.classList.toggle('field-has-data',n>0);el.classList.toggle('field-zero',n===0);el.classList.toggle('field-active',el.classList.contains('filter-active'))}
}
function xmlEscape(v){return String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function crc32(bytes){let x=0xffffffff;for(const b of bytes){x^=b;for(let k=0;k<8;k++)x=(x>>>1)^((x&1)?0xedb88320:0)}return(x^0xffffffff)>>>0}
function u16(n){return new Uint8Array([n&255,(n>>>8)&255])}function u32(n){return new Uint8Array([n&255,(n>>>8)&255,(n>>>16)&255,(n>>>24)&255])}
function cat(parts){const len=parts.reduce((n,p)=>n+p.length,0),out=new Uint8Array(len);let o=0;for(const p of parts){out.set(p,o);o+=p.length}return out}
function zipStored(files){const enc=new TextEncoder(),locals=[],centrals=[];let offset=0;for(const [name,text] of files){const nb=enc.encode(name),data=enc.encode(text),crc=crc32(data),local=cat([u32(0x04034b50),u16(20),u16(0x0800),u16(0),u16(0),u16(0),u32(crc),u32(data.length),u32(data.length),u16(nb.length),u16(0),nb,data]);locals.push(local);const central=cat([u32(0x02014b50),u16(20),u16(20),u16(0x0800),u16(0),u16(0),u16(0),u32(crc),u32(data.length),u32(data.length),u16(nb.length),u16(0),u16(0),u16(0),u16(0),u32(0),u32(offset),nb]);centrals.push(central);offset+=local.length}const size=centrals.reduce((n,p)=>n+p.length,0);return cat([...locals,...centrals,u32(0x06054b50),u16(0),u16(0),u16(files.length),u16(files.length),u32(size),u32(offset),u16(0)])}
function makeXlsx(rows){const cell=v=>'<c t="inlineStr"><is><t xml:space="preserve">'+xmlEscape(v)+'</t></is></c>',sheet='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+rows.map((r,i)=>'<row r="'+(i+1)+'">'+r.map(cell).join('')+'</row>').join('')+'</sheetData></worksheet>';return new Blob([zipStored([['[Content_Types].xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'],['_rels/.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'],['xl/workbook.xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="设备记录" sheetId="1" r:id="rId1"/></sheets></workbook>'],['xl/_rels/workbook.xml.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'],['xl/worksheets/sheet1.xml',sheet]])],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'})}
async function localExport(ev){if(/MicroMessenger/i.test(navigator.userAgent||''))return;ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();const rows=(await allRecords()).sort((a,b)=>(a.createdAt||0)-(b.createdAt||0));if(!rows.length){alert('当前没有可导出的本地记录。');return}const head=['单位名称','科室','检定日期','检定员','设备名称','生产厂家','型号','出厂编号','温度（℃）','相对湿度（%RH）','备注','状态','铭牌文本'],body=rows.map(r=>[r.unitName||r.batch||'',r.dept||'',r.date||'',r.operatorName||'',r.name||'',r.manufacturer||'',r.model||'',r.code||'',r.temperature??'',r.humidity??'',r.remark||'',r.status==='confirmed'?'已确认':r.status==='pending'?'待审核':r.status||'',r.raw||'']),now=new Date(),p=n=>String(n).padStart(2,'0'),stamp=now.getFullYear()+p(now.getMonth()+1)+p(now.getDate())+'_'+p(now.getHours())+p(now.getMinutes())+p(now.getSeconds()),blob=makeXlsx([head,...body]),url=URL.createObjectURL(blob),a=d.createElement('a');a.href=url;a.download='设备铭牌数据_'+stamp+'.xlsx';d.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000)}
async function init(){
 if(started)return;started=true;
 const wrap=d.querySelector('.wrap');if(!wrap)return;const panels=[...wrap.children].filter(x=>x.classList?.contains('panel'));if(panels.length<3)return;
 const [work,stats,records]=panels;work.id='fieldWork';stats.id='fieldStats';records.id='fieldRecords';
 const brand=d.querySelector('.brand-inner');if(brand&&!brand.querySelector('.field-settings-btn')){const b=d.createElement('button');b.type='button';b.className='field-settings-btn';b.textContent='⚙ 设置';b.onclick=()=>{const s=$('advancedSettings');if(s){s.open=!s.open;s.scrollIntoView({behavior:'smooth',block:'start'})}};brand.appendChild(b)}
 const oldHead=records.querySelector(':scope > .row');if(oldHead)oldHead.remove();let head=records.querySelector('.field-head');if(!head){head=d.createElement('div');head.className='field-head';head.innerHTML='<h2>设备记录</h2>';records.prepend(head)}
 const net=$('networkPill');if(net){let h=head.querySelector('.field-network');if(!h){h=d.createElement('div');h.className='field-network';head.appendChild(h)}h.appendChild(net)}
 const csv=$('csvTopBtn');if(csv){let h=head.querySelector('.toolbar-download');if(!h){h=d.createElement('div');h.className='toolbar-download';head.appendChild(h)}h.appendChild(csv);csv.addEventListener('click',localExport,true)}
 const filter=$('statusFilter'),search=$('searchBox'),oldToolbar=all().find(el=>el!==records&&el.classList?.contains('toolbar-row')&&((filter&&el.contains(filter))||(search&&el.contains(search)))),tools=d.createElement('div');tools.className='field-record-tools';tools.innerHTML='<span class="tool-label">状态</span>';if(filter)tools.appendChild(filter);const l2=d.createElement('span');l2.className='tool-label';l2.textContent='搜索';tools.appendChild(l2);if(search)tools.appendChild(search);const page=records.querySelector('.pages');records.insertBefore(tools,page);if(oldToolbar)oldToolbar.remove();
 const bulk=stats.querySelector('.bulkbar')||records.querySelector('.bulkbar'),clear=$('clearAllLocalBtn')||[...d.querySelectorAll('button,.btn')].find(b=>(b.textContent||'').trim()==='清空');if(bulk){if(clear&&!bulk.contains(clear))bulk.appendChild(clear);const h=d.createElement('div');h.className='field-bulk';h.appendChild(bulk);records.insertBefore(h,page)}if(clear)clear.classList.add('field-clear-danger');
 const top=stats.querySelector('.topstat'),retry=$('retryFailedAllBtn'),order=['countAll','countOk','countPending','countSyncPending','selectedCount','queuePill','queueFailedPill'];if(top){order.forEach(id=>{const el=$(id);if(el)top.appendChild(el)});if(retry)top.appendChild(retry)}
 baselineIds=new Set((await allRecords()).map(r=>r.id));loadWeather();installWeather();setTimeout(()=>refreshWeather(false),150);$('workdate')?.addEventListener('change',()=>refreshWeather(false));
 const list=$('recordList');if(list)new MutationObserver(decorateCards).observe(list,{childList:true,subtree:true});decorateCards();paint();new MutationObserver(paint).observe(stats,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['class']});
 const foot=d.querySelector('.foot strong');if(foot)foot.textContent='版本：v1.153.4.4.2';
}
if(d.readyState==='complete')init();else window.addEventListener('load',init,{once:true});
})();