#!/usr/bin/env python3
"""Same-version production-only mobile dock recovery.
Test version is preserved byte-for-byte. Formal build from frozen dockfix baseline.
"""
from pathlib import Path
import json,re,hashlib,subprocess
root=Path('app')
formal=root/'index.html'
test=root/'test-adaptive'
old_test={name:hashlib.sha256((test/name).read_bytes()).hexdigest()
          for name in ('index.html','core.html','coi-serviceworker.js','version-v118-test.json','recognition-rules-v1184.json')}
text=formal.read_text(encoding='utf-8')
assert 'const CLIENT_VERSION="1.18.4.5";' in text
assert text.count('const v118ModalDockGuard=()=>{')==1
assert 'v11841-modal-back' in text
original="""    const blocked=selectors.some(selector=>trulyOpen(d.querySelector(selector)));
    dock.style.setProperty('display',blocked?'none':'grid','important');
"""
replacement="""    const blocked=selectors.some(selector=>trulyOpen(d.querySelector(selector)));
    const wanted=blocked?'none':'grid';
    // Avoid repeated style mutations and permit self-recovery when a stale
    // camera/re-OCR close path leaves the dock hidden.
    if(dock.style.display!==wanted ||
       dock.style.getPropertyPriority('display')!=='important'){
      dock.style.setProperty('display',wanted,'important');
    }
"""
assert text.count(original)==1
text=text.replace(original,replacement,1)
old="""        if(rec.type==='attributes'){
          const t=rec.target;
          return t.matches?.(dockModalSelectors);
        }
"""
new="""        if(rec.type==='attributes'){
          const t=rec.target;
          // A live modal can change visibility on its inner nodes, not only
          // its outer root. Also recover if an older UI action directly
          // sets mobileDock.style.display='none'.
          return t.matches?.(dockModalSelectors) ||
            !!t.closest?.(dockModalSelectors) ||
            (t.id==='mobileDock' && rec.attributeName==='style');
        }
"""
assert text.count(old)==1
text=text.replace(old,new,1)
# Close/camera-related UI events can modify visibility and display via
# native browser restoration without a modal root mutation.
anchor="""  d.defaultView?.addEventListener('resize',v118ScheduleUiFix);
"""
insertion="""  d.defaultView?.addEventListener('resize',v118ScheduleUiFix);
  // Re-check only while the dock is hidden; prevents stale state after
  // native camera returns. There is no background polling while visible.
  let dockRecoveryPending=false;
  const scheduleHiddenDockRecovery=()=>{
    const dock=d.getElementById('mobileDock');
    if(!dock || dockRecoveryPending || dock.style.display!=='none')return;
    dockRecoveryPending=true;
    setTimeout(()=>{
      dockRecoveryPending=false;
      v118ModalDockGuard();
    },260);
  };
  d.addEventListener('change',scheduleHiddenDockRecovery,true);
  d.addEventListener('input',scheduleHiddenDockRecovery,true);
"""
assert text.count(anchor)==1
text=text.replace(anchor,insertion,1)
formal.write_text(text,encoding='utf-8')
sw=root/'coi-serviceworker.js'
ss=sw.read_text(encoding='utf-8')
assert 'const APP_VERSION="1.18.4.5";' in ss
assert 'const SHELL_CACHE="mingpai-shell-v11845-dockfix-formal";' in ss
ss=ss.replace('const SHELL_CACHE="mingpai-shell-v11845-dockfix-formal";',
 'const SHELL_CACHE="mingpai-shell-v11845-dockfix-formal-recover";',1)
sw.write_text(ss,encoding='utf-8')
# Do not change visible versions or manifest; test is known-good.
assert json.loads((root/'version-v118-test.json').read_text())['version']=='1.18.4.5'
assert json.loads((test/'version-v118-test.json').read_text())['version']=='1.18.4.5-test'
assert "nativeChange('temperature',temp)" in text and "nativeChange('humidity',hum)" in text
assert 'view?.location?.reload()' not in text
assert (root/'recognition-rules-v1184.json').read_bytes()==(test/'recognition-rules-v1184.json').read_bytes()
for name,h in old_test.items():
    assert hashlib.sha256((test/name).read_bytes()).hexdigest()==h,'TEST_CHANGED:'+name
for label,html in [('index',text),('core',(root/'core.html').read_text(encoding='utf-8'))]:
    for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
        if js.strip():
            f=Path('/tmp')/f'v11845-dock-recover-{label}-{i}.js'
            f.write_text(js,encoding='utf-8')
            subprocess.run(['node','--check',str(f)],check=True)
f=Path('/tmp/v11845-dock-recover-sw.js')
f.write_text(ss,encoding='utf-8')
subprocess.run(['node','--check',str(f)],check=True)
for path in ['index.html','test-adaptive/index.html','recognition-rules-v1184.json']:
 print('RELEASE_SHA256',path,hashlib.sha256((root/path).read_bytes()).hexdigest())
print('PASS formal dock self-heal, tested route byte-identical, version unchanged')
