"""Run the native EBC -> AICC product and a separate closed-form reference."""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
LAB=HERE.parents[1]
SOURCE=LAB/'LAC_REPRO_R210/BASE_R401/18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/02_FOUNDRY_ALL_PRODUCTS/products/P083_HEAG/heag.py'
spec=importlib.util.spec_from_file_location('_heag_example_product',SOURCE)
heag=importlib.util.module_from_spec(spec);sys.modules[spec.name]=heag;spec.loader.exec_module(heag)


def decision(threshold, noise_variance, cost):
    return {'action_names':['hold','act'],'action_slopes':[[0.],[1.]],'action_intercepts':[0.,-threshold],
            'future_error_relation':'independent_of_evidence',
            'channels':[{'name':'new_independent_measurement','measurement_vector':[1.],
                         'noise_variance':noise_variance,'cost':cost}]}


def normal_two_action_value(mean, variance, threshold, noise):
    scale=variance/math.sqrt(variance+noise)
    gap=mean-threshold
    z=abs(gap)/scale
    return scale*math.exp(-z*z/2)/math.sqrt(2*math.pi)-abs(gap)*.5*math.erfc(z/math.sqrt(2))


def run(output):
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('Output must be new or empty')
    output.mkdir(parents=True,exist_ok=True)
    duplicate={'evidence':{'current_estimate':0.,'current_standard_error':1.,
                         'historical':[{'name':f'view_{i}','estimate':0.,'standard_error':1.,'observation_id':'one_record'} for i in range(5)]},
               'decision':decision(0.,1.,.15)}
    public_path=LAB/'examples/correlated-evidence/report/input.json'
    public={'evidence':json.loads(public_path.read_text()),'decision':decision(.2,.01,.005)}
    cases=[('declared_copies','Aynı gözlemin beş görünümü',duplicate,
            'Tamamen sentetik: current ve tek geçmiş gözlem bağımsız. Beş geçmiş kayıt aynı gözlemin kopyaları. Gelecek ölçüm ayrı; fayda/maliyet varsayımları örnek için verildi.'),
           ('public_clustered_estimates','56 yayımlanmış tahmin, 11 bölge',public,
            'Gözlemler yayımlanmış eğitim araştırması verisi; kovaryans yayımlanmış yuvarlanmış sabit bileşenlerden. İlk satır yalnız hesaplama için current seçildi; kronolojik bir ayrım değil. 0,2 eylem eşiği, 0,1 gelecek ölçüm standart hatası ve maliyet varsayımsal. Bu, okul politikası veya denetim önerisi değildir.')]
    reports=[];checks=[]
    for name,title,config,scope in cases:
        result=heag.review_dependency(config)
        (output/(name+'-input.json')).write_text(json.dumps(config,indent=2)+'\n')
        (output/(name+'-result.json')).write_text(json.dumps(result,indent=2)+'\n')
        if name=='public_clustered_estimates':
            y=np.array([config['evidence']['current_estimate']]+[r['estimate'] for r in config['evidence']['historical']])
            cov=np.array(config['evidence']['covariance']);one=np.ones(len(y))
            for key,matrix in [('dependency_preserved',cov),('independence_assumed',np.diag(np.diag(cov)))]:
                weights=np.linalg.solve(matrix,one);variance=float(1/(one@weights));mean=float(weights@y*variance)
                expected=normal_two_action_value(mean,variance,.2,.01)
                calculated=result[key]['with_history']['ranked_channels'][0]['expected_decision_improvement']
                assert abs(calculated-expected)<1e-12
                checks.append({'case':name,'model':key,'independent_gls_mean':mean,'independent_gls_variance':variance,
                               'closed_form_information_value':expected,'actual_information_value':calculated})
        else:
            for key,variance in [('dependency_preserved',.5),('independence_assumed',1/3)]:
                expected=normal_two_action_value(0.,variance,0.,1.)
                assert abs(result[key]['with_history']['ranked_channels'][0]['expected_decision_improvement']-expected)<1e-12
                checks.append({'case':name,'model':key,'closed_form_information_value':expected})
        reports.append({'id':name,'title':title,'scope':scope,'result':result,'cost':config['decision']['channels'][0]['cost']})
    # Duplicate-invariance is tested across all 1..20 aliases, not one selected count.
    series=[]
    for count in range(1,21):
        config=copy.deepcopy(duplicate)
        config['evidence']['historical']=[{'name':f'view_{i}','estimate':0.,'standard_error':1.,'observation_id':'one_record'} for i in range(count)]
        result=heag.review_dependency(config)
        values={k:result[k]['with_history']['ranked_channels'][0]['expected_decision_improvement'] for k in ('dependency_preserved','independence_assumed')}
        assert abs(values['dependency_preserved']-normal_two_action_value(0.,.5,0.,1.))<1e-12
        series.append({'copies':count,**values})
    receipt={'status':'PASS','cases':len(cases),'independent_references':checks,'copy_sensitivity':series,
             'source_hashes':{str(p.relative_to(LAB)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE,public_path,Path(__file__))},
             'scope':'Numerical composition behavior; one synthetic identity case and existing public clustered estimates with hypothetical utilities and next-measurement precision. Full powers and published rounded covariance parameters held fixed; no refitting or real-world acquisition benefit claimed.',
             'public_sources':['https://wviechtb.github.io/metadat/reference/dat.konstantopoulos2011.html','https://www.metafor-project.org/doku.php/tips:weights_in_rma.mv_models'],
             'original_data_acquisition':'See examples/correlated-evidence/SOURCES.json: numeric table transcribed from official HTML; no new raw data collection here.'}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    payload=json.dumps(reports,ensure_ascii=False).replace('</','<\\/')
    page=r'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lab · Kanıt bağımlılığı ve ek ölçüm kararı</title><style>*{box-sizing:border-box}body{font:16px/1.6 system-ui;background:#f0f4f5;color:#18343e;margin:0}header{background:#173b45;color:white;padding:32px max(24px,calc((100% - 1120px)/2))}main{max-width:1168px;margin:auto;padding:24px}.card{background:white;border:1px solid #cedbde;border-radius:8px;padding:24px;margin-bottom:20px}.notice{background:#fff4d6;border-left:4px solid #ad791a;padding:16px}h1{margin:0;font-size:29px}h2{font-size:20px}label{display:block}select,input{font:inherit}select{padding:9px;max-width:100%}input{width:100%;margin:20px 0}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:14px;border-bottom:1px solid #dae3e5}.scroll{overflow:auto}.pick{color:#076654;font-weight:700}.stop{color:#794722;font-weight:700}a{color:#086c6c}code{overflow-wrap:anywhere}small{color:#536e78}</style><header><h1>Tekrarlanan kanıt ek ölçüm kararını değiştirebilir</h1><p>EBC geçmiş bilgiyi birleştirir; AICC yeni ölçümün karar değerini hesaplar.</p></header><main><section class="card"><label for="case">Örneği seç</label><select id="case"></select><p id="scope" class="notice"></p><label for="cost">Yeni ölçüm maliyeti: <b id="cost-label"></b> <small>(verilen eylem faydasıyla aynı birimde)</small></label><input id="cost" type="range"><p>Maliyeti değiştirdiğinde aşağıdaki net değer ve seçim güncellenir. Tahminler ve brüt bilgi değerleri gerçek Python motorundan alınmıştır.</p></section><section class="card"><h2 id="conclusion"></h2><div class="scroll"><table><thead><tr><th>Model</th><th>Tahmin / SE</th><th>Ölçümün brüt değeri</th><th>Net değer</th><th>Modelin seçimi</th></tr></thead><tbody id="rows"></tbody></table></div><p id="interval"></p><p><a id="input" href="#">Girdi</a> · <a id="result" href="#">Motor çıktısı</a> · <a href="receipt.json">Bağımsız hesap referansı ve 1–20 kopya deneyi</a></p></section><section class="card"><h2>Bu birleşim neyi varsayıyor?</h2><p>EBC'nin tahmini ve standart hatası, AICC için bir normal çalışma dağılımına çevrilir. Uyarlanan ağırlıkların kalibrasyonu kanıtlanmış değildir. Gelecek ölçüm hatasının kullanılan kanıttan bağımsız olduğu açıkça verilmelidir; bu araç benzer dosyalardan bağımsızlık veya kovaryans üretmez.</p><p>Buradaki fark, aynı veriye iki farklı bağımlılık varsayımı uygulamanın hesap sonucudur. Daha fazla kontrolün gerçekten faydalı olduğunu, geçmişin doğru olduğunu veya bir denetim görüşünü kanıtlamaz.</p><p><a href="https://wviechtb.github.io/metadat/reference/dat.konstantopoulos2011.html">Yayımlanmış veri</a> · <a href="https://www.metafor-project.org/doku.php/tips:weights_in_rma.mv_models">Sabit kovaryans referansı</a></p><code>.venv/bin/python lab.py evidence-acquisition GİRDİ.json --review</code></section></main><script>const cases=PAYLOAD;const $=s=>document.querySelector(s);const fmt=x=>x!==0&&Math.abs(x)<1e-5?Number(x).toExponential(3):Number(x).toFixed(6);const labels=['Yalnız current','Bağımlılık korunuyor','Bağımsızlık varsayılıyor'];cases.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=c.title;$('#case').append(o)});function models(c){return [c.result.dependency_preserved.current_only,c.result.dependency_preserved.with_history,c.result.independence_assumed.with_history]}function draw(){const c=cases[Number($('#case').value)],cost=Number($('#cost').value),m=models(c);$('#cost-label').textContent=fmt(cost);$('#rows').innerHTML=m.map((r,i)=>{const gross=r.ranked_channels[0].expected_decision_improvement,net=gross-cost;return `<tr><th>${labels[i]}</th><td>${fmt(r.working_mean)} / ${fmt(r.working_standard_error)}</td><td>${fmt(gross)}</td><td>${fmt(net)}</td><td class="${net>0?'pick':'stop'}">${net>0?'Yeni ölçümü seç':'Yeni ölçüm seçme'}</td></tr>`}).join('');const a=m[1].ranked_channels[0].expected_decision_improvement,b=m[2].ranked_channels[0].expected_decision_improvement;$('#conclusion').textContent=(a>cost)!==(b>cost)?'Bu maliyette bağımlılık varsayımı seçimi değiştiriyor':'Bu maliyette iki model aynı seçimi yapıyor';$('#interval').textContent=`Seçimin ayrıştığı maliyet aralığı: ${fmt(Math.min(a,b))} ≤ maliyet < ${fmt(Math.max(a,b))}. Bu aralık modelden hesaplandı; piyasa fiyatı değil.`}function select(){const c=cases[Number($('#case').value)];$('#scope').textContent=c.scope;$('#cost').min=0;$('#cost').max=Math.max(...models(c).map(m=>m.ranked_channels[0].expected_decision_improvement),c.cost)*1.2;$('#cost').step='any';$('#cost').value=c.cost;$('#input').href=c.id+'-input.json';$('#result').href=c.id+'-result.json';draw()}$('#case').addEventListener('change',select);$('#cost').addEventListener('input',draw);select();</script></html>'''
    (output/'index.html').write_text(page.replace('PAYLOAD',payload))
    print(json.dumps({'report':str(output/'index.html'),'checks':checks},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    run(parser.parse_args().output)
