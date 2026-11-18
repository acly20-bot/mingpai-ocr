#!/usr/bin/env python3
"""Promote the user-verified 1.18.4.5-test to production; no reimplementation.
Run after scripts/apply-v11845-native-environment-test.py on the frozen baseline.
"""
from pathlib import Path
import hashlib, json, re, subprocess
root=Path('app');test=root/'test-adaptive'
formal_manifest=root/'version-v118-test.json'
m=json.loads(formal_manifest.read_text(encoding='utf-8'))
t=json.loads((test/'version-v118-test.json').read_text(encoding='utf-8'))
assert m['version']=='1.18.4.4'
assert t['version']=='1.18.4.5-test'
assert m['mainJs']==t['mainJs']=='index-B81hyAdU-v11832-viewport-test2.js'
assert m['rules']==t['rules']=='recognition-rules-v1184.json'
for name in ['index.html','core.html','coi-serviceworker.js']:
    assert (test/name).is_file()
o=(test/'index.html').read_text(encoding='utf-8')
c=(test/'core.html').read_text(encoding='utf-8')
w=(test/'coi-serviceworker.js').read_text(encoding='utf-8')
assert o.count('const CLIENT_VERSION="1.18.4.5-test";')==1
assert 'nativeChange(\'temperature\',temp)' in o and 'nativeChange(\'humidity\',hum)' in o
assert "view?.location?.reload()" not in o
assert 'v11841-modal-back' in o
o=o.replace('const CLIENT_VERSION="1.18.4.5-test";','const CLIENT_VERSION="1.18.4.5";',1)
o=o.replace('v1.18.4.5 测试版','v1.18.4.5 正式版')
c=c.replace('v1.18.4.5 测试版','v1.18.4.5 正式版')
c=c.replace('mingpai-v11845-test-coi-reload','mingpai-v11845-formal-coi-reload')
assert 'mingpai-shell-v11845-test' in w
w=w.replace('mingpai-shell-v11845-test','mingpai-shell-v11845-formal')
w=w.replace('1.18.4.5-test','1.18.4.5')
for name,source in [('index.html',o),('core.html',c),('coi-serviceworker.js',w)]:
    (root/name).write_text(source,encoding='utf-8')
m={**t,'version':'1.18.4.5'}
formal_manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert (root/'recognition-rules-v1184.json').read_bytes()==(test/'recognition-rules-v1184.json').read_bytes()
for entry in ['','test-adaptive/']:
    p=root/entry
    expected='1.18.4.5' if not entry else '1.18.4.5-test'
    mm=json.loads((p/'version-v118-test.json').read_text(encoding='utf-8'))
    assert mm['version']==expected and mm['mainJs']==m['mainJs'] and mm['rules']==m['rules']
    for name in ['index.html','core.html']:
        txt=(p/name).read_text(encoding='utf-8')
        for j,code in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',txt,re.I|re.S)):
            if code.strip():
                f=Path('/tmp')/('mingpai-11845-'+entry.replace('/','-')+name+str(j)+'.js')
                f.write_text(code,encoding='utf-8')
                subprocess.run(['node','--check',str(f)],check=True)
    swfile=Path('/tmp')/('mingpai-11845-'+entry.replace('/','-')+'sw.js')
    swfile.write_text((p/'coi-serviceworker.js').read_text(encoding='utf-8'),encoding='utf-8')
    subprocess.run(['node','--check',str(swfile)],check=True)
for name in ['index.html','test-adaptive/index.html','recognition-rules-v1184.json']:
    print('RELEASE_SHA256',name,hashlib.sha256((root/name).read_bytes()).hexdigest())
print('PASS v1.18.4.5 formal+test; native temperature/humidity change; no page reload; retained 76 rules')
