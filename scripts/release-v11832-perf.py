#!/usr/bin/env python3
"""Generate a separate v1.18.3.2 performance route without changing formal/stabletest."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess
root=Path('app')
required=['index.html','core.html','coi-serviceworker.js','version-v118-test.json','recognition-rules-v1183.json']
for f in required: assert (root/f).exists(),f
base=json.loads((root/'version-v118-test.json').read_text())
assert base['version']=='1.18.3.1' and base['mainJs']=='index-B81hyAdU-v1183-weather-test1.js',base
before={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in required}
assert json.loads((root/'test-adaptive/version-v118-test.json').read_text())['version']=='1.18.3-test'
test=root/'perf-v11832'
assert not test.exists()
test.mkdir(parents=True)
for f in required:shutil.copy2(root/f,test/f)
p=test/'index.html';s=p.read_text(encoding='utf-8')
def replace_once(old,new,tag):
 global s
 n=s.count(old)
 assert n==1,(tag,n)
 s=s.replace(old,new,1)
replace_once("  async function allRecords(){",'''  async function allRecordIds(){
    const db=await openDb();
    return new Promise((resolve,reject)=>{
      const q=db.transaction(STORE,'readonly').objectStore(STORE).getAllKeys();
      q.onsuccess=()=>resolve(q.result||[]);q.onerror=()=>reject(q.error);
    });
  }
  async function allRecords(){''','key-only read')
replace_once('const baselineIds=new Set((await allRecords()).map(r=>r.id));',
             'const baselineIds=new Set(await allRecordIds());','baseline keys')
start='  let envCaptureRunning=false;\n  async function captureEnvironmentForAllNewRecords(){'
end='\n  function weatherText(w)'
a=s.index(start);b=s.index(end,a)
assert a>=0 and b>a
s=s[:a]+'''  let envCaptureRunning=false;
  let lastEnvKeyScan=Date.now();
  async function captureEnvironmentForAllNewRecords(){
    if(envCaptureRunning||!validWeather(currentWeather))return;
    const cards=d.querySelectorAll('#recordList .card');
    let visibleNew=false;
    for(const card of cards){
      const id=card.querySelector('[data-select-id]')?.getAttribute('data-select-id')||card.querySelector('[data-id]')?.getAttribute('data-id');
      if(id&&!baselineIds.has(id)){visibleNew=true;break}
    }
    // Reconcile hidden/filtered records too, but avoid scans on every small
    // DOM mutation. Read only keys; fetch full records only for new IDs.
    const now=Date.now();
    if(!visibleNew && now-lastEnvKeyScan<1500)return;
    lastEnvKeyScan=now;
    envCaptureRunning=true;
    try{
      const ids=await allRecordIds();
      for(const id of ids){
        if(baselineIds.has(id))continue;
        const rec=await getRecord(id);
        if(!rec)continue;
        if((rec.temperature==null||rec.temperature==='')&&(rec.humidity==null||rec.humidity==='')){
          rec.temperature=Number(currentWeather.temperature).toFixed(1);
          rec.humidity=String(Math.round(+currentWeather.humidity));
          rec.envCapturedAt=Date.now();
          await putRecord(rec);
        }
        baselineIds.add(id);
      }
    }catch(e){console.warn('incremental environment capture failed',e)}
    finally{envCaptureRunning=false}
  }
''' +s[b:]
replace_once('''  async function decorateCards(){
    await captureEnvironmentForAllNewRecords();
    d.querySelectorAll('#recordList .card').forEach(card=>decorateCard(card));
  }''','''  async function decorateCards(onlyCards){
    await captureEnvironmentForAllNewRecords();
    const cards=onlyCards||d.querySelectorAll('#recordList .card');
    for(const card of cards)if(card?.isConnected)decorateCard(card);
  }''','incremental card decoration')
replace_once('''  let envCardsScheduled=false;
  const cardsObserver=new MutationObserver(()=>{
    if(envCardsScheduled)return;
    envCardsScheduled=true;
    setTimeout(()=>{envCardsScheduled=false;decorateCards()},80);
  });
  const list=d.getElementById('recordList');if(list)cardsObserver.observe(list,{childList:true,subtree:true});
  decorateCards();''','''  let envCardsScheduled=false;
  const pendingCardRefresh=new Set();
  const scheduleCardRefresh=()=>{
    if(envCardsScheduled)return;
    envCardsScheduled=true;
    setTimeout(()=>{
      envCardsScheduled=false;
      const batch=[...pendingCardRefresh];pendingCardRefresh.clear();
      if(batch.length)decorateCards(batch);
    },80);
  };
  const cardsObserver=new MutationObserver(mutations=>{
    for(const mutation of mutations){
      for(const node of mutation.addedNodes){
        if(node.nodeType!==1)continue;
        if(node.matches?.('.card'))pendingCardRefresh.add(node);
        node.querySelectorAll?.('.card').forEach(card=>pendingCardRefresh.add(card));
      }
      // Status labels may change without replacing the whole card.
      // Exclude our own sync-mini mutations to prevent a feedback loop.
      const target=mutation.target;
      if(target?.nodeType===1&&target.closest?.('.cardhead')&&!target.closest?.('.sync-mini')){
        const card=target.closest('.card');if(card)pendingCardRefresh.add(card);
      }
    }
    if(pendingCardRefresh.size)scheduleCardRefresh();
  });
  const list=d.getElementById('recordList');if(list)cardsObserver.observe(list,{childList:true,subtree:true});
  decorateCards();''','targeted DOM observer')
replace_once("  if(v118StatsRoot)new MutationObserver(paint).observe(v118StatsRoot,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['class']});",'''  let fieldPaintScheduled=false;
  const scheduleFieldPaint=()=>{
    if(fieldPaintScheduled)return;
    fieldPaintScheduled=true;
    requestAnimationFrame(()=>{fieldPaintScheduled=false;paint()});
  };
  if(v118StatsRoot)new MutationObserver(scheduleFieldPaint).observe(v118StatsRoot,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['class']});''','coalesce status repaint')
# Search has no periodic poll in current stable; preserve verified mobile behavior.
assert "searchGuard.addEventListener('input'" in s and 'v11821Restore' in s
assert s.count('setInterval(')==2
assert 'const CLIENT_VERSION="1.18.3.1";' in s
s=s.replace('const CLIENT_VERSION="1.18.3.1";','const CLIENT_VERSION="1.18.3.2-perf";',1)
s=s.replace('v1.18.3.1 正式版','v1.18.3.2 性能测试版')
p.write_text(s,encoding='utf-8')
core=test/'core.html';cs=core.read_text(encoding='utf-8')
cs=cs.replace('v1.18.3.1 正式版','v1.18.3.2 性能测试版')
cs=cs.replace('mingpai-v11831-weather-formal-coi-reload','mingpai-v11832-perf-coi-reload')
assert 'index-B81hyAdU-v1183-weather-test1.js' in cs
core.write_text(cs,encoding='utf-8')
w=test/'coi-serviceworker.js';ws=w.read_text(encoding='utf-8')
assert 'mingpai-shell-v11831-weather-formal' in ws
ws=ws.replace('mingpai-shell-v11831-weather-formal','mingpai-shell-v11832-perf')
ws=ws.replace('const APP_VERSION="1.18.3.1"','const APP_VERSION="1.18.3.2-perf"')
w.write_text(ws,encoding='utf-8')
manifest=test/'version-v118-test.json';m=json.loads(manifest.read_text())
m['version']='1.18.3.2-perf'
manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
assert all(hashlib.sha256((root/f).read_bytes()).hexdigest()==h for f,h in before.items())
assert json.loads((root/'test-adaptive/version-v118-test.json').read_text())['version']=='1.18.3-test'
for name,html in [('outer',s),('core',cs)]:
 for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
  if js.strip():
   tmp=Path(f'/tmp/v11832-{name}-{i}.js');tmp.write_text(js,encoding='utf-8')
   subprocess.run(['node','--check',str(tmp)],check=True)
Path('/tmp/v11832-perf-sw.js').write_text(ws,encoding='utf-8')
subprocess.run(['node','--check','/tmp/v11832-perf-sw.js'],check=True)
assert 'getAllKeys()' in s and 'pendingCardRefresh' in s and 'scheduleFieldPaint' in s
print('PASS v1.18.3.2 perf isolated; formal byte-identical')
