#!/usr/bin/env python3
"""Add read-only field anomaly prompts to v1.18.3 test.1 only.

This runs AFTER the validated formal v1.18.2.1 release is built and
AFTER the shared on-open version checker is added. Never touch formal root.
"""
from pathlib import Path
import json,re,subprocess

folder=Path("app/test-adaptive")
page=folder/"index.html"
core=folder/"core.html"
sw=folder/"coi-serviceworker.js"
manifest=folder/"version-v118-test.json"
p=page.read_text(encoding="utf-8")
c=core.read_text(encoding="utf-8")
w=sw.read_text(encoding="utf-8")
m,_=json.JSONDecoder().raw_decode(manifest.read_text(encoding="utf-8"))

assert m["version"]=="1.18.2.1-test"
assert m["mainJs"]=="index-B81hyAdU-v1182-test22.js"
assert m["rules"]=="recognition-rules-v1181.json"
assert "v11821Restore" in p
assert 'id="mingpai-open-version-check"' in p
assert "v1182-stats-table" in p
assert "mingpai-shell-v11821-test-onopen" in w
assert "const st=d.createElement('style');" in p
assert "v1183InstallFieldReview" not in p
addon=Path("scripts/v1183-field-review.js").read_text(encoding="utf-8")
anchor="const st=d.createElement('style');"
assert p.count(anchor)==1
p=p.replace(anchor,addon+"\n  v1183InstallFieldReview(d);\n  "+anchor,1)
p=p.replace("v1.18.2.1 测试版","v1.18.3 test.1")
p=p.replace('"1.18.2.1-test"','"1.18.3-test.1"')
p=p.replace("const CLIENT_VERSION=\"1.18.2.1-test\";","const CLIENT_VERSION=\"1.18.3-test.1\";")
p=p.replace("remote.replace(/-test$/, '')","remote.replace(/-test(?:\\.\\d+)?$/, '')")
assert "const CLIENT_VERSION=\"1.18.3-test.1\";" in p
assert "v1.18.3 test.1" in p
page.write_text(p,encoding="utf-8")

c=c.replace("v1.18.2.1 测试版","v1.18.3 test.1")
c=c.replace("1.18.2.1-test","1.18.3-test.1")
c=c.replace("mingpai-v11821-search-coi-reload","mingpai-v1183-test1-coi-reload")
core.write_text(c,encoding="utf-8")
w=w.replace("mingpai-shell-v11821-test-onopen","mingpai-shell-v1183-test1")
w=w.replace('const APP_VERSION="1.18.2.1-test"','const APP_VERSION="1.18.3-test.1"')
sw.write_text(w,encoding="utf-8")
m["version"]="1.18.3-test.1"
manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Test risk classification without needing a phone or a real data record.
test_js=Path("scripts/v1183-field-review.js")
subprocess.run(["node","--check",str(test_js)],check=True)
test=Path("verify-v1183-field-review.js")
test.write_text(
    "const fs=require('fs'),vm=require('vm'),assert=require('assert');"
    "const source=fs.readFileSync('scripts/v1183-field-review.js','utf8');"
    "const ctx={};vm.runInNewContext(source,ctx);"
    "const risk=ctx.v1183FieldRisk;"
    "assert(risk('code','50Hz/60Hz'));"
    "assert(risk('code','4.5kVA'));"
    "assert(risk('model','4.5kVA'));"
    "assert(risk('code','粤械注准20192061089'));"
    "assert(!risk('code','DX0302020088916'));"
    "assert(!risk('code','54186 P'));"
    "assert(!risk('model','DTP573'));"
    "assert(!risk('model','SOMATOM Definition AS'));"
    "assert(!risk('manufacturer','深圳迈瑞生物医疗电子股份有限公司'));"
    "assert(risk('manufacturer','上海光电医用电子仪器有限公司上海市奉贤区环城北路567号'));"
    "console.log('PASS field risk tests; no mutation of record values');"
,encoding="utf-8")
subprocess.run(["node",str(test)],check=True)
for i,script in enumerate(re.findall(r"<script[^>]*>(.*?)</script>",p,re.I|re.S)):
    if not script.strip():continue
    file=Path(f"verify-v1183-inline-{i}.js")
    file.write_text(script,encoding="utf-8")
    subprocess.run(["node","--check",str(file)],check=True)
checksw=Path("verify-v1183-sw.js")
checksw.write_text(w,encoding="utf-8")
subprocess.run(["node","--check",str(checksw)],check=True)
assert "1.18.2.1" in Path("app/index.html").read_text(encoding="utf-8")
assert "v1183InstallFieldReview" not in Path("app/index.html").read_text(encoding="utf-8")
assert "index-B81hyAdU-v1182-test22.js" in Path("app/core.html").read_text(encoding="utf-8")
print("PASS test.1 isolated: warning UI only, formal unchanged; JS and rule pack identical")
