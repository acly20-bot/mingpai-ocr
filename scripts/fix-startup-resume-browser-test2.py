#!/usr/bin/env python3
"""Test-only startup follow-up:
- already-controlled browser resumes directly without waiting on SW registration/ready;
- cached shell HTML falls back promptly on slow network, avoids returning index for core;
- no forced reload except the existing one-time first SW controller transition.
Keep formal and visible versions unchanged. Base: 84-rule bootfix test.
"""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path('app');test=root/'test-adaptive'
files=('index.html','core.html','coi-serviceworker.js','version-v118-test.json','recognition-rules-v1184.json')
old_formal={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files}
fm=json.loads((root/'version-v118-test.json').read_text())
tm=json.loads((test/'version-v118-test.json').read_text())
assert fm['version']=='1.18.4.5' and tm['version']=='1.18.4.5-test'
assert fm['rules']==tm['rules']=='recognition-rules-v1184.json'
assert len(json.loads((root/'recognition-rules-v1184.json').read_text())['rules'])==84

# Bypass repeated SW registration and wait when the browser already has a
# controller from its previous session. The existing first-install logic
# remains in place unchanged.
core=test/'core.html'
s=core.read_text(encoding='utf-8')
needle="""  if(!('serviceWorker' in navigator)||location.protocol!=='https:'){
    await loadMain();return;
  }
  try{
    const reg=await deadline("""
assert s.count(needle)==1
replacement="""  if(!('serviceWorker' in navigator)||location.protocol!=='https:'){
    await loadMain();return;
  }
  // A restored tab normally has the existing SW controlling the document.
  // Do not wait 4.8s for register plus 4.2s for ready in that case.
  // Update the registration asynchronously for next navigation.
  const resumedController=navigator.serviceWorker.controller;
  if(resumedController?.scriptURL?.includes('v=1.153.4.4')){
    navigator.serviceWorker.getRegistration('./')
      .then(reg=>reg?.update()).catch(e=>console.debug('SW update on resume',e));
    await loadMain();
    return;
  }
  try{
    const reg=await deadline("""
s=s.replace(needle,replacement,1)
assert s.count('if(resumedController?.scriptURL?.includes')==1
assert s.count("deadline(navigator.serviceWorker.ready,4200") == 1
core.write_text(s,encoding='utf-8')

# Network-first with a bounded wait only when cached shell is available.
# Without a cache, keep normal network loading, don't create a duplicate
# fetch that wastes bandwidth on initial installation.
sw=test/'coi-serviceworker.js'
w=sw.read_text(encoding='utf-8')
start=w.index('async function shell(req,event){')
end=w.index('\nself.addEventListener("install",',start)
old=w[start:end]
assert 'await fetch(req,{cache:"no-store"})' in old
assert 'await cache.put(req,net.clone())' in old
assert 'cache.match("./index.html")' in old
new=r"""async function shell(req,event){
  const cache=await caches.open(SHELL_CACHE);
  const path=new URL(req.url).pathname;
  const isIndex=path===scopeUrl.pathname||path.endsWith("/index.html");
  // Only the actual index route may fall back to cached index.html.
  // Do not accidentally serve index.html inside core.html iframe.
  const cached=await cache.match(req,{ignoreSearch:true})||
    (isIndex?await cache.match(new URL("./index.html",scopeUrl)):null);
  const ctrl=new AbortController();
  const timer=cached?setTimeout(()=>ctrl.abort(),2400):null;
  try{
    const response=await fetch(req,{cache:"no-store",signal:ctrl.signal});
    if(!response||!response.ok){
      if(cached)return isolate(cached);
      return isolate(response);
    }
    const write=cache.put(req,response.clone()).catch(err=>
      console.debug("HTML shell cache write",err));
    // CacheStore writes should not hold up the first paint.
    if(event?.waitUntil)event.waitUntil(write);
    else await write;
    return isolate(response);
  }catch(err){
    if(cached)return isolate(cached);
    // No cache on first visit: expose failure rather than silently showing
    // the wrong HTML document. Browser retry remains possible.
    throw err;
  }finally{
    if(timer)clearTimeout(timer);
  }
}
"""
w=w[:start]+new+w[end:]
old_cache='const SHELL_CACHE="mingpai-shell-v11845-bootfix-test";'
assert w.count(old_cache)==1
w=w.replace(old_cache,'const SHELL_CACHE="mingpai-shell-v11845-bootfix2-test";',1)
assert w.count('async function shell(req,event){')==1
assert 'cache.match("./index.html")' not in w
sw.write_text(w,encoding='utf-8')

# Keep old stable outer wrapper unchanged: already has bounded version check.
assert 'pendingConfirmRefreshBound' in (test/'index.html').read_text(encoding='utf-8')
assert 'v11845-stats-unit-label' in (test/'index.html').read_text(encoding='utf-8')
for label,folder in [('formal',root),('test',test)]:
    manifest=json.loads((folder/'version-v118-test.json').read_text())
    assert manifest['version']==('1.18.4.5' if label=='formal' else '1.18.4.5-test')
    assert len(json.loads((folder/'recognition-rules-v1184.json').read_text())['rules'])==84
    for name in ['index.html','core.html']:
        html=(folder/name).read_text(encoding='utf-8')
        for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
            if js.strip():
                fn=Path('/tmp')/f'boot-resume2-{label}-{name}-{i}.js'
                fn.write_text(js,encoding='utf-8')
                subprocess.run(['node','--check',str(fn)],check=True)
    fn=Path('/tmp')/f'boot-resume2-{label}-sw.js'
    fn.write_text((folder/'coi-serviceworker.js').read_text(),encoding='utf-8')
    subprocess.run(['node','--check',str(fn)],check=True)
for p,sha in old_formal.items():
    assert hashlib.sha256((root/p).read_bytes()).hexdigest()==sha,'Formal modified '+p
print('PASS second-stage resume optimization, shell timeout fallback and cached core isolation; formal untouched')
