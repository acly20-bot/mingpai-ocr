#!/usr/bin/env python3
"""Same-version recognition rule r9 for Pigeon infant CPAP serial number.
Release to both formal and test without changing the 1.18.4.5 application.
Base: release-baseline/v11845-bootdiag-test, already deployed and contains 84 rules.
"""
from pathlib import Path
import json,hashlib,re,subprocess
root=Path("app"); sites=[root,root/"test-adaptive"]
original=(root/"recognition-rules-v1184.json").read_bytes()
assert original==(root/"test-adaptive/recognition-rules-v1184.json").read_bytes()
rules=json.loads(original)
assert len(rules["rules"])==84
assert rules["rulesVersion"]=="v1.18.4-20261121-r8"
assert not any(r["id"]=="user-20261121-pigeon-cpap-serial-iii" for r in rules["rules"])
new={
    "id":"user-20261121-pigeon-cpap-serial-iii",
    "priority":15120,
    "match":{
        "containsAll":["小儿CPAP持续气道正压通气系统"],
        "containsAny":["20126III012","20126111012"]
    },
    "set":{"code":"20126III012","model":"AD-III"},
    "note":"现场铭牌核实：产品编号20126III012，中间为三个字母I。兼容OCR误读为20126111012；不误用注册证号。型号AD-III。"
}
def matches(rule,text):
    m=rule["match"];up=text.upper()
    return (all(x.upper() in up for x in m["containsAll"])
       and any(x.upper() in up for x in m["containsAny"]))
samples=[
 ("小儿CPAP持续气道正压通气系统\n规格型号\n20126III012\n产品编号\n广东鸽子医疗器械有限公司",True),
 ("小儿CPAP持续气道正压通气系统\n规格垫号AD-IIT\n产品编号\n20126111012",True),
 ("其他设备\n20126111012",False),
 ("小儿CPAP持续气道正压通气系统\n产品编号20126999012",False),
 ("小儿CPAP持续气道正压通气系统\n粤械注准20192081009",False),
 ("小儿CPAP持续气道正压通气系统\n产品编号20126III012X",True)]
for sample,expected in samples:
    assert matches(new,sample)==expected,(sample,expected)
assert all(r["priority"]<new["priority"] for r in rules["rules"])
rules["rules"].insert(0,new)
rules["rulesVersion"]="v1.18.4-20261121-r9"
rules["description"]="原84条规则基础上新增小儿CPAP产品编号字母I与数字1的纠偏；网页版本不变"
rules["updatedAt"]="2026-11-21"
out=json.dumps(rules,ensure_ascii=False,indent=2)+"\n"
for folder in sites:
    f=folder/"recognition-rules-v1184.json"
    f.write_text(out,encoding="utf-8")
    core=folder/"core.html"
    content=core.read_text(encoding="utf-8")
    prev="recognition-rules-v1184.json?r=20261121-r8"
    assert content.count(prev)==1
    content=content.replace(prev,"recognition-rules-v1184.json?r=20261121-r9",1)
    # Rotate only this versioned rule-storage key to guarantee existing
    # users do not reuse old JSON from localStorage after cache bust.
    prevKey="mingpai-recognition-rules-v1184-test-cache"
    assert content.count(prevKey)==1
    content=content.replace(prevKey,prevKey+"-r9",1)
    core.write_text(content,encoding="utf-8")
    sw=folder/"coi-serviceworker.js"
    text=sw.read_text(encoding="utf-8")
    old_cache=(
       "mingpai-shell-v11845-rules-r8-formal" if folder==root
       else "mingpai-shell-v11845-bootdiag-test")
    assert text.count(old_cache)==1,(folder,text[:170])
    text=text.replace(old_cache,old_cache+"-r9",1)
    sw.write_text(text,encoding="utf-8")
    version=json.loads((folder/"version-v118-test.json").read_text())
    assert version["version"]==("1.18.4.5" if folder==root else "1.18.4.5-test")
    assert version["rules"]=="recognition-rules-v1184.json"
    for name in ["core.html"]:
        html=(folder/name).read_text(encoding="utf-8")
        for i,js in enumerate(re.findall(r"<script[^>]*>(.*?)</script>",html,re.I|re.S)):
            if js.strip():
                p=Path("/tmp")/f"pigeon-r9-{folder.name}-{i}.js";p.write_text(js)
                subprocess.run(["node","--check",str(p)],check=True)
    p=Path("/tmp")/f"pigeon-r9-sw-{folder.name}.js"
    p.write_text(sw.read_text(encoding="utf-8"))
    subprocess.run(["node","--check",str(p)],check=True)
assert (root/"recognition-rules-v1184.json").read_bytes()==(root/"test-adaptive/recognition-rules-v1184.json").read_bytes()
assert len(json.loads((root/"recognition-rules-v1184.json").read_text())["rules"])==85
for path in ("index.html","test-adaptive/index.html","recognition-rules-v1184.json"):
    print("RELEASE_SHA256",path,hashlib.sha256((root/path).read_bytes()).hexdigest())
print("PASS: 85 rules, precise CPAP code 20126III012, both sites, same app versions, existing UI intact")
