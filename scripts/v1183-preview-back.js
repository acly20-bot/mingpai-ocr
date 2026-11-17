// v1.18.3 test.2 - Android/WeChat Back closes the full-screen photo preview.
// Loaded on the outer same-origin page so Back works even when preview is inside iframe.
(function v1183PreviewBackInit(){
  "use strict";
  const frame=document.getElementById("app");
  if(!frame)return;
  let armed=false, observing=null, observedDoc=null, disposed=false;
  const getDoc=()=>{try{return frame.contentDocument}catch{return null}};
  const hasPreview=()=>!!getDoc()?.getElementById("v155ImagePreview");
  const leavePreview=()=>{
    const d=getDoc();
    const close=d?.querySelector("#v155ImagePreview [data-v155-preview='close']");
    if(close)close.click();
  };
  const marker="__mingpaiPreviewBack1183";
  const changed=()=>{
    if(disposed)return;
    const shown=hasPreview();
    if(shown&&!armed){
      try{
        history.pushState({...history.state,[marker]:true},"",location.href);
        armed=true;
      }catch(err){console.warn("Preview history state unavailable",err)}
    }else if(!shown&&armed){
      armed=false;
      // The user chose Close, Retake or OCR; consume only our own modal entry.
      // The popstate callback sees armed=false and cannot close any new modal.
      try{history.back()}catch(err){console.warn("Preview history return unavailable",err)}
    }
  };
  const onPop=()=>{
    if(armed){
      armed=false;
      if(hasPreview())leavePreview();
    }
  };
  window.addEventListener("popstate",onPop);
  const attach=()=>{
    const d=getDoc();
    if(!d||d===observedDoc)return;
    observing?.disconnect();
    if(armed){armed=false}
    observedDoc=d;
    observing=new MutationObserver(changed);
    if(d.body)observing.observe(d.body,{childList:true,subtree:true});
    changed();
  };
  frame.addEventListener("load",attach);
  attach();
})();