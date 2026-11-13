#!/usr/bin/env python3
"""Minimal test.3.2.6 WeChat re-recognition scroll fix, based on test325 COS JS."""
from pathlib import Path
import hashlib
import sys
import subprocess
import zipfile

SRC="index-B81hyAdU-v118-test325.js"
DST="index-B81hyAdU-v118-test326.js"

def patch(source: str) -> str:
    data=source
    def rep(old, new, label):
        nonlocal data
        count=data.count(old)
        if count!=1:
            raise RuntimeError(f"{label}: expected exactly one match, got {count}")
        data=data.replace(old,new,1)
        print("PASS patch:",label)

    anchor='async function enqueueExistingV9(i,N,U,h="重新识别"){'
    helper='''function v118RetryStatusNoRender(rec){try{
const card=v151FindRecordCard(rec.id);
if(card){const badge=card.querySelector(".cardhead .badge");if(badge){badge.textContent="待审核";badge.classList.remove("ok")}
const toggle=card.querySelector('button[data-action="toggle"]');if(toggle){toggle.textContent="确认记录";toggle.classList.remove("light");toggle.classList.add("secondary")}}
v11712RefreshCounts();
const running=c("queueRunningPill"),waiting=c("queueWaitingPill"),failed=c("queueFailedPill");
if(running)running.textContent="识别中："+v.filter(v112Running).length;
if(waiting)waiting.textContent="等待："+v.filter(v112Waiting).length;
if(failed)failed.textContent="失败："+v.filter(v112Failed).length;
}catch(e){console.warn("重识别状态局部更新失败",e)}}
'''
    rep(anchor,helper+anchor,"inject-inline-status-helper")

    rep(
        'await PA(i),await AI(),v151KeepScroll(v151Y),photoQueueV9.push({file:N,record:i,mode:U,label:h,queuedAt:Date.now(),focusRecordTop:',
        'await PA(i);if(h==="重拍照片"){await AI();v151KeepScroll(v151Y)}else v118RetryStatusNoRender(i);photoQueueV9.push({file:N,record:i,mode:U,label:h,queuedAt:Date.now(),focusRecordTop:',
        "enqueue-retry-no-list-rebuild"
    )
    tick=chr(96)
    prefix='N.error='+tick+'识别中：'+chr(36)+'{i.label}'+tick+',await PA(N),'
    rep(
        prefix+'CI(),v151KeepScroll(v151Y),UA(',
        prefix+'i.focusRecordTop&&i.label!=="重拍照片"?v118RetryStatusNoRender(N):(CI(),v151KeepScroll(v151Y)),UA(',
        "start-retry-no-list-rebuild"
    )
    rep(
        'try{await AI()}catch{}if(i.focusRecordTop){window.__v118FocusRecordTop=String(N.id)}else v151KeepScroll(v151Y);',
        'if(!(i.focusRecordTop&&i.label!=="重拍照片"))try{await AI()}catch{}if(i.focusRecordTop){window.__v118FocusRecordTop=String(N.id)}else v151KeepScroll(v151Y);',
        "finish-retry-single-list-rebuild"
    )

    assert data.count("function v118RetryStatusNoRender(rec)") == 1
    assert data.count("async function enqueueExistingV9(")==1
    assert data.count("async function runPhotoQueueV9(")==1
    assert "if(focusLatestAfterBatch)" in data
    assert "const v118FinalFocusId=" in data
    assert "U.hidden=!1},d.onerror=" in data
    assert "v118PlaceStatus" in data
    print("PASS structural checks: new-photo, final focus, crop and floating status retained")
    return data

def main():
    src=Path(sys.argv[1] if len(sys.argv)>1 else SRC)
    dst=Path(sys.argv[2] if len(sys.argv)>2 else DST)
    data=patch(src.read_text(encoding="utf-8"))
    dst.write_text(data,encoding="utf-8")
    subprocess.run(["node","--check",str(dst)],check=True)
    print("PASS node --check")
    print("SHA256",hashlib.sha256(dst.read_bytes()).hexdigest())
    out=Path("mingpai-v1.18-test.3.2.6-COS.zip")
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        z.write(dst,dst.name)
        z.writestr("README.txt",
                   "v1.18 test.3.2.6 WeChat re-recognition no-intermediate-redraw fix.\n"
                   "Upload index-B81hyAdU-v118-test326.js to Tencent COS assets/.\n"
                   "SCF 1.0.8 and stable v1.17 unchanged.\n")
    print("PASS ZIP",out,out.stat().st_size)

if __name__=="__main__":
    main()
