#!/usr/bin/env python3
"""Test-only fix: on native Confirm in Pending filter, reapply native filter.
Never mutate record status, Feishu sync state, data, or force page reload.
Visible version v1.18.4.5 stays unchanged; production byte-identical.
"""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path('app');test=root/'test-adaptive'
formal_files=['index.html','core.html','coi-serviceworker.js','version-v118-test.json','recognition-rules-v1184.json']
formal_before={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in formal_files}
assert json.loads((root/'version-v118-test.json').read_text(encoding='utf-8'))['version']=='1.18.4.5'
assert json.loads((test/'version-v118-test.json').read_text(encoding='utf-8'))['version']=='1.18.4.5-test'
p=test/'index.html';s=p.read_text(encoding='utf-8')
anchor="""  let envCaptureRunning=false;"""
assert s.count(anchor)==1
enhancement=r"""  // Native pending-list reconciliation: the core updates the record's
  // in-memory + IndexedDB status but can leave its old confirmed card
  // visible until the status filter is applied again.
  // Observe ONLY a real click on the core's existing Confirm button.
  // Wait for its successful native state commit before touching the list.
  const pendingConfirmList=d.getElementById('recordList');
  const pendingStatusSelect=d.getElementById('statusFilter');
  if(pendingConfirmList && pendingStatusSelect &&
     !pendingConfirmList.dataset.pendingConfirmRefreshBound){
    pendingConfirmList.dataset.pendingConfirmRefreshBound='1';
    const refreshing=new Set();
    const lookupCard=id=>[...pendingConfirmList.querySelectorAll('article.card')]
      .find(card=>card.querySelector('[data-select-id="'+id+'"],[data-id="'+id+'"]'));
    pendingConfirmList.addEventListener('click',e=>{
      if(pendingStatusSelect.value!=='pending')return;
      const button=e.target.closest('button[data-action="toggle"]');
      if(!button || !/确认记录/.test(button.textContent||''))return;
      const id=String(button.dataset.id||'');
      if(!id || refreshing.has(id))return;
      refreshing.add(id);
      // Reuse the native selector's own change event, not a custom renderer.
      // Do not clear search, change page size, or call IndexedDB.put.
      let attempts=0;
      const onConfirmed=async()=>{
        if(pendingStatusSelect.value!=='pending'){refreshing.delete(id);return}
        try{
          const rec=await getRecord(id);
          if(rec?.status==='confirmed'){
            pendingStatusSelect.dispatchEvent(new Event('change',{bubbles:true}));
            // Some older core paths update counters but leave the stale card
            // mounted; only remove a card after its persisted status is known
            // to be confirmed and while the Pending filter is still selected.
            setTimeout(()=>{
              if(pendingStatusSelect.value!=='pending')return;
              const stale=lookupCard(id);
              if(stale && /已确认/.test(stale.querySelector('.badge')?.textContent||'')){
                stale.remove();
              }
            },180);
            refreshing.delete(id);
            return;
          }
        }catch(err){console.debug('pending filter reconciliation deferred',err)}
        if(++attempts<28){
          setTimeout(onConfirmed,140);
        }else refreshing.delete(id);
      };
      setTimeout(onConfirmed,100);
    },true);
  }
"""
s=s.replace(anchor,enhancement+anchor,1)
assert "pendingConfirmRefreshBound" in s
assert "pendingStatusSelect.dispatchEvent(new Event('change',{bubbles:true}))" in s
assert "rec?.status==='confirmed'" in s
assert "stale.remove()" in s
assert "nativeChange('temperature',temp)" in s and "nativeChange('humidity',hum)" in s
assert 'scheduleHiddenDockRecovery' not in s # formal-only
assert 'dockModalSelectors' in s and 'trulyOpen' in s
assert 'v11845-stats-unit-label' in s
assert 'const CLIENT_VERSION="1.18.4.5-test";' in s
assert 'view?.location?.reload()' not in s
p.write_text(s,encoding='utf-8')
sw=test/'coi-serviceworker.js'
w=sw.read_text(encoding='utf-8')
old_cache='const SHELL_CACHE="mingpai-shell-v11845-stats-restored-test";'
assert w.count(old_cache)==1, 'unexpected test cache namespace'
w=w.replace(old_cache,'const SHELL_CACHE="mingpai-shell-v11845-pending-refresh-test";',1)
sw.write_text(w,encoding='utf-8')
for n,sha in formal_before.items():
  assert hashlib.sha256((root/n).read_bytes()).hexdigest()==sha,'formal modified: '+n
for label,html in [('outer',s),('core',(test/'core.html').read_text(encoding='utf-8'))]:
  for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
    if js.strip():
      f=Path('/tmp')/f'mingpai-pending-{label}-{i}.js'
      f.write_text(js,encoding='utf-8')
      subprocess.run(['node','--check',str(f)],check=True)
f=Path('/tmp/mingpai-pending-sw.js');f.write_text(w,encoding='utf-8')
subprocess.run(['node','--check',str(f)],check=True)
assert json.loads((test/'version-v118-test.json').read_text())['version']=='1.18.4.5-test'
print('PASS test-only native pending-filter refresh after confirmation, no version bump, formal unchanged')
