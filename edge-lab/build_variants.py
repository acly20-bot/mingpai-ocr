#!/usr/bin/env python3
"""Build two isolated Edge restore comparators from the pinned site artifact.

C (ui): full HTML/CSS, no OCR runtime.
D (direct): full app, load original COS runtime directly without registering
the test path's own worker or using a test-path runtime proxy.

The parent production SW can still control these same-origin pages; this
experiment does NOT claim to disable all Service Workers.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys

app = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("app")
lab = app / "edge-lab"
core_source = (app / "core.html").read_text(encoding="utf-8")
index_source = (app / "index.html").read_text(encoding="utf-8")

core_anchor = """  if(!('serviceWorker' in navigator)||location.protocol!=='https:'){
    await loadMain();return;
  }"""
assert core_source.count(core_anchor) == 1
assert index_source.count("async function run(){if(running||!navigator.onLine)return;") == 1

version_tag = re.compile(r'<script id="mingpai-open-version-check">.*?</script>', re.S)
assert len(version_tag.findall(index_source)) == 1

diagnostic = """<script id="edge-lab-lifecycle">
(function(){
 'use strict';
 const badge=document.createElement('div');
 badge.style.cssText='position:fixed;top:7px;right:8px;z-index:2147483640;background:#eafff6;color:#064a38;border:1px solid #7abfa6;border-radius:9px;max-width:225px;padding:6px 9px;font:12px/1.4 sans-serif;box-shadow:0 2px 10px #0002';
 const status=document.createElement('span');
 const btn=document.createElement('button');
 btn.type='button';btn.textContent='测试响应';
 btn.style.cssText='display:inline-block;font:12px sans-serif;margin-top:4px;padding:5px 8px;border:1px solid #61ae93;background:#fff;color:#06553c;border-radius:7px';
 let count=0;
 function refresh(ev){status.textContent='Edge '+MODE+'：'+ev+'；点击 '+count+' 次';}
 btn.addEventListener('click',()=>{count++;refresh('按钮有效')});
 badge.append(status,document.createElement('br'),btn);
 document.body.appendChild(badge);
 refresh('脚本启动');
 window.addEventListener('pageshow',e=>refresh('pageshow '+!!e.persisted));
 window.addEventListener('focus',()=>refresh('focus'));
 document.addEventListener('visibilitychange',()=>refresh(document.hidden?'隐藏':'返回可见'));
 if(document.wasDiscarded)refresh('页面被丢弃后重载');
})();
</script>
"""
for mode in ("ui", "direct"):
    dest = lab / mode
    dest.mkdir(parents=True, exist_ok=True)
    core = core_source
    # Return from the module IIFE before all SW logic. The installed
    # root-scope worker may remain the controlling parent for this path.
    if mode == "ui":
        replacement = "  // Edge C: UI-only; no OCR runtime, IndexedDB or records.\n  return;"
    else:
        replacement = "  // Edge D: direct COS runtime; no own SW registration/proxy.\n  await loadMain();return;"
        # Force COS first even if the parent-scope worker controls the page.
        order = """      const sources=controlled
        ?[MAIN,MAIN_DIRECT,MAIN_DIRECT+'&retry=1',MAIN_DIRECT+'&retry=2']
        :[MAIN_DIRECT,MAIN_DIRECT+'&retry=1',MAIN_DIRECT+'&retry=2'];"""
        assert core.count(order)==1
        core=core.replace(order,"      const sources=[MAIN_DIRECT,MAIN_DIRECT+'&retry=1',MAIN_DIRECT+'&retry=2'];")
    core=core.replace(core_anchor,replacement)
    assert core.count(replacement)==1
    # No new SW registration or background prefetch from the outer wrapper.
    index = version_tag.sub("<!-- version upgrades disabled on independent Edge diagnostic routes -->",index_source)
    head = "async function run(){if(running||!navigator.onLine)return;"
    index=index.replace(head,"async function run(){return; /* no SW upgrade on Edge diagnostic */ if(running||!navigator.onLine)return;")
    # The iframe is still a complete copy of the original app shell.
    # Add a small event badge to the outer page; do not add polling.
    index=index.replace("</body>", diagnostic.replace("MODE",repr(mode))+"</body>")
    index=index.replace("<title>设备铭牌识别｜v1.18.6 正式版</title>","<title>Edge 恢复对照 "+mode+"</title>")
    assert "edge-lab-lifecycle" in index
    assert "const sources=[MAIN_DIRECT" in core if mode=="direct" else True
    assert "navigator.serviceWorker.register('./coi-serviceworker.js',{scope:'./'})" in index
    assert "async function run(){return;" in index
    assert "v1186-direct-image-save" in core
    assert "index-B81hyAdU-v1186-test1-qqgpu-thumbfix.js" in core
    (dest/"index.html").write_text(index,encoding="utf-8")
    (dest/"core.html").write_text(core,encoding="utf-8")
    shutil.copy2(app/"version-v118-test.json",dest/"version-v118-test.json")
    # Do not copy/register coi-serviceworker.js into Edge comparator paths.
    for page in ("index.html","core.html"):
        source=(dest/page).read_text(encoding="utf-8")
        scripts=re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',source,re.S|re.I)
        for n,body in enumerate(scripts):
            if not body.strip(): continue
            temp=Path("/tmp") / ("edge-"+mode+"-"+page+"-"+str(n)+".js")
            temp.write_text(body,encoding="utf-8")
            subprocess.run(["node","--check",str(temp)],check=True)
    print("PASS Edge",mode,"full UI",len(index),"core",len(core))
