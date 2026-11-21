#!/usr/bin/env python3
"""Promote validated boot/review fixes to v1.18.4.5 formal; remove opt-in diagnostic.
Preserve exact 85-rule JSON and formal-only dock self-recovery and audit UI.
Base release-baseline/v11845-rules-cpap-r9.
"""
from pathlib import Path
import re,hashlib,json,subprocess
r=Path("app"); t=r/"test-adaptive"
rules0=(r/"recognition-rules-v1184.json").read_bytes()
assert rules0==(t/"recognition-rules-v1184.json").read_bytes()
assert len(json.loads(rules0)["rules"])==85
f=(r/"index.html").read_text();q=(t/"index.html").read_text()
assert "scheduleHiddenDockRecovery" in f
assert "scheduleHiddenDockRecovery" not in q
assert "const confirmed=/已确认/" in q
assert "const confirmed=/已确认/" not in f
assert 'mingpai-optin-boot-diagnosis' in q
marker='<script id="mingpai-optin-boot-diagnosis">'
assert q.count(marker)==1
a=q.index(marker);b=q.index('</script>',a)+len('</script>')
q=q[:a]+q[b:]
(t/"index.html").write_text(q)
start="function v1183InstallFieldReview(d) {"
end="\n\n  v1183InstallFieldReview(d);"
assert f.count(start)==q.count(start)==1
fs=f.index(start);fe=f.index(end,fs)
qs=q.index(start);qe=q.index(end,qs)
function=q[qs:qe]
assert "const confirmed=/已确认/" in function
assert "list.addEventListener('click'" in function
f=f[:fs]+function+f[fe:]
assert "scheduleHiddenDockRecovery" in f and "pendingConfirmRefreshBound" in f
assert "v11845-stats-unit-label" in f
assert "nativeChange('temperature',temp)" in f and "nativeChange('humidity',hum)" in f
(r/"index.html").write_text(f)
# Bootstrap: copy only the script whose tested handling is user-approved.
fc=(r/"core.html").read_text();tc=(t/"core.html").read_text()
open_tag='<script type="module">'
assert fc.count(open_tag)==tc.count(open_tag)==1
def script_region(s):
    a=s.index(open_tag)
    b=s.index('</script>',a)+len('</script>')
    return a,b
a,b=script_region(fc);c,d=script_region(tc)
boot=tc[c:d]
assert "if(resumedController?.scriptURL?.includes" in boot
assert "deadline(navigator.serviceWorker.ready,4200" in boot
assert "const FLAG='mingpai-v11845-test-coi-reload';" in boot
boot=boot.replace("const FLAG='mingpai-v11845-test-coi-reload';","const FLAG='mingpai-v11845-formal-coi-reload';",1)
fc=fc[:a]+boot+fc[b:]
assert "v1.18.4.5 正式版" in fc
assert "v1.18.4.5 测试版" in tc
(r/"core.html").write_text(fc)
# SW: reuse tested implementation, but keep two isolated cache namespaces.
tw=(t/"coi-serviceworker.js").read_text()
assert 'const APP_VERSION="1.18.4.5-test";' in tw
assert 'const SHELL_CACHE="mingpai-shell-v11845-bootdiag-test-r9";' in tw
fw=tw.replace('const APP_VERSION="1.18.4.5-test";',
              'const APP_VERSION="1.18.4.5";',1)
fw=fw.replace('const SHELL_CACHE="mingpai-shell-v11845-bootdiag-test-r9";',
              'const SHELL_CACHE="mingpai-shell-v11845-bootclose-formal-r9";',1)
(r/"coi-serviceworker.js").write_text(fw)
(t/"coi-serviceworker.js").write_text(
    tw.replace('const SHELL_CACHE="mingpai-shell-v11845-bootdiag-test-r9";',
               'const SHELL_CACHE="mingpai-shell-v11845-bootclose-test-r9";',1))
assert "mingpai-optin-boot-diagnosis" not in (t/"index.html").read_text()
for folder,label in [(r,"formal"),(t,"test")]:
    m=json.loads((folder/"version-v118-test.json").read_text())
    assert m["version"]==("1.18.4.5" if label=="formal" else "1.18.4.5-test")
    assert m["rules"]=="recognition-rules-v1184.json"
    for name in ["index.html","core.html"]:
        h=(folder/name).read_text()
        for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',h,re.I|re.S)):
            if js.strip():
                fp=Path("/tmp")/f"close-{label}-{name}-{i}.js";fp.write_text(js)
                subprocess.run(["node","--check",str(fp)],check=True)
    fp=Path("/tmp")/f"close-{label}-sw.js"
    fp.write_text((folder/"coi-serviceworker.js").read_text())
    subprocess.run(["node","--check",str(fp)],check=True)
assert (r/"recognition-rules-v1184.json").read_bytes()==rules0
assert (t/"recognition-rules-v1184.json").read_bytes()==rules0
print("PASS closeout: 85 rules; confirmed hints; Edge startup; diag removed; native records and dock intact")
for p in ["index.html","test-adaptive/index.html","recognition-rules-v1184.json"]:
    print("RELEASE_SHA256",p,hashlib.sha256((r/p).read_bytes()).hexdigest())
