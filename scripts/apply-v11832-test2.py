#!/usr/bin/env python3
"""Apply exact user-approved v1.18.3.2 test.2 UI and runtime to separate perf route."""
from pathlib import Path
import base64,zlib,hashlib,json,re,subprocess,urllib.request
site=Path('app/perf-v11832')
page=site/'index.html';core=site/'core.html';worker=site/'coi-serviceworker.js';manifest=site/'version-v118-test.json'
s=page.read_text(encoding='utf-8')
assert hashlib.sha256(s.encode()).hexdigest()=='01b9d4292757546d75755e5d59f0eeb3231dc6eee10385dde7faa557c764ff1c','unexpected perf page base'
s=s.replace("""        installWeatherChip();
        decorateCards();
      };""","""        installWeatherChip();
        setWeatherButton('manual','人工填写温湿度优先，点击↻可获取天气值');
        showWeatherFeedback('顶部温湿度已按手动值保存；点击↻可强制刷新天气。');
        decorateCards();
      };""",1)
s=s.replace("refresh.addEventListener('click',()=>{refreshWeather(true);});","refresh.addEventListener('click',()=>{refreshWeather(true);}); // explicit refresh bypasses both auto cache and manual lock",1)
needle="""    if(!hi.dataset.fitBound){hi.dataset.fitBound='1';hi.addEventListener('input',()=>fitWeatherInput(hi));}
  }
  function loadWeatherCache(){"""
assert s.count(needle)==1
s=s.replace(needle,"""    if(!hi.dataset.fitBound){hi.dataset.fitBound='1';hi.addEventListener('input',()=>fitWeatherInput(hi));}
    let modeMark=wrap.querySelector('.field-weather-mode');
    if(!modeMark){
      modeMark=d.createElement('small');modeMark.className='field-weather-mode';
      modeMark.style.cssText='font-size:9px;line-height:1.1;white-space:nowrap;opacity:.92';
      refresh.after(modeMark);
    }
    modeMark.textContent=currentWeather?.manual?'手动':validWeather(currentWeather)?'自动':'未获取';

  }
  function loadWeatherCache(){""",1)
blob='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'
weather=zlib.decompress(base64.b64decode(blob)).decode('utf-8')
a=s.index('  function refreshWeather(force=false){');b=s.index('  function syncLabel(rec){',a)
assert a>=0 and b>a
s=s[:a]+weather+s[b:]
assert hashlib.sha256(s.encode()).hexdigest()=='2e0bd936e83e6952bc8bd9c11764e86ca817efdb068267e253fed45ff4e37ee7','weather patch differs from approved source'
s=s.replace('const CLIENT_VERSION="1.18.3.2-perf";','const CLIENT_VERSION="1.18.3.2-test.2";',1).replace('v1.18.3.2 性能测试版','v1.18.3.2-test.2 性能测试版')
page.write_text(s,encoding='utf-8')
old='index-B81hyAdU-v1183-weather-test1.js'
new='index-B81hyAdU-v11832-viewport-test2.js'
url='https://mingpai-ocr-1387910526.cos.ap-guangzhou.myqcloud.com/assets/'+new
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'mingpai-perf-test2-release'}),timeout=60) as rsp:
    sha=hashlib.sha256(rsp.read()).hexdigest()
assert sha=='2bbbb9f36af3f6cce6c1484325ec98b547381a45bc6c6f6da6a155844a7b5a2c','COS test.2 JS hash mismatch: '+sha
cs=core.read_text(encoding='utf-8')
assert cs.count(old)==2
cs=cs.replace(old,new).replace('?v=1.17','?v=1.18.3.2-test.2')
cs=cs.replace('v1.18.3.2 性能测试版','v1.18.3.2-test.2 性能测试版').replace('mingpai-v11832-perf-coi-reload','mingpai-v11832-test2-coi-reload')
core.write_text(cs,encoding='utf-8')
w=worker.read_text(encoding='utf-8')
assert 'const APP_VERSION="1.18.3.2-perf"' in w
w=w.replace('const APP_VERSION="1.18.3.2-perf"','const APP_VERSION="1.18.3.2-test.2"').replace('mingpai-shell-v11832-perf','mingpai-shell-v11832-test2')
worker.write_text(w,encoding='utf-8')
m=json.loads(manifest.read_text(encoding='utf-8'))
assert m['version']=='1.18.3.2-perf' and m['mainJs']==old and m['rules']=='recognition-rules-v1183.json'
m.update(version='1.18.3.2-test.2',mainJs=new,runtimeFiles=[new])
manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
formal=json.loads(Path('app/version-v118-test.json').read_text(encoding='utf-8'))
assert formal['version']=='1.18.3.1' and formal['mainJs']==old
assert json.loads(Path('app/test-adaptive/version-v118-test.json').read_text(encoding='utf-8'))['version']=='1.18.3-test'
for label,html in [('outer',s),('core',cs)]:
 for i,code in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
  if code.strip():
   p=Path(f'/tmp/mingpai-test2-{label}-{i}.js');p.write_text(code,encoding='utf-8');subprocess.run(['node','--check',str(p)],check=True)
p=Path('/tmp/mingpai-test2-worker.js');p.write_text(w,encoding='utf-8');subprocess.run(['node','--check',str(p)],check=True)
assert 'weatherForcePending' in s and 'force?0:60*60*1000' in s and new in cs and 'recognition-rules-v1183.json' in cs
print('PASS 1.18.3.2-test.2: COS SHA256, weather force refresh, isolated release, syntax, production unchanged')
