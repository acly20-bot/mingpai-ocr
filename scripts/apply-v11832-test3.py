#!/usr/bin/env python3
"""Restore verified v1.18.3.1 card observer and fix top weather button ReferenceError.
Runs AFTER v1.18.3.2-test.2 patch, only against perf-v11832 route.
"""
from pathlib import Path
import json,re,subprocess,hashlib
root=Path('app')
perf=root/'perf-v11832'
p=perf/'index.html'
s=p.read_text(encoding='utf-8')
assert 'const CLIENT_VERSION="1.18.3.2-test.2";' in s
assert s.count("refresh.after(modeMark);")==1, 'missing broken weather line'
s=s.replace("refresh.after(modeMark);","wrap.querySelector('.field-weather-refresh')?.after(modeMark);",1)
# The optimized observer skipped changes when the card was rebuilt; restore the
# confirmed-safe observer that always decorates every card after a batch change.
a=s.index('  let envCardsScheduled=false;')
b=s.index('  // v1.18.2.1-test test: compact field UI',a)
stable=(root/'index.html').read_text(encoding='utf-8')
sa=stable.index('  let envCardsScheduled=false;')
sb=stable.index('  // v1.18.2.1-test test: compact field UI',sa)
obs=stable[sa:sb]
assert "new MutationObserver(()=>{" in obs and "decorateCards()" in obs
s=s[:a]+obs+s[b:]
# Restore verified card observer; preserve key-only IDB and the user-approved
# OCR main JS with viewport behavior.
assert 'getAllKeys()' in s and 'WEATHER_TTL_MS' in s
assert "index-B81hyAdU-v11832-viewport-test2.js" in (perf/'core.html').read_text()
assert s.count('function installWeatherChip()')==1
assert "wrap.querySelector('.field-weather-refresh')?.after(modeMark)" in s
s=s.replace('const CLIENT_VERSION="1.18.3.2-test.2";',
            'const CLIENT_VERSION="1.18.3.2-test.3";',1)
s=s.replace('v1.18.3.2-test.2 性能测试版','v1.18.3.2-test.3 性能测试版')
p.write_text(s,encoding='utf-8')
core=perf/'core.html'
cs=core.read_text(encoding='utf-8')
assert 'v11832-viewport-test2.js' in cs
cs=cs.replace('v1.18.3.2-test.2 性能测试版','v1.18.3.2-test.3 性能测试版')
cs=cs.replace('mingpai-v11832-test2-coi-reload','mingpai-v11832-test3-coi-reload')
cs=cs.replace('?v=1.18.3.2-test.2','?v=1.18.3.2-test.3')
core.write_text(cs,encoding='utf-8')
worker=perf/'coi-serviceworker.js'
ws=worker.read_text(encoding='utf-8')
assert 'mingpai-shell-v11832-test2' in ws
ws=ws.replace('mingpai-shell-v11832-test2','mingpai-shell-v11832-test3')
ws=ws.replace('1.18.3.2-test.2','1.18.3.2-test.3')
worker.write_text(ws,encoding='utf-8')
manifest=perf/'version-v118-test.json'
m=json.loads(manifest.read_text(encoding='utf-8'))
assert m['version']=='1.18.3.2-test.2'
m['version']='1.18.3.2-test.3'
manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
formal=json.loads((root/'version-v118-test.json').read_text(encoding='utf-8'))
assert formal['version']=='1.18.3.1' and formal['mainJs']=='index-B81hyAdU-v1183-weather-test1.js'
assert "取消确认" in s and "btn.remove()" in s
for name,html in [('index',s),('core',cs)]:
    for i,code in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
        if code.strip():
            f=Path(f'/tmp/v11832-test3-{name}-{i}.js')
            f.write_text(code,encoding='utf-8')
            subprocess.run(['node','--check',str(f)],check=True)
f=Path('/tmp/v11832-test3-sw.js');f.write_text(ws,encoding='utf-8')
subprocess.run(['node','--check',str(f)],check=True)
print('PASS test.3: weather ReferenceError removed, stable DOM observer restored, formal untouched')
