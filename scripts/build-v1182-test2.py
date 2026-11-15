#!/usr/bin/env python3
"""v1.18.2 test.2: repair stale Feishu mapping with idempotent recovery key;
 preserve all test.1 UI/perf enhancements. Only test COS runtime is changed."""
from pathlib import Path
import subprocess,zipfile,hashlib
s=Path("index-B81hyAdU-v1182-test1.js").read_text("utf-8")
old=''' M=await JI("/sync",{record:{...v1182Record,feishuRecordId:""}});
 if(!M||!M.recordId)throw new Error("飞书重建未返回新记录ID；旧本地映射已保留，请检查后重试。");
 M.action="recreated";'''
new=''' // The sync service can remember the stale mapping by LOCAL id, even when
 // feishuRecordId is blank. Use a deterministic new sync key for this ONE
 // deleted remote record. Keep i.id unchanged in local IndexedDB.
 const v11822RecoveryKey=String(i.id)+"__restored__"+String(v1182Record.feishuRecordId||"missing-cloud-id").replace(/[^a-z0-9]/gi,"").slice(-14);
 try{
   M=await JI("/sync",{record:{...v1182Record,id:v11822RecoveryKey,feishuRecordId:"",remoteRecordId:""}});
 }catch(secondError){
   throw new Error("飞书原记录不存在，改用新映射重建仍失败："+String(secondError?.message||secondError||"未知错误"));
 }
 if(!M||!M.recordId)throw new Error("飞书重建未返回新记录ID；旧本地映射已保留，请检查后重试。");
 M.action="recreated";'''
assert s.count(old)==1,s.count(old)
# Backend may still map LOCAL id to deleted Feishu record when old cloud ID
# was not stored in IndexedDB.
guard='if(!v1182Record.feishuRecordId||!/1254043/.test(message)'
assert s.count(guard)==1,("stale cloud guard",s.count(guard))
s=s.replace(guard,'if(!/1254043/.test(message)',1)

s=s.replace(old,new,1)
assert s.count('function v118RetryStatusNoRender(rec)')==1
assert s.count('function v1188CorrectNameplate(rec)')==1
assert 'recognition-rules-v1181.json' in s
assert 'index-B81hyAdU-v1182-test1.js' not in s
out=Path("index-B81hyAdU-v1182-test2.js")
out.write_text(s,"utf-8")
subprocess.run(["node","--check",str(out)],check=True)
# Check the REAL recovery branch against a server model that persists
# stale cloud record references using either cloud ID or LOCAL ID.
test=r'''
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const s=fs.readFileSync('index-B81hyAdU-v1182-test2.js','utf8');
const start=s.indexOf('const v1182Record={id:i.id,');
const end=s.indexOf('i.syncStatus="synced",i.syncError=',start);
assert(start>0&&end>start);
const snippet=s.slice(start,end);
assert(snippet.includes('v11822RecoveryKey'));
async function scenario(errorType,initialCloudId){
 let calls=[];
 const i={id:"local-unique-123",batch:"",unitName:"医院",dept:"放射",date:"2026/11/15",name:"设备",manufacturer:"厂家",model:"X",code:"Y",raw:"",remark:"",operatorName:"检定员",feishuRecordId:initialCloudId||"",remoteRecordId:""};
 const staleId="local-unique-123";
 const JI=async(_,body)=>{
   let rec=body.record;calls.push(rec);
   if(errorType==="permission")throw new Error("403 insufficient permission");
   if(errorType==="network")throw new Error("network timeout");
   if(!rec.id.endsWith('__restored__'+String(initialCloudId||'missing-cloud-id').replace(/[^a-z0-9]/gi,"").slice(-14))) {
     throw new Error("飞书接口错误 1254043: record not found,id = rec_deleted");
   }
   if(rec.feishuRecordId)throw new Error("stale cloud id leaked");
   if(rec.id===staleId)throw new Error("stale LOCAL id reused");
   if(errorType==="new-failure")throw new Error("429 rate limit");
   return {recordId:"rec_fresh_777",action:"created"};
 };
 const sandbox={i,JI,console};
 try {
   await vm.runInNewContext('(async()=>{'+snippet+';return M})()',sandbox);
   return {ok:true,calls};
 } catch(e){return {ok:false,error:String(e.message||e),calls}}
}
(async()=>{
 let a=await scenario("success","rec_deleted");
 assert(a.ok,a.error);
 assert.equal(a.calls.length,2);
 assert.equal(a.calls[0].id,"local-unique-123");
 assert.notEqual(a.calls[1].id,"local-unique-123");
 assert.equal(a.calls[1].feishuRecordId,"");
 let b=await scenario("new-failure","rec_deleted");
 assert(!b.ok);assert(b.error.includes("新映射重建仍失败"));assert.equal(b.calls.length,2);
 for(const type of ["network","permission"]){
   let x=await scenario(type,"rec_deleted");assert(!x.ok);assert.equal(x.calls.length,1);
 }
 let x=await scenario("success","");assert(x.ok,x.error);assert.equal(x.calls.length,2);
 console.log("PASS: deterministic recovery ID, fail-closed retry, never change local ID and no retry on network/permission");
})().catch(e=>{console.error(e);process.exit(1)});
'''
Path("test-v1182-test2.js").write_text(test,"utf-8")
subprocess.run(["node","test-v1182-test2.js"],check=True)
z=Path("mingpai-v1.18.2-test.2-COS.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as archive:
 archive.write(out,out.name)
 archive.writestr("README.txt",
    "Upload index-B81hyAdU-v1182-test2.js into COS assets/; keep v1.18.1 and test.1 files unchanged.\n"
    "v1.18.2 test.2 retries deleted Feishu cloud record with deterministic fresh mapping key; keeps local record id.\n")
print("PASS zip",z,z.stat().st_size,"SHA256",hashlib.sha256(out.read_bytes()).hexdigest())
