/* v1.18.3 test.1: read-only risk hints for existing record inputs.
 * Injected into test-adaptive wrapper; no changes to OCR runtime, records,
 * event delegation, Feishu synchronization, or confirmed data.
 */
function v1183FieldRisk(field, value) {
  const v=String(value||'').replace(/\s+/g,' ').trim();
  if (!v) return '';
  const electrical=/^(?:(?:AC|DC)\s*)?\d+(?:\.\d+)?\s*(?:Hz|kHz|V|kV|W|kW|VA|kVA|mA|A|Ω)(?:\s*[/／]\s*\d+(?:\.\d+)?\s*(?:Hz|kHz|V|kV|W|kW|VA|kVA|mA|A|Ω))?$/i;
  if((field==='code'||field==='model')&&electrical.test(v))return field==='code'
    ? '疑似电压、频率或功率，不像出厂编号，请核对铭牌中的 SN、序列号或产品编码。'
    : '疑似电气参数，不像设备型号，请核对铭牌中的“型号/Model”。';
  if(field==='code'&&/^(?:粤械注准|国械注准|国食药监械|沪食药监械|医疗器械注册证|生产许可)/i.test(v))
    return '疑似医疗器械注册证号或许可证号，请核对出厂编号。';
  if(field==='manufacturer'&&/(?:[\u4e00-\u9fa5]{1,8}[路街道巷]\s*\d+\s*号|邮编\s*[:：]?\s*\d{6}|地址\s*[:：])/.test(v))
    return '厂家名称中疑似包含地址，请核对是否需要去掉地址信息。';
  return '';
}
function v1183InstallFieldReview(d) {
  const list=d.getElementById('recordList');
  if(!list || list.dataset.v1183ReviewMounted==='1')return;
  list.dataset.v1183ReviewMounted='1';
  const className='v1183-field-risk';
  const update=(card)=>{
    if(!card || !card.matches?.('article.card'))return;
    for(const field of ['code','model','manufacturer']){
      const input=card.querySelector('input[data-field="'+field+'"]');
      if(!input)continue;
      const holder=input.parentElement;
      if(!holder)continue;
      let note=holder.querySelector('.'+className+'[data-audit-field="'+field+'"]');
      const message=v1183FieldRisk(field,input.value);
      if(!message){if(note)note.remove();continue}
      if(!note){
        note=d.createElement('div');
        note.className=className;
        note.dataset.auditField=field;
        note.style.cssText='margin-top:5px;font-size:12px;line-height:1.45;color:#8a5a00;padding:6px 9px;border-radius:8px;background:#fff6df;border:1px solid #f2dfac;';
        holder.appendChild(note);
      }
      note.textContent='⚠ '+message;
    }
  };
  const scan=()=>list.querySelectorAll('article.card').forEach(update);
  // Only direct record-list replacements trigger a scan; editing the hint
  // inside a card does not create a recursive MutationObserver loop.
  new MutationObserver(records=>{
    if(records.some(r=>[...r.addedNodes].some(n=>n.nodeType===1&&n.matches?.('article.card'))))
      requestAnimationFrame(scan);
  }).observe(list,{childList:true});
  list.addEventListener('input',e=>{
    const field=e.target?.dataset?.field;
    if(['code','model','manufacturer'].includes(field)){
      const card=e.target.closest('article.card');
      if(card)update(card);
    }
  },true);
  list.addEventListener('change',e=>{
    if(['code','model','manufacturer'].includes(e.target?.dataset?.field)){
      const card=e.target.closest('article.card');
      if(card)update(card);
    }
  },true);
  scan();
}
