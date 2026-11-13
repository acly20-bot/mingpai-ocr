// v1.18: Eight field corrections verified against the user's nameplate OCR texts.
// Scope is deliberately narrow: do not rewrite unrelated devices or records.
function v1188CorrectNameplate(rec){
  if(!rec)return rec;
  const raw=String(rec.raw||'');
  if(!raw.trim())return rec;
  const DR='医用数字摄影系统（DR）X射线辐射源';
  const hits=[];
  const assign=(field,value)=>{if(value&&rec[field]!==value){rec[field]=value;return true}return false};
  const mark=(label,changed)=>{if(changed)hits.push(label)};
  // 1. SONTU digital X-ray imaging: model + plate title must both agree.
  if(/SONTU\s*100\s*[-–]\s*RAD\s*\(?m\)?/i.test(raw)&&/数字化\s*X\s*射线成像系统/i.test(raw))
    mark('SONTU100 DR标准名称',assign('name',DR));
  // 2. Blue-ray 7100A: do not rely on the classifier's old DR word order.
  if(/\b7100A\b/i.test(raw)&&/数字化摄影\s*X\s*射线系统/i.test(raw))
    mark('7100A DR标准名称',assign('name',DR));
  // 3. Vehicle-mounted digital radiography: not a generic mobile fluoroscope.
  if(/XH40M\s*[-–]\s*I\b/i.test(raw)&&/数字化车载\s*X\s*射线摄影系统/i.test(raw))
    mark('XH40M-I DR标准名称',assign('name',DR));
  // 4. Mindray ME7: Chinese legal manufacturer name takes precedence.
  if(/\bME7\b/i.test(raw)&&/深圳迈瑞生物医疗电子股份有限公司/.test(raw))
    mark('ME7中文厂家优先',assign('manufacturer','深圳迈瑞生物医疗电子股份有限公司'));
  // 5. Hitachi EXAVISTA: this specific R/F plate was explicitly classified as DR.
  if(/\bEXAVISTA\b/i.test(raw)&&/(?:HITACHI|株式会社日立制作所)/i.test(raw)&&/数字\s*X\s*射线透视摄影系统/i.test(raw)){
    let changed=assign('name',DR);
    changed=assign('manufacturer','株式会社日立制作所')||changed;
    changed=assign('model','EXAVISTA')||changed;
    mark('EXAVISTA三字段纠偏',changed);
  }
  // 6. Angell DTP573 main unit: the DC-DT-3 lower plate is a separate bed.
  if(/\bDTP\s*573\b/i.test(raw)&&/数字化透视摄影\s*X\s*射线系统/i.test(raw)){
    let changed=assign('name',DR);
    changed=assign('model','DTP573')||changed;
    mark('DTP573主机优先',changed);
  }
  // 7. Siemens Definition AS: avoid taking '(128 Slice)' as the model.
  if(/\bSOMATOM\s+Definition\s+AS\b/i.test(raw)&&/(?:SIEMENS|西门子|128\s*(?:Slice|层))/i.test(raw))
    mark('Definition AS型号',assign('model','SOMATOM Definition AS'));
  // 8. Nihon Kohden ECG-1150: accessory sticker ECG-1150P is not the serial.
  if(/\bECG\s*[-–]\s*1150\b/i.test(raw)&&/上海光电医用电子仪器有限公司/.test(raw)){
    let changed=assign('manufacturer','上海光电医用电子仪器有限公司');
    const sn=raw.match(/(?:^|[\r\n])\s*SN\s*[:：]?\s*(\d{4,7}\s*[A-Z])(?=\s|$)/im);
    if(sn)changed=assign('code',sn[1].replace(/\s+/g,' ').trim().toUpperCase())||changed;
    mark('ECG-1150厂家与SN',changed);
  }
  if(hits.length)rec.classifyNote=(rec.classifyNote?rec.classifyNote+' + ':'')+hits.join(' + ');
  return rec;
}
