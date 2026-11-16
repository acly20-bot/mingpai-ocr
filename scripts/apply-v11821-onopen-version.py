#!/usr/bin/env python3
"""Apply on-open version check to both generated v1.18.2.1 Pages entries.

Generated runtime files only; never rewrites the 10 MB OCR program or IndexedDB.
The server manifest is authoritative; only a different version triggers one reload.
"""
from pathlib import Path
import json,re,subprocess

ROOT=Path("app")
ENTRIES=[(ROOT,"1.18.2.1"),(ROOT/"test-adaptive","1.18.2.1-test")]

bootstrap=r"""<script id="mingpai-open-version-check">
(()=>{
  'use strict';
  const CLIENT_VERSION=__VERSION__;
  const MANIFEST='./version-v118-test.json';
  const ATTEMPT_PREFIX='mingpai-open-upgrade-';
  let checking=false;
  function read(key){try{return sessionStorage.getItem(key)}catch{return null}}
  function save(key,value){try{sessionStorage.setItem(key,value)}catch{}}
  function clear(key){try{sessionStorage.removeItem(key)}catch{}}
  function timeout(ms){return new Promise(resolve=>setTimeout(resolve,ms))}
  async function check(){
    if(checking||navigator.onLine===false)return;
    checking=true;
    try{
      // The worker handles this endpoint network-first; no stale app shell JSON.
      const url=MANIFEST+'?check='+Date.now();
      const response=await fetch(url,{cache:'no-store'});
      if(!response.ok)return;
      const manifest=await response.json();
      const remote=String(manifest?.version||'').trim();
      if(!remote||!manifest?.mainJs)return;
      const marker=ATTEMPT_PREFIX+remote;
      // Even when the top-level HTML is current, the previous service
      // worker may have served a stale cached core.html to the iframe.
      // Compare the actual rendered footer version, not only wrapper version.
      let coreOutdated=false;
      try{
        const frame=document.getElementById('app');
        if(frame&&frame.contentDocument?.readyState!=='complete'){
          await Promise.race([
            new Promise(resolve=>frame.addEventListener('load',resolve,{once:true})),
            timeout(4500)
          ]);
        }
        const text=frame?.contentDocument?.body?.innerText||'';
        const footer=[...text.matchAll(/版本\s*[:：]\s*v?(\d+(?:\.\d+)+)/g)];
        const actual=footer.length?footer[footer.length-1][1]:'';
        if(actual&&actual!==remote.replace(/-test$/, ''))coreOutdated=true;
      }catch(error){console.debug('[铭牌版本] 无法读取内页版本',error)}
      if(remote===CLIENT_VERSION&&!coreOutdated){
        clear(marker);
        return;
      }
      // Avoid loops if a captive portal, WebView or SW keeps supplying stale
      // HTML. A failed attempt is eligible for a new try after 2 minutes.
      const previous=Number(read(marker)||0);
      if(previous&&Date.now()-previous<120000)return;
      save(marker,String(Date.now()));
      try{
        // Activate the freshly published SW before navigating, so its
        // network-first core.html handler never serves yesterday's shell.
        if('serviceWorker' in navigator){
          const registration=await navigator.serviceWorker.getRegistration('./');
          if(registration){
            await Promise.race([registration.update(),timeout(3500)]);
            if(registration.waiting)registration.waiting.postMessage({type:'SKIP_WAITING'});
            await Promise.race([
              new Promise(resolve=>navigator.serviceWorker.addEventListener('controllerchange',resolve,{once:true})),
              timeout(1000)
            ]);
          }
        }
      }catch(error){console.debug('[铭牌版本] Service Worker 更新暂不可用',error)}
      // Only a verified server-version mismatch can cause this reload.
      // Query parameter isolates browser HTTP cache without changing the path.
      const next=new URL(location.href);
      next.searchParams.set('mpv',remote);
      location.replace(next.href);
    }catch(error){
      // Offline, server timeouts, or invalid manifest must not interrupt OCR.
      console.debug('[铭牌版本] 本次启动保持当前版本',error);
    }finally{checking=false}
  }
  // Check without blocking first paint or local-record restoration.
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',check,{once:true});
  else check();
})();
</script>"""
old_core="""  // Core HTML is versioned with the service worker. Serve its cached copy
  // immediately; refreshing it must not block the first visible page.
  const isCore=new URL(req.url).pathname.endsWith("/core.html");
  if(isCore){
    const cached=await cache.match(req,{ignoreSearch:true});
    if(cached){
      if(event)event.waitUntil(fetch(req,{cache:"no-store"}).then(async net=>{
        if(net&&net.ok)await cache.put(req,net.clone());
      }).catch(()=>{}));
      return isolate(cached);
    }
  }
"""
new_core="""  // Versioned shell HTML must be network-first to prevent a cached core.html
  // from showing an obsolete app after the version check succeeds.
  // The existing catch branch below still provides offline cache fallback.
"""
for directory,version in ENTRIES:
    index=directory/"index.html"
    sw=directory/"coi-serviceworker.js"
    manifest=directory/"version-v118-test.json"
    m,_=json.JSONDecoder().raw_decode(manifest.read_text(encoding="utf-8"))
    assert m["version"]==version,(directory,m["version"])
    assert m["mainJs"]=="index-B81hyAdU-v1182-test22.js"
    assert m["rules"]=="recognition-rules-v1181.json"
    html=index.read_text(encoding="utf-8")
    assert "v11821Restore" in html, "tested search fix must be retained"
    assert html.count("</head>")==1
    assert 'id="mingpai-open-version-check"' not in html
    index.write_text(html.replace("</head>",bootstrap.replace("__VERSION__",json.dumps(version))+"\n</head>",1),encoding="utf-8")
    sw_code=sw.read_text(encoding="utf-8")
    assert sw_code.count(old_core)==1,("SW cache-first fragment",directory)
    sw_code=sw_code.replace(old_core,new_core,1)
    # Versioned cache name makes the fixed SW install into old clients.
    if version=="1.18.2.1":
        old_cache="mingpai-shell-v11821-formal"
        new_cache="mingpai-shell-v11821-formal-onopen"
    else:
        old_cache="mingpai-shell-v11821-search"
        new_cache="mingpai-shell-v11821-test-onopen"
    assert old_cache in sw_code
    sw_code=sw_code.replace(old_cache,new_cache)
    sw_code=sw_code.replace('self.addEventListener("message",e=>{',
        'self.addEventListener("message",e=>{\n  if(e.data?.type==="SKIP_WAITING"){e.waitUntil(self.skipWaiting());return}\n',1)
    sw.write_text(sw_code,encoding="utf-8")
    scripts=re.findall(r"<script[^>]*>(.*?)</script>",index.read_text(encoding="utf-8"),re.I|re.S)
    for i,source in enumerate(scripts):
        if not source.strip():continue
        chk=Path(f"check-mingpai-open-{version}-{i}.js")
        chk.write_text(source,encoding="utf-8")
        subprocess.run(["node","--check",str(chk)],check=True)
    sw_chk=Path(f"check-mingpai-sw-{version}.js")
    sw_chk.write_text(sw_code,encoding="utf-8")
    subprocess.run(["node","--check",str(sw_chk)],check=True)
    assert old_core not in sw_code
    assert new_cache in sw_code
    print("PASS",directory,"server-version probe, reload-once guard, network-first core and syntax")

assert "1.18.2.1" in (ROOT/"index.html").read_text(encoding="utf-8")
assert "1.18.2.1-test" in (ROOT/"test-adaptive"/"index.html").read_text(encoding="utf-8")
print("PASS original OCR JS, rules, Feishu SCF remain unchanged")
