#!/usr/bin/env python3
"""Promote user-verified 1.18.4.4-test to 1.18.4.4 formal.
All runtime behaviors are byte-identical aside from shell labels and SW scope.
Preserve the previously released formal shell for rollback.
"""
from pathlib import Path
import hashlib,json,re,shutil,subprocess
root=Path("app");test=root/"test-adaptive"
files=("index.html","core.html","coi-serviceworker.js","version-v118-test.json","recognition-rules-v1184.json")
formal=json.loads((root/"version-v118-test.json").read_text())
tested=json.loads((test/"version-v118-test.json").read_text())
assert formal['version']=='1.18.4' and tested['version']=='1.18.4.4-test'
assert formal['rules']==tested['rules']=='recognition-rules-v1184.json'
assert formal['mainJs']==tested['mainJs']=='index-B81hyAdU-v11832-viewport-test2.js'
assert (root/formal['rules']).read_bytes()==(test/tested['rules']).read_bytes()
rollback=root/"release-snapshots"/"before-v11844-formal"
assert not rollback.exists()
rollback.mkdir(parents=True)
for name in files: shutil.copy2(root/name,rollback/name)
src={f:(test/f).read_text(encoding='utf-8') if f.endswith(('.html','.js','.json')) else None for f in files}
html=src['index.html']
core=src['core.html']
worker=src['coi-serviceworker.js']
assert html.count('const CLIENT_VERSION="1.18.4.4-test";')==1
assert 'nativeField.dispatchEvent(new Event' in html
assert 'view?.location?.reload()' not in html
assert 'v11841-modal-back' in html
html=html.replace('const CLIENT_VERSION="1.18.4.4-test";','const CLIENT_VERSION="1.18.4.4";')
html=html.replace('v1.18.4.4 测试版','v1.18.4.4 正式版')
core=core.replace('v1.18.4.4 测试版','v1.18.4.4 正式版')
assert 'mingpai-v11844-test-coi-reload' in core
core=core.replace('mingpai-v11844-test-coi-reload','mingpai-v11844-formal-coi-reload')
assert 'mingpai-shell-v11844-test' in worker
worker=worker.replace('mingpai-shell-v11844-test','mingpai-shell-v11844-formal')
worker=worker.replace('1.18.4.4-test','1.18.4.4')
m={**tested,'version':'1.18.4.4'}
for name,content in [('index.html',html),('core.html',core),('coi-serviceworker.js',worker)]:
    (root/name).write_text(content,encoding='utf-8')
(root/"version-v118-test.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert (root/"recognition-rules-v1184.json").read_bytes()==(test/"recognition-rules-v1184.json").read_bytes()
assert (test/"version-v118-test.json").read_text(encoding='utf-8')==src["version-v118-test.json"]
assert 'const CLIENT_VERSION="1.18.4.4";' in html
assert 'nativeField.dispatchEvent(new Event' in (root/'index.html').read_text()
assert "view?.location?.reload()" not in (root/'index.html').read_text()
for label,source in [('outer',html),('core',core)]:
    for i,script in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',source,re.I|re.S)):
        if script.strip():
            fn=Path('/tmp')/f'v11844-formal-{label}-{i}.js'
            fn.write_text(script,encoding='utf-8')
            subprocess.run(['node','--check',str(fn)],check=True)
fn=Path('/tmp/v11844-formal-sw.js')
fn.write_text(worker,encoding='utf-8')
subprocess.run(['node','--check',str(fn)],check=True)
print('PASS v1.18.4.4 formal: user-approved native review UI, same COS JS/rules, tested route unchanged')
print('FORMAL_SHA256',hashlib.sha256((root/'index.html').read_bytes()).hexdigest())
print('TEST_SHA256',hashlib.sha256((test/'index.html').read_bytes()).hexdigest())
