#!/usr/bin/env python3
"""Promote the user-tested v1.18.3 test.2.1 to formal stable v1.18.3.
The existing test-adaptive endpoint becomes a stable mirror, reserved for
regression testing. Future major quick-review work must use a NEW endpoint.
No changes to 10 MB COS JS, Feishu SCF, IndexedDB schema, or OCR models.
"""
from pathlib import Path
import json,hashlib,re,shutil,subprocess

root=Path("app")
test=root/"test-adaptive"
formal_files=["index.html","core.html","coi-serviceworker.js","version-v118-test.json"]
for name in formal_files:
    assert (root/name).is_file() and (test/name).is_file(),name

prior=json.loads((root/"version-v118-test.json").read_text(encoding="utf-8"))
tm=json.loads((test/"version-v118-test.json").read_text(encoding="utf-8"))
assert prior["version"]=="1.18.2.1",prior
assert tm["version"]=="1.18.3-test.2.1",tm
assert prior["mainJs"]==tm["mainJs"]=="index-B81hyAdU-v1182-test22.js"
assert prior["rules"]=="recognition-rules-v1181.json"
assert tm["rules"]=="recognition-rules-v1183-test2.json"
source_rules=test/tm["rules"]
pack=json.loads(source_rules.read_text(encoding="utf-8"))
assert pack["schemaVersion"]==1 and len(pack["rules"])==69
rules_fingerprint=hashlib.sha256(json.dumps(pack["rules"],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
assert "v118321CanonSerialRisk" in (test/"index.html").read_text(encoding="utf-8")
assert "v1183PreviewBackInit" in (test/"index.html").read_text(encoding="utf-8")
assert "v118321PreviewCloseStyle" in (test/"core.html").read_text(encoding="utf-8")
assert "v1183-test2-rule-redirect" in (test/"core.html").read_text(encoding="utf-8")
assert 'const CLIENT_VERSION="1.18.3-test.2.1";' in (test/"index.html").read_text(encoding="utf-8")

# A deployable copy of former production is kept for reliable rollback.
previous=root/"rollback-v11821"
assert not previous.exists()
previous.mkdir()
for name in formal_files:shutil.copy2(root/name,previous/name)
assert json.loads((previous/"version-v118-test.json").read_text())["version"]=="1.18.2.1"

# Immutable copy of the proven test site (before changing release labels).
tested=root/"release-snapshots"/"v1183-test21"
tested.mkdir(parents=True,exist_ok=True)
for name in formal_files+[tm["rules"]]:shutil.copy2(test/name,tested/name)

# Canonical rule match/set data stays identical: only name+metadata change.
canonical_rules="recognition-rules-v1183.json"
stable_pack={**pack,"rulesVersion":"v1.18.3-20261118","updatedAt":"2026-11-18",
  "description":"经用户测试的 v1.18.3 稳定版：21 条原有 + 48 条针对性规则",
  "supersedes":"recognition-rules-v1181.json"}
assert hashlib.sha256(json.dumps(stable_pack["rules"],sort_keys=True,ensure_ascii=False).encode()).hexdigest()==rules_fingerprint

def build(origin,folder,version,label,scope):
    p=(origin/"index.html").read_text(encoding="utf-8")
    c=(origin/"core.html").read_text(encoding="utf-8")
    w=(origin/"coi-serviceworker.js").read_text(encoding="utf-8")
    assert "v1.18.3 test.2.1" in p and "v1.18.3 test.2.1" in c
    assert "1.18.3-test.2.1" in p and "1.18.3-test.2.1" in c
    assert "v1183PreviewBackInit" in p
    assert "v118321CanonSerialRisk" in p
    assert "v118321PreviewCloseStyle" in c
    assert "recognition-rules-v1183-test2.json" in c
    p=p.replace("v1.18.3 test.2.1",label)
    c=c.replace("v1.18.3 test.2.1",label)
    p=p.replace("1.18.3-test.2.1",version)
    c=c.replace("1.18.3-test.2.1",version)
    w=w.replace("1.18.3-test.2.1",version)
    c=c.replace("recognition-rules-v1183-test2.json",canonical_rules)
    # Important: prevent collision with the formal v1.18.2.1 cached 21 rules.
    c=c.replace("mingpai-recognition-rules-v1183-test2-cache","mingpai-recognition-rules-v1183-stable-cache")
    c=c.replace("v1183-test2-rule-redirect","v1183-stable-rule-redirect")
    c=c.replace("mingpai-v1183-test21-coi-reload",f"mingpai-v1183-{scope}-coi-reload")
    w=w.replace("mingpai-shell-v1183-test21",f"mingpai-shell-v1183-{scope}")
    assert 'const CLIENT_VERSION="'+version+'";' in p
    assert "v118321CanonSerialRisk" in p and "v1183PreviewBackInit" in p
    assert "v118321PreviewCloseStyle" in c
    assert "v1183-stable-rule-redirect" in c
    assert "recognition-rules-v1183-test2.json" not in c
    assert "recognition-rules-v1183.json" in c
    assert 'index-B81hyAdU-v1182-test22.js' in c
    assert "mingpai-shell-v1183-"+scope in w
    assert "v1183-test21-coi-reload" not in c
    assert "1.18.3-test.2.1" not in p+c+w

    (folder/"index.html").write_text(p,encoding="utf-8")
    (folder/"core.html").write_text(c,encoding="utf-8")
    (folder/"coi-serviceworker.js").write_text(w,encoding="utf-8")
    (folder/canonical_rules).write_text(json.dumps(stable_pack,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    manifest={**tm,"version":version,"rules":canonical_rules}
    (folder/"version-v118-test.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # All generated inline scripts and service workers must parse.
    for name,html in [("index",p),("core",c)]:
        for i,script in enumerate(re.findall(r"<script[^>]*>(.*?)</script>",html,re.I|re.S)):
            if script.strip():
                local=Path(f"/tmp/v1183-{scope}-{name}-{i}.js")
                local.write_text(script,encoding="utf-8")
                subprocess.run(["node","--check",str(local)],check=True)
    local=Path(f"/tmp/v1183-{scope}-sw.js")
    local.write_text(w,encoding="utf-8")
    subprocess.run(["node","--check",str(local)],check=True)
    return manifest

# Two separate SW scopes and manifest versions, identical functional code.
formal_manifest=build(tested,root,"1.18.3","v1.18.3 正式版","formal")
test_manifest=build(tested,test,"1.18.3-test","v1.18.3 稳定测试版","stabletest")
assert formal_manifest["mainJs"]==test_manifest["mainJs"]
assert formal_manifest["rules"]==test_manifest["rules"]
assert formal_manifest["version"]=="1.18.3" and test_manifest["version"]=="1.18.3-test"
assert json.loads((root/canonical_rules).read_text(encoding="utf-8"))["rules"]==json.loads((test/canonical_rules).read_text(encoding="utf-8"))["rules"]
assert "v1.18.3 正式版" in (root/"index.html").read_text(encoding="utf-8")
assert "v1.18.3 稳定测试版" in (test/"index.html").read_text(encoding="utf-8")
assert "v1183PreviewBackInit" not in (previous/"index.html").read_text(encoding="utf-8")
assert "v118321CanonSerialRisk" not in (previous/"index.html").read_text(encoding="utf-8")
assert 'index-B81hyAdU-v1182-test22.js' in (previous/"core.html").read_text(encoding="utf-8")
assert "recognition-rules-v1183.json" not in (previous/"core.html").read_text(encoding="utf-8")

stable_snapshot=root/"release-snapshots"/"v1183-stable"
stable_snapshot.mkdir(parents=True,exist_ok=True)
for name in formal_files+[canonical_rules]:
    shutil.copy2(root/name,stable_snapshot/name)
# A small release record is also copied to Pages so future build validation
# can verify its provenance without mutating existing records.
release_record={
 "version":"1.18.3",
 "sourceTestVersion":"1.18.3-test.2.1",
 "mainJs":"index-B81hyAdU-v1182-test22.js",
 "ruleCount":len(stable_pack["rules"]),
 "ruleSource":"GitHub Pages (local to each entry)",
 "ruleFingerprint":rules_fingerprint,
 "feishuSCF":"unchanged",
 "indexedDB":"unchanged",
 "formerStable":"1.18.2.1",
 "futureReviewDevelopment":"independent new route; keep formal and test-adaptive unchanged"
}
(stable_snapshot/"release-info.json").write_text(json.dumps(release_record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS v1.18.3 stable promotion: root formal + isolated stable mirror, 69 unchanged matching rules, original COS JS, SCF and local data untouched")
print("RELEASE_FINGERPRINT",rules_fingerprint)
