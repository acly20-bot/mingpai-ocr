#!/usr/bin/env python3
"""v1.18.3 test.2.1: preview Close color on first frame; honest Canon serial warning.
Runs only after test.2. Leaves production, COS and all saved records unchanged.
"""
from pathlib import Path
import json,re,subprocess

site=Path("app/test-adaptive")
pfile=site/"index.html"
cfile=site/"core.html"
swfile=site/"coi-serviceworker.js"
mfile=site/"version-v118-test.json"
p=pfile.read_text(encoding="utf-8")
c=cfile.read_text(encoding="utf-8")
w=swfile.read_text(encoding="utf-8")
m=json.loads(mfile.read_text(encoding="utf-8"))
assert m["version"]=="1.18.3-test.2"
assert m["rules"]=="recognition-rules-v1183-test2.json"
assert m["mainJs"]=="index-B81hyAdU-v1182-test22.js"
assert "function v1183FieldRisk(" in p
assert "function v1183InstallFieldReview(" in p
assert "const message=v1183FieldRisk(field,input.value);" in p
assert "v1183PreviewBackInit" in p
assert "v1183-test2-rule-redirect" in c
assert "v118321CanonSerialRisk" not in p
assert "v118321PreviewCloseStyle" not in c

# This Canon label is a SUP.SYMBOL / printing code, NOT proof of serial.
# Correct serial N511843213 is absent from the user's new OCR text.
# Do not populate it automatically across other machines of same model.
risk=r"""
function v118321CanonSerialRisk(card,field,value) {
  if(field!=='code')return '';
  const model=String(card?.querySelector('input[data-field="model"]')?.value||'');
  if(!/(?:TUS\s*[-–]\s*A300|APLIO\s*300)/i.test(model))return '';
  const code=String(value||'').replace(/\s+/g,'').trim();
  if(!/^4M30[-–]92129(?:[°*]?B)?$/i.test(code))return '';
  return '此编号疑似佳能标签印刷代码，而非主设备制造号码。当前 OCR 未读出“制造号码”后的编号；请裁剪放大该位置重新识别，核对后再确认。';
}
"""
p=p.replace("function v1183InstallFieldReview(d) {",risk+"\nfunction v1183InstallFieldReview(d) {",1)
p=p.replace("const message=v1183FieldRisk(field,input.value);",
            "const message=v1183FieldRisk(field,input.value)||v118321CanonSerialRisk(card,field,input.value);",1)

# The existing wrapper asynchronously assigns this exact red style on
# the 2nd render; declare it early so there is no white-to-red flash.
style="""<style id="v118321PreviewCloseStyle">
#v155ImagePreview [data-v155-preview="close"]{
  background:#fff1f1!important;
  color:#a33!important;
  border:1px solid #efb5b5!important;
  border-radius:10px!important;
  font-weight:700!important;
}
</style>
"""
assert c.count("<head>")==1
c=c.replace("<head>","<head>\n"+style,1)

p=p.replace("v1.18.3 test.2","v1.18.3 test.2.1")
p=p.replace("1.18.3-test.2","1.18.3-test.2.1")
p=p.replace("remote.replace(/-test(?:\\.\\d+)?$/, '')",
            "remote.replace(/-test(?:\\.\\d+)*$/, '')")
c=c.replace("v1.18.3 test.2","v1.18.3 test.2.1")
c=c.replace("1.18.3-test.2","1.18.3-test.2.1")
c=c.replace("mingpai-v1183-test2-coi-reload","mingpai-v1183-test21-coi-reload")
w=w.replace("mingpai-shell-v1183-test2","mingpai-shell-v1183-test21")
w=w.replace('const APP_VERSION="1.18.3-test.2"','const APP_VERSION="1.18.3-test.2.1"')
m["version"]="1.18.3-test.2.1"
pfile.write_text(p,encoding="utf-8")
cfile.write_text(c,encoding="utf-8")
swfile.write_text(w,encoding="utf-8")
mfile.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Validate actual generated JS, guard untouched production and original 69 rules.
assert "v1.18.3 test.2.1" in p
assert 'const CLIENT_VERSION="1.18.3-test.2.1";' in p
assert "v118321PreviewCloseStyle" in c
assert "v1183PreviewBackInit" in p
assert "v1183-test2-rule-redirect" in c
pack=json.loads((site/"recognition-rules-v1183-test2.json").read_text(encoding="utf-8"))
assert len(pack["rules"])==69
assert "N511843213" not in risk   # No blind per-model serial substitution.
assert "v1.18.2.1 正式版" in Path("app/index.html").read_text(encoding="utf-8")
assert "v118321CanonSerialRisk" not in Path("app/index.html").read_text(encoding="utf-8")
assert "v118321PreviewCloseStyle" not in Path("app/core.html").read_text(encoding="utf-8")
for name,source in [("wrapper",p),("core",c)]:
  for i,script in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',source,re.I|re.S)):
    if not script.strip():continue
    tmp=Path(f"/tmp/v118321-{name}-{i}.js")
    tmp.write_text(script,encoding="utf-8")
    subprocess.run(["node","--check",str(tmp)],check=True)
swtest=Path("/tmp/v118321-sw.js")
swtest.write_text(w,encoding="utf-8")
subprocess.run(["node","--check",str(swtest)],check=True)

# Test targeted warning in a JS VM.
risktest=Path("/tmp/v118321-test.js")
risktest.write_text("""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const s=fs.readFileSync('app/test-adaptive/index.html','utf8');
const block=s.match(/function v118321CanonSerialRisk\\([\\s\\S]*?\\n}\\n/);
assert(block);
const ctx={};vm.runInNewContext(block[0],ctx);
const f=ctx.v118321CanonSerialRisk;
const card=model=>({querySelector:()=>({value:model})});
assert(f(card('APLIO 300 TUS-A300'),'code','4M30-92129'));
assert(f(card('TUS-A300'),'code','4M30-92129°B'));
assert(!f(card('APLIO 300 TUS-A300'),'code','N511843213'));
assert(!f(card('Voluson E10'),'code','4M30-92129'));
assert(!f(card('TUS-A300'),'model','4M30-92129'));
console.log('PASS Canon A300 warning scopes to wrong OCR code only');
""",encoding="utf-8")
subprocess.run(["node",str(risktest)],check=True)
print("PASS isolated v1.18.3 test.2.1: red button consistent, Canon OCR missing-SN warning, formal unchanged; 69 rules retained")
