#!/usr/bin/env python3
"""Fix the missing native Confirm button after an environment edit.
v1.18.4.2-test builds on the reviewed v1.18.4.1-test output only.
Re-run the app's own record renderer through its status filter: do not
manufacture or click a fake confirmation button. Formal remains unchanged.
"""
from pathlib import Path
import hashlib,re,subprocess,json
root=Path("app");test=root/"test-adaptive"
p=test/"index.html";c=test/"core.html";sw=test/"coi-serviceworker.js";mf=test/"version-v118-test.json"
s=p.read_text(encoding="utf-8");core=c.read_text(encoding="utf-8");w=sw.read_text(encoding="utf-8")
m=json.loads(mf.read_text(encoding="utf-8"))
assert m["version"]=="1.18.4.1-test" and m["rules"]=="recognition-rules-v1184.json"
assert 'const CLIENT_VERSION="1.18.4.1-test";' in s
needle="""                // Reconcile only the two counters; leave all OCR and queue state alone.
                const recs=await allRecords();"""
assert s.count(needle)==1
# A status change in IndexedDB does not re-create the card DOM: it still has
# the confirmed-state controls. Ask the original render function to re-render
# by emitting a genuine filter change. When the user is filtering to Confirmed,
# switch to Pending so the just-edited record stays visible for review.
insert="""                // Native app re-render, required to restore its real "确认记录"
                // control. Setting the badge text alone leaves stale action buttons.
                const statusFilter=d.getElementById('filterStatus');
                if(statusFilter){
                  const selected=statusFilter.options[statusFilter.selectedIndex];
                  const selectedText=(selected?.textContent||'').trim();
                  if(/已确认/.test(selectedText)){
                    const pendingOption=[...statusFilter.options].find(o=>/待审核/.test(o.textContent||''));
                    if(pendingOption)statusFilter.value=pendingOption.value;
                  }
                  statusFilter.dispatchEvent(new Event('change',{bubbles:true}));
                }
                // Reconcile only the two counters; leave all OCR and queue state alone.
                const recs=await allRecords();"""
s=s.replace(needle,insert,1)
# Versioned SW and shell ensure an already-open testing browser gets refreshed.
assert s.count('const CLIENT_VERSION="1.18.4.1-test";')==1
s=s.replace('const CLIENT_VERSION="1.18.4.1-test";','const CLIENT_VERSION="1.18.4.2-test";',1)
s=s.replace('v1.18.4.1 测试版','v1.18.4.2 测试版')
core=core.replace('v1.18.4.1 测试版','v1.18.4.2 测试版').replace('mingpai-v11841-test-coi-reload','mingpai-v11842-test-coi-reload')
w=w.replace('mingpai-shell-v11841-test','mingpai-shell-v11842-test').replace('1.18.4.1-test','1.18.4.2-test')
m['version']='1.18.4.2-test'
assert "statusFilter.dispatchEvent(new Event('change',{bubbles:true}))" in s
assert "scheduleEnvironmentResync(id)" not in s[s.index("          const persist=async e=>"):s.index("          ti.addEventListener('blur',persist);")]
assert "r.status='pending'" in s
assert "index-B81hyAdU-v11832-viewport-test2.js" in core
p.write_text(s,encoding="utf-8");c.write_text(core,encoding="utf-8");sw.write_text(w,encoding="utf-8")
mf.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for label,html in [('outer',s),('core',core)]:
    for i,code in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
        if code.strip():
            path=Path('/tmp')/f"v11842-{label}-{i}.js"
            path.write_text(code,encoding="utf-8")
            subprocess.run(["node","--check",str(path)],check=True)
path=Path('/tmp/v11842-sw.js');path.write_text(w,encoding="utf-8")
subprocess.run(["node","--check",str(path)],check=True)
formal=json.loads((root/'version-v118-test.json').read_text(encoding="utf-8"))
assert formal['version']=='1.18.4' and formal['rules']=='recognition-rules-v1184.json'
assert m['mainJs']==formal['mainJs']
print('PASS v1.18.4.2-test: native confirm control rerendered, manual re-review preserved, production unchanged')
