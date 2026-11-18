#!/usr/bin/env python3
"""v1.18.3.2-test.4: reuse built-in floating progress for weather feedback, remove text mode label.
Apply only to perf-v11832 after test.3, leaving v1.18.3.1 formal and test-adaptive untouched."""
from pathlib import Path
import json,re,subprocess,hashlib
root=Path("app"); perf=root/"perf-v11832"; page=perf/"index.html"; core=perf/"core.html"; worker=perf/"coi-serviceworker.js"
s=page.read_text(encoding="utf-8")
assert s.count('const CLIENT_VERSION="1.18.3.2-test.3";')==1
start=s.index("    let modeMark=wrap.querySelector('.field-weather-mode');")
end=s.index("  function loadWeatherCache(){",start)
assert "modeMark.textContent=currentWeather?.manual?" in s[start:end]
assert "wrap.querySelector('.field-weather-refresh')?.after(modeMark)" in s[start:end]
s=s[:start]+"""    // Keep just the refresh icon. Avoid adding “自动/手动” text.
  }
"""+s[end:]
start=s.index("  function showWeatherFeedback(message,isError=false){")
end=s.index("  function refreshWeather(force=false){",start)
assert 'v11832WeatherFeedback' in s[start:end]
old_banner=s[start:end]
new_banner="""  // The OCR program already provides a fixed floating status bar.
  // Reuse it for weather messages instead of creating a second overlay.
  let weatherFeedbackBaseline=null,weatherFeedbackShown='',weatherFeedbackToken=0;
  function showWeatherFeedback(message,isError=false){
    const bar=d.getElementById('v118FloatingProgress');
    if(!bar)return;
    const existing=(bar.textContent||'').trim();
    // Do not take over the bar while the batch OCR queue is updating it.
    const isOcrActivity=/正在识别第|正在处理第|识别队列|批量识别中/.test(existing);
    if(isOcrActivity && existing!==weatherFeedbackShown){
      bar.title=message;
      return;
    }
    if(weatherFeedbackBaseline===null || (weatherFeedbackShown && existing!==weatherFeedbackShown)){
      weatherFeedbackBaseline={text:bar.textContent,display:bar.style.display};
    }
    const displayMessage=(isError?'⚠ ':'')+String(message||'');
    weatherFeedbackShown=displayMessage;
    bar.textContent=displayMessage;
    bar.style.display='block';
    clearTimeout(weatherFeedbackTimer);
    const token=++weatherFeedbackToken;
    weatherFeedbackTimer=setTimeout(()=>{
      if(token!==weatherFeedbackToken)return;
      if(bar.isConnected && bar.textContent===displayMessage && weatherFeedbackBaseline){
        bar.textContent=weatherFeedbackBaseline.text;
        bar.style.display=weatherFeedbackBaseline.display;
      }
      weatherFeedbackShown='';
      weatherFeedbackBaseline=null;
    },4200);
  }
"""
s=s[:start]+new_banner+s[end:]
assert 'v11832WeatherFeedback' not in s
assert "modeMark.textContent" not in s
assert "d.getElementById('v118FloatingProgress')" in s
assert 'weatherFeedbackToken' in s
s=s.replace('const CLIENT_VERSION="1.18.3.2-test.3";','const CLIENT_VERSION="1.18.3.2-test.4";',1)
s=s.replace('v1.18.3.2-test.3 性能测试版','v1.18.3.2-test.4 性能测试版')
page.write_text(s,encoding='utf-8')
c=core.read_text(encoding='utf-8')
assert 'index-B81hyAdU-v11832-viewport-test2.js' in c
assert 'v1.18.3.2-test.3 性能测试版' in c
c=c.replace('v1.18.3.2-test.3 性能测试版','v1.18.3.2-test.4 性能测试版')
c=c.replace('mingpai-v11832-test3-coi-reload','mingpai-v11832-test4-coi-reload')
c=c.replace('?v=1.18.3.2-test.3','?v=1.18.3.2-test.4')
core.write_text(c,encoding='utf-8')
w=worker.read_text(encoding='utf-8')
assert 'mingpai-shell-v11832-test3' in w
w=w.replace('mingpai-shell-v11832-test3','mingpai-shell-v11832-test4')
w=w.replace('1.18.3.2-test.3','1.18.3.2-test.4')
worker.write_text(w,encoding='utf-8')
manifest=perf/'version-v118-test.json'
m=json.loads(manifest.read_text(encoding='utf-8'))
assert m['version']=='1.18.3.2-test.3'
m['version']='1.18.3.2-test.4'
manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
formal=json.loads((root/'version-v118-test.json').read_text(encoding='utf-8'))
assert formal['version']=='1.18.3.1' and formal['mainJs']=='index-B81hyAdU-v1183-weather-test1.js'
assert json.loads((root/'test-adaptive/version-v118-test.json').read_text())['version']=='1.18.3-test'
assert "new MutationObserver(()=>{" in s and "getAllKeys()" in s
for label,html in [('outer',s),('core',c)]:
    for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
        if js.strip():
            path=Path(f'/tmp/mingpai-11832-test4-{label}-{i}.js')
            path.write_text(js,encoding='utf-8')
            subprocess.run(['node','--check',str(path)],check=True)
path=Path('/tmp/mingpai-11832-test4-sw.js')
path.write_text(w,encoding='utf-8')
subprocess.run(['node','--check',str(path)],check=True)
print('PASS test.4: top floating weather feedback, no auto/manual label; formal unchanged')
