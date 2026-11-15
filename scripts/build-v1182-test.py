#!/usr/bin/env python3
"""v1.18.2 test.1: narrow sync recovery; UI stats/observers/startup diagnostics; resource audit."""
from pathlib import Path
import subprocess,zipfile,json,re,hashlib
source=Path("index-B81hyAdU-v1181-candidate.js").read_text(encoding="utf-8")
wrapper=Path("stable-wrapper/test-v118-test3.html").read_text(encoding="utf-8")
def patch(s,old,new,label):
 n=s.count(old)
 if n!=1:raise ValueError(f"{label}: expected one source anchor, found {n}")
 print("PASS",label)
 return s.replace(old,new,1)

# Missing Feishu record is the only case that may be retried as a new sync,
# and the prior ID stays persisted unless the second /sync succeeds.
original='const M=await JI("/sync",{record:{id:i.id,unitName:i.unitName||i.batch||"",dept:i.dept||"",date:i.date||"",raw:i.raw||"",name:i.name||"",manufacturer:i.manufacturer||"",model:i.model||"",code:i.code||"",operatorName:i.operatorName||"",remark:i.remark||"",feishuRecordId:i.feishuRecordId||i.remoteRecordId||""}});'
replacement='''const v1182Record={id:i.id,unitName:i.unitName||i.batch||"",dept:i.dept||"",date:i.date||"",raw:i.raw||"",name:i.name||"",manufacturer:i.manufacturer||"",model:i.model||"",code:i.code||"",operatorName:i.operatorName||"",remark:i.remark||"",feishuRecordId:i.feishuRecordId||i.remoteRecordId||""};
let M;
try{M=await JI("/sync",{record:v1182Record})}
catch(e){
 const message=String(e?.message||e||"");
 // A stale cloud ID (1254043, record not found) is not a network/permission failure.
 if(!v1182Record.feishuRecordId||!/1254043/.test(message)||!/record\\s+not\\s+found/i.test(message))throw e;
 console.warn("已确认飞书原记录不存在，使用原本地记录ID尝试新建一次",i.id);
 M=await JI("/sync",{record:{...v1182Record,feishuRecordId:""}});
 if(!M||!M.recordId)throw new Error("飞书重建未返回新记录ID；旧本地映射已保留，请检查后重试。");
 M.action="recreated";
}
'''
source=patch(source,original,replacement,"specific 1254043 fallback")
source=patch(source,'M.action==="recovered"?"已找回先前已创建的云端记录并恢复同步。":"已新增云端记录。"','M.action==="recovered"?"已找回先前已创建的云端记录并恢复同步。":M.action==="recreated"?"原飞书记录已删除，已作为新记录重新同步。":"已新增云端记录。"',"recreated success messaging")
assert source.count("function v118RetryStatusNoRender(rec)")==1
assert source.count("function v1188CorrectNameplate(rec)")==1
assert "recognition-rules-v1181.json" in source
assert source.count('JI("/sync"')==2,source.count('JI("/sync"')
out=Path("index-B81hyAdU-v1182-test1.js")
out.write_text(source,encoding="utf-8")
subprocess.run(["node","--check",str(out)],check=True)

# Layout: 4 headers in one row, preferred widths name > unit > department > count.
old_table='''<table style="width:100%;border-collapse:collapse;font-size:14px"><thead><tr>'+headers.map(h=>'<th style="padding:7px 4px;text-align:left">'+h+'</th>').join('')+'</tr></thead><tbody>'+data.map(r=>'<tr>'+r.map((v,i)=>'<td style="padding:7px 4px;border-top:1px solid #e5ebe7;'+(i===r.length-1?'text-align:center;font-weight:700':'')+'">'+esc(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table>'''
new_table='''<table class="v1182-stats-table" style="width:100%;table-layout:fixed;border-collapse:collapse;font-size:13px"><colgroup>'+(mode==='dept'?'<col style="width:20%"><col style="width:13%"><col><col style="width:38px">':'<col style="width:26%"><col><col style="width:38px">')+'</colgroup><thead><tr>'+headers.map((h,i)=>'<th style="padding:9px 3px;text-align:'+(i===headers.length-1?'center':'left')+';font-size:12px;white-space:nowrap;font-weight:750;color:#506059;border-bottom:1px solid #dce7e1">'+h+'</th>').join('')+'</tr></thead><tbody>'+data.map(r=>'<tr>'+r.map((v,i)=>'<td style="padding:9px 3px;border-top:1px solid #e5ebe7;overflow-wrap:anywhere;word-break:break-word;vertical-align:top;line-height:1.45;'+(i===r.length-1?'text-align:center;font-weight:800;white-space:nowrap':'')+'">'+esc(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table>'''
wrapper=patch(wrapper,old_table,new_table,"single-line four-column statistics table")

# Replace expensive recurring search-input poll with trusted input + blur/change.
old_search='''let trustedSearch=searchGuard.value||'';
    searchGuard.addEventListener('input',e=>{if(e.isTrusted)trustedSearch=searchGuard.value},true);
    setInterval(()=>{if(searchGuard.value!==trustedSearch)searchGuard.value=trustedSearch},350);'''
new_search='''let trustedSearch=searchGuard.value||'';
    searchGuard.addEventListener('input',e=>{if(e.isTrusted)trustedSearch=searchGuard.value},true);
    const v1182SyncTrusted=()=>{if(searchGuard.value!==trustedSearch)searchGuard.value=trustedSearch;};
    searchGuard.addEventListener('change',v1182SyncTrusted);
    searchGuard.addEventListener('blur',v1182SyncTrusted);'''
wrapper=patch(wrapper,old_search,new_search,"replace 350ms search polling")

# Keep observer but schedule expensive DOM modal classification only when
# actual modal-like nodes are inserted, or when a directly handled click occurs.
old_obs='''try{new MutationObserver(v118ScheduleUiFix).observe(d.body,{subtree:true,childList:true})}catch{}'''
new_obs='''try{
    const modalSelector='[role="dialog"],[id*="Modal"],[id*="modal"],[class*="modal"],[class*="overlay"],[class*="dialog"]';
    new MutationObserver(changes=>{
      for(const change of changes){
        if([...change.addedNodes,...change.removedNodes].some(node=>
            node.nodeType===1&&(node.matches?.(modalSelector)||node.querySelector?.(modalSelector)))){
          v118ScheduleUiFix();return;
        }
      }
    }).observe(d.body,{subtree:true,childList:true});
  }catch{}'''
wrapper=patch(wrapper,old_obs,new_obs,"filter full-page modal observer work")

# Non-blocking startup timings; no telemetry uploaded; read console/localStorage.
boot_anchor="const frame=document.getElementById('app');\nconst v11711BaseSrc="
boot_extra='''const v1182StartAt=performance.now();
window.__mingpaiBootMetrics={version:"1.18.2-test.1",startAt:v1182StartAt};
frame.addEventListener('load',()=>{
 const metrics=window.__mingpaiBootMetrics;
 metrics.frameReadyMs=Math.round(performance.now()-v1182StartAt);
 try{
 const doc=frame.contentDocument,list=doc?.getElementById('recordList');
 if(!list)return;
 let complete=false;
 const finish=()=>{
  if(complete||!list.querySelector('article.card'))return;
  complete=true;metrics.firstRecordMs=Math.round(performance.now()-v1182StartAt);
  observer.disconnect();
  try{localStorage.setItem('mingpai-startup-diagnostics-v1182',JSON.stringify(metrics))}catch{}
  console.info('[铭牌启动诊断 v1.18.2]',metrics);
 };
 const observer=new MutationObserver(finish);
 observer.observe(list,{childList:true,subtree:true});
 finish();
 setTimeout(()=>observer.disconnect(),20000);
 }catch(e){console.debug('startup diagnostics unavailable',e)}
},{once:true});
'''
wrapper=patch(wrapper,boot_anchor,boot_anchor.replace("const v11711BaseSrc=",boot_extra+"const v11711BaseSrc="),"passive startup timing")
wrapper=wrapper.replace("1.18.1-test-baseline","1.18.2-test.1").replace("v1.18.1 测试基线","v1.18.2 测试版")
assert "setInterval(()=>{if(searchGuard.value" not in wrapper
assert "v1182-stats-table" in wrapper
assert "v1182StartAt" in wrapper

# Versioned test shell will be deployed separately after COS upload.
Path("test-v1182-test1.html").write_text(wrapper,encoding="utf-8")
# Verify embedded browser scripts as actual JavaScript, not just HTML text.
for index,part in enumerate(re.findall(r"<script(?:\\s[^>]*)?>([\\s\\S]*?)</script>",wrapper,re.I),1):
    if not part.strip():continue
    script=Path(f"verify-v1182-inline-{index}.js")
    script.write_text(part,encoding="utf-8")
    subprocess.run(["node","--check",str(script)],check=True)
print("PASS inline wrapper JS syntax")

subprocess.run(["node","--check",str(Path("test-v1182-test1.html"))],check=False) if False else None

# Offline unit testing of recovery guard without any Feishu network calls.
snippet=re.search(r'let M;\ntry\{M=await JI\("/sync".*?M.action="recreated";\n\}',source,re.S)
assert snippet
test_js='''const assert=require("assert");
async function run(oldId,error){
 let i={id:"local-123"},v1182Record={id:i.id,feishuRecordId:oldId},calls=[];
 const JI=async(path,{record})=>{calls.push({...record});if(calls.length===1)throw Error(error);return {recordId:"new-rec-id"}};
 '''+snippet.group(0)+'''
 return {M,calls};
}
(async()=>{
 let a=await run("deleted-id","飞书接口错误 1254043: record not found,id = deleted-id");
 assert.equal(a.calls.length,2);assert.equal(a.calls[1].feishuRecordId,"");
 assert.equal(a.calls[1].id,"local-123");assert.equal(a.M.action,"recreated");
 for(let msg of ["HTTP 403 permission denied","network timeout","1254043 different error","record not found without code"]){
 let thrown=false;try{await run("old-id",msg)}catch{thrown=true}assert(thrown,msg);
 }
 let thrown=false;try{await run("","1254043: record not found")}catch{thrown=true}assert(thrown);
 console.log("PASS: stale cloud record recovered once; unrelated errors not retried");
})().catch(e=>{console.error(e);process.exit(1)});
'''
Path("test-v1182-sync.js").write_text(test_js,encoding="utf-8")
subprocess.run(["node","test-v1182-sync.js"],check=True)

# resource references: do not delete runtime resources solely because one
# name is not detected; this audit prevents unsafe deletion decisions.
resources=[
"ort-wasm-simd-threaded.jsep-MDYUKy93.wasm",
"ort-wasm-simd-threaded.jsep.wasm",
"ort.bundle.min-DkPMlImt.js",
"worker-entry-C9UNuyOJ-EhIzhVdm.js"
]
report={name:source.count(name) for name in resources}
Path("v1182-runtime-audit.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("RUNTIME AUDIT",report)
print("PASS syntax; runtime bytes",out.stat().st_size)
z=Path("mingpai-v1.18.2-test.1-COS.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as f:
 f.write(out,out.name)
 f.write("v1182-runtime-audit.json")
 f.writestr("README.txt","Only upload index-B81hyAdU-v1182-test1.js to COS assets/ for the isolated test. Do not change stable v1.18.1.\n")
print("PASS ZIP",z,z.stat().st_size,"SHA256",hashlib.sha256(out.read_bytes()).hexdigest())
