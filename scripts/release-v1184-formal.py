#!/usr/bin/env python3
"""Promote verified v1.18.3.2-test.4 to 1.18.4 formal and test, adding six
strictly scoped OCR rule corrections. No COS/SCF changes or OCR binary rebuild."""
from pathlib import Path
import json,hashlib,shutil,re,subprocess
root=Path('app')
perf=root/'perf-v11832'
test=root/'test-adaptive'
files=['index.html','core.html','coi-serviceworker.js','version-v118-test.json']
for name in files+['recognition-rules-v1183.json']:
    assert (perf/name).is_file(),name
manifest=json.loads((perf/'version-v118-test.json').read_text(encoding='utf-8'))
assert manifest['version']=='1.18.3.2-test.4',manifest
main=manifest['mainJs']
assert main=='index-B81hyAdU-v11832-viewport-test2.js',main
assert manifest['rules']=='recognition-rules-v1183.json',manifest
original=json.loads((perf/manifest['rules']).read_text(encoding='utf-8'))
assert original['schemaVersion']==1 and len(original['rules'])==69
prior=json.loads((root/'version-v118-test.json').read_text(encoding='utf-8'))
assert prior['version']=='1.18.3.1',prior
assert json.loads((test/'version-v118-test.json').read_text())['version']=='1.18.3-test'
# Copy immutable previous releases to preserve direct rollback.
backup=root/'release-snapshots'/'v1184-before'
assert not backup.exists()
backup.mkdir(parents=True)
for kind,src in [('formal',root),('test',test),('validated-perf',perf)]:
    dst=backup/kind;dst.mkdir()
    for name in files+['recognition-rules-v1183.json']:
        if (src/name).exists():shutil.copy2(src/name,dst/name)
source={name:(perf/name).read_bytes() for name in files}
source_hash=hashlib.sha256(source['index.html']).hexdigest()
rule_records=[]
def rule(key,all_terms,fields,note,any_terms=()):
    match={'containsAll':list(all_terms)}
    if any_terms:match['containsAny']=list(any_terms)
    rule_records.append({'id':'v1184-case-'+key,'priority':14000+len(rule_records)+1,
       'match':match,'set':fields,'note':note})
# Each match uses a distinctive device/model marker, not manufacturer alone.
rule('01-morita',['Veraviewepocs','X550'],
     {'name':'医用诊断全景牙科X射线辐射源'},'森田 X550 设备名称')
rule('02-esco',['ESCO','AC2-4S1'],
     {'manufacturer':'新加坡艺思高'},'ESCO AC2-4S1 厂家；覆盖旧 ESCO 缩写规则')
rule('03-philips-model',['PrimaryDiagnost DR'],
     {'model':'PrimaryDiagnost DR'},'PrimaryDiagnost DR 电气参数误入型号')
rule('03-philips-serial',['PrimaryDiagnost DR','160072'],
     {'model':'PrimaryDiagnost DR','code':'160072'},'PrimaryDiagnost DR 编号需原文出现 160072 才回填')
rule('04-sorvall',['Sorvall ST 16R'],
     {'model':'Sorvall ST 16R','manufacturer':'热电实验设备有限公司奥斯特罗德分公司'},'Sorvall ST 16R 制冷参数及备案人前缀')
rule('05-brivo',['Brivo OEC 785'],
     {'manufacturer':'北京通用电气华伦医疗设备有限公司'},'Brivo OEC 785 注册人前缀')
rule('06-primedic',['PRIMEDIC','Defi-B','M110'],
     {'name':'心脏除颤器','manufacturer':'METRAX GmbH'},'PRIMEDIC Defi-B M110 厂家与设备名称')
assert len(rule_records)==7
ids=[v['id'] for v in rule_records]
assert len(ids)==len(set(ids))
assert not set(ids)&{v['id'] for v in original['rules']}
pack={**original,'rulesVersion':'v1.18.4-20261118',
 'updatedAt':'2026-11-18',
 'description':'v1.18.4：沿用 v1.18.3 的69条规则，新增6例设备的7条精确匹配规则',
 'supersedes':'recognition-rules-v1183.json',
 'rules':rule_records+original['rules']}
assert len(pack['rules'])==76
def hit(r,txt):
    m=r['match'];up=txt.upper()
    return all(term.upper() in up for term in m.get('containsAll',[])) and (not m.get('containsAny') or any(term.upper() in up for term in m['containsAny']))
fixtures=[
 ('MORITA Veraviewepocs X550 数字化口腔全景', 'name','医用诊断全景牙科X射线辐射源'),
 ('ESCO Model AC2-4S1 Manufacturer Esco/', 'manufacturer','新加坡艺思高'),
 ('PHILIPS PrimaryDiagnost DR 1N~ 230V 50/60Hz','model','PrimaryDiagnost DR'),
 ('PHILIPS PrimaryDiagnost DR 编号 160072 301234347','code','160072'),
 ('Thermo Fisher Sorvall ST 16R Refrigerant R-134a','manufacturer','热电实验设备有限公司奥斯特罗德分公司'),
 ('Brivo OEC 785 注册人：北京通用电气华伦医疗设备有限公司','manufacturer','北京通用电气华伦医疗设备有限公司'),
 ('PRIMEDIC Defi-B (M110) GmbH','manufacturer','METRAX GmbH'),
 ('PRIMEDIC Defi-B (M110) 除颤仪','name','心脏除颤器')]
for raw,field,expected in fixtures:
    matching=[r for r in sorted(pack['rules'],key=lambda v:-v.get('priority',0)) if hit(r,raw)]
    assert matching and matching[0]['set'].get(field)==expected,(raw,field,matching[:2])
negative=[
 ('ESCO other model unrelated', 'v1184-case-02-esco'),
 ('PHILIPS other device 160072', 'v1184-case-03-philips-serial'),
 ('Thermo Fisher unrelated centrifuge', 'v1184-case-04-sorvall'),
 ('General Electric Brivo 100', 'v1184-case-05-brivo')]
for raw,key in negative:
    assert not any(r['id']==key and hit(r,raw) for r in rule_records),(raw,key)
rules_name='recognition-rules-v1184.json'
for target,version,label,scope in [
 (root,'1.18.4','v1.18.4 正式版','formal'),
 (test,'1.18.4-test','v1.18.4 测试版','test')]:
    p=source['index.html'].decode('utf-8')
    c=source['core.html'].decode('utf-8')
    w=source['coi-serviceworker.js'].decode('utf-8')
    assert 'const CLIENT_VERSION="1.18.3.2-test.4";' in p
    assert 'v1.18.3.2-test.4 性能测试版' in p+c
    assert main in c and 'recognition-rules-v1183.json' in c
    assert 'mingpai-shell-v11832-test4' in w
    p=p.replace('const CLIENT_VERSION="1.18.3.2-test.4";','const CLIENT_VERSION="'+version+'";')
    p=p.replace('v1.18.3.2-test.4 性能测试版',label)
    c=c.replace('v1.18.3.2-test.4 性能测试版',label)
    c=c.replace('recognition-rules-v1183.json',rules_name)
    # Avoid collision with previously installed v1.18.3 rules cache.
    c=c.replace('mingpai-recognition-rules-v1183-stable-cache','mingpai-recognition-rules-v1184-'+scope+'-cache')
    c=c.replace('mingpai-v11832-test4-coi-reload','mingpai-v1184-'+scope+'-coi-reload')
    c=c.replace('v1183-stable-rule-redirect','v1184-'+scope+'-rule-redirect')
    c=c.replace('?v=1.18.3.2-test.4','?v='+version)
    w=w.replace('mingpai-shell-v11832-test4','mingpai-shell-v1184-'+scope)
    w=w.replace('1.18.3.2-test.4',version)
    assert 'const CLIENT_VERSION="'+version+'";' in p
    assert 'mingpai-shell-v1184-'+scope in w
    assert main in c
    assert rules_name in c
    assert 'getAllKeys()' in p and 'WEATHER_TTL_MS' in p
    assert 'v118FloatingProgress' in p
    assert 'recognition-rules-v1183.json' not in c
    for name,content in [('index.html',p),('core.html',c),('coi-serviceworker.js',w)]:
        (target/name).write_text(content,encoding='utf-8')
    target_manifest={**manifest,'version':version,'rules':rules_name}
    (target/'version-v118-test.json').write_text(json.dumps(target_manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (target/rules_name).write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for filename,html in [('index',p),('core',c)]:
        for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',html,re.I|re.S)):
            if js.strip():
                dst=Path('/tmp')/('v1184-'+scope+'-'+filename+'-'+str(i)+'.js')
                dst.write_text(js,encoding='utf-8')
                subprocess.run(['node','--check',str(dst)],check=True)
    swfile=Path('/tmp')/('v1184-'+scope+'-sw.js')
    swfile.write_text(w,encoding='utf-8')
    subprocess.run(['node','--check',str(swfile)],check=True)
    assert hashlib.sha256((target/'index.html').read_bytes()).hexdigest()!=source_hash
assert json.loads((root/'version-v118-test.json').read_text())['mainJs']==json.loads((test/'version-v118-test.json').read_text())['mainJs']
assert json.loads((root/rules_name).read_text())['rules']==json.loads((test/rules_name).read_text())['rules']
assert hashlib.sha256((perf/'index.html').read_bytes()).hexdigest()==source_hash
assert json.loads((perf/'version-v118-test.json').read_text())['version']=='1.18.3.2-test.4'
print('PASS 1.18.4 formal and test: 69 base + 7 targeted rules; 8 positive and 4 negative fixtures; validated performance route unchanged; syntax passed')
