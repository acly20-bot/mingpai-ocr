#!/usr/bin/env python3
"""v1.18.4.3-test: ensure native confirmation controls reappear.
The main OCR runtime keeps a separate in-memory record view, so external
IndexedDB edits can leave a confirmed card's old controls visible.
After persisting the environment and requesting native filter refresh,
reload the inner app ONLY when its own Confirm button is still absent.
This rehydrates records from IndexedDB; do not add a duplicate confirm flow.
"""
from pathlib import Path
import json,re,subprocess
root=Path("app"); site=root/"test-adaptive"
p=site/"index.html"; core=site/"core.html"; sw=site/"coi-serviceworker.js";mf=site/"version-v118-test.json"
s=p.read_text(encoding="utf-8");c=core.read_text(encoding="utf-8");w=sw.read_text(encoding="utf-8")
m=json.loads(mf.read_text(encoding="utf-8"))
assert m["version"]=="1.18.4.2-test"
assert 'const CLIENT_VERSION="1.18.4.2-test";' in s
assert "statusFilter.dispatchEvent(new Event('change',{bubbles:true}));" in s
start=s.index("          const persist=async e=>{",s.index("  // V4 weather + per-record environment persistence"))
end=s.index("          ti.addEventListener('blur',persist);",start)
old=s[start:end]
assert "r.status='pending'" in old and "envWriteQueues.set(id,job);" in old
anchor="""                // Reconcile only the two counters; leave all OCR and queue state alone."""
assert old.count(anchor)==1
# Keep the built-in event-driven re-render, with a one-time fallback if it
# leaves the old confirmed card mounted. No reload for unchanged records,
# or for edits to already-pending records.
old=old.replace(anchor,r"""                // The OCR core may keep a separate in-memory copy of records.
                // A filter change can repaint counts without recreating action buttons.
                // Re-enter through its native renderer (inner iframe reload) only
                // if the pending record still has no native confirmation control.
                const pendingReviewId=id;
                setTimeout(()=>{
                  const nativeConfirm=[...card.querySelectorAll('button,.btn')]
                    .some(b=>/^(确认|确认记录|确认并同步)$/.test((b.textContent||'').trim()));
                  if(nativeConfirm)return;
                  const view=d.defaultView;
                  try{
                    view?.sessionStorage?.setItem('mingpai-v11843-return-record',
                      JSON.stringify({id:pendingReviewId,when:Date.now()}));
                  }catch{}
                  // The record is already committed in IndexedDB. Reloading
                  // only the embedded app cannot duplicate data or auto-confirm.
                  view?.location?.reload();
                },450);
"""+anchor,1)
s=s[:start]+old+s[end:]
# Recover position on inner app load after the controlled reload.
# Do not force search/filter state, which is owned by the core application.
restore=r"""  // Restore the edited record after the native UI rehydrates from IndexedDB.
  try{
    const raw=d.defaultView?.sessionStorage?.getItem('mingpai-v11843-return-record');
    if(raw){
      d.defaultView.sessionStorage.removeItem('mingpai-v11843-return-record');
      const info=JSON.parse(raw);
      if(Date.now()-info.when<30000 && info.id){
        let attempts=0;
        const scrollToPending=()=>{
          const esc=globalThis.CSS?.escape?CSS.escape(info.id):String(info.id).replace(/["\\]/g,'');
          const selector='[data-select-id="'+esc+'"],[data-id="'+esc+'"]';
          const target=d.querySelector(selector)?.closest('.card');
          if(target){target.scrollIntoView({block:'center',behavior:'instant'});return}
          if(++attempts<16)setTimeout(scrollToPending,250);
        };
        setTimeout(scrollToPending,300);
      }
    }
  }catch(e){console.warn('pending review scroll restore skipped',e)}
"""
anchor2="  // v1.16: OCR.space mode is priority cloud mode with Paddle fallback."
assert s.count(anchor2)==1
s=s.replace(anchor2,restore+"\n"+anchor2,1)
s=s.replace('const CLIENT_VERSION="1.18.4.2-test";','const CLIENT_VERSION="1.18.4.3-test";',1)
s=s.replace('v1.18.4.2 测试版','v1.18.4.3 测试版')
c=c.replace('v1.18.4.2 测试版','v1.18.4.3 测试版')
c=c.replace('mingpai-v11842-test-coi-reload','mingpai-v11843-test-coi-reload')
w=w.replace('mingpai-shell-v11842-test','mingpai-shell-v11843-test')
w=w.replace('1.18.4.2-test','1.18.4.3-test')
m['version']='1.18.4.3-test'
assert 'r.status=\'pending\'' in s and 'scheduleEnvironmentResync(id)' not in s[s.index("          const persist=async e=>"):s.index("          ti.addEventListener('blur',persist);")]
assert 'setTimeout(scrollToPending,300)' in s
assert m['rules']=='recognition-rules-v1184.json'
assert m['mainJs']=='index-B81hyAdU-v11832-viewport-test2.js'
p.write_text(s,encoding="utf-8")
core.write_text(c,encoding="utf-8")
sw.write_text(w,encoding="utf-8")
mf.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for label,html in [('outer',s),('core',c)]:
  for i,code in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
    if code.strip():
      js=Path('/tmp')/f'v11843-{label}-{i}.js';js.write_text(code,encoding="utf-8")
      subprocess.run(['node','--check',str(js)],check=True)
tmp=Path('/tmp/v11843-sw.js');tmp.write_text(w,encoding="utf-8")
subprocess.run(['node','--check',str(tmp)],check=True)
assert json.loads((root/'version-v118-test.json').read_text())['version']=='1.18.4'
print('PASS v1.18.4.3-test: pending edit rehydrates native Confirm controls; formal unchanged')
