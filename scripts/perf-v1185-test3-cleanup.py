#!/usr/bin/env python3
"""v1.18.5-test.3 remove obsolete startup diagnostics and redundant full-list risk scan.
Never rewrite native records/IDB or OCR; formal stays byte-identical.
Starts from validated v1.18.5-test.2 snapshot.
"""
from pathlib import Path
import json,hashlib,re,subprocess
r=Path("app");t=r/"test-adaptive"
formal_files=("index.html","core.html","coi-serviceworker.js","version-v118-test.json","recognition-rules-v1184.json")
formal={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in formal_files}
assert json.loads((r/"version-v118-test.json").read_text())["version"]=="1.18.4.5"
assert json.loads((t/"version-v118-test.json").read_text())["version"]=="1.18.5-test.2"
assert len(json.loads((t/"recognition-rules-v1184.json").read_text())["rules"])==85
p=t/"index.html";s=p.read_text(encoding="utf-8")
# Legacy v1.18.2 20-second tracing observer has no consumer and has been
# superseded by actual real-device launch tests. Preserve boot retry logic.
start="const v1182StartAt=performance.now();"
end="const v11711BaseSrc=frame.getAttribute('src');"
assert s.count(start)==s.count(end)==1
a=s.index(start);b=s.index(end,a)
legacy=s[a:b]
assert "new MutationObserver(finish)" in legacy
assert "mingpai-startup-diagnostics-v1182" in legacy
assert "window.__mingpaiBootMetrics" in legacy
s=s[:a]+s[b:]
assert "v11711BootTimer=setInterval" in s
# The risk-hint observer scanned all cards each time any one was inserted.
# Update only added record cards, including replacement wrapper fragments.
old="""  // Only direct record-list replacements trigger a scan; editing the hint
  // inside a card does not create a recursive MutationObserver loop.
  new MutationObserver(records=>{
    if(records.some(r=>[...r.addedNodes].some(n=>n.nodeType===1&&n.matches?.('article.card'))))
      requestAnimationFrame(scan);
  }).observe(list,{childList:true});"""
new="""  // v1.18.5-test.3: update only new risk-hint cards, not the whole list.
  // Do not observe inner descendants: editing warnings cannot cause loops.
  const addedRiskCards=new Set();
  let riskPaintScheduled=false;
  new MutationObserver(records=>{
    for(const change of records){
      for(const node of change.addedNodes){
        if(node.nodeType!==1)continue;
        if(node.matches?.('article.card'))addedRiskCards.add(node);
        node.querySelectorAll?.('article.card').forEach(card=>addedRiskCards.add(card));
      }
    }
    if(!addedRiskCards.size||riskPaintScheduled)return;
    riskPaintScheduled=true;
    requestAnimationFrame(()=>{
      riskPaintScheduled=false;
      const cards=[...addedRiskCards];
      addedRiskCards.clear();
      cards.forEach(card=>{if(card.isConnected)update(card)});
    });
  }).observe(list,{childList:true});"""
assert s.count(old)==1
s=s.replace(old,new,1)
assert "const confirmed=/已确认/" in s
assert "pendingConfirmRefreshBound" in s
assert "decorateCards(current)" in s
assert "v11845-stats-unit-label" in s
assert "nativeChange('temperature',temp)" in s and "nativeChange('humidity',hum)" in s
assert "mingpai-optin-boot-diagnosis" not in s
assert "scheduleHiddenDockRecovery" not in s # formal-only
assert s.count('const CLIENT_VERSION="1.18.5-test.2";')==1
s=s.replace('const CLIENT_VERSION="1.18.5-test.2";','const CLIENT_VERSION="1.18.5-test.3";',1)
s=s.replace("v1.18.5-test.2 性能测试版","v1.18.5-test.3 性能测试版")
p.write_text(s,encoding="utf-8")
core=t/"core.html";c=core.read_text(encoding="utf-8")
c=c.replace("v1.18.5-test.2 性能测试版","v1.18.5-test.3 性能测试版")
assert "const FLAG='mingpai-v1185-test2-coi-reload';" in c
c=c.replace("const FLAG='mingpai-v1185-test2-coi-reload';","const FLAG='mingpai-v1185-test3-coi-reload';",1)
core.write_text(c,encoding="utf-8")
sw=t/"coi-serviceworker.js";w=sw.read_text(encoding="utf-8")
assert 'const APP_VERSION="1.18.5-test.2";' in w
assert 'const SHELL_CACHE="mingpai-shell-v1185-test2";' in w
w=w.replace('const APP_VERSION="1.18.5-test.2";','const APP_VERSION="1.18.5-test.3";',1)
w=w.replace('const SHELL_CACHE="mingpai-shell-v1185-test2";','const SHELL_CACHE="mingpai-shell-v1185-test3";',1)
sw.write_text(w,encoding="utf-8")
m=json.loads((t/"version-v118-test.json").read_text(encoding="utf-8"))
m["version"]="1.18.5-test.3"
(t/"version-v118-test.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for name,sha in formal.items():
    assert hashlib.sha256((r/name).read_bytes()).hexdigest()==sha,"formal modified: "+name
assert (r/"recognition-rules-v1184.json").read_bytes()==(t/"recognition-rules-v1184.json").read_bytes()
for label,folder in [("formal",r),("test",t)]:
    manifest=json.loads((folder/"version-v118-test.json").read_text())
    assert manifest["version"]==("1.18.4.5" if label=="formal" else "1.18.5-test.3")
    for name in ("index.html","core.html"):
        html=(folder/name).read_text()
        for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
            if js.strip():
                f=Path("/tmp")/f"perf-v1185-test3-{label}-{name}-{i}.js"
                f.write_text(js);subprocess.run(["node","--check",str(f)],check=True)
    f=Path("/tmp")/f"perf-v1185-test3-{label}-sw.js"
    f.write_text((folder/"coi-serviceworker.js").read_text())
    subprocess.run(["node","--check",str(f)],check=True)
print("PASS: test3 removes unused 20s diagnostics, processes only new risk-hint cards, leaves native features intact")
for name in ["index.html","test-adaptive/index.html","recognition-rules-v1184.json"]:
    print("RELEASE_SHA256",name,hashlib.sha256((r/name).read_bytes()).hexdigest())
