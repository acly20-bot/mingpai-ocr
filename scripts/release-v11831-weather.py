#!/usr/bin/env python3
"""Release weather patch to formal Pages after the existing v1.18.3 promotion.
Keep test-adaptive as the unchanged previous stable version for rollback."""
from pathlib import Path
import hashlib,json,re,subprocess,urllib.request
old='index-B81hyAdU-v1182-test22.js'
new='index-B81hyAdU-v1183-weather-test1.js'
expected='e4ec0addb9e5e3f874cdea2c3c8a247a43e9b9a0ec20b94c8cdb912df2691dfa'
url='https://mingpai-ocr-1387910526.cos.ap-guangzhou.myqcloud.com/assets/'+new
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'mingpai-weather-release/1.18.3.1'}),timeout=50) as r:
    actual=hashlib.sha256(r.read()).hexdigest()
assert actual==expected,('COS object does not match approved build',actual)
root=Path('app')
manifest=root/'version-v118-test.json'
m=json.loads(manifest.read_text(encoding='utf-8'))
assert m['version']=='1.18.3' and m['mainJs']==old and m['rules']=='recognition-rules-v1183.json',m
p=root/'index.html';c=root/'core.html';w=root/'coi-serviceworker.js'
html=p.read_text(encoding='utf-8')
source=Path('stable-wrapper/test-v118-test3.html').read_text(encoding='utf-8')
start='  // V4 weather + per-record environment persistence'
end='  // V6 外部浏览器本地导出'
assert all(x.count(start)==x.count(end)==1 for x in (source,html))
part=source[source.index(start):source.index(end)]
assert all(x in part for x in ('WEATHER_TTL_MS','scheduleEnvironmentResync','numeric(temp)','mingpaiEnvironmentChangedV1183'))
html=html[:html.index(start)]+part+html[html.index(end):]
assert 'const CLIENT_VERSION="1.18.3";' in html
html=html.replace('const CLIENT_VERSION="1.18.3";','const CLIENT_VERSION="1.18.3.1";',1)
html=html.replace('v1.18.3 正式版','v1.18.3.1 正式版')
p.write_text(html,encoding='utf-8')
core=c.read_text(encoding='utf-8')
assert old in core
core=core.replace(old,new).replace('v1.18.3 正式版','v1.18.3.1 正式版')
core=core.replace('mingpai-v1183-formal-coi-reload','mingpai-v11831-weather-formal-coi-reload')
c.write_text(core,encoding='utf-8')
sw=w.read_text(encoding='utf-8')
assert 'const APP_VERSION="1.18.3"' in sw and 'mingpai-shell-v1183-formal' in sw
sw=sw.replace('const APP_VERSION="1.18.3"','const APP_VERSION="1.18.3.1"')
sw=sw.replace('mingpai-shell-v1183-formal','mingpai-shell-v11831-weather-formal')
w.write_text(sw,encoding='utf-8')
m.update(version='1.18.3.1',mainJs=new,runtimeFiles=[new])
manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert new in c.read_text(encoding='utf-8')
assert 'recognition-rules-v1183.json' in c.read_text(encoding='utf-8')
assert json.loads((root/'test-adaptive'/'version-v118-test.json').read_text())['version']=='1.18.3-test'
for label,body in [('page',html),('core',core)]:
    for i,src in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',body,re.I|re.S)):
        if src.strip():
            tmp=Path(f'/tmp/v11831-weather-{label}-{i}.js');tmp.write_text(src,encoding='utf-8')
            subprocess.run(['node','--check',str(tmp)],check=True)
tmp=Path('/tmp/v11831-weather-sw.js');tmp.write_text(sw,encoding='utf-8')
subprocess.run(['node','--check',str(tmp)],check=True)
print('PASS 1.18.3.1 formal; test-adaptive unchanged')
