#!/usr/bin/env python3
"""v1.18.2 test.2.2: correct the source of stale sync error card display.
Patch the EXISTING card refresh function (not an external mutation observer).
Keep 1.18.2 test.2 Feishu recovery and all other code unchanged.
"""
from pathlib import Path
import subprocess,zipfile,hashlib
src=Path("index-B81hyAdU-v1182-test2.js")
s=src.read_text(encoding="utf-8")
old='rawdetails&&(rawdetails.open=rec.status!=="confirmed");strong&&'
new='''rawdetails&&(rawdetails.open=rec.status!=="confirmed");
if(rec.syncStatus==="synced"&&!String(rec.syncError||"").trim()){
  card.querySelectorAll(".errornote").forEach(note=>{
    if(/^\\s*飞书同步失败\\s*[:：]/.test(String(note.textContent||"")))note.remove();
  });
}
strong&&'''
assert s.count(old)==1,("patch card anchor",s.count(old))
assert s.count("function v11713PatchCard(rec)")==1
assert s.count('function v118RetryStatusNoRender(rec)')==1
assert 'v11822RecoveryKey' in s
assert 'recognition-rules-v1181.json' in s
s=s.replace(old,new,1)
out=Path("index-B81hyAdU-v1182-test22.js")
out.write_text(s,encoding="utf-8")
subprocess.run(["node","--check",str(out)],check=True)
test=r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('index-B81hyAdU-v1182-test22.js','utf8');
const start=source.indexOf('function v11713PatchCard(rec)');
const end=source.indexOf('function Cg(i)',start);
assert(start>0&&end>start);
const code=source.slice(start,end);
const mocks=()=>{
 let removeCount=0;
 const notes=[
   {textContent:'飞书同步失败： 飞书接口错误 1254043: record not found',remove(){removeCount++}},
   {textContent:'普通识别错误：未识别出厂编号',remove(){throw Error('should not remove unrelated note')}}
 ];
 const title={textContent:'',innerHTML:''};
 const card={
  querySelector(selector){
   if(selector==='.cardtitle strong'||selector==='.cardtitle small')return title;
   return null;
  },
  querySelectorAll(selector){assert.equal(selector,'.errornote');return notes}
 };
 const context={v151FindRecordCard:()=>card,Cg:()=> '已同步',jA:s=>String(s),console};
 vm.runInNewContext(code,context);
 return {context,getRemoved:()=>removeCount};
};
let a=mocks();a.context.v11713PatchCard({id:'1',syncStatus:'synced',syncError:'',status:'confirmed',name:'Test'});
assert.equal(a.getRemoved(),1,'Remove one stale red sync error after successful sync');
let b=mocks();b.context.v11713PatchCard({id:'1',syncStatus:'error',syncError:'1254043',status:'confirmed'});
assert.equal(b.getRemoved(),0,'Keep real sync errors while failed');
let c=mocks();c.context.v11713PatchCard({id:'1',syncStatus:'synced',syncError:'still exists',status:'confirmed'});
assert.equal(c.getRemoved(),0,'Do not mask active error');
console.log('PASS: redraw removes stale Feishu error only after successful sync; unrelated errors remain');
"""
Path("test-v1182-test22-card.js").write_text(test,encoding="utf-8")
subprocess.run(["node","test-v1182-test22-card.js"],check=True)
z=Path("mingpai-v1.18.2-test.2.2-COS.zip")
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as archive:
 archive.write(out,out.name)
 archive.writestr("README.txt","Upload index-B81hyAdU-v1182-test22.js to COS assets/. Does not change v1.18.1 formal or Feishu SCF.\n")
print('PASS',out.name,len(s),'SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),'zip',z)
