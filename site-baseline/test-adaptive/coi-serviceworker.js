const APP_VERSION="1.18.5-test.3";
const SHELL_CACHE="mingpai-shell-v1185-test3-rules-r10";
const RUNTIME_CACHE="mingpai-runtime-long-v1";
const COS_RUNTIME="https://mingpai-ocr-1387910526.cos.ap-guangzhou.myqcloud.com/assets/";
const scopeUrl=new URL(self.registration.scope);
const runtimePrefix=new URL("./runtime/",scopeUrl).pathname;
const shellFiles=["./","./index.html","./core.html","./version-v118-test.json"];

function isolate(resp){
  if(!resp||resp.type==="opaque")return resp;
  const h=new Headers(resp.headers);
  h.set("Cross-Origin-Opener-Policy","same-origin");
  h.set("Cross-Origin-Embedder-Policy","credentialless");
  h.delete("Content-Disposition");
  return new Response(resp.body,{status:resp.status,statusText:resp.statusText,headers:h});
}
function ctype(path,h){
  if(path.endsWith(".js"))h.set("Content-Type","application/javascript; charset=utf-8");
  else if(path.endsWith(".wasm"))h.set("Content-Type","application/wasm");
}
async function fetchRuntimeByRel(rel,requestKey,event){
  const target=new URL(rel,COS_RUNTIME),cache=await caches.open(RUNTIME_CACHE);
  const key=requestKey||new Request(new URL("./runtime/"+rel,scopeUrl),{method:"GET"});
  const hit=await cache.match(key,{ignoreSearch:true});
  if(hit)return isolate(hit);
  const up=await fetch(target,{mode:"cors",credentials:"omit",cache:"no-store"});
  if(!up.ok)throw new Error("COS "+up.status);
  const h=new Headers(up.headers);ctype(rel,h);h.delete("Content-Disposition");
  h.set("Cross-Origin-Opener-Policy","same-origin");
  h.set("Cross-Origin-Embedder-Policy","credentialless");
  h.set("Cross-Origin-Resource-Policy","same-origin");
  const clean=new Response(up.body,{status:up.status,statusText:up.statusText,headers:h});
  // Do not block module evaluation on saving a large JS bundle to CacheStorage.
  const saving=cache.put(key,clean.clone()).catch(err=>console.debug('runtime cache save',err));
  if(event?.waitUntil)event.waitUntil(saving);
  else await saving; // prefetch caller must only report success after saved
  return clean;
}
async function runtime(req,url,event){
  const rel=url.pathname.slice(runtimePrefix.length);
  return fetchRuntimeByRel(rel,req,event);
}
async function shell(req,event){
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

self.addEventListener("install",e=>e.waitUntil((async()=>{
  const cache=await caches.open(SHELL_CACHE);
  await Promise.all(shellFiles.map(async p=>{try{const r=await fetch(new URL(p,scopeUrl),{cache:"no-store"});if(r.ok)await cache.put(new Request(new URL(p,scopeUrl)),r.clone())}catch{}}));
  await self.skipWaiting();
})()));
self.addEventListener("activate",e=>e.waitUntil((async()=>{
  for(const k of await caches.keys())if(k.startsWith("mingpai-shell-v118-test-")&&k!==SHELL_CACHE)await caches.delete(k);
  await self.clients.claim();
})()));
self.addEventListener("message",e=>{
  if(e.data?.type==="SKIP_WAITING"){e.waitUntil(self.skipWaiting());return}

  const d=e.data||{};
  if(d.type==="PREFETCH_VERSION"&&Array.isArray(d.runtimeFiles)){
    e.waitUntil((async()=>{
      const reply=msg=>{
        try{
          if(e.ports&&e.ports[0]) e.ports[0].postMessage(msg);
          else e.source?.postMessage?.(msg);
        }catch{}
      };
      try{
        for(const rel of d.runtimeFiles)await fetchRuntimeByRel(String(rel||""));
        reply({type:"PREFETCH_VERSION_DONE",version:d.version||"",ok:true});
      }catch(err){
        reply({type:"PREFETCH_VERSION_DONE",version:d.version||"",ok:false,error:err?.message||String(err)});
      }
    })());
  }
});
self.addEventListener("fetch",e=>{
  const req=e.request,url=new URL(req.url);
  if(req.cache==="only-if-cached"&&req.mode!=="same-origin")return;
  if(url.origin===scopeUrl.origin&&url.pathname.startsWith(runtimePrefix)){
    e.respondWith(runtime(req,url,e).catch(err=>new Response("runtime proxy failed: "+err.message,{status:502,headers:{"Content-Type":"text/plain; charset=utf-8","Cross-Origin-Opener-Policy":"same-origin","Cross-Origin-Embedder-Policy":"credentialless"}})));
    return;
  }
  if(url.origin===scopeUrl.origin){
    if(url.pathname.endsWith("/version-v118-test.json")){
      e.respondWith(fetch(req,{cache:"no-store"}).then(isolate).catch(()=>caches.match(req,{ignoreSearch:true}).then(r=>r?isolate(r):new Response("{}",{headers:{"Content-Type":"application/json"}}))));
      return;
    }
    if(req.mode==="navigate"||url.pathname.endsWith(".html")||url.pathname===scopeUrl.pathname){
      e.respondWith(shell(req,e));
      return;
    }
    e.respondWith(fetch(req).then(isolate).catch(async()=>{const c=await caches.open(SHELL_CACHE),r=await c.match(req,{ignoreSearch:true});if(r)return isolate(r);throw new Error("offline")}));
  }
});