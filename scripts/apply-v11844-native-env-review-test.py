#!/usr/bin/env python3
"""v1.18.4.4-test: use native record change and re-render for environment edits.
Never reload the page or replace native confirm buttons. Preserve Feishu link."""
from pathlib import Path
import re,json,subprocess
root=Path("app");site=root/"test-adaptive"
p=site/"index.html";core=site/"core.html";sw=site/"coi-serviceworker.js";mf=site/"version-v118-test.json"
s=p.read_text(encoding="utf-8");c=core.read_text(encoding="utf-8");w=sw.read_text(encoding="utf-8")
m=json.loads(mf.read_text(encoding="utf-8"))
assert m['version']=='1.18.4.3-test' and m['rules']=='recognition-rules-v1184.json'
assert 'const CLIENT_VERSION="1.18.4.3-test";' in s
# Delete the now-obsolete state-restoration/reload workaround.
start=s.index("  // Restore the edited record after the native UI rehydrates from IndexedDB.")
end=s.index("  // v1.16: OCR.space mode is priority cloud mode with Paddle fallback.",start)
assert 'mingpai-v11843-return-record' in s[start:end]
s=s[:start]+s[end:]
start=s.index("          const persist=async e=>{",s.index("  // V4 weather + per-record environment persistence"))
end=s.index("          ti.addEventListener('blur',persist);",start)
old=s[start:end]
assert "view?.location?.reload()" in old and "envWriteQueues.set(id,job)" in old
# The core runtime's normal edit event for an existing record:
# recordList.addEventListener('change',... dataset.id/dataset.field ... status pending ... PA(record); AI())
# Wait for that transaction and rendered buttons before writing env fields.
replacement=r"""          const persist=async e=>{
            e.stopPropagation();
            const draft=envDrafts.get(id)||{temperature:ti.value,humidity:hi.value};
            const temp=String(draft.temperature??'').trim(),hum=String(draft.humidity??'').trim();
            const tn=numeric(temp),hn=numeric(hum);
            if((temp!==''&&(tn===null||tn< -100||tn>70))||(hum!==''&&(hn===null||hn<0||hn>100))){
              alert('温湿度输入无效：温度应为数字，湿度应在 0～100 之间。');
              return;
            }
            const prior=envWriteQueues.get(id)||Promise.resolve();
            const job=prior.catch(()=>{}).then(async()=>{
              let rec=await getRecord(id);
              if(!rec)return;
              if(String(rec.temperature??'').trim()===temp&&String(rec.humidity??'').trim()===hum){
                envDrafts.delete(id);return;
              }
              if(rec.status==='confirmed'){
                // The OCR app keeps its own in-memory record array.
                // Let its original field-change handler mark the SAME record pending
                // and rebuild the native confirmation control. No iframe reload.
                const nativeField=card.querySelector(
                  'textarea[data-field="remark"][data-id],input[data-field="model"][data-id],input[data-field="name"][data-id]');
                if(!nativeField || nativeField.dataset.id!==id){
                  throw new Error('无法定位原生记录编辑字段，请勿自动修改已确认状态');
                }
                nativeField.dispatchEvent(new Event('change',{bubbles:true}));
                // The native handler writes IndexedDB asynchronously.
                // Wait for its pending-state transaction AND native button repaint,
                // then persist environment so the core cannot overwrite the new value.
                let pendingReady=false;
                for(let tries=0;tries<24;tries++){
                  await new Promise(resolve=>setTimeout(resolve,75));
                  rec=await getRecord(id);
                  const nativeCard=[...d.querySelectorAll('#recordList .card')].find(el=>
                    el.querySelector('[data-select-id="'+id+'"]')||
                    el.querySelector('[data-id="'+id+'"]'));
                  const nativeButton=nativeCard?.querySelector('[data-action="toggle"]');
                  if(rec?.status==='pending' &&
                     nativeButton && /确认记录|确认这条记录/.test(nativeButton.textContent||'')){
                    pendingReady=true;break;
                  }
                }
                if(!pendingReady){
                  throw new Error('原生待审核按钮未完成更新，未执行强制刷新');
                }
              }
              // Re-read the persisted record AFTER native re-render.
              rec=await getRecord(id);
              if(!rec)return;
              rec.temperature=temp;rec.humidity=hum;rec.envCapturedAt=Date.now();
              if(rec.status==='pending'){rec.syncStatus='pending';rec.syncError=''}
              await putRecord(rec);
              envDrafts.delete(id);
              const rendered=[...d.querySelectorAll('#recordList .card')].find(el=>
                el.querySelector('[data-select-id="'+id+'"]')||
                el.querySelector('[data-id="'+id+'"]'));
              const env=rendered?.querySelector('.env-inline');
              if(env){
                const tempInput=env.querySelector('.temp'),humInput=env.querySelector('.hum');
                if(tempInput && d.activeElement!==tempInput)tempInput.value=temp;
                if(humInput && d.activeElement!==humInput)humInput.value=hum;
              }
              // Never invoke automatic environment->Feishu update;
              // explicit native Confirm is now required.
            });
            envWriteQueues.set(id,job);
            try{await job}catch(err){
              console.warn('native environment review transition failed',err);
              alert('温湿度已修改，但待审核操作尚未更新成功，请检查记录后再确认。');
            }finally{
              if(envWriteQueues.get(id)===job)envWriteQueues.delete(id);
            }
          };
"""
s=s[:start]+replacement+s[end:]
s=s.replace('const CLIENT_VERSION="1.18.4.3-test";','const CLIENT_VERSION="1.18.4.4-test";',1)
s=s.replace('v1.18.4.3 测试版','v1.18.4.4 测试版')
c=c.replace('v1.18.4.3 测试版','v1.18.4.4 测试版').replace('mingpai-v11843-test-coi-reload','mingpai-v11844-test-coi-reload')
w=w.replace('mingpai-shell-v11843-test','mingpai-shell-v11844-test').replace('1.18.4.3-test','1.18.4.4-test')
m['version']='1.18.4.4-test'
assert "view?.location?.reload()" not in s
assert "mingpai-v11843-return-record" not in s
assert "nativeField.dispatchEvent(new Event('change',{bubbles:true}))" in s
assert "data-action=\"toggle\"" in s
assert 'r.status=\'pending\'' not in s[s.index("          const persist=async e=>"):s.index("          ti.addEventListener('blur',persist);")]
assert m['mainJs']=='index-B81hyAdU-v11832-viewport-test2.js'
assert json.loads((root/'version-v118-test.json').read_text())['version']=='1.18.4'
p.write_text(s,encoding="utf-8");core.write_text(c,encoding="utf-8");sw.write_text(w,encoding="utf-8")
mf.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for label,html in [('outer',s),('core',c)]:
  for i,script in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
    if script.strip():
      tmp=Path('/tmp')/f'v11844-{label}-{i}.js';tmp.write_text(script,encoding="utf-8")
      subprocess.run(['node','--check',str(tmp)],check=True)
tmp=Path('/tmp/v11844-sw.js');tmp.write_text(w,encoding='utf-8')
subprocess.run(['node','--check',str(tmp)],check=True)
print('PASS v1.18.4.4-test: native change->pending->native confirm UI without reload; formal unchanged')
