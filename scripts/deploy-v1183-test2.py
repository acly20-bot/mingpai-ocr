#!/usr/bin/env python3
"""Build isolated v1.18.3 test.2 rule pack and phone Back-to-close preview.
Never modify formal root, its manifest, or COS. The huge OCR JS stays unchanged.
"""
from pathlib import Path
import json, re, subprocess, urllib.request
site=Path("app/test-adaptive")
page=site/"index.html"
core=site/"core.html"
sw=site/"coi-serviceworker.js"
manifest=site/"version-v118-test.json"
p=page.read_text(encoding="utf-8")
c=core.read_text(encoding="utf-8")
w=sw.read_text(encoding="utf-8")
m=json.loads(manifest.read_text(encoding="utf-8"))
assert m["version"]=="1.18.3-test.1"
assert m["mainJs"]=="index-B81hyAdU-v1182-test22.js"
assert m["rules"]=="recognition-rules-v1181.json"
assert "v1183InstallFieldReview" in p
assert "v1.18.2.1 正式版" in Path("app/index.html").read_text(encoding="utf-8")
url="https://mingpai-ocr-1387910526.cos.ap-guangzhou.myqcloud.com/assets/recognition-rules-v1181.json"
with urllib.request.urlopen(url,timeout=80) as response:
    base=json.load(response)
assert base["schemaVersion"]==1 and len(base["rules"])==21

DR="医用数字摄影系统（DR）X射线辐射源"
US="医用超声诊断仪（B超）超声源"
entries=[]
def rule(n,all=(),any=(),rx=None,**fields):
    match={}
    if all:match["containsAll"]=list(all)
    if any:match["containsAny"]=list(any)
    if rx:match["regex"]=rx
    assert match and fields
    entries.append({"id":f"v1183-issue-{n:02d}","priority":12000+n,
                    "match":match,"set":fields,"note":f"用户核对样本 #{n:02d}"})
# Exact product markers and adjacent context prevent cross-device contamination.
rule(1,all=["MPC","2201001511"],any=["医用冷藏保存箱","中科都菱"],code="2201001511MPC-5V316(AL)")
rule(2,all=["7100A","数字化摄影X射线系统"],name=DR)
rule(3,all=["XH40M-I","数字化车载X射线摄影系统"],name=DR)
rule(4,all=["ME7","深圳迈瑞生物医疗电子股份有限公司"],manufacturer="深圳迈瑞生物医疗电子股份有限公司")
rule(5,all=["EXAVISTA","数字X射线透视摄影系统"],name=DR,manufacturer="株式会社日立制作所",model="EXAVISTA")
rule(6,all=["DTP573","DX0302020088916","数字化透视摄影X射线系统"],name=DR,code="DX0302020088916")
rule(7,all=["SOMATOM Definition AS","SIEMENS"],model="SOMATOM Definition AS")
rule(8,all=["ECG-1150","54186 P"],manufacturer="上海光电医用电子仪器有限公司",code="54186 P")
rule(9,all=["X射线","SONTU100-RAD(m)"],name=DR)
rule(10,all=["ME7","JH6-44001343"],manufacturer="深圳迈瑞生物医疗电子股份有限公司")
rule(11,all=["iMAC 100","武汉中旗"],name="数字心电图机",manufacturer="武汉中旗生物医疗电子有限公司")
rule(12,all=["BBS-V800","BIOBASE"],manufacturer="济南鑫贝西生物技术有限公司",code="BBS8V1711393D")
rule(13,all=["Planmeca ProMax 3D","Planmeca Oy"],manufacturer="Planmeca Oy")
rule(14,all=["MECG-300","北京麦迪克斯"],name="数字心电图机",manufacturer="北京麦迪克斯科技有限公司")
rule(15,all=["EXTEND XT","Air liquide"],manufacturer="液化空气医疗系统公司")
rule(16,all=["M8105A","Boeblingen"],manufacturer="Philips Medizin Systeme Boeblingen GmbH")
rule(17,all=["型号：1379","赛默飞世尔"],manufacturer="赛默飞世尔（苏州）仪器有限公司")
rule(18,all=["LC-630","200108571110200090","浙江华美"],code="200108571110200090")
rule(19,all=["840","Puritan-Bennett Corporation"],model="PURITAN BENNETT 840",manufacturer="Puritan-Bennett Corporation")
rule(20,all=["840","Covidien"],model="PURITAN BENNETT 840")
rule(21,all=["Uni-Vision","61Z757"],name=DR,code="61Z757")
rule(22,all=["Voluson E10","E79990"],model="Voluson E10")
rule(23,all=["TCI-IV","桂76-D-11091322"],name="单通道注射泵",manufacturer="广西威利方舟科技有限公司",model="TCI-IV",code="W桂76-D-11091322")
rule(24,all=["Eppendorf AG","5424FP872181"],name="医用离心机",manufacturer="Eppendorf AG",model="5424",code="5424FP872181")
rule(25,all=["TUS-A300","N511843213"],name=US,model="APLIO 300 TUS-A300",code="N511843213")
rule(26,all=["CP-2200","北京思路高"],name="双通道注射泵",manufacturer="北京思路高医疗科技有限公司")
rule(27,all=["VINNO","U0252GY005"],name=US,model="VINNO G86")
rule(28,all=["KC170402032G","科曼"],name="多参数监护仪",model="C60")
rule(29,all=["ESCO","AC2-4S1"],name="生物安全柜",manufacturer="ESCO")
# Extra explicit single-device match for the user-confirmed original sample:
rule(30,all=["数字胃肠X射线系统","RF0720C00002"],name="医用诊断X射线辐射源（胃肠机）",model="7600",code="RF0720C00002")
rule(31,all=["DW-25L262","HRB8X"],code="BE02Q 900N0 0QEH4 HRB8X")
rule(32,all=["HYC-650","8QFUG"],code="BE03L L00N0 0QJN8 8QFUG")
rule(33,all=["YC-1006","28BG"],code="55A0 6973 9009 28BG 0112")
rule(34,all=["ALOKA ARIETTA 850","株式会社日立制作所"],name=US,manufacturer="株式会社日立制作所")
rule(35,all=["K5210222049","科曼"],name="多参数监护仪",manufacturer="深圳市科曼医疗设备有限公司")
rule(36,all=["Aelite NXT","SPD22210116WA"],name="麻醉机（呼吸部分）")
# User original OCR may omit spaces/newlines in serials; add narrowly scoped corrective patterns.
rule(37,all=["LC-630","华美"],rx="200108571110200090",code="200108571110200090")
rule(38,all=["医用冷藏箱","HYC-650","8QFUG"],rx="BE03L",code="BE03L L00N0 0QJN8 8QFUG")
rule(39,all=["DW-25L262","Serial Number","HRB8X"],rx="BE0[2OQ0]",code="BE02Q 900N0 0QEH4 HRB8X")
rule(40,all=["医用注射泵","CP-2200型"],manufacturer="北京思路高医疗科技有限公司")
rule(41,all=["数字化彩色超声诊断仪","飞依诺科技"],name=US,model="VINNO G86")
rule(42,all=["多道心电图机","54186 P"],name="数字心电图机",code="54186 P")
rule(43,all=["数字医用诊断X射线透视摄影系统","61Z757"],name=DR,code="61Z757")
rule(44,all=["Air liquide Medical Systems S.A.","EXTEND XT"],name="呼吸机",manufacturer="液化空气医疗系统公司")
rule(45,all=["840","PURITAN BENNETT"],rx="Ventilator System",name="呼吸机",model="PURITAN BENNETT 840")
rule(46,all=["BBS-V800","BBS8V1711393D"],manufacturer="济南鑫贝西生物技术有限公司",code="BBS8V1711393D")
rule(47,all=["SN99B1845761","N511843213"],code="N511843213")
# Strong product identification when the long serial is present.
rule(48,all=["2201001511MPC-5V316(AL)","医用冷藏保存箱"],code="2201001511MPC-5V316(AL)")

ids=[r["id"] for r in entries]
assert len(ids)==len(set(ids))
pack={**base,"rulesVersion":"v1.18.3-test.2-20261118","updatedAt":"2026-11-18",
      "description":"v1.18.1 验证规则21条 + v1.18.3 独立样本纠偏；仅供隔离测试版",
      "supersedes":"recognition-rules-v1181.json","rules":entries+base["rules"]}
assert len(pack["rules"])==len(entries)+21
(site/"recognition-rules-v1183-test2.json").write_text(json.dumps(pack,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# The existing OCR runtime fetches a hardcoded COS URL. Redirect ONLY in
# test iframe, before loading module code. Segregate fallback cache key too.
hook=r"""<script id="v1183-test2-rule-redirect">
(()=>{
  'use strict';
  const originalFetch=window.fetch.bind(window);
  const oldUrl='https://mingpai-ocr-1387910526.cos.ap-guangzhou.myqcloud.com/assets/recognition-rules-v1181.json';
  window.fetch=(input,init)=>{
    const url=typeof input==='string'?input:(input&&input.url)||'';
    if(url===oldUrl||url.startsWith(oldUrl+'?')){
      return originalFetch(new URL('./recognition-rules-v1183-test2.json',location.href).href,{...init,cache:'no-cache'});
    }
    return originalFetch(input,init);
  };
  const oldKey='mingpai-recognition-rules-v1181-cache';
  const newKey='mingpai-recognition-rules-v1183-test2-cache';
  const realGet=Storage.prototype.getItem,realSet=Storage.prototype.setItem;
  Storage.prototype.getItem=function(k){return realGet.call(this,k===oldKey?newKey:k);};
  Storage.prototype.setItem=function(k,v){return realSet.call(this,k===oldKey?newKey:k,v);};
})();
</script>
"""
assert "<head>" in c and "v1183-test2-rule-redirect" not in c
c=c.replace("<head>","<head>\n"+hook,1)
c=c.replace("v1.18.3 test.1","v1.18.3 test.2").replace("1.18.3-test.1","1.18.3-test.2")
c=c.replace("mingpai-v1183-test1-coi-reload","mingpai-v1183-test2-coi-reload")
core.write_text(c,encoding="utf-8")

# Top-level history entries handle Android Back inside the iframe reliably.
# No global Back interception when preview is closed.
back_script=Path("scripts/v1183-preview-back.js").read_text(encoding="utf-8")
assert "</body>" in p and "v1183PreviewBackInit" not in p
p=p.replace("</body>","<script>\n"+back_script+"\n</script>\n</body>",1)
p=p.replace("v1.18.3 test.1","v1.18.3 test.2").replace("1.18.3-test.1","1.18.3-test.2")
p=p.replace("const CLIENT_VERSION=\"1.18.3-test.1\";","const CLIENT_VERSION=\"1.18.3-test.2\";")
page.write_text(p,encoding="utf-8")

w=w.replace("mingpai-shell-v1183-test1","mingpai-shell-v1183-test2")
w=w.replace('const APP_VERSION="1.18.3-test.1"','const APP_VERSION="1.18.3-test.2"')
sw.write_text(w,encoding="utf-8")
m["version"]="1.18.3-test.2"
m["rules"]="recognition-rules-v1183-test2.json"
manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Static proof of isolation, external rule integrity, basic matching.
assert 'index-B81hyAdU-v1182-test22.js' in c
assert "recognition-rules-v1183-test2.json" in c
assert "1.18.3-test.2" in p
assert "v1.18.2.1 正式版" in Path("app/index.html").read_text(encoding="utf-8")
assert "v1183-test2-rule-redirect" not in Path("app/core.html").read_text(encoding="utf-8")
assert "v1183PreviewBackInit" not in Path("app/index.html").read_text(encoding="utf-8")
subprocess.run(["node","--check","scripts/v1183-preview-back.js"],check=True)
for i,s in enumerate(re.findall(r"<script[^>]*>(.*?)</script>",p,re.I|re.S)):
    if s.strip():
        f=Path(f"/tmp/v1183-test2-wrapper-{i}.js")
        f.write_text(s,encoding="utf-8")
        subprocess.run(["node","--check",str(f)],check=True)
for i,s in enumerate(re.findall(r"<script[^>]*>(.*?)</script>",c,re.I|re.S)):
    if s.strip():
        f=Path(f"/tmp/v1183-test2-core-{i}.js")
        f.write_text(s,encoding="utf-8")
        subprocess.run(["node","--check",str(f)],check=True)
assert len([x for x in pack["rules"] if x["id"].startswith("v1183-issue-")])>=29
def match(r,txt):
    m=r["match"];up=txt.upper()
    return (all(x.upper() in up for x in m.get("containsAll",[]))
         and (not m.get("containsAny") or any(x.upper() in up for x in m["containsAny"]))
         and (not m.get("regex") or re.search(m["regex"],txt,re.I)))
cases=[
  ("Uni-Vision No. 61Z757 MODEL ZUD-L40D","code","61Z757"),
  ("Voluson E10 SN E79990","model","Voluson E10"),
  ("Eppendorf AG Serial no.: 5424FP872181","name","医用离心机"),
  ("ESCO Model: AC2-4S1","name","生物安全柜"),
  ("iMAC 100 武汉中旗生物医疗电子有限公司","name","数字心电图机"),
  ("COMEN 科曼 SN KC170402032G","model","C60"),
  ("医用冷藏保存箱 2201001511MPC-5V316(AL)","code","2201001511MPC-5V316(AL)"),
  ("VINNO U0252GY005","model","VINNO G86")
]
for raw,field,expected in cases:
    found=next((r for r in sorted(pack["rules"],key=lambda r:-r.get("priority",0)) if match(r,raw)),None)
    assert found and found.get("set",{}).get(field)==expected,(raw,field,found)
print("PASS v1.18.3 test.2: test-only rules",len(pack["rules"]),"case smoke",len(cases),"modal Back script syntax, formal unchanged")
