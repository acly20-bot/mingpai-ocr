from pathlib import Path
import sys,hashlib,zipfile,subprocess

SOURCE='index-B81hyAdU-v118-test324.js'
TARGET='index-B81hyAdU-v118-test325.js'

def patch(src):
    data=src
    def rep(old,new,label):
        nonlocal data
        n=data.count(old)
        if n!=1: raise RuntimeError(f'{label}: expected 1 occurrence, found {n}')
        data=data.replace(old,new)
        print('PATCH',label,n)

    rep('focusRecordTop:h==="重拍照片"',
        'focusRecordTop:h==="重拍照片"||/重识别|重新识别/.test(String(h||""))',
        'retry-record-top-focus')
    rep('if(window.__v118FocusRecordTop&&!focusLatestAfterBatch){const rid=String(window.__v118FocusRecordTop);window.__v118FocusRecordTop="";',
        'const v118FinalFocusId=String(window.__v118FocusRecordTop||"");window.__v118FocusRecordTop="";if(v118FinalFocusId&&!focusLatestAfterBatch){const rid=v118FinalFocusId;',
        'clear-final-focus-marker')
    rep('d.onload=()=>{render(),U.hidden=!1,h.onpointerdown=',
        'd.onload=()=>{render(),h.onpointerdown=',
        'crop-no-early-reveal')
    rep('c("cropCancel").onclick=()=>{FA(),N(null)}}},d.onerror=',
        'c("cropCancel").onclick=()=>{FA(),N(null)}}U.hidden=!1},d.onerror=',
        'crop-reveal-after-button-layout')
    rep('actions&&custom&&(actions.innerHTML=defaultActions)',
        'actions&&custom&&(actions.innerHTML=defaultActions,actions.style.gridTemplateColumns="",delete actions.dataset.cropMode)',
        'crop-cleanup-grid-state')
    rep('if(custom&&actions){actions.style.gridTemplateColumns=',
        'if(custom&&actions){actions.dataset.cropMode=String(custom);actions.style.gridTemplateColumns=',
        'crop-prelayout-grid-mode')
    rep('data-crop-action="close">关闭</button><button class="btn light" data-crop-action="retake"',
        'data-crop-action="close">取消</button><button class="btn light" data-crop-action="retake"',
        'crop-preview-cancel')
    rep('data-crop-action="close">关闭</button>\';actions.querySelectorAll',
        'data-crop-action="close">取消</button>\';actions.querySelectorAll',
        'crop-retry-cancel')

    old='let v118StatusTimer=null;function v118StatusEl(){let e=document.getElementById("v118FloatingProgress");if(!e){e=document.createElement("div");e.id="v118FloatingProgress";e.style.cssText="position:fixed;top:calc(env(safe-area-inset-top) + 60px);left:10px;right:10px;transform:none;z-index:99990;width:auto;max-width:none;box-sizing:border-box;padding:5px 8px;border-radius:7px;background:rgba(0,109,91,.84);color:#fff;font-size:11.5px;line-height:1.3;font-weight:650;box-shadow:0 5px 18px rgba(0,0,0,.18);pointer-events:none;display:none;white-space:pre-wrap";document.body.appendChild(e)}return e}function UA(i){const p=c("progress");if(p){p.textContent="";p.style.display="none"}const e=v118StatusEl(),m=String(i||"").trim();if(v118StatusTimer){clearTimeout(v118StatusTimer);v118StatusTimer=null}e.textContent=m;e.style.display=m?"block":"none"}'
    new='let v118StatusTimer=null;function v118StatusEl(){let e=document.getElementById("v118FloatingProgress");if(!e){e=document.createElement("div");e.id="v118FloatingProgress";e.style.cssText="position:fixed;left:10px;right:10px;transform:none;z-index:99990;width:auto;max-width:none;box-sizing:border-box;padding:2px 7px;border-radius:5px;background:rgba(0,109,91,.88);color:#fff;font-size:10.5px;line-height:1.2;font-weight:650;box-shadow:0 2px 6px rgba(0,0,0,.12);pointer-events:none;display:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis";document.body.appendChild(e)}return e}function v118PlaceStatus(e){try{const hd=document.querySelector(".brand-header"),label=document.querySelector("label[for=unitName]");if(hd){const r=hd.getBoundingClientRect(),eh=e.offsetHeight||18,lt=label?.getBoundingClientRect().top??1e5;e.style.top=Math.max(0,Math.round(Math.min(r.bottom-2,lt-eh-3)))+"px";return}}catch{}e.style.top="48px"}function UA(i){const p=c("progress");if(p){p.textContent="";p.style.display="none"}const e=v118StatusEl(),m=String(i||"").trim();if(v118StatusTimer){clearTimeout(v118StatusTimer);v118StatusTimer=null}e.textContent=m;e.style.display=m?"block":"none";if(m){v118PlaceStatus(e);requestAnimationFrame(()=>v118PlaceStatus(e))}}'
    rep(old,new,'status-header-gap-position')
    assert 'focusRecordTop:h==="重拍照片"||/重识别|重新识别/' in data
    assert 'd.onload=()=>{render(),U.hidden=!1' not in data
    assert 'U.hidden=!1},d.onerror=' in data
    assert 'safe-area-inset-top) + 60px' not in data
    return data

if __name__=='__main__':
    src=Path(sys.argv[1] if len(sys.argv)>1 else SOURCE)
    out=Path(sys.argv[2] if len(sys.argv)>2 else TARGET)
    result=patch(src.read_text(encoding='utf-8'))
    out.write_text(result,encoding='utf-8')
    subprocess.run(['node','--check',str(out)],check=True)
    print('SHA256',hashlib.sha256(out.read_bytes()).hexdigest())
    zip_path=out.with_suffix('.zip')
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(out,out.name)
        z.writestr('README.txt','v1.18 test.3.2.5: upload JS to COS assets/; keep SCF v1.0.8 unchanged.\n')
    print('OUTPUT',zip_path)
