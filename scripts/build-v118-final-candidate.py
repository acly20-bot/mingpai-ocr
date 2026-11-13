#!/usr/bin/env python3
"""Build v1.18 candidate from validated COS test326 runtime; preserve all runtime behavior."""
from pathlib import Path
import subprocess,zipfile,hashlib,sys
src=Path(sys.argv[1] if len(sys.argv)>1 else "index-B81hyAdU-v118-test326.js")
dst=Path("index-B81hyAdU-v118-final-candidate.js")
s=src.read_text(encoding="utf-8")
needle="await v1174ApplyExternalRules(N);await v1171Dfm100Supplement(i,N,MA,M);"
replacement="await v1174ApplyExternalRules(N);v1188CorrectNameplate(N);await v1171Dfm100Supplement(i,N,MA,M);"
assert s.count(needle)==1,("pipeline insertion",s.count(needle))
assert s.count("async function Hg(i,N,U,h=null)")==1
assert "function v118RetryStatusNoRender(rec)" in s, "326 WeChat fix missing"
assert "function v1188CorrectNameplate(" not in s
helper=r"""
// v1.18: eight narrowly scoped nameplate recognition fixes; run after external rules.
function v1188CorrectNameplate(rec){
 if(!rec)return rec;
 const raw=String(rec.raw||"");
 if(!raw.trim())return rec;
 const DR="医用数字摄影系统（DR）X射线辐射源",hits=[];
 const assign=(key,val)=>{if(val&&rec[key]!==val){rec[key]=val;return true}return false};
 const mark=(label,changed)=>{if(changed)hits.push(label)};
 if(/SONTU\s*100\s*[-–]\s*RAD\s*\(?m\)?/i.test(raw)&&/数字化\s*X\s*射线成像系统/i.test(raw))mark("SONTU100 DR标准名称",assign("name",DR));
 if(/\b7100A\b/i.test(raw)&&/数字化摄影\s*X\s*射线系统/i.test(raw))mark("7100A DR标准名称",assign("name",DR));
 if(/XH40M\s*[-–]\s*I\b/i.test(raw)&&/数字化车载\s*X\s*射线摄影系统/i.test(raw))mark("XH40M-I DR标准名称",assign("name",DR));
 if(/\bME7\b/i.test(raw)&&/深圳迈瑞生物医疗电子股份有限公司/.test(raw))mark("ME7中文厂家优先",assign("manufacturer","深圳迈瑞生物医疗电子股份有限公司"));
 if(/\bEXAVISTA\b/i.test(raw)&&/(?:HITACHI|株式会社日立制作所)/i.test(raw)&&/数字\s*X\s*射线透视摄影系统/i.test(raw)){
  let changed=assign("name",DR);
  changed=assign("manufacturer","株式会社日立制作所")||changed;
  changed=assign("model","EXAVISTA")||changed;
  mark("EXAVISTA三字段纠偏",changed);
 }
 if(/\bDTP\s*573\b/i.test(raw)&&/数字化透视摄影\s*X\s*射线系统/i.test(raw)){
  let changed=assign("name",DR);
  changed=assign("model","DTP573")||changed;
  mark("DTP573主机优先",changed);
 }
 if(/\bSOMATOM\s+Definition\s+AS\b/i.test(raw)&&/(?:SIEMENS|西门子|128\s*(?:Slice|层))/i.test(raw))mark("Definition AS型号",assign("model","SOMATOM Definition AS"));
 if(/\bECG\s*[-–]\s*1150\b/i.test(raw)&&/上海光电医用电子仪器有限公司/.test(raw)){
  let changed=assign("manufacturer","上海光电医用电子仪器有限公司");
  const sn=raw.match(/(?:^|[\r\n])\s*SN\s*[:：]?\s*(\d{4,7}\s*[A-Z])(?=\s|$)/im);
  if(sn)changed=assign("code",sn[1].replace(/\s+/g," ").trim().toUpperCase())||changed;
  mark("ECG-1150厂家与SN",changed);
 }
 if(hits.length)rec.classifyNote=(rec.classifyNote?rec.classifyNote+" + ":"")+hits.join(" + ");
 return rec;
}
"""
s=s.replace(needle,replacement,1)
s=s.replace("async function Hg(i,N,U,h=null)",helper+"\nasync function Hg(i,N,U,h=null)",1)
assert s.count("function v1188CorrectNameplate(")==1
dst.write_text(s,encoding="utf-8")
subprocess.run(["node","--check",str(dst)],check=True)
print("PASS syntax",dst.name,"bytes",dst.stat().st_size)
# Check eight cases by running only extracted helper with Node VM, no DOM.
import json
cases=[
("SONTU100-RAD(m)\n数字化X射线成像系统",{"name":"医用数字摄影系统（DR）X射线辐射源"}),
("7100A\n数字化摄影X射线系统",{"name":"医用数字摄影系统（DR）X射线辐射源"}),
("XH40M-I\n数字化车载X射线摄影系统",{"name":"医用数字摄影系统（DR）X射线辐射源"}),
("ME7\n深圳迈瑞生物医疗电子股份有限公司",{"manufacturer":"深圳迈瑞生物医疗电子股份有限公司"}),
("HITACHI\n数字X射线透视摄影系统\nEXAVISTA\n株式会社日立制作所",{"name":"医用数字摄影系统（DR）X射线辐射源","manufacturer":"株式会社日立制作所","model":"EXAVISTA"}),
("数字化透视摄影X射线系统\nDTP573\n动态遥控床 DC-DT-3",{"name":"医用数字摄影系统（DR）X射线辐射源","model":"DTP573"}),
("SIEMENS\nSOMATOM Definition AS (128 Slice)",{"model":"SOMATOM Definition AS"}),
("ECG-1150\nSN\n54186 P\n上海光电医用电子仪器有限公司上海市奉贤区环城北路567号\nECG-1150P",{"manufacturer":"上海光电医用电子仪器有限公司","code":"54186 P"}),
]
test_js="const vm=require('vm'),fs=require('fs'),assert=require('assert');let s=fs.readFileSync(process.argv[2],'utf8');let start=s.indexOf('function v1188CorrectNameplate('),end=s.indexOf('async function Hg(i,N,U,h=null)',start);assert(start>0&&end>start);let ctx={};vm.runInNewContext(s.slice(start,end),ctx);let cases="+json.dumps(cases,ensure_ascii=False)+";for(let [raw,expected] of cases){let rec={raw,name:'未识别设备名称',model:'4.5kVA',manufacturer:'ENGLISH NAME',code:'ECG-1150P'};ctx.v1188CorrectNameplate(rec);for(let k of Object.keys(expected))assert.equal(rec[k],expected[k]);}let unrelated={raw:'动态遥控床 DC-DT-3',name:'动态遥控床'};ctx.v1188CorrectNameplate(unrelated);assert.equal(unrelated.name,'动态遥控床');console.log('PASS eight cases and unrelated-device negative test');"
test=Path("test-v118-eight.js")
test.write_text(test_js,encoding="utf-8")
subprocess.run(["node",str(test),str(dst)],check=True)
with zipfile.ZipFile("mingpai-v1.18-final-candidate-COS.zip","w",zipfile.ZIP_DEFLATED) as z:
 z.write(dst,dst.name)
 z.writestr("README.txt","v1.18 final candidate; upload JS to COS assets/ after user approval; do not overwrite v1.17 stable.\n")
print("PASS zip",hashlib.sha256(dst.read_bytes()).hexdigest())
