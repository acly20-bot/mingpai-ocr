#!/usr/bin/env python3
"""Test-only stats-table adaptive column and unit-label layout.
Keep display version v1.18.4.5; preserve production and all data/OCR logic.
Base: release-baseline/v11845-dock-recovery.
"""
from pathlib import Path
import hashlib,re,subprocess,json
root=Path('app'); test=root/'test-adaptive'
formal_names=('index.html','core.html','coi-serviceworker.js','version-v118-test.json','recognition-rules-v1184.json')
formal_before={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in formal_names}
m=json.loads((test/'version-v118-test.json').read_text())
assert m['version']=='1.18.4.5-test' and json.loads((root/'version-v118-test.json').read_text())['version']=='1.18.4.5'
p=test/'index.html';s=p.read_text()
old="""(mode==='dept'?'<col style="width:20%"><col style="width:13%"><col><col style="width:38px">':'<col style="width:26%"><col><col style="width:38px">')"""
new="""(mode==='dept'?'<col style="width:var(--stats-unit-width,35%)"><col style="width:var(--stats-dept-width,18%)"><col><col style="width:38px">':'<col style="width:var(--stats-unit-width,36%)"><col><col style="width:38px">')"""
assert s.count(old)==1,'stats original colgroup not found'
s=s.replace(old,new,1)
anchor="""      modal.querySelectorAll('[data-mode]').forEach(btn=>btn.onclick=()=>{mode=btn.dataset.mode;render()});"""
assert s.count(anchor)==1
enhancement=r"""      // Adaptive stats columns. No modification of actual record values.
      // Prefer a one-line unit; if too long, fit at most two visible lines,
      // shrinking only the unit label instead of shrinking the entire table.
      const table=modal.querySelector('.v1182-stats-table');
      const maxUnitChars=Math.max(4,...data.map(row=>[...String(row[0]||'')].length));
      const maxDeptChars=mode==='dept'
        ?Math.max(2,...data.map(row=>[...String(row[1]||'')].length)):0;
      const unitWidth=Math.min(43,Math.max(31,27+Math.ceil(maxUnitChars*.72)));
      const deptWidth=mode==='dept'
        ?Math.min(21,Math.max(16,12+Math.ceil(maxDeptChars*.7))):0;
      table.style.setProperty('--stats-unit-width',unitWidth+'%');
      if(mode==='dept')table.style.setProperty('--stats-dept-width',deptWidth+'%');
      const ctx=d.createElement('canvas').getContext('2d');
      table.querySelectorAll('tbody tr').forEach(row=>{
        const unit=row.cells[0];
        if(!unit)return;
        const full=unit.textContent||'';
        unit.title=full; // long-press or desktop hover exposes full hospital name
        unit.style.overflowWrap='normal';
        unit.style.wordBreak='normal';
        const label=d.createElement('span');
        label.className='v11845-stats-unit-label';
        label.textContent=full;
        label.style.cssText='display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;line-clamp:2;overflow:hidden;overflow-wrap:anywhere;word-break:break-word;line-height:1.32';
        unit.replaceChildren(label);
        if(!ctx)return;
        const available=Math.max(24,unit.getBoundingClientRect().width-7);
        const family=d.defaultView.getComputedStyle(unit).fontFamily||'sans-serif';
        const textWidth=size=>{ctx.font=size+'px '+family;return ctx.measureText(full).width};
        // Keep 13px when two lines fit; shrink only when it enables a
        // single line or is needed to avoid a third line.
        let size=13;
        for(let candidate=13;candidate>=10;candidate-=.5){
          if(textWidth(candidate)<=available){size=candidate;break}
        }
        if(textWidth(size)>available){
          while(size>9&&textWidth(size)>available*1.85)size-=.5;
        }
        label.style.fontSize=size+'px';
      });
"""
s=s.replace(anchor,enhancement+anchor,1)
# Re-run responsive measurement on viewport resize WITHOUT polling.
# Existing render is already the normal mode-change mechanism; do not
# recalculate data or rebuild the modal on every DOM mutation.
# Avoid adding external overlays or changing record data.
assert 'v11845-stats-unit-label' in s
assert 'width:20%' not in s[s.index("const headers=mode==="):s.index("modal.querySelectorAll('[data-mode]')")]
assert 'nativeChange(\'temperature\',temp)' in s
assert 'dockModalSelectors' in s and 'trulyOpen' in s
p.write_text(s)
sw=test/'coi-serviceworker.js';w=sw.read_text()
old_cache='const SHELL_CACHE="mingpai-shell-v11845-dockfix-test";'
assert w.count(old_cache)==1
w=w.replace(old_cache,'const SHELL_CACHE="mingpai-shell-v11845-stats-restored-test";',1)
sw.write_text(w)
assert json.loads((test/'version-v118-test.json').read_text())['version']=='1.18.4.5-test'
for name,oldhash in formal_before.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==oldhash, 'formal modified '+name
for name,doc in [('outer',s),('core',(test/'core.html').read_text())]:
    for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',doc,re.I|re.S)):
        if js.strip():
            path=Path('/tmp')/f'v11845-stats-{name}-{i}.js'
            path.write_text(js)
            subprocess.run(['node','--check',str(path)],check=True)
path=Path('/tmp/v11845-stats-sw.js');path.write_text(w)
subprocess.run(['node','--check',str(path)],check=True)
print('PASS adaptive statistics width in test, unchanged version, unchanged formal')


# Promote the IDENTICAL layout to formal, changing only version labels and
# cache namespace. Keep original OCR runtime, database, and review logic.
trial=(test/'index.html').read_text(encoding='utf-8')
assert trial.count('const CLIENT_VERSION="1.18.4.5-test";')==1
assert 'v11845-stats-unit-label' in trial
stable=trial.replace('const CLIENT_VERSION="1.18.4.5-test";',
                     'const CLIENT_VERSION="1.18.4.5";',1)
stable=stable.replace('v1.18.4.5 测试版','v1.18.4.5 正式版')
assert 'const CLIENT_VERSION="1.18.4.5";' in stable
(root/'index.html').write_text(stable,encoding='utf-8')
formal_sw=root/'coi-serviceworker.js'
fw=formal_sw.read_text(encoding='utf-8')
old_formal_cache='const SHELL_CACHE="mingpai-shell-v11845-dockfix-formal-recover";'
assert fw.count(old_formal_cache)==1
fw=fw.replace(old_formal_cache,
  'const SHELL_CACHE="mingpai-shell-v11845-stats-restored-formal";',1)
formal_sw.write_text(fw,encoding='utf-8')
for label,html in [('formal',stable)]:
    for i,code in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
        if code.strip():
            f=Path('/tmp')/f'mingpai-stats-restore-{label}-{i}.js'
            f.write_text(code,encoding='utf-8')
            subprocess.run(['node','--check',str(f)],check=True)
f=Path('/tmp/mingpai-stats-restore-sw.js')
f.write_text(fw,encoding='utf-8')
subprocess.run(['node','--check',str(f)],check=True)
assert json.loads((root/'version-v118-test.json').read_text())['version']=='1.18.4.5'
assert json.loads((test/'version-v118-test.json').read_text())['version']=='1.18.4.5-test'
assert (root/'recognition-rules-v1184.json').read_bytes()==(test/'recognition-rules-v1184.json').read_bytes()
for name in ('index.html','test-adaptive/index.html','recognition-rules-v1184.json'):
    print('RELEASE_SHA256',name,hashlib.sha256((root/name).read_bytes()).hexdigest())
print('PASS restored previous screenshot layout to formal and test, no visible version bump')
