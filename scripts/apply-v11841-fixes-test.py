#!/usr/bin/env python3
"""Stage v1.18.4.1-test only. Source: published v1.18.4 shell.
Fix transient weather fetch feedback, re-review after temperature/humidity edits,
and Android Back close for supported modal overlays. Do not change formal root."""
from pathlib import Path
import json,hashlib,re,subprocess,shutil
root=Path("app")
site=root/"test-adaptive"
old="1.18.4-test"
new="1.18.4.1-test"
names=("index.html","core.html","coi-serviceworker.js","version-v118-test.json","recognition-rules-v1184.json")
assert json.loads((root/"version-v118-test.json").read_text())["version"]=="1.18.4"
m=json.loads((site/"version-v118-test.json").read_text(encoding="utf-8"))
assert m["version"]==old and m["rules"]=="recognition-rules-v1184.json"
source={name:(root/name).read_bytes() for name in names}
before={name:hashlib.sha256(body).hexdigest() for name,body in source.items()}
p=site/"index.html"
s=p.read_text(encoding="utf-8")
assert 'const CLIENT_VERSION="1.18.4-test";' in s
assert "scheduleEnvironmentResync(id)" in s and "mingpaiEnvironmentChangedV1183" in s
# 1: One network retry for ephemeral failures. Existing caching and manual
# override stay unchanged; error still passes through built-in feedback.
weather_helper=r"""  async function fetchWeatherReliable(url,options){
    if(!navigator.onLine)throw new Error('网络离线，已保留原温湿度');
    let last=null;
    for(let attempt=0;attempt<2;attempt++){
      const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),9000);
      try{
        const response=await fetch(url,{...options,signal:ctrl.signal});
        if(!response.ok && response.status>=500 && attempt===0){
          last=new Error('天气服务器 HTTP '+response.status);
        }else{
          return response;
        }
      }catch(err){
        last=err;
        if(err?.name==='AbortError'&&attempt===1)break;
      }finally{clearTimeout(timer)}
      if(attempt===0)await new Promise(resolve=>setTimeout(resolve,650));
    }
    const reason=last?.name==='AbortError'?'天气接口超时':'天气接口无法连接';
    throw new Error(reason+'，已保留原温湿度（可稍后再刷新）');
  }
"""
def single(old,new,tag):
    global s
    count=s.count(old)
    assert count==1,(tag,count)
    s=s.replace(old,new,1)
single('  function refreshWeather(force=false){',weather_helper+'  function refreshWeather(force=false){','weather helper')
# A single weather fetch in the weather code. Leave other network calls alone.
single("const resp=await fetch(url,{cache:'no-store'});","const resp=await fetchWeatherReliable(url,{cache:'no-store'});","weather request retry")
# 2: A saved environment edit is a new review, not an automatic Feishu sync.
# Preserve the previously confirmed remote record ID and mark sync pending
# so the next explicit confirmation updates (rather than creates) its record.
single("  const envSyncTimers=new Map();", """  const envSyncTimers=new Map(); // historic helper retained for regression compatibility
  const envWriteQueues=new Map();""", "environment serialization")
start=s.index("          const persist=async e=>{",s.index("  // V4 weather + per-record environment persistence"))
end=s.index("          ti.addEventListener('blur',persist);",start)
old_persist=s[start:end]
assert "scheduleEnvironmentResync(id)" in old_persist
assert "r.syncStatus='pending'" in old_persist
s=s[:start]+r"""          const persist=async e=>{
            e.stopPropagation();
            const draft=envDrafts.get(id)||{temperature:ti.value,humidity:hi.value};
            const temp=String(draft.temperature??'').trim(),hum=String(draft.humidity??'').trim();
            const tn=numeric(temp),hn=numeric(hum);
            if((temp!==''&&(tn===null||tn< -100||tn>70))||(hum!==''&&(hn===null||hn<0||hn>100))){
              alert('温湿度输入无效：温度应为数字，湿度应在 0～100 之间。');
              return;
            }
            const prior=envWriteQueues.get(id)||Promise.resolve();
            const job=prior.catch(()=>{}).then(async()=>{
              const r=await getRecord(id);if(!r)return;
              if(String(r.temperature??'').trim()===temp&&String(r.humidity??'').trim()===hum){
                envDrafts.delete(id);return;
              }
              const wasConfirmed=r.status==='confirmed';
              r.temperature=temp;r.humidity=hum;r.envCapturedAt=Date.now();
              if(wasConfirmed){
                r.status='pending';     // require the usual explicit review
                r.syncStatus='pending'; // retain remote link for the next confirmed update
                r.syncError='';
              }
              await putRecord(r);
              envDrafts.delete(id);
              ti.value=temp;hi.value=hum;
              // Do not call mingpaiEnvironmentChangedV1183 or scheduleEnvironmentResync:
              // those paths automatically submit an already-confirmed record to Feishu.
              if(wasConfirmed){
                const badge=card.querySelector('.cardhead .badge');
                if(badge){badge.textContent='待审核';badge.classList.remove('ok','confirmed','success')}
                const small=card.querySelector('.card-status-stack .sync-mini');
                if(small)small.textContent='飞书：修改待确认';
                // Reconcile only the two counters; leave all OCR and queue state alone.
                const recs=await allRecords();
                for(const [sel,num] of [['#countOk',recs.filter(v=>v.status==='confirmed').length],
                                        ['#countPending',recs.filter(v=>v.status==='pending').length]]){
                  const el=d.querySelector(sel);
                  if(el)el.textContent=(el.textContent||'').replace(/\d+/,String(num));
                }
              }
            });
            envWriteQueues.set(id,job);
            try{await job}catch(err){
              console.warn('failed to save environment change',err);
              alert('温湿度保存失败，请稍后重试。');
            }finally{
              if(envWriteQueues.get(id)===job)envWriteQueues.delete(id);
            }
          };
"""+s[end:]
# Android hardware Back behavior: existing image preview owns its history
# marker. Add a separate marker only when another closeable modal is visible.
modal_js=r"""<script id="v11841-modal-back">
(()=>{
  'use strict';
  const frame=document.getElementById('app');
  if(!frame)return;
  const marker='__mingpaiModalBack11841';
  let armed=false,doc=null,observer=null,cropWatcher=null,syncTimer=0;
  const visible=(el,control=false)=>{
    if(!el||!el.isConnected)return false;
    const w=el.ownerDocument.defaultView,style=w.getComputedStyle(el);
    if(style.display==='none'||style.visibility==='hidden'||Number(style.opacity||1)===0)return false;
    const rect=el.getBoundingClientRect();
    if(control?(rect.width<8||rect.height<8):(rect.width<140||rect.height<100))return false;
    for(let parent=el.parentElement;parent&&parent!==el.ownerDocument.body;parent=parent.parentElement){
      const css=w.getComputedStyle(parent);
      if(css.display==='none'||css.visibility==='hidden')return false;
    }
    return true;
  };
  const closeControl=(modal)=>{
    const buttons=[...modal.querySelectorAll('button,.btn,[role="button"]')]
      .filter(el=>!el.disabled&&visible(el,true));
    const keyed=modal.querySelector('#cropCancel,[data-close-stats],[data-crop-action="close"],[data-action="cancel"],[data-action="close"]');
    if(keyed&&!keyed.disabled&&visible(keyed,true))return keyed;
    return buttons.find(b=>/^(关闭|取消|返回|退出|放弃|取消裁剪)$/.test((b.textContent||'').trim()))||null;
  };
  const findModal=()=>{
    if(!doc?.body)return null;
    // The existing preview-specific handler already owns this modal.
    if(visible(doc.getElementById('v155ImagePreview')))return null;
    const els=[...doc.querySelectorAll('#fieldStatsModalV1171,#cropModal,[role="dialog"],dialog[open],.modal,.dialog,.overlay,[id*="Modal"],[id*="Dialog"]')];
    for(const el of els.reverse()){
      if(el.id==='v155ImagePreview'||el.closest('#v155ImagePreview'))continue;
      if(!visible(el))continue;
      const candidate=closeControl(el);
      if(candidate)return {el,button:candidate};
    }
    return null;
  };
  const sync=()=>{
    if(!doc?.body)return;
    const modal=findModal();
    if(modal&&!armed){
      try{
        history.pushState({...history.state,[marker]:true},'',location.href);
        armed=true;
      }catch(e){console.warn('modal Back entry unavailable',e)}
    }else if(!modal&&armed){
      armed=false;
      if(history.state?.[marker])history.back();
    }
  };
  const schedule=()=>{clearTimeout(syncTimer);syncTimer=setTimeout(sync,40)};
  window.addEventListener('popstate',()=>{
    if(!armed)return;
    armed=false;
    const modal=findModal();
    if(modal)modal.button.click();
    schedule();
  });
  const attach=()=>{
    let next;try{next=frame.contentDocument}catch{return}
    if(!next?.body||next===doc)return;
    observer?.disconnect();cropWatcher?.disconnect();
    doc=next;armed=false;
    observer=new MutationObserver(schedule);
    observer.observe(doc.body,{childList:true,subtree:true});
    const crop=doc.getElementById('cropModal');
    if(crop){cropWatcher=new MutationObserver(schedule);cropWatcher.observe(crop,{attributes:true,attributeFilter:['style','class','aria-hidden']})}
    doc.addEventListener('click',()=>setTimeout(schedule,0),true);
    sync();
  };
  frame.addEventListener('load',attach);
  attach();
})();
</script>
"""
assert "v1183PreviewBackInit" in s and "v11841-modal-back" not in s
single("</body>",modal_js+"</body>","modal Back module")
single('const CLIENT_VERSION="1.18.4-test";','const CLIENT_VERSION="1.18.4.1-test";',"version")
s=s.replace("v1.18.4 测试版","v1.18.4.1 测试版")
p.write_text(s,encoding="utf-8")
core=site/"core.html"
c=core.read_text(encoding="utf-8")
assert "v1.18.4 测试版" in c
c=c.replace("v1.18.4 测试版","v1.18.4.1 测试版")
c=c.replace("mingpai-v1184-test-coi-reload","mingpai-v11841-test-coi-reload")
core.write_text(c,encoding="utf-8")
sw=site/"coi-serviceworker.js"
w=sw.read_text(encoding="utf-8")
assert 'mingpai-shell-v1184-test' in w and '1.18.4-test' in w
w=w.replace('mingpai-shell-v1184-test','mingpai-shell-v11841-test')
w=w.replace('1.18.4-test','1.18.4.1-test')
sw.write_text(w,encoding="utf-8")
m["version"]=new
(site/"version-v118-test.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert "recognition-rules-v1184.json" in c and m["rules"]=="recognition-rules-v1184.json"
assert "index-B81hyAdU-v11832-viewport-test2.js" in c
assert "getAllKeys()" in s and "WEATHER_TTL_MS" in s
assert "scheduleEnvironmentResync(id)" not in s[s.index("          const persist=async e=>"):s.index("          ti.addEventListener('blur',persist);")]
assert "r.status='pending'" in s
assert "v11841-modal-back" in s and "v1183PreviewBackInit" in s
for name,html in [('index',s),('core',c)]:
    for i,code in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
        if code.strip():
            tmp=Path(f"/tmp/v11841-{name}-{i}.js")
            tmp.write_text(code,encoding="utf-8")
            subprocess.run(["node","--check",str(tmp)],check=True)
tmp=Path('/tmp/v11841-sw.js');tmp.write_text(w,encoding="utf-8")
subprocess.run(["node","--check",str(tmp)],check=True)
for name in names:
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==before[name], "formal changed "+name
print("PASS v1.18.4.1-test weather backoff + manual review + modal Back; formal v1.18.4 untouched")
