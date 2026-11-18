#!/usr/bin/env python3
"""v1.18.4.5-test: record environment fields through the native change handler.
Prevents stale in-memory record from overwriting edited temp/humidity on Confirm.
Formal 1.18.4.4 remains byte-identical to pinned baseline.
"""
from pathlib import Path
import hashlib,re,json,subprocess
root=Path('app'); test=root/'test-adaptive'
formal_before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in
 ('index.html','core.html','coi-serviceworker.js','version-v118-test.json','recognition-rules-v1184.json')}
manifest=json.loads((test/'version-v118-test.json').read_text())
assert manifest['version']=='1.18.4.4-test' and manifest['mainJs']=='index-B81hyAdU-v11832-viewport-test2.js'
p=test/'index.html';s=p.read_text(encoding='utf-8')
a=s.index('          const persist=async e=>{',s.index('  // V4 weather + per-record environment persistence'))
b=s.index("          ti.addEventListener('blur',persist);",a)
old=s[a:b]
assert 'nativeField.dispatchEvent(new Event' in old
assert 'await putRecord(rec)' in old
assert 'envWriteQueues.set(id,job)' in old
updated=r"""          // Native core owns both the live record object and its database writes.
          // Dispatch a field change for temperature/humidity through the same
          // delegated handler as model/code, instead of an external IndexedDB put.
          const persist=async e=>{
            e.stopPropagation();
            const draft=envDrafts.get(id)||{temperature:ti.value,humidity:hi.value};
            const temp=String(draft.temperature??'').trim(),hum=String(draft.humidity??'').trim();
            const tn=numeric(temp),hn=numeric(hum);
            if((temp!==''&&(tn===null||tn< -100||tn>70))||(hum!==''&&(hn===null||hn<0||hn>100))){
              alert('温湿度输入无效：温度应为数字，湿度应在 0～100 之间。');return;
            }
            const previous=envWriteQueues.get(id)||Promise.resolve();
            const job=previous.catch(()=>{}).then(async()=>{
              let rec=await getRecord(id);
              if(!rec)return;
              if(String(rec.temperature??'').trim()===temp&&String(rec.humidity??'').trim()===hum){
                envDrafts.delete(id);return;
              }
              const list=d.getElementById('recordList');
              if(!list)throw Error('找不到原生记录列表');
              const nativeChange=async(field,value)=>{
                const nativeInput=d.createElement('input');
                nativeInput.type='hidden';
                nativeInput.dataset.id=id;
                nativeInput.dataset.field=field;
                nativeInput.value=value;
                list.appendChild(nativeInput);
                nativeInput.dispatchEvent(new Event('change',{bubbles:true}));
                nativeInput.remove();
                // The core handler mutates its in-memory record synchronously,
                // then writes IndexedDB asynchronously. Await its own commit.
                let saved=false;
                for(let tries=0;tries<30;tries++){
                  await new Promise(resolve=>setTimeout(resolve,60));
                  const check=await getRecord(id);
                  if(check && String(check[field]??'').trim()===value){
                    saved=true;break;
                  }
                }
                if(!saved)throw Error('主程序没有完成'+field+'保存');
              };
              if(rec.status==='confirmed'){
                // Use an unchanged native field to trigger the same review
                // transition as editing manufacturer/model or serial number.
                const nativeField=[...d.querySelectorAll('#recordList .card')]
                  .filter(el=>el.querySelector('[data-id="'+id+'"]'))
                  .flatMap(el=>[...el.querySelectorAll('input[data-field="model"][data-id],textarea[data-field="remark"][data-id]')])[0];
                if(!nativeField)throw Error('找不到原生审核字段');
                nativeField.dispatchEvent(new Event('change',{bubbles:true}));
                let pending=false;
                for(let tries=0;tries<30;tries++){
                  await new Promise(resolve=>setTimeout(resolve,60));
                  rec=await getRecord(id);
                  if(rec?.status==='pending'){pending=true;break}
                }
                if(!pending)throw Error('原生待审核状态未保存');
              }
              rec=await getRecord(id);
              if(String(rec.temperature??'').trim()!==temp)await nativeChange('temperature',temp);
              rec=await getRecord(id);
              if(String(rec.humidity??'').trim()!==hum)await nativeChange('humidity',hum);
              // Important: do NOT call putRecord() here. A separate writer
              // would reintroduce the in-memory/database divergence.
              envDrafts.delete(id);
              const rendered=[...d.querySelectorAll('#recordList .card')]
                .find(el=>el.querySelector('[data-id="'+id+'"]'));
              const env=rendered?.querySelector('.env-inline');
              if(env){
                const t=env.querySelector('.temp'),h=env.querySelector('.hum');
                if(t&&d.activeElement!==t)t.value=temp;
                if(h&&d.activeElement!==h)h.value=hum;
              }
            });
            envWriteQueues.set(id,job);
            try{await job}catch(err){
              console.warn('native environment save failed',err);
              alert('温湿度保存尚未完成，请检查数值后再确认。');
            }finally{
              if(envWriteQueues.get(id)===job)envWriteQueues.delete(id);
            }
          };
"""
s=s[:a]+updated+s[b:]
# Protect against confirmation being clicked during asynchronous native field
# writes. Replay one click after the genuine core commit has completed.
needle="  let envCaptureRunning=false;"
assert s.count(needle)==1
gate=r"""  const environmentNativeList=d.getElementById('recordList');
  if(environmentNativeList && !environmentNativeList.dataset.envConfirmWaitBound){
    environmentNativeList.dataset.envConfirmWaitBound='1';
    environmentNativeList.addEventListener('click',e=>{
      const button=e.target.closest('button[data-action="toggle"]');
      if(!button)return;
      const id=button.dataset.id;
      const running=envWriteQueues.get(id);
      if(!running)return;
      e.preventDefault();e.stopImmediatePropagation();
      running.then(()=>{
        const ready=[...environmentNativeList.querySelectorAll('button[data-action="toggle"]')]
          .find(btn=>btn.dataset.id===id&&/确认记录/.test(btn.textContent||''));
        ready?.click();
      }).catch(err=>console.warn('confirmation deferred until environment saved',err));
    },true);
  }
"""
s=s.replace(needle,gate+needle,1)
assert 'view?.location?.reload()' not in s
assert 'await putRecord(rec)' not in s[s.index('          const persist=async e=>'):s.index("          ti.addEventListener('blur',persist);")]
assert "nativeChange('temperature',temp)" in s and "nativeChange('humidity',hum)" in s
assert "envConfirmWaitBound" in s
assert s.count('const CLIENT_VERSION="1.18.4.4-test";')==1
s=s.replace('const CLIENT_VERSION="1.18.4.4-test";','const CLIENT_VERSION="1.18.4.5-test";',1)
s=s.replace('v1.18.4.4 测试版','v1.18.4.5 测试版')
p.write_text(s,encoding='utf-8')
c=test/'core.html';cs=c.read_text(encoding='utf-8')
cs=cs.replace('v1.18.4.4 测试版','v1.18.4.5 测试版')
cs=cs.replace('mingpai-v11844-test-coi-reload','mingpai-v11845-test-coi-reload')
c.write_text(cs,encoding='utf-8')
sw=test/'coi-serviceworker.js';w=sw.read_text(encoding='utf-8')
w=w.replace('mingpai-shell-v11844-test','mingpai-shell-v11845-test').replace('1.18.4.4-test','1.18.4.5-test')
sw.write_text(w,encoding='utf-8')
manifest['version']='1.18.4.5-test'
(test/'version-v118-test.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for label,html in [('outer',s),('core',cs)]:
  for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
    if js.strip():
      fn=Path('/tmp')/f'v11845-{label}-{i}.js';fn.write_text(js,encoding='utf-8')
      subprocess.run(['node','--check',str(fn)],check=True)
fn=Path('/tmp/v11845-sw.js');fn.write_text(w,encoding='utf-8')
subprocess.run(['node','--check',str(fn)],check=True)
for name,old_hash in formal_before.items():
  assert hashlib.sha256((root/name).read_bytes()).hexdigest()==old_hash, 'FORMAL CHANGED: '+name
assert json.loads((root/'version-v118-test.json').read_text())['version']=='1.18.4.4'
print('PASS 1.18.4.5 test: native memory + IndexedDB temp/humidity writes; no formal change')
