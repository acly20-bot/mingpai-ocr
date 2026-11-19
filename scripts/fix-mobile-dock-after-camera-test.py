#!/usr/bin/env python3
"""v1.18.4.5 test-only hotfix: mobile dock stuck hidden after photo/re-OCR.
Keep user-visible version unchanged, production SHA unchanged.
"""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path('app'); test=root/'test-adaptive'
paths=['index.html','core.html','coi-serviceworker.js','version-v118-test.json','recognition-rules-v1184.json']
before={x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths}
f=test/'index.html';s=f.read_text(encoding='utf-8')
m=json.loads((test/'version-v118-test.json').read_text(encoding='utf-8'))
assert m['version']=='1.18.4.5-test' and json.loads((root/'version-v118-test.json').read_text())['version']=='1.18.4.5'
a=s.index('  const v118ModalDockGuard=()=>{')
b=s.index('\n\n  /* v1.18.4.5 正式版:',a)
old=s[a:b]
assert "modalOpen?'none':'grid'" in old
assert "position!=='fixed'" in old
assert "new MutationObserver(changes=>" in old
new=r"""  // Dock visibility follows actual modal visibility, NOT arbitrary fixed
  // elements (such as OCR progress, which can cover the viewport).
  const v118ModalDockGuard=()=>{
    const dock=d.getElementById('mobileDock')||d.querySelector('.mobile-dock');
    if(!dock)return;
    const selectors=[
      '#cropModal',
      '#v155ImagePreview',
      '#v15333ShareOverlay',
      '#fieldStatsModalV1171'
    ];
    const trulyOpen=el=>{
      if(!el||!el.isConnected||el.hidden||el.hasAttribute('inert')||
         el.getAttribute('aria-hidden')==='true')return false;
      let n=el;
      while(n&&n.nodeType===1){
        const css=d.defaultView.getComputedStyle(n);
        if(css.display==='none'||css.visibility==='hidden'||css.visibility==='collapse'||
           Number(css.opacity)===0)return false;
        n=n.parentElement;
      }
      const box=el.getBoundingClientRect();
      return box.width>30&&box.height>30;
    };
    const blocked=selectors.some(selector=>trulyOpen(d.querySelector(selector)));
    dock.style.setProperty('display',blocked?'none':'grid','important');
  };
  v118ModalDockGuard();

  let v118UiFixTimer=0;
  const v118ScheduleUiFix=()=>{
    clearTimeout(v118UiFixTimer);
    v118UiFixTimer=setTimeout(()=>{
      v118NormalizeDialogs();
      v118ModalDockGuard();
    },50);
  };
  // Watch open/close state transitions as well as node insertions.
  // Do not watch our dock style changes: prevents mutation loops.
  const dockModalSelectors='#cropModal,#v155ImagePreview,#v15333ShareOverlay,#fieldStatsModalV1171';
  try{
    const watcher=new MutationObserver(records=>{
      if(records.some(rec=>{
        if(rec.type==='attributes'){
          const t=rec.target;
          return t.matches?.(dockModalSelectors);
        }
        return [...rec.addedNodes,...rec.removedNodes].some(n=>
          n.nodeType===1&&(n.matches?.(dockModalSelectors)||
                            n.querySelector?.(dockModalSelectors)));
      }))v118ScheduleUiFix();
    });
    watcher.observe(d.body,{subtree:true,childList:true,
      attributes:true,attributeFilter:['hidden','style','class','aria-hidden']});
  }catch(e){console.debug('dock modal observer unavailable',e)}
  // Camera apps suspend and resume the page without necessarily changing DOM.
  d.addEventListener('click',v118ScheduleUiFix,true);
  d.addEventListener('visibilitychange',()=>{
    if(!d.hidden)v118ScheduleUiFix();
  });
  d.defaultView?.addEventListener('focus',v118ScheduleUiFix);
  d.defaultView?.addEventListener('pageshow',v118ScheduleUiFix);
  d.defaultView?.addEventListener('resize',v118ScheduleUiFix);
"""
s=s[:a]+new+s[b:]
assert s.count('const v118ModalDockGuard=()=>{')==1
assert 'modalOpen?' not in s[s.index('const v118ModalDockGuard=()=>{'):s.index('const dockModalSelectors=')]
assert 'fixed' not in new.split('const trulyOpen=')[1].split('const blocked=')[0]
assert s.count('const CLIENT_VERSION="1.18.4.5-test";')==1
assert "nativeChange('temperature',temp)" in s and "nativeChange('humidity',hum)" in s
assert "view?.location?.reload()" not in s
f.write_text(s,encoding='utf-8')
# Internal cache revision only; do NOT modify page/version manifest display labels.
sw=test/'coi-serviceworker.js'
w=sw.read_text(encoding='utf-8')
assert 'const SHELL_CACHE="mingpai-shell-v11845-test";' in w
w=w.replace('const SHELL_CACHE="mingpai-shell-v11845-test";','const SHELL_CACHE="mingpai-shell-v11845-dockfix-test";',1)
sw.write_text(w,encoding='utf-8')
temp=Path('/tmp/dock-11845-sw.js')
temp.write_text(w,encoding='utf-8')
subprocess.run(['node','--check',str(temp)],check=True)
for label,html in [('outer',s),('core',(test/'core.html').read_text(encoding='utf-8'))]:
    for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
        if js.strip():
            temp=Path('/tmp')/f'dock-11845-{label}-{i}.js'
            temp.write_text(js,encoding='utf-8')
            subprocess.run(['node','--check',str(temp)],check=True)
for name,hash_before in before.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==hash_before,'FORMAL_CHANGED:'+name
assert json.loads((test/'version-v118-test.json').read_text())['version']=='1.18.4.5-test'
assert 'recognition-rules-v1184.json' in (test/'core.html').read_text()
print('PASS: no version bump; dock ignores fixed OCR overlay; modal hidden-state changes observed; formal bytes unchanged')
