#!/usr/bin/env python3
"""Test-only opt-in browser restoration diagnosis (?bootdiag=1).
Base: immutable v1.18.4.5 / 84 rules / bootfix-test2.
No reloads, no IndexedDB writes, no API calls, no production changes.
"""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path('app');test=root/'test-adaptive'
formal_files=['index.html','core.html','coi-serviceworker.js','version-v118-test.json','recognition-rules-v1184.json']
old={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in formal_files}
fm=json.loads((root/'version-v118-test.json').read_text(encoding='utf-8'))
tm=json.loads((test/'version-v118-test.json').read_text(encoding='utf-8'))
assert fm['version']=='1.18.4.5' and tm['version']=='1.18.4.5-test'
assert fm['rules']==tm['rules']=='recognition-rules-v1184.json'
assert len(json.loads((test/'recognition-rules-v1184.json').read_text(encoding='utf-8'))['rules'])==84
p=test/'index.html';s=p.read_text(encoding='utf-8')
anchor='<script id="mingpai-open-version-check">'
assert s.count(anchor)==1
block=r"""<script id="mingpai-optin-boot-diagnosis">
(()=>{
  // Disabled unless user explicitly opens the diagnostic URL.
  if(new URLSearchParams(location.search).get('bootdiag')!=='1')return;
  const begun=Date.now();
  const diag={event:'脚本开始',resumeCount:0};
  const persist=(state)=>{
    try{
      sessionStorage.setItem('mingpai-optin-boot-diag',
        JSON.stringify({when:Date.now(),state}));
    }catch(e){}
  };
  const readState=()=>{
    const f=document.getElementById('app');
    let frame='未创建',inner='未就绪',js='否',records='—';
    try{
      if(f){
        frame=f.contentDocument?.readyState||'等待HTML';
        const d=f.contentDocument;
        if(d){
          const pill=(d.getElementById('networkPill')?.textContent||'').trim();
          inner=(d.getElementById('progress')?.textContent||'').trim().slice(0,18)||pill||'未就绪';
          js=d.querySelector('script[data-mingpai-main]')?'已请求':'未请求';
          records=String(d.querySelectorAll('#recordList article.card').length);
        }
      }
    }catch(e){frame='跨域或未接管'}
    return {frame,inner,js,records};
  };
  const update=()=>{
    const e=document.getElementById('mingpaiBootDiag');
    if(!e)return;
    const now=new Date().toLocaleTimeString('zh-CN',{hour12:false});
    const state=readState();
    const sw=!!navigator.serviceWorker?.controller?'有':'无';
    e.querySelector('[data-mingpai-boot-state]').textContent=
      '诊断 '+now+'｜页面运行 '+Math.floor((Date.now()-begun)/1000)+'秒｜最后事件 '+diag.event+
      '｜内页 '+state.frame+'｜OCR '+state.js+'｜记录卡 '+state.records+
      '｜SW '+sw+'｜'+state.inner;
    persist({...state,event:diag.event,sw,now});
  };
  const install=()=>{
    if(document.getElementById('mingpaiBootDiag'))return;
    const panel=document.createElement('div');
    panel.id='mingpaiBootDiag';
    panel.style.cssText='position:fixed;top:0;left:0;right:0;z-index:2147483646;background:#202b41;color:white;padding:5px 7px;font:11px/1.5 sans-serif;overflow-wrap:anywhere;box-shadow:0 2px 6px #0003';
    panel.innerHTML='<span data-mingpai-boot-state>诊断开始</span><button type="button" style="float:right;margin-left:6px;font:11px sans-serif" data-mingpai-close>×</button>';
    document.body.appendChild(panel);
    panel.querySelector('[data-mingpai-close]').onclick=()=>{
      panel.remove();
      clearInterval(interval);
    };
    update();
  };
  const on=(name)=>{diag.event=name;diag.resumeCount++;update()};
  window.addEventListener('pageshow',e=>on('pageshow('+e.persisted+')'));
  document.addEventListener('visibilitychange',()=>on('visibility:'+document.visibilityState));
  document.addEventListener('resume',()=>on('resume'));
  window.addEventListener('focus',()=>on('focus'));
  window.addEventListener('error',()=>on('页面脚本报错'));
  window.addEventListener('unhandledrejection',()=>on('加载Promise失败'));
  document.addEventListener('DOMContentLoaded',install,{once:true});
  const interval=setInterval(update,1250);
  setTimeout(()=>{if(!document.hidden)update()},8000);
})();
</script>
"""
s=s.replace(anchor,block+anchor,1)
assert s.count('mingpai-optin-boot-diagnosis')==1
assert "if(new URLSearchParams(location.search).get('bootdiag')!=='1')return;" in s
assert 'location.reload()' not in block and 'frame.src=' not in block
assert 'pendingConfirmRefreshBound' in s
assert "nativeChange('temperature',temp)" in s
assert 'v11845-stats-unit-label' in s
p.write_text(s,encoding='utf-8')
# Preserve same version; rotate test-only shell to reach users who explicitly
# open the diagnostic route while retaining reliable offline fallback.
sw=test/'coi-serviceworker.js'
w=sw.read_text(encoding='utf-8')
needle='const SHELL_CACHE="mingpai-shell-v11845-bootfix2-test";'
assert w.count(needle)==1
w=w.replace(needle,'const SHELL_CACHE="mingpai-shell-v11845-bootdiag-test";',1)
sw.write_text(w,encoding='utf-8')
for path,sha in old.items():
    assert hashlib.sha256((root/path).read_bytes()).hexdigest()==sha,path
for name,html in [('outer',s),('core',(test/'core.html').read_text(encoding='utf-8'))]:
    for i,code in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
        if code.strip():
            fn=Path('/tmp')/f'bootdiag-{name}-{i}.js';fn.write_text(code,encoding='utf-8')
            subprocess.run(['node','--check',str(fn)],check=True)
fn=Path('/tmp/bootdiag-sw.js');fn.write_text(w,encoding='utf-8')
subprocess.run(['node','--check',str(fn)],check=True)
assert json.loads((test/'version-v118-test.json').read_text())['version']=='1.18.4.5-test'
print('PASS: opt-in-only boot diagnosis. No app reload, no data modification, formal byte-identical')
