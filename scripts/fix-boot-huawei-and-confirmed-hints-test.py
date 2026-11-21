#!/usr/bin/env python3
"""v1.18.4.5 TEST ONLY: bounded startup, first-load COS fallback,
no redundant 10MB prefetch, hide risk warnings for confirmed records.
Input: exact pinned 84-rule 2026-11-21 release baseline.
DO NOT modify formal or OCR worker/runtime bundle.
"""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path("app");test=root/"test-adaptive"
names=["index.html","core.html","coi-serviceworker.js","version-v118-test.json","recognition-rules-v1184.json"]
formal_sha={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in names}
fm=json.loads((root/"version-v118-test.json").read_text())
tm=json.loads((test/"version-v118-test.json").read_text())
assert fm["version"]=="1.18.4.5" and tm["version"]=="1.18.4.5-test"
assert fm["rules"]==tm["rules"]=="recognition-rules-v1184.json"
assert len(json.loads((root/"recognition-rules-v1184.json").read_text())["rules"])==84
# 1. Original core has unbounded serviceWorker.ready and no retries for
# failed first-time COS module loading. Preserve COI controller transition.
core=test/"core.html";cs=core.read_text(encoding="utf-8")
start=cs.index("  async function loadMain(){")
end=cs.index("\n})();\n</script>",start)
original=cs[start:end]
assert "await navigator.serviceWorker.ready;" in original
assert "try{await attach(MAIN,false);return;}" in original
replacement=r"""  // Start app promptly even on browsers with slow/broken service-worker
  // registration (some first-run Huawei/QQ/UC browsers).
  const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const deadline=(promise,ms,label)=>new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(new Error(label+' timeout')),ms);
    Promise.resolve(promise).then(
      value=>{clearTimeout(timer);resolve(value)},
      err=>{clearTimeout(timer);reject(err)}
    );
  });
  let loadingMain=null;
  function loadMain(){
    if(loadingMain)return loadingMain;
    loadingMain=(async()=>{
      if(document.querySelector('script[data-mingpai-main]'))return true;
      const controlled=!!navigator.serviceWorker?.controller;
      const sources=controlled
        ?[MAIN,MAIN_DIRECT,MAIN_DIRECT+'&retry=1',MAIN_DIRECT+'&retry=2']
        :[MAIN_DIRECT,MAIN_DIRECT+'&retry=1',MAIN_DIRECT+'&retry=2'];
      const attach=(src,isDirect)=>new Promise((resolve,reject)=>{
        const el=document.createElement('script');
        el.type='module';el.src=src;el.dataset.mingpaiMain='1';
        el.onload=()=>resolve(true);
        el.onerror=()=>{
          try{el.remove()}catch(e){}
          reject(new Error(isDirect?'COS direct load failed':'runtime proxy load failed'));
        };
        document.head.appendChild(el);
      });
      for(let i=0;i<sources.length;i++){
        try{
          await attach(sources[i],sources[i].startsWith('https://'));
          return true;
        }catch(e){
          console.warn('主程序加载失败，尝试备用地址',i+1,e);
          if(i<sources.length-1)await delay(550+350*i);
        }
      }
      const p=document.getElementById('networkPill'),s=document.getElementById('progress');
      if(p){p.textContent='资源：主程序加载失败';p.className='pill mini-net netbad'}
      if(s)s.textContent='主程序暂时无法加载。请检查网络，点击重新加载；本地设备记录不会清除。';
      const parent=s?.parentElement||document.body;
      let retry=document.getElementById('v11845LoadRetry');
      if(!retry){
        retry=document.createElement('button');retry.id='v11845LoadRetry';
        retry.className='btn';retry.type='button';retry.textContent='重新尝试加载主程序';
        parent.appendChild(retry);
      }
      retry.onclick=()=>{retry.disabled=true;loadMain().finally(()=>{retry.disabled=false})};
      return false;
    })().finally(()=>{loadingMain=null});
    return loadingMain;
  }
  if(!('serviceWorker' in navigator)||location.protocol!=='https:'){
    await loadMain();return;
  }
  try{
    const reg=await deadline(
      navigator.serviceWorker.register(SW,{scope:'./',updateViaCache:'none'}),
      4800,'Service Worker register');
    // Do not block the UI waiting on a network service-worker update.
    reg.update().catch(err=>console.debug('SW background update',err));
    await deadline(navigator.serviceWorker.ready,4200,'Service Worker ready');
    const ctl=navigator.serviceWorker.controller;
    if(!ctl||!ctl.scriptURL.includes('v=1.153.4.4')){
      if(!sessionStorage.getItem(FLAG)){
        sessionStorage.setItem(FLAG,'1');
        if(reg.waiting)try{reg.waiting.postMessage({type:'SKIP_WAITING'})}catch(e){}
        let done=false;
        const reload=()=>{if(done)return;done=true;location.reload()};
        navigator.serviceWorker.addEventListener('controllerchange',reload,{once:true});
        setTimeout(reload,1300);
        return;
      }
    }
    sessionStorage.removeItem(FLAG);
    await loadMain();
  }catch(e){
    // Fallback does not require SW support. The following visit can use
    // the worker once registration is complete.
    console.warn('浏览器启动支持组件超时，直接加载主程序',e);
    await loadMain();
  }
  window.addEventListener('pageshow',event=>{
    if(event.persisted && !document.querySelector('script[data-mingpai-main]')){
      setTimeout(()=>loadMain(),250);
    }
  });
"""
cs=cs[:start]+replacement+cs[end:]
assert cs.count('function loadMain(){')==1
assert 'deadline(navigator.serviceWorker.ready,4200' in cs
assert "v11845LoadRetry" in cs
assert cs.count('location.reload()')==1 # only the first SW controller transition
core.write_text(cs,encoding="utf-8")

# 2. First-load 10MB runtime was cached synchronously before being returned.
# Stream it immediately; persist in the SW event lifetime in parallel.
sw=test/"coi-serviceworker.js";w=sw.read_text(encoding="utf-8")
assert "async function fetchRuntimeByRel(rel,requestKey){" in w
w=w.replace("async function fetchRuntimeByRel(rel,requestKey){",
            "async function fetchRuntimeByRel(rel,requestKey,event){",1)
assert "const hit=await cache.match(key);" in w
w=w.replace("const hit=await cache.match(key);",
            "const hit=await cache.match(key,{ignoreSearch:true});",1)
old="""  try{await cache.put(key,clean.clone())}catch{}
  return clean;"""
new="""  // Do not block module evaluation on saving a large JS bundle to CacheStorage.
  const saving=cache.put(key,clean.clone()).catch(err=>console.debug('runtime cache save',err));
  if(event?.waitUntil)event.waitUntil(saving);
  else await saving; // prefetch caller must only report success after saved
  return clean;"""
assert w.count(old)==1
w=w.replace(old,new,1)
assert "async function runtime(req,url){" in w
w=w.replace("async function runtime(req,url){\n  const rel=url.pathname.slice(runtimePrefix.length);\n  return fetchRuntimeByRel(rel,req);\n}",
"""async function runtime(req,url,event){
  const rel=url.pathname.slice(runtimePrefix.length);
  return fetchRuntimeByRel(rel,req,event);
}""",1)
assert "e.respondWith(runtime(req,url).catch(" in w
w=w.replace("e.respondWith(runtime(req,url).catch(","e.respondWith(runtime(req,url,e).catch(",1)
old_cache='const SHELL_CACHE="mingpai-shell-v11845-rules-r8-test";'
assert w.count(old_cache)==1
w=w.replace(old_cache,
  'const SHELL_CACHE="mingpai-shell-v11845-bootfix-test";',1)
sw.write_text(w,encoding="utf-8")

# 3. Avoid automatic redundant COS 10MB download at cold startup when the
# active JS is already running and the version manifest has not changed.
outer=test/"index.html";s=outer.read_text(encoding="utf-8")
needle="const hit=await c.match(key)"
assert needle not in s # actual old implementation uses a return expression
assert "return!!(await c.match(key))" in s
s=s.replace("return!!(await c.match(key))","return!!(await c.match(key,{ignoreSearch:true}))",1)
needle="if(!ver||!main)return;if(await has(main)){localStorage.setItem('mingpai-v118-manifest-version',ver);return}"
assert s.count(needle)==1
s=s.replace(needle,
"""if(!ver||!main)return;const previously=localStorage.getItem('mingpai-v118-manifest-version');
  // On first install the current core has already loaded the runtime;
  // never prefetch the same huge JS a second time in the background.
  if(!previously){localStorage.setItem('mingpai-v118-manifest-version',ver);return}
  if(previously===ver)return;
  if(await has(main)){localStorage.setItem('mingpai-v118-manifest-version',ver);return}""",1)

# 4. A checked/confirmed record should not display pre-confirmation suspicious
# electrical/model/serial hints. Use the native badge; restore hints if edited
# back to Pending. Do not alter original verification status.
needle="    for(const field of ['code','model','manufacturer']){"
assert s.count(needle)==1
s=s.replace(needle,
"""    const confirmed=/已确认/.test(card.querySelector('.cardhead .badge, .badge')?.textContent||'');
    if(confirmed){
      card.querySelectorAll('.'+className).forEach(note=>note.remove());
      return;
    }
"""+needle,1)
anchor="  scan();\n}\n\n  v1183InstallFieldReview(d);"
assert s.count(anchor)==1
s=s.replace(anchor,
"""  // Native confirm changes the state after the click. Re-check the
  // confirmed badge without requesting any additional database writes.
  list.addEventListener('click',e=>{
    if(!e.target.closest('button[data-action="toggle"]'))return;
    const card=e.target.closest('article.card');
    for(const ms of [180,600,1200])
      setTimeout(()=>{if(card?.isConnected)update(card);else scan()},ms);
  },true);
  scan();
}

  v1183InstallFieldReview(d);""",1)
assert "pendingConfirmRefreshBound" in s and "scheduleHiddenDockRecovery" not in s
assert "v11845-stats-unit-label" in s
assert "nativeChange('temperature',temp)" in s and "nativeChange('humidity',hum)" in s
assert 'const CLIENT_VERSION="1.18.4.5-test";' in s
outer.write_text(s,encoding="utf-8")

for name,sha in formal_sha.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha,('FORMAL_CHANGED',name)
for label,folder in [('formal',root),('test',test)]:
    m=json.loads((folder/"version-v118-test.json").read_text())
    assert m["version"]==("1.18.4.5" if label=="formal" else "1.18.4.5-test")
    assert m["rules"]=="recognition-rules-v1184.json"
    assert len(json.loads((folder/"recognition-rules-v1184.json").read_text())["rules"])==84
    for name in ('index.html','core.html'):
        html=(folder/name).read_text(encoding="utf-8")
        for i,code in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
            if code.strip():
                f=Path('/tmp')/f'boot11845-{label}-{name}-{i}.js'
                f.write_text(code,encoding="utf-8")
                subprocess.run(['node','--check',str(f)],check=True)
    f=Path('/tmp')/f'boot11845-{label}-sw.js'
    f.write_text((folder/"coi-serviceworker.js").read_text())
    subprocess.run(['node','--check',str(f)],check=True)
print("PASS test-only finite SW boot, first-run fallback/retry, no redundant prefetch, confirmed hint hides")
