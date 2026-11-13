#!/usr/bin/env python3
"""Build v1.18.1 candidate, preserving the proven 1.18 runtime and existing COS rules.

Inputs:
  index-B81hyAdU-v118-final-candidate.js from COS
  recognition-rules-v11714-test.json from COS
  scripts/recognition-rules-v1181-additions.json from this repository
Outputs:
  index-B81hyAdU-v1181-candidate.js
  recognition-rules-v1181.json
  mingpai-v1.18.1-candidate-COS.zip
"""
from pathlib import Path
import json, hashlib, subprocess, zipfile, sys

def change_exact(s,old,new,tag):
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f"{tag}: expected 1 match, found {n}")
    return s.replace(old,new,1)

src=Path("index-B81hyAdU-v118-final-candidate.js")
old_rules=Path("recognition-rules-v11714-test.json")
additions=Path("scripts/recognition-rules-v1181-additions.json")
assert src.stat().st_size>10000000
base=json.loads(old_rules.read_text(encoding="utf-8-sig"))
extra=json.loads(additions.read_text(encoding="utf-8-sig"))
assert base.get("schemaVersion")==1 and isinstance(base.get("rules"),list)
assert extra.get("schemaVersion")==1 and len(extra.get("rules",[]))==8
old_ids=[r.get("id") for r in base["rules"]]
new_ids=[r.get("id") for r in extra["rules"]]
assert len(set(new_ids))==8 and not(set(new_ids)&set(old_ids))
# New scoped fixes first; all previously deployed rules remain unchanged.
merged=dict(base)
merged["schemaVersion"]=1
merged["rulesVersion"]="v1.18.1-20261114"
merged["rules"]=extra["rules"]+base["rules"]
merged["supersedes"]="recognition-rules-v11714-test.json"
merged["baseRulesCount"]=len(base["rules"])
outfile=Path("recognition-rules-v1181.json")
outfile.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert merged["rules"][8:]==base["rules"]
print("PASS rules preserve old",len(base["rules"]),"new",len(extra["rules"]),"total",len(merged["rules"]))

s=src.read_text(encoding="utf-8")
old_url='https://mingpai-ocr-1387910526.cos.ap-guangzhou.myqcloud.com/assets/recognition-rules-v11714-test.json'
new_url='https://mingpai-ocr-1387910526.cos.ap-guangzhou.myqcloud.com/assets/recognition-rules-v1181.json'
s=change_exact(s,old_url,new_url,"versioned rules URL")
s=change_exact(s,
 'mingpai-recognition-rules-v11714-test-cache',
 'mingpai-recognition-rules-v1181-cache',"isolated rule cache")
s=change_exact(s,
 'await v1174ApplyExternalRules(N);v1188CorrectNameplate(N);await v1171Dfm100Supplement(i,N,MA,M);',
 'v1188CorrectNameplate(N);await v1174ApplyExternalRules(N);await v1171Dfm100Supplement(i,N,MA,M);',
 "external rules after embedded final correction")
offline='window.addEventListener("offline",()=>{CI(),UA("当前网络已断开。拍照、审核和本机保存仍可继续；恢复网络后会自动尝试补传飞书。")})'
s=change_exact(s,offline,
 'window.addEventListener("offline",()=>{CI(),UAS("当前网络已断开。拍照、审核和本机保存仍可继续；恢复网络后会自动尝试补传飞书。",4500)})',
 "offline timeout")
online='window.addEventListener("online",()=>{CI(),setTimeout(F,800)})'
online_new='window.addEventListener("online",()=>{const e=document.getElementById("v118FloatingProgress");if(e&&/^当前网络已断开/.test(e.textContent||"")){e.textContent="";e.style.display="none"}CI(),setTimeout(F,800)})'
s=change_exact(s,online,online_new,"clear offline banner on reconnect")
s=change_exact(s,
 'UA("网络已恢复，待同步记录自动补传完成。")',
 'UAS("网络已恢复，待同步记录自动补传完成。",4500)',
 "autosync completion timeout")
assert "function v118RetryStatusNoRender(rec)" in s
assert "function v1188CorrectNameplate(rec)" in s
assert "async function enqueueExistingV9(" in s
assert s.count("async function Hg(i,N,U,h=null)")==1
assert old_url not in s
assert "v118PlaceStatus" in s
dst=Path("index-B81hyAdU-v1181-candidate.js")
dst.write_text(s,encoding="utf-8")
subprocess.run(["node","--check",str(dst)],check=True)
print("PASS JS syntax and preserved 326 scroll fix",dst.stat().st_size)

# Exercise real matching/extraction functions and rule priority in JS, including
# an intentionally conflicting embedded field value to verify final JSON wins.
cases=[
 ("SONTU100-RAD(m)\n数字化X射线成像系统",{"name":"医用数字摄影系统（DR）X射线辐射源"}),
 ("7100A\n数字化摄影X射线系统",{"name":"医用数字摄影系统（DR）X射线辐射源"}),
 ("XH40M-I\n数字化车载X射线摄影系统",{"name":"医用数字摄影系统（DR）X射线辐射源"}),
 ("ME7\n深圳迈瑞生物医疗电子股份有限公司",{"manufacturer":"深圳迈瑞生物医疗电子股份有限公司"}),
 ("HITACHI\n数字X射线透视摄影系统\nEXAVISTA\n株式会社日立制作所",{"name":"医用数字摄影系统（DR）X射线辐射源","manufacturer":"株式会社日立制作所","model":"EXAVISTA"}),
 ("数字化透视摄影X射线系统\nDTP573\n产品编码\nDX0302020088916\n50Hz/60Hz",{"name":"医用数字摄影系统（DR）X射线辐射源","model":"DTP573","code":"DX0302020088916"}),
 ("SIEMENS\nSOMATOM Definition AS (128 Slice)",{"model":"SOMATOM Definition AS"}),
 ("ECG-1150\nSN\n54186 P\n上海光电医用电子仪器有限公司上海市奉贤区环城北路567号",{"manufacturer":"上海光电医用电子仪器有限公司","code":"54186 P"}),
]
node=Path("test-v1181-rules.js")
node.write_text("""const assert=require('assert'),fs=require('fs');
const text=fs.readFileSync('index-B81hyAdU-v1181-candidate.js','utf8');
const start=text.indexOf('function v1174RuleMatches('),end=text.indexOf('function v1174RulesStatusHtml()',start);
assert(start>0&&end>start);
const vm=require('vm'),ctx={};
vm.runInNewContext(text.slice(start,end).replace('async function v1174ApplyExternalRules(rec)','async function v1174ApplyExternalRules(rec)'),ctx);
ctx.v1174LoadRules=async()=>JSON.parse(fs.readFileSync('recognition-rules-v1181.json','utf8'));
(async()=>{
 const cases=JSON.parse(fs.readFileSync('test-v1181-cases.json','utf8'));
 for(const [raw,expected] of cases){
   let rec={raw,name:'旧名称',manufacturer:'ENGLISH',model:'4.5kVA',code:'50Hz/60Hz'};
   await ctx.v1174ApplyExternalRules(rec);
   for(const [k,val] of Object.entries(expected))assert.equal(rec[k],val,k+' failed for '+raw.slice(0,40));
 }
 const x={raw:'数字化透视摄影X射线系统\\nDC-DT-3',name:'动态遥控床',code:'50Hz/60Hz'};
 await ctx.v1174ApplyExternalRules(x);assert.equal(x.name,'动态遥控床');
 const y={raw:'数字化透视摄影X射线系统\\nDTP573\\n50Hz/60Hz',code:'50Hz/60Hz'};
 await ctx.v1174ApplyExternalRules(y);assert.equal(y.code,'50Hz/60Hz');
 console.log('PASS eight fixes, DTP negative and final priority');
})().catch(e=>{console.error(e);process.exit(1)});
""",encoding="utf-8")
Path("test-v1181-cases.json").write_text(json.dumps(cases,ensure_ascii=False),encoding="utf-8")
subprocess.run(["node",str(node)],check=True)
for line in ["当前网络已断开","v118FloatingProgress","网络已恢复，待同步记录自动补传完成"]:
 assert line in s
z=Path("mingpai-v1.18.1-candidate-COS.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as f:
 f.write(dst,dst.name)
 f.write(outfile,outfile.name)
 f.writestr("README.txt",
   "v1.18.1 candidate. Upload BOTH files to COS assets/. Do not overwrite v1.18 formal.\n"
   "Main JS: index-B81hyAdU-v1181-candidate.js\n"
   "Rules: recognition-rules-v1181.json\n")
print("PASS artifact",z,z.stat().st_size,"main_sha256",hashlib.sha256(dst.read_bytes()).hexdigest())
