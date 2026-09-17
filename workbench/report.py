"""A self-contained viewer of observed dependencies and declared counterfactuals."""
import html
import json
from .methods import R207Batch
from .problems import failure_scenarios


def analyze_problem(problem):
    if len(problem.sources) > 4000:
        raise ValueError('Interactive pilot limit: 4000 source cells')
    solver = R207Batch(problem)
    scenarios = failure_scenarios(problem)
    masks = solver.solve_masks(scenarios)
    full = (1 << len(scenarios)) - 1
    single = {source: [] for source in problem.sources}
    cuts = {t: [] for t in problem.targets}
    for target, mask in masks.items():
        if not mask & 1: continue
        failed = full ^ mask
        while failed:
            bit = failed & -failed
            removed = scenarios[bit.bit_length() - 1]
            failed ^= bit
            if len(removed) == 1:
                single[next(iter(removed))].append(target)
            if 0 < len(removed) <= 2 and not any(set(old) <= removed for old in cuts[target]):
                cuts[target].append(sorted(removed))
    return {'schema_version': 1, 'problem': problem.to_dict(), 'engine': 'R207 compiled circuit + bitset evaluation',
            'circuit_nodes': solver.circuit.nodes, 'roots': {t: solver.roots[t] for t in problem.targets},
            'source_impacts': single, 'observed_cuts_up_to_two': cuts,
            'scenario_count': len(scenarios),
            'cut_scope': 'All single-source failures and at most 512 sampled source pairs. Pair lists are not exhaustive when the source count is large; larger cuts are not searched.',
            'interpretation': ('Availability under the explicitly declared support rules; not correctness of the conclusion.'
                               if problem.mode == 'declared_support' else
                               'Potential static formula dependency; not a necessary value change or an audit conclusion.')}


def write_report(analysis, path):
    payload = json.dumps(analysis, ensure_ascii=False).replace('</', '<\\/')
    page = r'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lab · Kaynak bağımlılığı</title>
<style>*{box-sizing:border-box}body{margin:0;color:#172634;background:#f5f6f7;font:15px system-ui}header{background:#142d3b;color:white;padding:28px max(24px,calc((100% - 1180px)/2))}h1{margin:0 0 8px;font-size:29px}h2{font-size:19px}p{line-height:1.6}main{max-width:1230px;margin:auto;padding:24px}.notice{border-left:4px solid #b07829;background:#fff8ed;padding:13px 18px}.grid{display:grid;grid-template-columns:360px 1fr;gap:22px;margin-top:20px}.panel{background:white;padding:20px;border:1px solid #d7dfe5;border-radius:6px}input[type=search]{width:100%;padding:10px;font:inherit;border:1px solid #b1bec7}button{font:inherit;padding:8px 12px;background:white;border:1px solid #aabdc4;border-radius:4px;cursor:pointer}label{display:flex;gap:9px;padding:10px 0;border-bottom:1px solid #edf0f1;overflow-wrap:anywhere}label input{flex-shrink:0}#sources{max-height:470px;overflow:auto}.muted{color:#61727a;font-size:13px}.target{padding:15px 0;border-bottom:1px solid #e0e6e9}.status{display:inline-block;font-size:12px;padding:4px 7px;border-radius:4px;background:#e1f3e9;color:#226242;margin-left:9px}.off{background:#f9e6dc;color:#873912}code,pre{font:12px ui-monospace,monospace;overflow-wrap:anywhere}pre{white-space:pre-wrap;background:#f3f5f6;padding:12px}details{margin-top:14px}summary{cursor:pointer;font-weight:600}table{border-collapse:collapse;width:100%;font-size:13px}td,th{text-align:left;padding:10px;border-bottom:1px solid #e0e6e9;overflow-wrap:anywhere}a{color:#13776e}#live{font-weight:600;margin:16px 0}@media(max-width:760px){.grid{grid-template-columns:1fr}#sources{max-height:230px}h1{font-size:25px}} </style>
<header><h1>Kaynaklardan biri yoksa ne değişiyor?</h1><div id="title"></div></header><main>
<p id="mode" class="notice"></p><p id="coverage"></p><p id="counts"></p>
<div class="grid"><section class="panel"><h2>Kaynakları devreden çıkar</h2><p class="muted">İşaretli kaynaklar erişilebilir kabul edilir. Değişiklik yalnız bu görünümdeki senaryoyu etkiler.</p><button id="reset">Hepsini geri getir</button><p><input type="search" id="search" aria-label="Kaynak ara" placeholder="Kaynak veya hücre ara"></p><div id="sources"></div></section>
<section class="panel"><h2>Sonuçlara etkisi</h2><p id="live" aria-live="polite"></p><div id="targets"></div><details><summary>İki kaynak birlikte kaybedilirse</summary><p class="muted">Tek kaynak kaybıyla açıklanmayan, sınanan ikili kayıplar. Büyük dosyalarda bütün çiftler denenmez.</p><div id="pairs"></div></details></section></div>
<section class="panel" style="margin-top:20px"><h2 id="extra-title"></h2><div id="extra"></div><details><summary>Dosyalar arası bağlantılar</summary><div id="workbook-links"></div></details><details id="function-ranges" hidden><summary>Formülün fiilen kullandığı aralık</summary><p class="muted">SUMIF/AVERAGEIF, üçüncü argümandaki sol üst hücreden başlayıp ilk argümanın boyutunu kullanır.</p><div id="function-range-list"></div></details><details><summary>Çözülemeyen bağlantılar</summary><div id="issues"></div></details><details><summary>Bu hesabın kapsamı ve kullanılan motor</summary><p id="interpretation"></p><ul id="limits"></ul><p class="muted">R207, mevcut lab kaynak dosyasından gerçekten çağrıldı. Bu görünüm onun derlediği AND/OR devresini değerlendirir. Ayrı benchmark, güçlü referans yöntemlerle doğruluk ve süreyi karşılaştırır.</p><pre id="rules"></pre></details></section>
</main><script>const data=PAYLOAD;
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const p=data.problem, labels=p.metadata.labels||{}, sourceIds=[...new Set(Object.values(p.bases))].sort(),enabled=new Set(sourceIds),workbook=p.mode==='static_formula_lineage';
const label=x=>labels[x]||x;
$('#title').textContent=p.metadata.title||p.id;
$('#mode').textContent=workbook?'Excel formüllerinin statik kaynak izleri. Bir hücrenin devre dışı olması, ona bağlı hesapları işaretler; sayısal sonucun yanlış olduğunu veya audit görüşünü kanıtlamaz.':'Örnek destek kuralları: bir kuralın bütün öncülleri gerekir; aynı sonuç için farklı kurallar alternatif yollardır. Bu kurallar sentetik örnekte açıkça tanımlanmıştır.';
if(workbook){$('#coverage').textContent=`${p.metadata.resolved_formula_count} / ${p.metadata.formula_count} formülün bağlantıları çözüldü. ${p.metadata.unresolved.length} formül, çözülemeyen bağlantılar nedeniyle etki hesabının dışında.`;if(p.metadata.unresolved.length)$('#coverage').className='notice';}
$('#counts').textContent=(workbook?`${p.metadata.input_files?.length||1} dosya · `:'')+`${sourceIds.length} kaynak kimliği · ${p.targets.length} sonuç · ${p.rules.length} kural · ${data.scenario_count} sınanan senaryo`;
function renderSources(){const q=$('#search').value.toLowerCase(),rows=sourceIds.filter(s=>(label(s)+' '+s).toLowerCase().includes(q));$('#sources').innerHTML=rows.slice(0,150).map(s=>`<label><input type="checkbox" data-source="${esc(s)}" ${enabled.has(s)?'checked':''}><span>${esc(label(s))}<br><small class="muted">Tek başına kaybı ${data.source_impacts[s]?.length||0} sonucu etkiler</small></span></label>`).join('')+(rows.length>150?'<p class="muted">İlk 150 gösteriliyor. Aramayla daralt.</p>':'');}
function update(){const values=[];for(const [op,arg] of data.circuit_nodes){let v;if(op==='true')v=true;else if(op==='false')v=false;else if(op==='var')v=enabled.has(arg);else if(op==='and')v=arg.every(i=>values[i]);else if(op==='or')v=arg.some(i=>values[i]);values.push(v);}const changed=p.targets.filter(t=>!values[data.roots[t]]);$('#live').textContent=`${sourceIds.length-enabled.size} kaynak devre dışı · ${changed.length} / ${p.targets.length} sonuç ${workbook?'etkilenebilir':'desteksiz kalıyor'}`;
$('#targets').innerHTML=p.targets.slice(0,200).map(t=>`<div class="target"><b>${esc(label(t))}</b><span class="status ${values[data.roots[t]]?'':'off'}">${values[data.roots[t]]?(workbook?'Referanslar erişilebilir':'Destek yolu var'):(workbook?'Referans kaybı':'Destek yolu yok')}</span>${p.metadata.formula_text?.[t]?'<pre>'+esc(p.metadata.formula_text[t])+'</pre>':''}<div class="muted">Tekil kritik kaynaklar: ${sourceIds.filter(s=>data.source_impacts[s]?.includes(t)).map(s=>esc(label(s))).join(', ')||'Yok'}</div></div>`).join('')+(p.targets.length>200?'<p>İlk 200 sonuç gösteriliyor; JSON çıktısı tam listeyi içerir.</p>':'');}
$('#sources').addEventListener('change',e=>{if(!e.target.dataset.source)return;const s=e.target.dataset.source;e.target.checked?enabled.add(s):enabled.delete(s);update()});$('#search').addEventListener('input',renderSources);$('#reset').addEventListener('click',()=>{sourceIds.forEach(s=>enabled.add(s));renderSources();update()});
const pairs=Object.entries(data.observed_cuts_up_to_two).flatMap(([t,cuts])=>cuts.filter(c=>c.length===2).map(c=>`<li>${esc(label(t))}: ${c.map(s=>esc(label(s))).join(' + ')}</li>`));$('#pairs').innerHTML=pairs.length?'<ul>'+pairs.slice(0,100).join('')+'</ul>':'<p>Yeni bir ikili kesinti bulunmadı.</p>';
$('#extra-title').textContent=workbook?'Aynı girdi hücrelerinden türeyen hesaplar':'Aynı kaynağın farklı görünümleri';
if(workbook){const groups=p.metadata.same_origin_groups||[];$('#extra').innerHTML=groups.length?'<table><thead><tr><th>Girdi kökleri</th><th>Türeyen hücreler</th></tr></thead><tbody>'+groups.slice(0,60).map(g=>`<tr><td>${g.root_cells.map(esc).join(', ')}</td><td>${g.formula_cells.map(esc).join(', ')}</td></tr>`).join('')+'</tbody></table><p class="muted">Ortak girdi, otomatik olarak yanlış hesap veya yetersiz kanıt demek değildir.</p>':'<p>Çözülen formüller arasında aynı kök kümesi bulunmadı.</p>';}else{$('#extra').innerHTML=sourceIds.map(s=>`<p><b>${esc(label(s))}</b> → ${Object.entries(p.bases).filter(([_,v])=>v===s).map(([k])=>esc(k)).join(', ')}</p>`).join('');}
const workbookLinks=p.metadata.linked_workbooks||[];$('#workbook-links').innerHTML=workbookLinks.length?'<ul>'+workbookLinks.map(l=>'<li>'+esc(l.from_workbook)+' → '+esc(l.matched_workbook)+'<br><small>'+esc(l.declared_locator)+'</small></li>').join('')+'</ul><p class="muted">Bağlantı yalnız verilen dosyalar arasında, tekil dosya adıyla eşlendi. Dosyanın özgün sürümü veya doğruluğu kanıtlanmış değildir.</p>':'<p>Bu girdide çözülen dosyalar arası bağlantı yok.</p>';
const adjustments=p.metadata.function_range_adjustments||[];if(adjustments.length){$('#function-ranges').hidden=false;$('#function-range-list').innerHTML='<table><thead><tr><th>Formül hücresi</th><th>Yazılan aralık</th><th>Kullanılan aralık</th></tr></thead><tbody>'+adjustments.map(a=>'<tr><td>'+esc(a.cell)+' · '+esc(a.function)+'</td><td>'+esc(a.declared_reference)+'</td><td>'+esc(a.effective_reference)+'</td></tr>').join('')+'</tbody></table>';}
const issues=p.metadata.unresolved||[];$('#issues').innerHTML=issues.length?'<ul>'+issues.map(i=>'<li>'+esc(i.cell)+': '+i.reasons.map(esc).join('; ')+'</li>').join('')+'</ul>':'<p>Bu girdide raporlanan çözülemeyen bağlantı yok.</p>';
$('#interpretation').textContent=data.interpretation;$('#limits').innerHTML=(p.metadata.assumptions||[]).map(x=>'<li>'+esc(x)+'</li>').join('');$('#rules').textContent=p.rules.slice(0,100).map(r=>r.head+' ← '+(r.body.join(' AND ')||'TRUE')).join('\n');renderSources();update();</script></html>'''
    path.write_text(page.replace('PAYLOAD', payload))


def write_benchmark_report(report, path):
    labels = {'and_or_forward': 'AND/OR referans', 'and_or_bitset': 'AND/OR toplu referans',
              'r207_scalar': 'R207 tekil', 'r207_bitset': 'R207 toplu'}
    rows = ''.join(f'<tr><td>{labels.get(k,k)}</td><td>{v["correct"]}</td><td>{v["errors"]}</td><td>{v["sum_case_median_ms"]:.3f}</td></tr>' for k, v in report['summary'].items())
    details = ''.join('<tr><td>'+html.escape(c['id'])+'</td><td>'+str(c['queries'])+'</td>'+''.join(f'<td>{c["methods"][k]["total_ms_median"]:.3f}</td>' for k in report['summary'])+'</tr>' for c in report['cases'])
    path.write_text(f'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lab · Bağımlılık deneyi</title><style>body{{max-width:1080px;margin:40px auto;padding:0 22px;font:15px system-ui;color:#193341}}p{{line-height:1.6}}table{{border-collapse:collapse;width:100%}}td,th{{padding:12px;border-bottom:1px solid #d9e1e5;text-align:left}}a{{color:#086c62}}</style><h1>Bağımlılık motorlarının karşılaştırması</h1><p>{len(report['cases'])} sentetik problem. Her yöntem aynı kaynak kimlikleri, destek kuralları ve kaynak kaybı senaryolarını aldı. Sonuçlar ayrı bir referans hesapla karşılaştırıldı.</p><table><tr><th>Yöntem</th><th>Doğru kontrol</th><th>Hata</th><th>Toplam süre (ms)</th></tr>{rows}</table><p>Süre, her problem için derleme + tüm sorguların tekrar medyanlarının toplamıdır. Küçük ve sıcak bir Python çalıştırmasıdır; genel hız iddiası veya istatistiksel güven aralığı değildir. Toplu referans, toplu işlemin kazancını R207'nin katkısından ayırır.</p><p>Bütün yöntemler aynı doğruluğa ulaşıyorsa R207 için doğruluk üstünlüğü gösterilmiş değildir. Gerçek auditor verisi ve kullanıcı faydası bu deneyde ölçülmedi.</p><p><a href="receipt.json">Tam kayıt</a> · <a href="predictions.csv">Her tahmin ve beklenen sonuç</a></p><h2>Problem bazında süreler</h2><table><tr><th>Problem</th><th>Sorgu</th>{''.join('<th>'+html.escape(labels[k])+'</th>' for k in report['summary'])}</tr>{details}</table></html>''')
