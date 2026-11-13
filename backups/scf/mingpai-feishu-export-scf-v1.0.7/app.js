const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const VERSION = '1.0.7';
const PORT = Number(process.env.PORT || 9000);
const ALLOWED_ORIGIN = 'https://acly20-bot.github.io';
const FEISHU_API = 'https://open.feishu.cn/open-apis';
const TOKEN_URL = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal';

const text = v => String(v ?? '').trim();
const appToken = () => text(process.env.FEISHU_APP_TOKEN);
const tableId = () => text(process.env.FEISHU_TABLE_ID);
const tmpDir = '/tmp/mingpai-feishu-export';
try { fs.mkdirSync(tmpDir, { recursive: true }); } catch {}

function corsHeaders(extra={}) {
  return {
    'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Mingpai-Key',
    'Cache-Control': 'no-store',
    ...extra
  };
}
function sendJson(res, status, obj) {
  res.writeHead(status, corsHeaders({'Content-Type':'application/json; charset=utf-8'}));
  res.end(JSON.stringify(obj));
}
function safeJson(s) { try { return JSON.parse(s); } catch { return null; } }
function readBody(req) {
  return new Promise((resolve,reject)=>{
    let data='';
    req.on('data', c => { data += c; if(data.length > 2_000_000) req.destroy(); });
    req.on('end', ()=>resolve(data));
    req.on('error', reject);
  });
}
function requireConfig() {
  const missing = ['FEISHU_APP_ID','FEISHU_APP_SECRET','MINGPAI_SHARED_KEY','FEISHU_APP_TOKEN','FEISHU_TABLE_ID']
    .filter(k => !text(process.env[k]));
  if(missing.length) throw new Error('缺少环境变量：' + missing.join('、'));
}
function requireKey(req) {
  if(text(req.headers['x-mingpai-key']) !== text(process.env.MINGPAI_SHARED_KEY)) {
    const e = new Error('共享访问密钥不正确。'); e.status = 401; throw e;
  }
}
let cachedToken = '', cachedTokenAt = 0;
async function getToken() {
  if(cachedToken && Date.now() - cachedTokenAt < 90*60*1000) return cachedToken;
  const r = await fetch(TOKEN_URL, {
    method:'POST',
    headers:{'Content-Type':'application/json; charset=utf-8'},
    body:JSON.stringify({app_id:text(process.env.FEISHU_APP_ID), app_secret:text(process.env.FEISHU_APP_SECRET)})
  });
  const raw = await r.text();
  const j = safeJson(raw) || {};
  if(!r.ok || Number(j.code||0)!==0 || !j.tenant_access_token) {
    throw new Error('获取飞书 tenant_access_token 失败：' + (j.msg || raw || r.status));
  }
  cachedToken = text(j.tenant_access_token); cachedTokenAt = Date.now(); return cachedToken;
}
async function feishu(pathname, {method='GET', body}={}) {
  let token = await getToken();
  async function once(tok) {
    const opt = {method, headers:{Authorization:`Bearer ${tok}`,'Content-Type':'application/json; charset=utf-8'}};
    if(body !== undefined) opt.body = JSON.stringify(body);
    const r = await fetch(FEISHU_API + pathname, opt);
    const raw = await r.text();
    const j = safeJson(raw) || {msg:raw};
    return {r,j};
  }
  let z = await once(token);
  if(z.r.status === 401) { cachedToken=''; token=await getToken(); z=await once(token); }
  if(!z.r.ok || Number(z.j.code||0)!==0) throw new Error(`飞书接口失败：${z.j.msg||z.j.message||z.r.status}`);
  return z.j;
}
function fieldText(v) {
  if(v==null) return '';
  if(typeof v==='string'||typeof v==='number'||typeof v==='boolean') return String(v).trim();
  if(Array.isArray(v)) return v.map(fieldText).filter(Boolean).join('、');
  if(typeof v==='object') {
    if('text' in v) return fieldText(v.text);
    if('name' in v) return fieldText(v.name);
    if('value' in v) return fieldText(v.value);
  }
  return text(v);
}
function dateText(v) {
  if(v==null || v==='') return '';
  if(typeof v==='number' || /^\d{12,13}$/.test(String(v))) {
    const d = new Date(Number(v));
    if(!Number.isNaN(d.getTime())) {
      const parts = new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(d);
      const m = Object.fromEntries(parts.map(x=>[x.type,x.value]));
      return `${m.year}-${m.month}-${m.day}`;
    }
  }
  return fieldText(v).slice(0,10).replace(/\//g,'-');
}
function parseDay(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s||''));
  if(!m) return null;
  return Date.UTC(Number(m[1]),Number(m[2])-1,Number(m[3]));
}
function fmtDay(ms) {
  const d = new Date(ms);
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth()+1).padStart(2,'0')}-${String(d.getUTCDate()).padStart(2,'0')}`;
}
async function searchExact(unitName, operatorName) {
  const u = text(unitName), op = text(operatorName);
  if(!u) throw new Error('缺少单位名称。');
  if(!op) throw new Error('缺少检定员。');
  const conditions = [
    {field_name:'单位名称', operator:'is', value:[u]},
    {field_name:'检定员', operator:'is', value:[op]}
  ];
  let pageToken='', out=[];
  for(let guard=0; guard<50; guard++) {
    const qs = new URLSearchParams({page_size:'500'});
    if(pageToken) qs.set('page_token',pageToken);
    const p = `/bitable/v1/apps/${encodeURIComponent(appToken())}/tables/${encodeURIComponent(tableId())}/records/search?${qs}`;
    const j = await feishu(p,{method:'POST',body:{filter:{conjunction:'and',conditions}}});
    for(const item of (j?.data?.items||[])) {
      const f = item.fields || {};
      const rec = {
        remoteRecordId:text(item.record_id),
        unitName:fieldText(f['单位名称']),
        dept:fieldText(f['科室']),
        date:dateText(f['检定日期']),
        operatorName:fieldText(f['检定员']),
        name:fieldText(f['设备名称']),
        manufacturer:fieldText(f['生产厂家']),
        model:fieldText(f['型号']),
        code:fieldText(f['出厂编号']),
        temperature:fieldText(f['温度（℃）']),
        humidity:fieldText(f['相对湿度（%RH）']),
        remark:fieldText(f['备注']),
        raw:fieldText(f['铭牌文本']),
        status:'confirmed'
      };
      if(text(rec.unitName) !== u) continue;
      if(text(rec.operatorName) !== op) continue;
      out.push(rec);
    }
    if(!j?.data?.has_more || !j?.data?.page_token) break;
    pageToken = text(j.data.page_token);
  }
  return out;
}
function escXml(v){return String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&apos;')}
function colName(n){let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s}
function sheetXml(rows,widths=[]){
  let body='';
  for(let r=0;r<rows.length;r++){body+=`<row r="${r+1}">`;for(let c=0;c<rows[r].length;c++){const ref=`${colName(c)}${r+1}`,v=rows[r][c]??'';body+=`<c r="${ref}" t="inlineStr"><is><t xml:space="preserve">${escXml(v)}</t></is></c>`}body+='</row>'}
  const cols=widths.length?'<cols>'+widths.map((w,i)=>`<col min="${i+1}" max="${i+1}" width="${w}" customWidth="1"/>`).join('')+'</cols>':'';
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetFormatPr defaultRowHeight="15"/>${cols}<sheetData>${body}</sheetData></worksheet>`;
}
let CRC_TABLE=null;
function crc32(bytes){if(!CRC_TABLE)CRC_TABLE=Array.from({length:256},(_,i)=>{let c=i;for(let k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;return c>>>0});let c=0xffffffff;for(const b of bytes)c=CRC_TABLE[(c^b)&255]^(c>>>8);return(c^0xffffffff)>>>0}
function u16(a,n){a.push(n&255,(n>>>8)&255)} function u32(a,n){a.push(n&255,(n>>>8)&255,(n>>>16)&255,(n>>>24)&255)}
function concat(parts){const total=parts.reduce((n,p)=>n+p.length,0),out=Buffer.alloc(total);let o=0;for(const p of parts){Buffer.from(p).copy(out,o);o+=p.length}return out}
function zipStore(files){const enc=new TextEncoder(),locals=[],centrals=[];let offset=0;const now=new Date(),tm=((now.getHours()<<11)|(now.getMinutes()<<5)|(now.getSeconds()>>1))&65535,dt=(((now.getFullYear()-1980)<<9)|((now.getMonth()+1)<<5)|now.getDate())&65535;for(const [name,data0] of files){const nameB=Buffer.from(enc.encode(name)),data=Buffer.isBuffer(data0)?data0:Buffer.from(typeof data0==='string'?enc.encode(data0):data0),crc=crc32(data),h=[];u32(h,0x04034b50);u16(h,20);u16(h,2048);u16(h,0);u16(h,tm);u16(h,dt);u32(h,crc);u32(h,data.length);u32(h,data.length);u16(h,nameB.length);u16(h,0);const hb=Buffer.from(h);locals.push(hb,nameB,data);const c=[];u32(c,0x02014b50);u16(c,20);u16(c,20);u16(c,2048);u16(c,0);u16(c,tm);u16(c,dt);u32(c,crc);u32(c,data.length);u32(c,data.length);u16(c,nameB.length);u16(c,0);u16(c,0);u16(c,0);u16(c,0);u32(c,0);u32(c,offset);const cb=Buffer.from(c);centrals.push(cb,nameB);offset+=hb.length+nameB.length+data.length}const central=concat(centrals),end=[];u32(end,0x06054b50);u16(end,0);u16(end,0);u16(end,files.length);u16(end,files.length);u32(end,central.length);u32(end,offset);u16(end,0);return concat([...locals,central,Buffer.from(end)])}
function workbookBytes(records){
  const headers=['单位名称','科室','检定日期','检定员','设备名称','生产厂家','型号','出厂编号','温度（℃）','相对湿度（%RH）','备注','状态','铭牌文本'];
  const rows=[headers,...records.map(r=>[r.unitName,r.dept,r.date,r.operatorName,r.name,r.manufacturer,r.model,r.code,r.temperature,r.humidity,r.remark,'已确认',r.raw])];
  const counts=new Map(); for(const r of records){const k=JSON.stringify([r.unitName||'未填写',r.date||'未填写',r.name||'未填写']);counts.set(k,(counts.get(k)||0)+1)}
  const summary=[['单位名称','检定日期','设备名称','台数'],...[...counts.entries()].map(([k,n])=>[...JSON.parse(k),n])];
  const types=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>`;
  const rels=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>`;
  const wb=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="数据明细" sheetId="1" r:id="rId1"/><sheet name="统计汇总" sheetId="2" r:id="rId2"/></sheets></workbook>`;
  const wbr=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/></Relationships>`;
  return zipStore([['[Content_Types].xml',types],['_rels/.rels',rels],['xl/workbook.xml',wb],['xl/_rels/workbook.xml.rels',wbr],['xl/worksheets/sheet1.xml',sheetXml(rows,[22,18,14,14,28,28,22,22,12,16,24,12,55])],['xl/worksheets/sheet2.xml',sheetXml(summary,[22,14,30,10])]]);
}
function baseUrl(req) {
  const proto = text(req.headers['x-forwarded-proto']) || 'https';
  const host = text(req.headers['x-forwarded-host']) || text(req.headers.host);
  return `${proto}://${host}`;
}
function saveDownload(buf, filename) {
  const token = crypto.randomUUID().replace(/-/g,'');
  const file = path.join(tmpDir, token + '.xlsx');
  const meta = path.join(tmpDir, token + '.json');
  fs.writeFileSync(file, buf);
  fs.writeFileSync(meta, JSON.stringify({filename, expiresAt:Date.now()+15*60*1000}));
  return token;
}
function loadDownload(token) {
  const file = path.join(tmpDir, token + '.xlsx');
  const meta = path.join(tmpDir, token + '.json');
  if(!fs.existsSync(file)||!fs.existsSync(meta)) return null;
  const m = safeJson(fs.readFileSync(meta,'utf8')) || {};
  if(Date.now() > Number(m.expiresAt||0)) { try{fs.unlinkSync(file)}catch{} try{fs.unlinkSync(meta)}catch{} return null; }
  return {buf:fs.readFileSync(file), filename:text(m.filename)||'mingpai.xlsx'};
}
async function prepareExport(req, body) {
  const filters = body?.filters || {};
  const unitName = text(filters.unitName), operatorName = text(filters.operatorName);
  let rows = await searchExact(unitName, operatorName);
  if(!rows.length) throw new Error(`飞书中没有“单位=${unitName}、检定员=${operatorName}”的已确认记录。`);
  const dated = rows.map(r=>({r,ms:parseDay(r.date)})).filter(x=>x.ms!=null);
  if(!dated.length) throw new Error('符合单位和检定员的记录中没有有效检定日期。');
  const latest = Math.max(...dated.map(x=>x.ms));
  const start = latest - 6*86400000;
  rows = dated.filter(x=>x.ms>=start && x.ms<=latest).map(x=>x.r);
  const filename = text(body?.filename) || `铭牌数据_${Date.now()}.xlsx`;
  const token = saveDownload(workbookBytes(rows), filename);
  return {downloadUrl:`${baseUrl(req)}/download?token=${encodeURIComponent(token)}`, count:rows.length, confirmed:rows.length, pending:0, startDate:fmtDay(start), endDate:fmtDay(latest), expiresIn:900};
}
async function syncEnvironment(body) {
  const recordId = text(body?.recordId);
  if(!recordId) throw new Error('缺少飞书 recordId。');
  const fields = {};
  if(body?.temperature !== undefined && body?.temperature !== null) fields['温度（℃）'] = String(body.temperature);
  if(body?.humidity !== undefined && body?.humidity !== null) fields['相对湿度（%RH）'] = String(body.humidity);
  if(!Object.keys(fields).length) return {ok:true,updated:false};
  const p=`/bitable/v1/apps/${encodeURIComponent(appToken())}/tables/${encodeURIComponent(tableId())}/records/batch_update`;
  await feishu(p,{method:'POST',body:{records:[{record_id:recordId,fields}]}});
  return {ok:true,updated:true};
}

const server = http.createServer(async (req,res)=>{
  try {
    const url = new URL(req.url, `http://${req.headers.host||'localhost'}`);
    if(req.method==='OPTIONS'){res.writeHead(204,corsHeaders());res.end();return;}
    if(req.method==='GET' && url.pathname==='/health'){
      sendJson(res,200,{ok:true,service:'mingpai-feishu-export-scf',version:VERSION,configured:Boolean(text(process.env.FEISHU_APP_ID)&&text(process.env.FEISHU_APP_SECRET)&&text(process.env.MINGPAI_SHARED_KEY)&&appToken()&&tableId()),appToken:appToken(),tableId:tableId()}); return;
    }
    if(req.method==='GET' && url.pathname==='/download'){
      const token=text(url.searchParams.get('token')); const d=loadDownload(token);
      if(!d){res.writeHead(404,corsHeaders({'Content-Type':'text/plain; charset=utf-8'}));res.end('下载链接已过期，请回到微信重新点击“下载数据”。');return;}
      res.writeHead(200,corsHeaders({'Content-Type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','Content-Disposition':`attachment; filename*=UTF-8''${encodeURIComponent(d.filename)}`,'Content-Length':d.buf.length}));
      res.end(d.buf); return;
    }
    if(req.method==='POST' && ['/prepare-export','/prepare-export-v118','/sync-environment'].includes(url.pathname)){
      requireConfig(); requireKey(req);
      const raw=await readBody(req); const body=safeJson(raw||'{}');
      if(!body) throw new Error('请求体不是有效 JSON。');
      if(url.pathname==='/sync-environment'){sendJson(res,200,await syncEnvironment(body));return;}
      const x=await prepareExport(req,body);
      sendJson(res,200,{ok:true,...x,message:`导出文件已生成：已确认 ${x.confirmed} 条。`}); return;
    }
    sendJson(res,404,{ok:false,error:'Not found'});
  } catch(e) {
    const msg=e?.message||String(e); const status=e?.status||(/共享访问密钥/.test(msg)?401:/缺少单位名称|缺少检定员|缺少飞书/.test(msg)?400:500);
    console.error('[mingpai-feishu-export]',msg);
    sendJson(res,status,{ok:false,error:msg});
  }
});
server.listen(PORT,'0.0.0.0',()=>console.log(`mingpai-feishu-export-scf ${VERSION} listening on ${PORT}`));
