#!/usr/bin/env python3
"""Independent rules release (8 cases) to formal and test, visible app version unchanged.
Input app/ is exact release-baseline/v11845-pending-confirm Pages artifact.
Only recognition JSON, rules URL cache revision, and SW shell namespace changed.
"""
from pathlib import Path
import json,re,hashlib,subprocess
root=Path("app")
folders=[root,root/"test-adaptive"]
original=(root/"recognition-rules-v1184.json").read_bytes()
data=json.loads(original)
assert len(data["rules"])==76 and data["schemaVersion"]==1
assert original==(root/"test-adaptive/recognition-rules-v1184.json").read_bytes()
assert json.loads((root/"version-v118-test.json").read_text())["version"]=="1.18.4.5"
assert json.loads((root/"test-adaptive/version-v118-test.json").read_text())["version"]=="1.18.4.5-test"
def rule(key,terms,fields,note):
    return {"id":"user-20261121-"+key,
        "priority":15000+len(newrules)+1,
        "match":{"containsAll":terms},
        "set":fields,"note":note}
newrules=[]
newrules.append(rule("kuanteng-raynova",["KUANTENG","RayNova","DRvs"],
    {"name":"医用数字摄影系统（DR）X射线辐射源","model":"RayNova DRvs"},
    "宽腾车载数字X射线摄影系统，修复型号被2.5kVA替代"))
newrules.append(rule("planmeca-prox-code",["Planmeca ProX","IPX016891"],
    {"code":"IPX016891"},"口腔内成像X射线机序列号，避免注册证号"))
newrules.append(rule("nidek-nt530-code",["NT-530","250614"],
    {"code":"250614"},"NIDEK NT-530: No. 250614 是出厂编号，不是印刷料号"))
newrules.append(rule("philips-duradiagnost-code",["DuraDiagnost 50DP","190055"],
    {"code":"190055"},"DuraDiagnost 50DP 出厂编号190055，排除100kVA输入功率"))
newrules.append(rule("mammography-dm158",["数字化医用X射线乳腺摄影系统","DM158"],
    {"name":"医用乳腺X射线辐射源"},"安健DM158乳腺摄影的标准设备名称"))
newrules.append(rule("hitachi-eclos16",["ECLOS 16","日立医疗器械"],
    {"model":"ECLOS 16","manufacturer":"株式会社日立医疗器械"},
    "日立ECLOS16不把(SFDA)前缀并入型号，生产厂家不取注册号"))
newrules.append(rule("mindray-benevision-n15or",["BeneVision N15 OR"],
    {"model":"BeneVision N15 OR"},"适用于同型号病人监护仪，型号不取F7序列号"))
newrules.append(rule("pigeon-cpap-ad3",["小儿CPAP持续气道正压通气系统","201261"],
    {"model":"AD-III"},"鸽子小儿CPAP型号AD-III，排除产品编号201261I1012"))
assert len(newrules)==8 and len(set(x["id"] for x in newrules))==8
assert not ({x["id"] for x in newrules}&{x["id"] for x in data["rules"]})
def matches(rec,text):
    m=rec["match"];up=text.upper()
    return all(str(word).upper() in up for word in m["containsAll"])
positives=[
    ("KUANTENG\n称：数字化车载X射线机\n型\n号：RayNova\na DRvs\n率：2.5kVA","kuanteng-raynova"),
    ("口腔内成像X射线机\n规格型号:Planmeca ProX\n序列号：\nIPX016891","planmeca-prox-code"),
    ("NIDEK\n型号:NT-530\nNo.250614\n18537-M806-CO","nidek-nt530-code"),
    ("PHILIPS\n产品型号：DuraDiagnost 50DP\n编号：190055\n100kVA","philips-duradiagnost-code"),
    ("数字化医用X射线乳腺摄影系统\n产品型号\nDM158\nDX0112017125253","mammography-dm158"),
    ("X射线计算机断层摄影设备\nECLOS 16\n规格型号(SFDA):ECLOS 16\n株式会社日立医疗器械\nKA13068401","hitachi-eclos16"),
    ("BeneVision N15 OR\nSN F7-16002403\n病人监护仪","mindray-benevision-n15or"),
    ("小儿CPAP持续气道正压通气系统\n规格型号:AD-II]\n产品编号201261I1012","pigeon-cpap-ad3")]
for sample,key in positives:
    hits=[r for r in newrules if matches(r,sample)]
    assert [r["id"] for r in hits]==["user-20261121-"+key],(key,hits)
negatives=[
    "KUANTENG another model 2.5kVA",
    "Planmeca ProX serial IPX017000",
    "NIDEK NT-530 No.251022",
    "DuraDiagnost 50DP no serial visible",
    "数字化医用X射线乳腺摄影系统 DM180",
    "ECLOS 16 without manufacturer OCR",
    "BeneVision N12 OR",
    "小儿CPAP持续气道正压通气系统 产品编号2012677777"]
for i,raw in enumerate(negatives):
    assert not matches(newrules[i],raw),(i,raw)
# Verify the highest-priority rule sets the intended field in every positive.
for sample,key in positives:
    hit=[r for r in sorted(newrules+data["rules"],key=lambda x:-x.get("priority",0)) if matches(r,sample)]
    assert hit[0]["id"]=="user-20261121-"+key
data["rules"]=newrules+data["rules"]
data["rulesVersion"]="v1.18.4-20261121-r8"
data["updatedAt"]="2026-11-21"
data["description"]="沿用v1.18.4.5的76条已验证规则，独立新增2026-11-21的8条设备识别纠偏规则；网页版本不变"
out=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
assert len(data["rules"])==84
rev="?r=20261121-r8"
for folder in folders:
    (folder/"recognition-rules-v1184.json").write_text(out,encoding="utf-8")
    core=folder/"core.html"
    html=core.read_text(encoding="utf-8")
    needle="new URL('./recognition-rules-v1184.json',location.href)"
    assert html.count(needle)==1,(folder,"missing redirect")
    html=html.replace(needle,"new URL('./recognition-rules-v1184.json"+rev+"',location.href)",1)
    core.write_text(html,encoding="utf-8")
    sw=folder/"coi-serviceworker.js";src=sw.read_text(encoding="utf-8")
    old='const SHELL_CACHE="mingpai-shell-v11845-pending-refresh-'+('formal' if folder==root else 'test')+'";'
    assert src.count(old)==1,(folder,src[:170])
    src=src.replace(old,'const SHELL_CACHE="mingpai-shell-v11845-rules-r8-'+('formal' if folder==root else 'test')+'";',1)
    sw.write_text(src,encoding="utf-8")
for folder in folders:
    manifest=json.loads((folder/"version-v118-test.json").read_text())
    assert manifest["version"]==("1.18.4.5" if folder==root else "1.18.4.5-test")
    assert manifest["rules"]=="recognition-rules-v1184.json"
    assert json.loads((folder/"recognition-rules-v1184.json").read_text())["rulesVersion"]==data["rulesVersion"]
    for name in ["core.html"]:
        s=(folder/name).read_text(encoding="utf-8")
        for i,js in enumerate(re.findall(r"<script[^>]*>(.*?)</script>",s,re.I|re.S)):
            if js.strip():
                path=Path("/tmp")/f"rule-r8-{folder.name}-{i}.js";path.write_text(js,encoding="utf-8")
                subprocess.run(["node","--check",str(path)],check=True)
    path=Path("/tmp")/f"rule-r8-sw-{folder.name}.js"
    path.write_text((folder/"coi-serviceworker.js").read_text())
    subprocess.run(["node","--check",str(path)],check=True)
assert (root/"recognition-rules-v1184.json").read_bytes()==(root/"test-adaptive/recognition-rules-v1184.json").read_bytes()
print("PASS 8 precise new rules; 84 total; positive/negative fixtures; same app versions")
print("RULE_SHA256",hashlib.sha256(out.encode()).hexdigest())
