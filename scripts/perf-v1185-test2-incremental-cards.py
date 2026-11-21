#!/usr/bin/env python3
"""v1.18.5-test.2: incremental record card decoration + IDB read reduction.
Changes ONLY the test wrapper; formal and recognition rules byte-identical.
Base: immutable v1.18.5-test.1 full Pages artifact.
"""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path("app");test=root/"test-adaptive"
formal_names=("index.html","core.html","coi-serviceworker.js","version-v118-test.json","recognition-rules-v1184.json")
formal_before={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in formal_names}
tm=json.loads((test/"version-v118-test.json").read_text(encoding="utf-8"))
fm=json.loads((root/"version-v118-test.json").read_text(encoding="utf-8"))
assert tm["version"]=="1.18.5-test.1" and fm["version"]=="1.18.4.5"
assert (root/"recognition-rules-v1184.json").read_bytes()==(test/"recognition-rules-v1184.json").read_bytes()
assert len(json.loads((root/"recognition-rules-v1184.json").read_text())["rules"])==85
p=test/"index.html"
s=p.read_text(encoding="utf-8")
old="""  // v1.18.5-test.1: avoid a full IndexedDB-backed card check for every
  // tooltip, button or metadata DOM change. Record insertion/re-render
  // is the only event that needs the original card decorator.
  let envCardsScheduled=false;
  const cardsObserver=new MutationObserver(records=>{
    let newCard=false;
    for(const mutation of records){
      for(const node of mutation.addedNodes){
        if(node.nodeType!==1)continue;
        if(node.matches?.('article.card,.card') ||
           node.querySelector?.('article.card,.card')){
          newCard=true;
          break;
        }
      }
      if(newCard)break;
    }
    if(!newCard || envCardsScheduled)return;
    envCardsScheduled=true;
    setTimeout(()=>{
      envCardsScheduled=false;
      // Keep original decorateCards() and record persistence unchanged.
      decorateCards();
    },80);
  });
  const list=d.getElementById('recordList');
  if(list)cardsObserver.observe(list,{childList:true,subtree:true});
  decorateCards();"""
new="""  // v1.18.5-test.2: only newly inserted cards are decorated.
  // The prior observer re-fetched every visible card from IndexedDB whenever
  // just one new card was inserted. Preserve the native persistence code.
  const addedEnvCards=new Set();
  let envCardsScheduled=false;
  const cardsObserver=new MutationObserver(records=>{
    for(const mutation of records){
      for(const node of mutation.addedNodes){
        if(node.nodeType!==1)continue;
        if(node.matches?.('article.card,.card'))addedEnvCards.add(node);
        node.querySelectorAll?.('article.card,.card').forEach(card=>addedEnvCards.add(card));
      }
    }
    if(!addedEnvCards.size || envCardsScheduled)return;
    envCardsScheduled=true;
    setTimeout(()=>{
      envCardsScheduled=false;
      const current=[...addedEnvCards].filter(card=>card.isConnected);
      addedEnvCards.clear();
      if(current.length)decorateCards(current);
    },80);
  });
  const list=d.getElementById('recordList');
  if(list)cardsObserver.observe(list,{childList:true,subtree:true});
  // First load still initializes all visible cards, as before.
  decorateCards();"""
assert s.count(old)==1,"test.1 card observer not found or changed"
s=s.replace(old,new,1)
assert s.count("decorateCards(current)") == 1
assert s.count("const addedEnvCards=new Set()")==1
assert "const CLIENT_VERSION=\"1.18.5-test.1\";" in s
s=s.replace('const CLIENT_VERSION="1.18.5-test.1";',
            'const CLIENT_VERSION="1.18.5-test.2";',1)
s=s.replace('v1.18.5-test.1 性能测试版','v1.18.5-test.2 性能测试版')
assert "pendingConfirmRefreshBound" in s
assert "v11845-stats-unit-label" in s
assert "nativeChange('temperature',temp)" in s and "nativeChange('humidity',hum)" in s
assert "scheduleHiddenDockRecovery" not in s
assert "mingpai-optin-boot-diagnosis" not in s
p.write_text(s,encoding="utf-8")

core=test/"core.html";c=core.read_text(encoding="utf-8")
c=c.replace('v1.18.5-test.1 性能测试版','v1.18.5-test.2 性能测试版')
assert "const FLAG='mingpai-v1185-test1-coi-reload';" in c
c=c.replace("const FLAG='mingpai-v1185-test1-coi-reload';",
            "const FLAG='mingpai-v1185-test2-coi-reload';",1)
core.write_text(c,encoding="utf-8")
sw=test/"coi-serviceworker.js"
w=sw.read_text(encoding="utf-8")
assert 'const APP_VERSION="1.18.5-test.1";' in w
assert 'const SHELL_CACHE="mingpai-shell-v1185-test1";' in w
w=w.replace('const APP_VERSION="1.18.5-test.1";',
            'const APP_VERSION="1.18.5-test.2";',1)
w=w.replace('const SHELL_CACHE="mingpai-shell-v1185-test1";',
            'const SHELL_CACHE="mingpai-shell-v1185-test2";',1)
sw.write_text(w,encoding="utf-8")
tm["version"]="1.18.5-test.2"
(test/"version-v118-test.json").write_text(json.dumps(tm,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for n,h in formal_before.items():
    assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,"formal changed: "+n
for label,site in [("formal",root),("test",test)]:
    m=json.loads((site/"version-v118-test.json").read_text())
    assert m["version"]==("1.18.4.5" if label=="formal" else "1.18.5-test.2")
    assert len(json.loads((site/"recognition-rules-v1184.json").read_text())["rules"])==85
    for name in ["index.html","core.html"]:
        html=(site/name).read_text(encoding="utf-8")
        for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
            if js.strip():
                f=Path("/tmp")/f"perf1185-test2-{label}-{name}-{i}.js"
                f.write_text(js,encoding="utf-8")
                subprocess.run(["node","--check",str(f)],check=True)
    f=Path("/tmp")/f"perf1185-test2-{label}-sw.js"
    f.write_text((site/"coi-serviceworker.js").read_text(encoding="utf-8"))
    subprocess.run(["node","--check",str(f)],check=True)
print("PASS v1.18.5-test.2: newly inserted cards only, first load full, native IDB and Feishu unchanged")
for path in ["index.html","test-adaptive/index.html","recognition-rules-v1184.json"]:
    print("RELEASE_SHA256",path,hashlib.sha256((root/path).read_bytes()).hexdigest())
