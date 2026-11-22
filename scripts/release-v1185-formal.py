#!/usr/bin/env python3
"""Promote fully user-tested v1.18.5-test.3 performance improvements to formal.
Only three reviewed observer sections move from test to formal, then version.
Keep formal-only dock recovery, native review, temp, synchronization unchanged.
"""
from pathlib import Path
import hashlib,json,re,subprocess
r=Path('app');t=r/'test-adaptive'
formal=r/'index.html';trial=t/'index.html'
a=formal.read_text(encoding='utf-8');b=trial.read_text(encoding='utf-8')
assert json.loads((r/'version-v118-test.json').read_text())['version']=='1.18.4.5'
assert json.loads((t/'version-v118-test.json').read_text())['version']=='1.18.5-test.3'
assert len(json.loads((r/'recognition-rules-v1184.json').read_text())['rules'])==85
assert (r/'recognition-rules-v1184.json').read_bytes()==(t/'recognition-rules-v1184.json').read_bytes()
def move(start,end):
    global a
    assert a.count(start)==b.count(start)==1,(start,'start missing')
    assert a.count(end)==b.count(end)==1,(end,'end missing')
    i=a.index(start);j=a.index(end,i)
    x=b.index(start);y=b.index(end,x)
    assert i<j and x<y
    a=a[:i]+b[x:y]+a[j:]
# Remove only orphaned legacy v1.18.2 observer, not boot retry logic.
legacy='const v1182StartAt=performance.now();'
end='const v11711BaseSrc=frame.getAttribute(\\'src\\');'
assert a.count(legacy)==1 and b.count(legacy)==0
a=a[:a.index(legacy)]+a[a.index(end,a.index(legacy)):]
# Promoted risk-checking logic does not rescan all visible cards on every insertion.
move('  // Only direct record-list replacements trigger a scan;',
     "  list.addEventListener('input',e=>{")
# Promoted card decoration only processes newly inserted cards.
move('  // v1.18.5-test.1: avoid a full IndexedDB-backed card check',
     '  // v1.18.2.1-test test: compact field UI + inline statistics')
assert 'const addedRiskCards=new Set()' in a
assert 'const addedEnvCards=new Set()' in a
assert 'v1182StartAt' not in a
assert 'scheduleHiddenDockRecovery' in a and 'scheduleHiddenDockRecovery' not in b
assert "nativeChange('temperature',temp)" in a and "nativeChange('humidity',hum)" in a
assert 'pendingConfirmRefreshBound' in a and 'const confirmed=/已确认/' in a
assert 'v11845-stats-unit-label' in a
assert "const CLIENT_VERSION=\"1.18.4.5\";" in a
a=a.replace('const CLIENT_VERSION="1.18.4.5";','const CLIENT_VERSION="1.18.5";',1)
a=a.replace('v1.18.4.5 正式版','v1.18.5 正式版')
formal.write_text(a,encoding='utf-8')
fc=r/'core.html';core=fc.read_text(encoding='utf-8')
core=core.replace('v1.18.4.5 正式版','v1.18.5 正式版')
fc.write_text(core,encoding='utf-8')
w=r/'coi-serviceworker.js';sw=w.read_text(encoding='utf-8')
assert 'const APP_VERSION="1.18.4.5";' in sw
assert 'const SHELL_CACHE="mingpai-shell-v11845-bootclose-formal-r9";' in sw
sw=sw.replace('const APP_VERSION="1.18.4.5";','const APP_VERSION="1.18.5";',1)
sw=sw.replace('const SHELL_CACHE="mingpai-shell-v11845-bootclose-formal-r9";','const SHELL_CACHE="mingpai-shell-v1185-formal";',1)
w.write_text(sw,encoding='utf-8')
m=json.loads((r/'version-v118-test.json').read_text())
m['version']='1.18.5'
(r/'version-v118-test.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
for label,site in [('formal',r),('test',t)]:
    expected='1.18.5' if label=='formal' else '1.18.5-test.3'
    assert json.loads((site/'version-v118-test.json').read_text())['version']==expected
    assert len(json.loads((site/'recognition-rules-v1184.json').read_text())['rules'])==85
    for name in ['index.html','core.html']:
        html=(site/name).read_text(encoding='utf-8')
        for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
            if js.strip():
                file=Path('/tmp')/f'v1185-promote-{label}-{name}-{i}.js'
                file.write_text(js,encoding='utf-8')
                subprocess.run(['node','--check',str(file)],check=True)
    file=Path('/tmp')/f'v1185-promote-{label}-sw.js'
    file.write_text((site/'coi-serviceworker.js').read_text(),encoding='utf-8')
    subprocess.run(['node','--check',str(file)],check=True)
assert (r/'recognition-rules-v1184.json').read_bytes()==(t/'recognition-rules-v1184.json').read_bytes()
for name in ['index.html','test-adaptive/index.html','recognition-rules-v1184.json']:
    print('RELEASE_SHA256',name,hashlib.sha256((r/name).read_bytes()).hexdigest())
print('PASS promoted 3 performance changes to formal v1.18.5; test3 kept, 85 rules preserved')
