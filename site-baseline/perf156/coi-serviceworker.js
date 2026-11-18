const VERSION='1.156.2';
const CACHE_NAME='mingpai-perf1562-cos-proxy-v1';
const COS_BASE_PROD='https://mingpai-ocr-1387910526.cos.ap-guangzhou.myqcloud.com/perf156/cos/';
const SCOPE_URL=new URL(self.registration.scope);
const PROXY_PREFIX=new URL('./cos/',SCOPE_URL).pathname;
function cosBase(){ return COS_BASE_PROD; }
function isolatedResponse(resp){
  if(!resp || resp.type==='opaque') return resp;
  const h=new Headers(resp.headers);
  h.set('Cross-Origin-Opener-Policy','same-origin');
  h.set('Cross-Origin-Embedder-Policy','credentialless');
  h.set('Cross-Origin-Resource-Policy','same-origin');
  h.delete('Content-Disposition');
  return new Response(resp.body,{status:resp.status,statusText:resp.statusText,headers:h});
}
function contentTypeFor(path,h){
  if(h.has('Content-Type')&&h.get('Content-Type')) return;
  if(path.endsWith('.js')) h.set('Content-Type','application/javascript; charset=utf-8');
  else if(path.endsWith('.wasm')) h.set('Content-Type','application/wasm');
  else if(path.endsWith('.onnx')) h.set('Content-Type','application/octet-stream');
}
async function proxyCos(req,url){
  const rel=url.pathname.slice(PROXY_PREFIX.length);
  const target=new URL(rel,cosBase());
  target.search=url.search;
  const cache=await caches.open(CACHE_NAME);
  const bypass=['reload','no-store'].includes(req.cache)||url.searchParams.has('nocache');
  if(!bypass){const hit=await cache.match(req); if(hit) return isolatedResponse(hit);}
  const headers=new Headers();
  const range=req.headers.get('Range'); if(range) headers.set('Range',range);
  const upstream=await fetch(target.toString(),{method:'GET',mode:'cors',credentials:'omit',redirect:'follow',headers,cache:bypass?'no-store':'default'});
  if(!upstream.ok) throw new Error(`COS ${upstream.status} ${target.pathname}`);
  const h=new Headers(upstream.headers);
  contentTypeFor(rel,h);
  h.delete('Content-Disposition');
  h.set('Cross-Origin-Opener-Policy','same-origin');
  h.set('Cross-Origin-Embedder-Policy','credentialless');
  h.set('Cross-Origin-Resource-Policy','same-origin');
  const clean=new Response(upstream.body,{status:upstream.status,statusText:upstream.statusText,headers:h});
  if(upstream.status===200 && !range){try{await cache.put(req,clean.clone());}catch(e){}}
  return clean;
}
self.addEventListener('install',event=>{self.skipWaiting();});
self.addEventListener('activate',event=>{event.waitUntil((async()=>{for(const k of await caches.keys())if(k.startsWith('mingpai-perf156')&&k!==CACHE_NAME)await caches.delete(k);await self.clients.claim();})());});
self.addEventListener('message',event=>{if(event.data&&event.data.type==='SKIP_WAITING')self.skipWaiting();});
self.addEventListener('fetch',event=>{
  const req=event.request, url=new URL(req.url);
  if(req.cache==='only-if-cached'&&req.mode!=='same-origin') return;
  if(url.origin===SCOPE_URL.origin && url.pathname.startsWith(PROXY_PREFIX)){
    event.respondWith(proxyCos(req,url).catch(async err=>{console.error('[v1562 proxy]',err);return new Response('COS proxy failed: '+err.message,{status:502,headers:{'Content-Type':'text/plain; charset=utf-8','Cross-Origin-Opener-Policy':'same-origin','Cross-Origin-Embedder-Policy':'credentialless'}});}));
    return;
  }
  event.respondWith(fetch(req).then(isolatedResponse).catch(()=>fetch(req)));
});
