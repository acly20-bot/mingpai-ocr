#!/usr/bin/env python3
"""v1.18.5-test.1: low-risk record card DOM mutation filter.
Only dispatch expensive environmental card decoration when added nodes
actually contain record cards. Keeps original decoration/database code.
Formal v1.18.4.5 and 85 rules byte-for-byte unchanged.
"""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path("app");test=root/"test-adaptive"
formal_files=["index.html","core.html","coi-serviceworker.js","version-v118-test.json","recognition-rules-v1184.json"]
original={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in formal_files}
assert json.loads((root/"version-v118-test.json").read_text())["version"]=="1.18.4.5"
m=json.loads((test/"version-v118-test.json").read_text())
assert m["version"]=="1.18.4.5-test"
assert len(json.loads((test/"recognition-rules-v1184.json").read_text())["rules"])==85
index=test/"index.html";s=index.read_text()
old="""  let envCardsScheduled=false;
  const cardsObserver=new MutationObserver(()=>{
    if(envCardsScheduled)return;
    envCardsScheduled=true;
    setTimeout(()=>{envCardsScheduled=false;decorateCards()},80);
  });
  const list=d.getElementById('recordList');if(list)cardsObserver.observe(list,{childList:true,subtree:true});
  decorateCards();"""
new="""  // v1.18.5-test.1: avoid a full IndexedDB-backed card check for every
  // tooltip, button or metadata DOM change. Record insertion/re-render
  // is the only event that needs the original card decorator.
  const pendingEnvCards=new Set();
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
assert s.count(old)==1
s=s.replace(old,new,1).replace("  const pendingEnvCards=new Set();\n","",1)
assert s.count("newCard=true;")==1
assert "decorateCards();" in s
assert s.count('const CLIENT_VERSION="1.18.4.5-test";')==1
s=s.replace('const CLIENT_VERSION="1.18.4.5-test";','const CLIENT_VERSION="1.18.5-test.1";',1)
s=s.replace('v1.18.4.5 测试版','v1.18.5-test.1 性能测试版')
assert "scheduleHiddenDockRecovery" not in s
assert 'pendingConfirmRefreshBound' in s
assert 'v11845-stats-unit-label' in s
assert "nativeChange('temperature',temp)" in s and "nativeChange('humidity',hum)" in s
assert 'mingpai-optin-boot-diagnosis' not in s
index.write_text(s)
core=test/"core.html";c=core.read_text()
c=c.replace("v1.18.4.5 测试版","v1.18.5-test.1 性能测试版")
assert "const FLAG='mingpai-v11845-test-coi-reload';" in c
c=c.replace("const FLAG='mingpai-v11845-test-coi-reload';",
            "const FLAG='mingpai-v1185-test1-coi-reload';",1)
core.write_text(c)
sw=test/"coi-serviceworker.js";w=sw.read_text()
assert 'const APP_VERSION="1.18.4.5-test";' in w
assert 'const SHELL_CACHE="mingpai-shell-v11845-bootclose-test-r9";' in w
w=w.replace('const APP_VERSION="1.18.4.5-test";',
            'const APP_VERSION="1.18.5-test.1";',1)
w=w.replace('const SHELL_CACHE="mingpai-shell-v11845-bootclose-test-r9";',
            'const SHELL_CACHE="mingpai-shell-v1185-test1";',1)
sw.write_text(w)
m["version"]="1.18.5-test.1"
(test/"version-v118-test.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n")
assert (root/"recognition-rules-v1184.json").read_bytes()==(test/"recognition-rules-v1184.json").read_bytes()
for fn,old_hash in original.items():
    assert hashlib.sha256((root/fn).read_bytes()).hexdigest()==old_hash,fn+" formal changed"
for folder,label in [(root,"formal"),(test,"test")]:
    ver=json.loads((folder/"version-v118-test.json").read_text())["version"]
    assert ver==("1.18.4.5" if label=="formal" else "1.18.5-test.1")
    for name in ("index.html","core.html"):
        html=(folder/name).read_text()
        for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
            if js.strip():
                f=Path("/tmp")/f"perf-test1-{label}-{name}-{i}.js"
                f.write_text(js)
                subprocess.run(["node","--check",str(f)],check=True)
    f=Path("/tmp")/f"perf-test1-{label}-sw.js"
    f.write_text((folder/"coi-serviceworker.js").read_text())
    subprocess.run(["node","--check",str(f)],check=True)
print("PASS v1.18.5-test.1 only: card added-node gating, stable 85 rules, no formal changes")
