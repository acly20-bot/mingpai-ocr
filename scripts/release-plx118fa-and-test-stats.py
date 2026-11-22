#!/usr/bin/env python3
"""v1.18.5 same-version targeted C-arm model rule + test-only stats normalization
and electrical-hint improvement. Formal app behavior remains unchanged.
Input pinned release-baseline/v1185-formal.
"""
from pathlib import Path
import json,re,hashlib,subprocess
root=Path("app");t=root/"test-adaptive"
m=json.loads((root/"version-v118-test.json").read_text())
assert m["version"]=="1.18.5"
assert json.loads((t/"version-v118-test.json").read_text())["version"]=="1.18.5-test.3"
old=(root/"recognition-rules-v1184.json").read_bytes()
assert old==(t/"recognition-rules-v1184.json").read_bytes()
data=json.loads(old)
assert data["rulesVersion"]=="v1.18.4-20261121-r9" and len(data["rules"])==85
rule={
 "id":"user-20261122-perlove-plx118fa-model",
 "priority":15140,
 "match":{"containsAll":["移动式平板C形臂X射线机","PLX118F/a"]},
 "set":{"model":"PLX118F/a"},
 "note":"南京普爱PLX118F/a标签产品型号独立于电源电压~220V/50Hz。只修正型号，不覆盖人工审核信息或出厂编号。"
}
assert all(x["id"]!=rule["id"] for x in data["rules"])
assert all(x["priority"]<rule["priority"] for x in data["rules"])
samples=[
 ("移动式平板C形臂X射线机\n产品型号\nPLX118F/a\n电源电压/频率\n~220V/50Hz",True),
 ("移动式平板C形臂X射线机\nPLX118F/a\n南京普爱医疗设备",True),
 ("移动式平板C形臂X射线机\nPLX118F/b\n~220V/50Hz",False),
 ("无创呼吸机\nPLX118F/a",False)]
for text,yes in samples:
 assert all(s.lower() in text.lower() for s in rule["match"]["containsAll"])==yes
data["rules"].insert(0,rule)
data["rulesVersion"]="v1.18.4-20261122-r10"
data["updatedAt"]="2026-11-22"
data["description"]="85条历史规则加南京普爱C形臂PLX118F/a型号纠偏，保持原有网页版本"
out=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
for site in (root,t):
 (site/"recognition-rules-v1184.json").write_text(out)
 core=site/"core.html";cs=core.read_text()
 assert cs.count("recognition-rules-v1184.json?r=20261121-r9")==1
 cs=cs.replace("recognition-rules-v1184.json?r=20261121-r9","recognition-rules-v1184.json?r=20261122-r10",1)
 assert cs.count("mingpai-recognition-rules-v1184-test-cache-r9")==1
 cs=cs.replace("mingpai-recognition-rules-v1184-test-cache-r9",
               "mingpai-recognition-rules-v1184-test-cache-r10",1)
 core.write_text(cs)
 sw=site/"coi-serviceworker.js";w=sw.read_text()
 cache='const SHELL_CACHE="mingpai-shell-v1185-'+('formal' if site==root else 'test3')+'";'
 # test SW uses its own exact cache; inspect this before writing.
 if site==t:
    cache='const SHELL_CACHE="mingpai-shell-v1185-test3";'
 assert w.count(cache)==1,(site,w[:180])
 w=w.replace(cache,cache[:-2]+'-rules-r10";',1)
 sw.write_text(w)
# Test only: grouping uses normalized names, no IndexedDB writes.
p=t/"index.html";s=p.read_text()
anchor="    const render=()=>{\n      const map=new Map();\n      rows.forEach(r=>{"
assert s.count(anchor)==1
norm=r"""    // Keep stored names untouched; normalize punctuation only for statistics.
    const statsName=v=>String(v||'').trim()
      .replace(/\s*[(（]\s*/g,'（').replace(/\s*[)）]\s*/g,'）')
      .replace(/）\s+(?=[\u4e00-\u9fa5A-Za-z])/g,'）');
"""
s=s.replace(anchor,norm+anchor,1)
oldname="const unit=r.unitName||r.batch||'',dept=r.dept||'',name=r.name||'';if(!name)return;"
newname="const unit=r.unitName||r.batch||'',dept=r.dept||'',name=statsName(r.name);if(!name)return;"
assert s.count(oldname)==1
s=s.replace(oldname,newname,1)
# Test-only electrical risk hint: leading ~ is a common AC voltage marker.
oldwarn="if((field==='code'||field==='model')&&electrical.test(v))"
newwarn="if((field==='code'||field==='model')&&electrical.test(v.replace(/^[~～∼]\\s*/,'')))"
assert s.count(oldwarn)==1
s=s.replace(oldwarn,newwarn,1)
assert "const addedEnvCards=new Set()" in s and "const addedRiskCards=new Set()" in s
assert "pendingConfirmRefreshBound" in s
assert "nativeChange('temperature',temp)" in s
p.write_text(s)
for label,folder in (("formal",root),("test",t)):
 manifest=json.loads((folder/"version-v118-test.json").read_text())
 assert manifest["version"]==("1.18.5" if label=="formal" else "1.18.5-test.3")
 assert len(json.loads((folder/"recognition-rules-v1184.json").read_text())["rules"])==86
 for name in ("index.html","core.html"):
  html=(folder/name).read_text()
  for i,js in enumerate(re.findall(r"<script[^>]*>(.*?)</script>",html,re.I|re.S)):
   if js.strip():
    f=Path("/tmp")/f"plx-r10-{label}-{name}-{i}.js"
    f.write_text(js);subprocess.run(["node","--check",str(f)],check=True)
 f=Path("/tmp")/f"plx-r10-sw-{label}.js"
 f.write_text((folder/"coi-serviceworker.js").read_text())
 subprocess.run(["node","--check",str(f)],check=True)
assert (root/"recognition-rules-v1184.json").read_bytes()==(t/"recognition-rules-v1184.json").read_bytes()
assert "statsName(v)" not in (root/"index.html").read_text() # formal unchanged
for path in ("index.html","test-adaptive/index.html","recognition-rules-v1184.json"):
 print("RELEASE_SHA256",path,hashlib.sha256((root/path).read_bytes()).hexdigest())
print("PASS 86 rules both; test-only stats normalizer and tilde-electrical hint")
