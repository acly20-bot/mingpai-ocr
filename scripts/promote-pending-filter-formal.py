#!/usr/bin/env python3
"""Promote the verified pending-filter behavior into formal while preserving
formal-only dock recovery and original user-visible version 1.18.4.5.
Only the known-good new inline block is moved from test to formal.
"""
from pathlib import Path
import json,hashlib,re,subprocess
root=Path('app');test=root/'test-adaptive'
formal=root/'index.html';tested=test/'index.html'
a=formal.read_text(encoding='utf-8');b=tested.read_text(encoding='utf-8')
fm=json.loads((root/'version-v118-test.json').read_text(encoding='utf-8'))
tm=json.loads((test/'version-v118-test.json').read_text(encoding='utf-8'))
assert fm['version']=='1.18.4.5' and tm['version']=='1.18.4.5-test'
assert fm['mainJs']==tm['mainJs']=='index-B81hyAdU-v11832-viewport-test2.js'
assert fm['rules']==tm['rules']=='recognition-rules-v1184.json'
assert (root/'recognition-rules-v1184.json').read_bytes()==(test/'recognition-rules-v1184.json').read_bytes()
start='  // Native pending-list reconciliation:'
end='  let envCaptureRunning=false;'
assert b.count(start)==1 and b.count(end)==1
assert a.count(start)==0 and a.count(end)==1
block=b[b.index(start):b.index(end)]
assert 'pendingConfirmRefreshBound' in block
assert "pendingStatusSelect.dispatchEvent(new Event('change',{bubbles:true}))" in block
assert "rec?.status==='confirmed'" in block
assert 'stale.remove()' in block
assert 'location.reload' not in block and 'putRecord(' not in block
assert 'environmentNativeList.addEventListener' in a
assert 'scheduleHiddenDockRecovery' in a and 'scheduleHiddenDockRecovery' not in b
assert "nativeChange('temperature',temp)" in a and "nativeChange('humidity',hum)" in a
assert 'v11845-stats-unit-label' in a
assert 'const CLIENT_VERSION="1.18.4.5";' in a
a=a.replace(end,block+end,1)
assert a.count('pendingConfirmRefreshBound')==2
assert 'scheduleHiddenDockRecovery' in a
assert 'v11845-stats-unit-label' in a
formal.write_text(a,encoding='utf-8')
sw=root/'coi-serviceworker.js'
w=sw.read_text(encoding='utf-8')
old='const SHELL_CACHE="mingpai-shell-v11845-stats-restored-formal";'
assert w.count(old)==1
w=w.replace(old,'const SHELL_CACHE="mingpai-shell-v11845-pending-refresh-formal";',1)
sw.write_text(w,encoding='utf-8')
# The test branch carries the same reviewed behavior with an independent cache.
assert 'pendingConfirmRefreshBound' in tested.read_text(encoding='utf-8')
assert json.loads((root/'version-v118-test.json').read_text())['version']=='1.18.4.5'
assert json.loads((test/'version-v118-test.json').read_text())['version']=='1.18.4.5-test'
for label,path in (('formal',root),('test',test)):
    for name in ('index.html','core.html'):
        html=(path/name).read_text(encoding='utf-8')
        for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
            if js.strip():
                f=Path('/tmp')/f'mingpai-pending-promote-{label}-{name}-{i}.js'
                f.write_text(js,encoding='utf-8')
                subprocess.run(['node','--check',str(f)],check=True)
    f=Path('/tmp')/f'mingpai-pending-promote-{label}-sw.js'
    f.write_text((path/'coi-serviceworker.js').read_text())
    subprocess.run(['node','--check',str(f)],check=True)
for name in ('index.html','test-adaptive/index.html','recognition-rules-v1184.json'):
    print('RELEASE_SHA256',name,hashlib.sha256((root/name).read_bytes()).hexdigest())
print('PASS: native pending filter synced formal/test, formal-only dock guard retained, no version change')
