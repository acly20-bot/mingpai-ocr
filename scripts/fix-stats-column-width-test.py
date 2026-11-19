#!/usr/bin/env python3
"""Mobile-first statistics: unit/department abbreviate, device/count take priority.
Test-only; base release-baseline/v11845-dock-recovery, visible version unchanged.
"""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path('app'); test=root/'test-adaptive'
formal_files=('index.html','core.html','coi-serviceworker.js',
              'version-v118-test.json','recognition-rules-v1184.json')
formal_sha={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in formal_files}
assert json.loads((root/'version-v118-test.json').read_text())['version']=='1.18.4.5'
assert json.loads((test/'version-v118-test.json').read_text())['version']=='1.18.4.5-test'
p=test/'index.html';s=p.read_text(encoding='utf-8')
old="""(mode==='dept'?'<col style="width:20%"><col style="width:13%"><col><col style="width:38px">':'<col style="width:26%"><col><col style="width:38px">')"""
new="""(mode==='dept'?'<col style="width:23%"><col style="width:17%"><col><col style="width:32px">':'<col style="width:25%"><col><col style="width:32px">')"""
assert s.count(old)==1,'expected original statistics colgroup'
s=s.replace(old,new,1)
needle="""      modal.querySelectorAll('[data-mode]').forEach(btn=>btn.onclick=()=>{mode=btn.dataset.mode;render()});"""
assert s.count(needle)==1
enhancement=r"""      // Field-checking view: equipment and quantity are the primary data.
      // Unit and department are hints only; keep their full text in title,
      // but show a short one-line ellipsis on mobile.
      const statsTable=modal.querySelector('.v1182-stats-table');
      statsTable.style.tableLayout='fixed';
      statsTable.style.fontSize='14px';
      statsTable.querySelectorAll('tbody tr').forEach(tr=>{
        const cells=[...tr.cells],countIndex=cells.length-1;
        for(let i=0;i<cells.length;i++){
          const td=cells[i];
          td.style.padding='11px 3px';
          td.style.verticalAlign='middle';
          if(i===countIndex){
            td.style.textAlign='center';
            td.style.fontSize='16px';
            td.style.fontWeight='800';
            td.style.whiteSpace='nowrap';
            continue;
          }
          const full=td.textContent||'';
          td.title=full;
          td.style.overflowWrap='normal';
          td.style.wordBreak='normal';
          const span=d.createElement('span');
          span.textContent=full;
          if(i===0 || (mode==='dept' && i===1)){
            span.className='stats-compact-hint';
            // Two secondary columns should never increase row height.
            // Ellipsis preserves the beginning of the hospital/department.
            span.style.cssText='display:block;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;line-height:1.4';
          }else{
            span.className='stats-priority-equipment';
            // Equipment is the important field: full text when possible,
            // up to two lines for long standardized equipment names.
            span.style.cssText='display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;line-clamp:2;overflow:hidden;overflow-wrap:anywhere;word-break:break-word;font-size:14px;line-height:1.35;font-weight:550';
          }
          td.replaceChildren(span);
        }
      });
"""
s=s.replace(needle,enhancement+needle,1)
assert 'stats-compact-hint' in s and 'stats-priority-equipment' in s
assert "nativeChange('temperature',temp)" in s and "nativeChange('humidity',hum)" in s
assert 'scheduleHiddenDockRecovery' not in s
assert 'dockModalSelectors' in s and 'trulyOpen' in s
assert 'const CLIENT_VERSION="1.18.4.5-test";' in s
p.write_text(s,encoding='utf-8')
sw=test/'coi-serviceworker.js'
w=sw.read_text(encoding='utf-8')
old_cache='const SHELL_CACHE="mingpai-shell-v11845-dockfix-test";'
assert w.count(old_cache)==1
w=w.replace(old_cache,'const SHELL_CACHE="mingpai-shell-v11845-stats-compact-test";',1)
sw.write_text(w,encoding='utf-8')
for filename,sha in formal_sha.items():
    assert hashlib.sha256((root/filename).read_bytes()).hexdigest()==sha,'Formal file modified: '+filename
for label,html in [('outer',s),('core',(test/'core.html').read_text(encoding='utf-8'))]:
    for i,code in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
        if code.strip():
            fp=Path('/tmp')/f'mingpai-stats-compact-{label}-{i}.js'
            fp.write_text(code,encoding='utf-8')
            subprocess.run(['node','--check',str(fp)],check=True)
fp=Path('/tmp/mingpai-stats-compact-sw.js')
fp.write_text(w,encoding='utf-8')
subprocess.run(['node','--check',str(fp)],check=True)
assert json.loads((test/'version-v118-test.json').read_text())['version']=='1.18.4.5-test'
print('PASS stats compact: unit and department single-line truncated, equipment and counts prioritized, production intact')
