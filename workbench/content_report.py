"""A local, self-contained viewer for verifiable content comparisons."""
import json


def write_content_report(result, path):
    payload = json.dumps(result, ensure_ascii=False).replace('</', '<\\/')
    page = r'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lab · Tekrarlanan veri</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f2f5f6;color:#17333e;font:15px system-ui}header{background:#14333c;color:white;padding:30px max(24px,calc((100% - 1180px)/2))}h1{font-size:30px;margin:0 0 10px}h2{font-size:20px}p{line-height:1.55}main{max-width:1230px;padding:24px;margin:auto}.notice{background:#fff7e9;border-left:4px solid #ad7930;padding:14px}.grid{display:grid;grid-template-columns:330px minmax(0,1fr);gap:20px}.panel{background:white;border:1px solid #d5e0e4;border-radius:8px;padding:20px;margin-bottom:20px}button,input{font:inherit}button{cursor:pointer;background:white;color:inherit;border:1px solid #b6c9cf;border-radius:5px;padding:10px}input[type=search]{width:100%;padding:10px;border:1px solid #bacbd1}.block{display:block;width:100%;margin-top:9px;text-align:left;overflow-wrap:anywhere}.block[aria-pressed=true]{background:#e0f2ed;border-color:#297767}.muted{color:#58707a;font-size:13px}.stats{font-size:18px;font-weight:650}.scroll{overflow:auto;max-height:560px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid #e2eaed;padding:10px;text-align:left;overflow-wrap:anywhere}tr.diff{background:#fff0df}a{color:#107664}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer}#selection{overflow-wrap:anywhere}label{display:block;margin:14px 0}@media(max-width:800px){.grid{grid-template-columns:1fr}h1{font-size:25px}.scroll{max-height:350px}}</style>
<header><h1>Aynı veri nerede tekrar görünüyor?</h1><div id="files"></div></header><main>
<p class="notice">Eşleşen içerik, kopyalamanın yönünü veya ortak kaynağı tek başına kanıtlamaz. Aşağıdaki hücreler inceleme için yan yana getirildi; bağımsız kanıt sayısı hesaplanmadı.</p>
<p id="example-context" class="notice" hidden></p>
<section class="panel"><div id="stats" class="stats"></div><p id="coverage"></p><div id="lineage"></div></section>
<div class="grid"><section class="panel"><h2 id="blocks-heading">Eşleşen bölgeler</h2><input id="search" type="search" placeholder="Dosya veya sayfa ara" aria-label="Eşleşme ara"><div id="blocks" class="scroll"></div></section>
<section class="panel"><h2 id="selection">Bir bölge seç</h2><p id="block-stats"></p><p id="alignment" class="muted"></p><p id="unmapped" class="muted"></p><p id="impact"></p><p id="difference-impact"></p><p id="uncompared-impact"></p><label><input id="differences" type="checkbox"> Yalnız farklı veya karşılaştırılamayan hücreler</label><div class="scroll"><table><thead><tr><th>Sol hücre / değer</th><th>Sağ hücre / değer</th><th>Gözlem</th></tr></thead><tbody id="cells"></tbody></table></div><p id="cell-limit" class="muted"></p></section></div>
<section class="panel"><details><summary>Aranan eşleşmeler ve kapsam</summary><ul id="scope"></ul><p class="muted">Yeni içerik karşılaştırıcısı eşleşmeleri bulur. Formül izi varsa labın R207 motoru ayrı olarak kaynak kaybı etkisini hesaplar. İçerik benzerliği, R207 grafiğine kanıtlanmış bağlantı olarak eklenmez.</p><p><a href="content.json">Hücreler ve dosya özetleri · JSON</a></p></details></section>
</main><script>const data=PAYLOAD;
const $=s=>document.querySelector(s),esc=s=>String(s??'∅').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const loc=b=>`${b.workbook} · ${b.sheet}!${b.range??'boş'}`;
let selected=data.blocks.length?0:-1;
$('#differences').checked=selected>=0 && data.blocks[selected].different_or_uncompared_cells>0;
if(data.example_context){$('#example-context').hidden=false;$('#example-context').textContent=data.example_context;}
$('#files').textContent=data.input_files.map(f=>f.name).join(' · ');
$('#stats').textContent=`${data.input_files.length} dosya · ${data.sheet_count} sayfa · ${data.total_blocks_found} eşleşen bölge çifti`;
$('#coverage').textContent=`${data.populated_cells} dolu hücre okundu. ${data.excluded_cells.formula||0} formül içerik eşleştirmesine alınmadı. ${data.blocks_omitted} bölge çıktı sınırı nedeniyle gösterilmiyor. Bölge çiftleri örtüşebilir; sayıları bağımsız kaynak sayısı değildir.`;
if(data.method==='same_layout_v1'){
 document.title='Lab · Sürüm karşılaştırması';
 document.querySelector('h1').textContent='Aynı yerleşimde hücre karşılaştırması';
 $('#blocks-heading').textContent='Karşılaştırılan sayfalar';
 document.querySelector('.notice').textContent='Kullanıcının seçtiği aynı yerleşim varsayımı: yalnız aynı sayfa adları ve hücre adresleri karşılaştırılır. Satır/sütun kaymaları otomatik eşlenmez; ortak kaynak kanıtlanmaz.';
 $('#stats').textContent=`${data.input_files.length} dosya · ${data.sheet_count} sayfa · ${data.total_blocks_found} ortak sayfa çifti`;
 $('#coverage').textContent=`${data.populated_cells} dolu hücre okundu. ${data.blocks_omitted} ortak sayfa ve ${data.positions_omitted} konum çıktı sınırı nedeniyle gösterilmiyor. Yalnız soldaki sayfalar: ${(data.unmatched_sheets.left||[]).join(', ')||'yok'}. Yalnız sağdaki sayfalar: ${(data.unmatched_sheets.right||[]).join(', ')||'yok'}. Bu sayfalar karşılaştırılmadı. Formül metinleri ayrı karşılaştırılır; aynı metin aynı sonuç demek değildir. Hatalar karşılaştırılamayan olarak kalır.`;
}
$('#lineage').innerHTML=data.lineage_available?'<a href="lineage.html">Formül bağlantılarını ve kaynak kaybı etkisini aç →</a>':'<p class="muted">Bu girdide çözülebilen formül izi yok. Değer eşleştirmesi yine yapıldı.</p>';
function list(){const q=$('#search').value.toLowerCase();$('#blocks').innerHTML=data.blocks.map((b,i)=>({b,i})).filter(({b})=>(loc(b.left)+' '+loc(b.right)).toLowerCase().includes(q)).map(({b,i})=>`<button class="block" data-index="${i}" aria-pressed="${i===selected}"><b>${b.kind==='same_layout'?b.matching_cells+' aynı değer · '+b.matching_formula_cells+' aynı formül · '+b.changed_cells+' değişen · '+b.uncompared_cells+' bilinmeyen':b.matching_cells+' eşleşme · '+b.different_or_uncompared_cells+' fark / kapsam dışı'}</b><br>${esc(loc(b.left))}<br>↔ ${esc(loc(b.right))}</button>`).join('')||'<p>Arama kapsamında eşleşme yok. Bu, kaynakların bağımsız olduğunu göstermez.</p>';}
const sameLayout=data.method==='same_layout_v1';
const changedOrUnknown=c=>!c.equal&&c.comparison!=='same_formula';
const observations={same_value:'Aynı değer ve tür',same_formula:'Aynı formül metni · sonuç hesaplanmadı',changed_formula:'Formül metni / hücre türü değişti',changed_value:'Değer veya tür değişti',added:'Sağ dosyada eklendi',removed:'Sağ dosyada kaldırıldı',uncompared:'Karşılaştırılamadı'};
function detail(){
 if(selected<0){$('#selection').textContent=sameLayout?'Ortak sayfa bulunmadı':'Arama kapsamında bölge bulunmadı';return}
 const b=data.blocks[selected];
 $('#selection').textContent=loc(b.left)+' ↔ '+loc(b.right);
 $('#block-stats').textContent=sameLayout
   ?`${b.matching_cells} aynı değer · ${b.matching_formula_cells} aynı formül metni · ${b.changed_cells} değişen konum · ${b.uncompared_cells} karşılaştırılamayan konum`
   :`${b.matching_cells} / ${b.compared_positions} konumda değer ve tür aynı. ${b.kind==='row_alignment'?'Yalnız eşlenen satır ve sütunlar gösteriliyor; aralıktaki diğer hücreler dahil değildir.':'Eşleşen uç hücreler arasındaki alan gösteriliyor.'}`;
 $('#alignment').textContent=b.kind==='row_alignment'
   ?`${b.matching_rows} satır eşlendi (başlıklar dahil olabilir). Sütunlar: `+b.column_mapping.map(c=>c.left+' ↔ '+c.right).join(', ')
   :sameLayout?'Aynı sayfa adı ve hücre adresi varsayımı. Formül metinleri karşılaştırıldı; sonuçları hesaplanmadı.':'Sabit satır/sütun kaymasıyla eşleşen bölge.';
 $('#unmapped').textContent=b.kind==='row_alignment'?`Eşlenmeyen satır: sol ${(b.unmapped_left_rows||[]).length}${b.unmapped_left_rows?.length?' ('+b.unmapped_left_rows.slice(0,12).join(', ')+(b.unmapped_left_rows.length>12?'…':'')+')':''}, sağ ${(b.unmapped_right_rows||[]).length}${b.unmapped_right_rows?.length?' ('+b.unmapped_right_rows.slice(0,12).join(', ')+(b.unmapped_right_rows.length>12?'…':'')+')':''}. Eşlenmeyen sütunlar: sol ${(b.unmapped_left_columns||[]).join(', ')||'yok'}; sağ ${(b.unmapped_right_columns||[]).join(', ')||'yok'}. Bu alanlar eşit kabul edilmedi.`:'';
 $('#difference-impact').textContent=b.difference_formula_targets?.length
   ?(sameLayout?'Değişen hücrelere potansiyel olarak bağlı sonuçlar: ':'Farklı veya karşılaştırılamayan hücrelere bağlı sonuçlar: ')+b.difference_formula_targets.slice(0,12).join(', ')
   :sameLayout?'Değişen hücreler için çözülen grafikte bağlı sonuç bulunmadı.':'';
 $('#uncompared-impact').textContent=b.uncompared_formula_targets?.length?'Karşılaştırılamayan hücrelere potansiyel olarak bağlı sonuçlar: '+b.uncompared_formula_targets.slice(0,12).join(', '):'';
 $('#impact').textContent=b.formula_targets?.length?`Eşleşen değerlere formülle bağlı ${b.formula_targets.length} sonuç var: `+b.formula_targets.slice(0,12).join(', '):'Bu bölge için eşleşen değerlere bağlı sonuç bulunmadı.';
 const cells=b.cells.filter(c=>!$('#differences').checked||changedOrUnknown(c));
 $('#cells').innerHTML=cells.slice(0,500).map(c=>`<tr class="${changedOrUnknown(c)?'diff':''}"><td><b>${esc(c.left)}</b><br>${esc(c.left_value)}<br><small>${esc(c.left_type)}</small></td><td><b>${esc(c.right)}</b><br>${esc(c.right_value)}<br><small>${esc(c.right_type)}</small></td><td>${esc(c.comparison?observations[c.comparison]:c.equal?'Aynı değer ve tür':'Farklı / karşılaştırılmadı')}</td></tr>`).join('');
 $('#cell-limit').textContent=cells.length>500?'İlk 500 konum gösteriliyor; tam bölge JSON dosyasında.':cells.length?'':'Bu seçimde gösterilecek fark yok.';
}
$('#blocks').addEventListener('click',e=>{const button=e.target.closest('[data-index]');if(!button)return;selected=Number(button.dataset.index);list();detail()});$('#search').addEventListener('input',list);$('#differences').addEventListener('change',detail);$('#scope').innerHTML=[...data.scope,...(data.record_alignment?[data.record_alignment.scope,`${data.record_alignment.ambiguous_rows_omitted} belirsiz satır eşleştirmesi gösterilmedi.`]:[])].map(s=>'<li>'+esc(s)+'</li>').join('');list();detail();</script></html>'''
    path.write_text(page.replace('PAYLOAD', payload))
