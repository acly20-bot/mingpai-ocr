#!/usr/bin/env python3
"""Promote approved mobile-dock test fix to formal without a version bump.
Run after fix-mobile-dock-after-camera-test.py on pinned v1.18.4.5 baseline.
Formal uses exactly the verified test UI with formal-only labels/cache scope.
"""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path('app'); test=root/'test-adaptive'
fm=json.loads((root/'version-v118-test.json').read_text(encoding='utf-8'))
tm=json.loads((test/'version-v118-test.json').read_text(encoding='utf-8'))
assert fm['version']=='1.18.4.5' and tm['version']=='1.18.4.5-test'
assert fm['rules']==tm['rules']=='recognition-rules-v1184.json'
assert fm['mainJs']==tm['mainJs']=='index-B81hyAdU-v11832-viewport-test2.js'
old=(root/'index.html').read_text(encoding='utf-8')
tested=(test/'index.html').read_text(encoding='utf-8')
assert "dockModalSelectors='#cropModal,#v155ImagePreview" in tested
assert "attributeFilter:['hidden','style','class','aria-hidden']" in tested
assert 'modalOpen?' not in tested[tested.index('const v118ModalDockGuard=()=>{'):tested.index('const dockModalSelectors=')]
assert 'const CLIENT_VERSION="1.18.4.5";' in old
assert 'const CLIENT_VERSION="1.18.4.5-test";' in tested
formal=tested.replace('const CLIENT_VERSION="1.18.4.5-test";','const CLIENT_VERSION="1.18.4.5";',1)
formal=formal.replace('v1.18.4.5 测试版','v1.18.4.5 正式版')
# Verify the page differs from approved test only by formal version labels.
assert formal.count('const CLIENT_VERSION="1.18.4.5";')==1
assert "nativeChange('temperature',temp)" in formal and "nativeChange('humidity',hum)" in formal
assert 'view?.location?.reload()' not in formal
(root/'index.html').write_text(formal,encoding='utf-8')
# Test's only SW change was internal cache namespace; use separate formal namespace.
sw=(root/'coi-serviceworker.js')
s=sw.read_text(encoding='utf-8')
assert 'const APP_VERSION="1.18.4.5";' in s
assert 'const SHELL_CACHE="mingpai-shell-v11845-formal";' in s
s=s.replace('const SHELL_CACHE="mingpai-shell-v11845-formal";',
            'const SHELL_CACHE="mingpai-shell-v11845-dockfix-formal";',1)
sw.write_text(s,encoding='utf-8')
# Keep formal/test manifests and cores unchanged, preserve original OCR rule bytes.
assert 'v1.18.4.5 正式版' in (root/'core.html').read_text(encoding='utf-8')
assert 'v1.18.4.5 测试版' in (test/'core.html').read_text(encoding='utf-8')
assert (root/'recognition-rules-v1184.json').read_bytes()==(test/'recognition-rules-v1184.json').read_bytes()
for label in ['', 'test-adaptive/']:
  page=root/label
  for name in ['index.html','core.html']:
    text=(page/name).read_text(encoding='utf-8')
    for i,script in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',text,re.I|re.S)):
      if script.strip():
        f=Path('/tmp')/('dockrelease-'+label.replace('/','-')+name+str(i)+'.js')
        f.write_text(script,encoding='utf-8')
        subprocess.run(['node','--check',str(f)],check=True)
  f=Path('/tmp')/('dockrelease-'+label.replace('/','-')+'sw.js')
  f.write_text((page/'coi-serviceworker.js').read_text(encoding='utf-8'),encoding='utf-8')
  subprocess.run(['node','--check',str(f)],check=True)
for name in ['index.html','test-adaptive/index.html','recognition-rules-v1184.json']:
  print('RELEASE_SHA256',name,hashlib.sha256((root/name).read_bytes()).hexdigest())
print('PASS dock bugfix promotion, formal and test v1.18.4.5 unchanged version')
