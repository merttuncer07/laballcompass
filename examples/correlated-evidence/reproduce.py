"""Reproduce two external arithmetic references using the repaired EBC code.

Run from any directory. Output must be new/empty; source observations remain
unchanged. The multilevel covariance parameters are published rounded fitted
values, held fixed here. This script does not refit a multilevel model.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
LAB=HERE.parents[1]
ENGINE=LAB/'LAC_REPRO_R210/BASE_R401/18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R026_S423_S424_EBC'
sys.path.insert(0,str(ENGINE))
from ebc import HistoricalEstimate, review_covariance, source_covariance


def run(output):
    folder=Path(output)
    if folder.exists() and any(folder.iterdir()):
        raise ValueError('Output folder must be new or empty')
    data=list(csv.DictReader((HERE/'dat.konstantopoulos2011.csv').open()))
    values=np.array([float(r['yi']) for r in data]);variances=np.array([float(r['vi']) for r in data])
    districts=np.array([r['district'] for r in data])
    # The published fitted covariance uses a shared district component plus
    # independent school/sampling variance. Parameters are held fixed here.
    cov=.0651*(districts[:,None]==districts[None,:])+np.diag(.0327+variances)
    se=np.sqrt(np.diag(cov))
    names=['study_'+r['study'] for r in data]
    config={'current_estimate':values[0],'current_standard_error':se[0], 'current_name':names[0],
            'historical':[{'name':names[i],'estimate':values[i],'standard_error':se[i]} for i in range(1,len(data))],
            'covariance':cov.tolist(),'covariance_names':names,'adaptive':False,'borrowing_cap_ratio':1e6}
    pooled=review_covariance(config)
    joint=pooled['joint_covariance'];diagonal=pooled['diagonal_assumption']
    # Independent inverse-matrix GLS reference (not the conditional EBC path).
    inverse=np.linalg.inv(cov);one=np.ones(len(data));normalizer=float(one@inverse@one)
    baseline={'estimate':float(one@inverse@values/normalizer),'standard_error':float(np.sqrt(1/normalizer))}
    assert abs(joint['posterior_estimate']-baseline['estimate'])<1e-10
    assert abs(joint['posterior_standard_error']-baseline['standard_error'])<1e-10
    assert abs(joint['posterior_estimate']-.1847132)<1e-4
    assert abs(joint['posterior_standard_error']-.0846)<1e-4
    assert abs(diagonal['posterior_estimate']-.127597)<1e-4
    public=json.loads((HERE/'shared-control.json').read_text())
    counts=np.array([a['responders'] for a in public['arms']],dtype=float)
    totals=np.array([a['n'] for a in public['arms']],dtype=float)
    logs=np.log(counts/(totals-counts))
    source_variances=1/counts+1/(totals-counts)
    loadings=np.array([[1,0,-1],[0,1,-1]],dtype=float)
    propagated=source_covariance(loadings,np.diag(source_variances))
    difference=np.array([1,-1])
    dependent_variance=float(difference@propagated@difference)
    diagonal_variance=float(np.diag(propagated).sum())
    direct_variance=float(source_variances[0]+source_variances[1])
    assert abs(dependent_variance-direct_variance)<1e-12
    control={'source':public['source'],'scope':public['scope'],'contrasts':(loadings@logs).tolist(),
             'contrast_covariance':propagated.tolist(),
             'difference_variance_joint':dependent_variance,'difference_variance_diagonal':diagonal_variance,
             'direct_treatment_difference_variance':direct_variance}
    receipt={'status':'PASS','external_dataset_rows':len(data),'external_groups':len(set(districts)),
             'published_estimate':.1847132,'published_se_rounded':.0846,'published_diagonal_estimate':.127597,
             'joint_estimate':joint['posterior_estimate'],'joint_se':joint['posterior_standard_error'],
             'diagonal_estimate':diagonal['posterior_estimate'],'diagonal_se':diagonal['posterior_standard_error'],
             'inverse_matrix_gls_baseline':baseline,
             'scope':'Fixed published rounded covariance parameters; no REML refit, adaptive-coverage, audit efficacy or superiority claim',
             'references':['https://www.metafor-project.org/doku.php/tips:weights_in_rma.mv_models','https://wviechtb.github.io/metadat/reference/dat.konstantopoulos2011.html',public['source']],
             'source_hashes':{str(p.relative_to(LAB)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'dat.konstantopoulos2011.csv',HERE/'shared-control.json',ENGINE/'ebc.py',ENGINE/'correlated.py']}}
    folder.mkdir(parents=True,exist_ok=True)
    for name,contents in [('input.json',config),('result.json',pooled),('shared-control-result.json',control),('receipt.json',receipt)]:
        (folder/name).write_text(json.dumps(contents,indent=2,allow_nan=False)+'\n')
    write_report(folder,pooled,control,data)
    print(json.dumps(receipt,indent=2))


def write_report(folder,pooled,control,rows):
    payload=json.dumps({'pooled':pooled,'control':control,'rows':rows}).replace('</','<\\/')
    page=r'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lab · Ortak verinin ağırlığı</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f3f6f7;color:#163641;font:16px system-ui}header{background:#173944;color:white;padding:30px max(24px,calc((100% - 1080px)/2))}main{max-width:1130px;margin:auto;padding:24px}h1{margin:0;font-size:31px}h2{font-size:21px}p{line-height:1.6}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.card{background:white;border:1px solid #d5e1e5;padding:22px;border-radius:8px;margin-bottom:20px}.big{font-size:36px;font-weight:700}.notice{background:#fff4df;border-left:4px solid #ad7c26;padding:15px}.muted{font-size:14px;color:#60757c}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;border-bottom:1px solid #dce7eb;padding:11px}select{font:inherit;padding:8px;margin:12px}a{color:#126c60}summary{cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere}@media(max-width:700px){.grid{grid-template-columns:1fr}h1{font-size:25px}}</style>
<header><h1>Ortak veri, sonucu ve belirsizliği değiştiriyor</h1><p>Lab EBC · yayımlanmış gözlemlerle kovaryans hesabı</p></header><main>
<p class="notice">56 okul çalışması, 11 bölge. Kaynakta yayımlanmış kovaryans parametreleri sabit tutularak hesap yeniden üretildi. Bu bir audit müşterisi verisi veya audit görüşü değildir; motorun sayısal doğrulamasıdır.</p>
<div class="grid"><section class="card"><h2>Kovaryans hesaba katılınca</h2><div id="joint-mean" class="big"></div><p id="joint-se"></p></section><section class="card"><h2>Yalnız ayrı varyanslar kullanılırsa</h2><div id="diagonal-mean" class="big"></div><p id="diagonal-se"></p></section></div>
<section class="card"><h2>Ağırlık hangi bölgelerde birikiyor?</h2><p>Aynı bölgedeki gözlemler modelde ortak bir değişkenlik bileşeni taşıyor. Aşağıdaki tablo, gözlem sayısıyla bilgi ağırlığının aynı şey olmadığını gösteriyor.</p><label>Gösterilen hesap <select id="model"><option value="joint_covariance">Ortak kovaryans</option><option value="diagonal_assumption">Yalnız ayrı varyanslar</option></select></label><table><thead><tr><th>Bölge</th><th>Gözlem</th><th>Toplam doğrusal ağırlık</th></tr></thead><tbody id="districts"></tbody></table></section>
<section class="card"><h2>Bağımlılık her zaman belirsizliği artırmaz</h2><p>İkinci yayımlanmış örnekte iki karşılaştırma aynı kontrol grubunu kullanıyor. Karşılaştırmaların farkını aldığımızda ortak kontrol terimi cebirsel olarak iptal oluyor. Kovaryansı sıfırlamak burada belirsizliği büyütüyor.</p><p id="control-result"></p><p class="muted">Lecrubier 1997: üç kolun yayımlanmış sayılarından log-odds varyansları için delta yöntemi. Farklı tedavi etkileri tek bir ortak etki gibi birleştirilmedi; klinik sonuç çıkarılmadı.</p></section>
<details class="card"><summary>Kaynaklar, varsayımlar ve yeniden üretim</summary><p>Bu çalıştırmada uyarlanan ağırlıklar kapalı, izin verilen güçler 1 ve ek bilgi sınırı etkisiz. Böylece EBC, standart GLS hesabına indirgenir. Ayrı matris tersleme referansıyla aynı sonuç elde edildi; GLS'ye üstünlük iddia edilmez.</p><p>Yayımlanan bölge varyansı 0,0651 ve okul varyansı 0,0327 kullanıldı. REML modeli yeniden fit edilmedi. Aralıklar kovaryans parametrelerinin tahmin belirsizliğini içermez. Kovaryanslı modelde doğrusal ağırlıklar negatif olabilir; sıfıra kırpılmaz.</p><ul><li><a href="https://www.metafor-project.org/doku.php/tips:weights_in_rma.mv_models">Metafor: çalıştırılmış örnek ve yayımlanmış sonuç</a></li><li><a href="https://wviechtb.github.io/metadat/reference/dat.konstantopoulos2011.html">56 gözlemin kaynak tablosu</a></li><li><a href="https://wviechtb.github.io/metadat/reference/dat.linde2015.html">Ortak kontrol sayılarının kaynak tablosu</a></li></ul><p><a href="receipt.json">Çalıştırma ve kaynak hash'leri</a> · <a href="input.json">Motor girdisi</a> · <a href="result.json">İki hesabın ayrıntıları</a> · <a href="shared-control-result.json">Kontrol grubu hesabı</a></p></details>
</main><script>const data=PAYLOAD;const $=s=>document.querySelector(s);for(const [prefix,key] of [['joint','joint_covariance'],['diagonal','diagonal_assumption']]){const r=data.pooled[key];$('#'+prefix+'-mean').textContent=r.posterior_estimate.toFixed(5);$('#'+prefix+'-se').textContent='Model standart hatası: '+r.posterior_standard_error.toFixed(5)}function update(){const result=data.pooled[$('#model').value],groups={};data.rows.forEach((r,i)=>{const g=groups[r.district]||(groups[r.district]={n:0,weight:0});g.n++;g.weight+=result.linear_weights[i]});$('#districts').replaceChildren();Object.entries(groups).sort((a,b)=>b[1].weight-a[1].weight).forEach(([name,g])=>{const row=document.createElement('tr');[name,g.n,(100*g.weight).toFixed(2)+'%'].forEach(x=>{const cell=document.createElement('td');cell.textContent=x;row.append(cell)});$('#districts').append(row)})}$('#model').addEventListener('change',update);update();$('#control-result').textContent='Farkın varyansı — ortak kontrol korununca: '+data.control.difference_variance_joint.toFixed(5)+'; kovaryans yok sayılınca: '+data.control.difference_variance_diagonal.toFixed(5)+'. Doğrudan iki tedavi kolundan hesap: '+data.control.direct_treatment_difference_variance.toFixed(5)+'.';</script></html>'''
    (folder/'index.html').write_text(page.replace('PAYLOAD',payload))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    run(parser.parse_args().output)
