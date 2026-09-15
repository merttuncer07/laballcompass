const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');
const {JSDOM, VirtualConsole} = require('/tmp/lab-dom-check/node_modules/jsdom');
const base = 'examples/public-spending/verified';
const results = [];
for (const name of ['changed_unique_voucher', 'changed_repeated_voucher', 'renamed_headers_changed_amount']) {
  const file = `${base}/${name}/report/index.html`;
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => errors.push(error.message));
  const dom = new JSDOM(fs.readFileSync(file, 'utf8'), {runScripts: 'dangerously', virtualConsole});
  const {document, Event} = dom.window;
  const $ = selector => document.querySelector(selector);
  assert.equal($('#example-context').hidden, false);
  assert.match($('#example-context').textContent, /bu deney için eklendi/);
  assert.match($('#alignment').textContent, /Sütunlar:/);
  assert.ok(fs.existsSync(path.join(path.dirname(file), $('#lineage a').getAttribute('href'))));
  if (name !== 'changed_repeated_voucher') {
    assert.equal($('#differences').checked, true);
    assert.equal(document.querySelectorAll('#cells tr').length, 1);
    assert.match($('#cells').textContent, /42305\.42/);
    assert.match($('#cells').textContent, /42181\.97/);
    assert.match($('#difference-impact').textContent, /derived.xlsx::Review total!A2/);
    assert.match($('#difference-impact').textContent, /published.xlsx::Review total!A2/);
    $('#differences').checked = false;
    $('#differences').dispatchEvent(new Event('change'));
    assert.equal(document.querySelectorAll('#cells tr').length, 500);
    assert.match($('#cell-limit').textContent, /İlk 500/);
  } else {
    assert.equal($('#differences').checked, false);
    assert.match($('#unmapped').textContent, /sol 1 \(80\), sağ 1 \(2\)/);
    assert.equal($('#difference-impact').textContent, '');
  }
  $('#search').value = 'no-such-sheet';
  $('#search').dispatchEvent(new Event('input'));
  assert.equal(document.querySelectorAll('#blocks button').length, 0);
  $('#search').value = 'Transformed data';
  $('#search').dispatchEvent(new Event('input'));
  $('#blocks button').click();
  assert.equal($('#blocks button').getAttribute('aria-pressed'), 'true');
  assert.deepEqual(errors, []);
  results.push({file, status: 'PASS'});
  dom.window.close();
}
fs.writeFileSync('restoration/20260914-row-matching/ui-check.json', JSON.stringify({
  status: 'PASS', scope: 'jsdom interaction; no real-browser visual verification',
  checks: ['synthetic transformation notice', 'reordered column display', 'changed amount shown initially',
           'both formula impacts', 'unmatched rows visible', 'filter and selection', '500-cell disclosure', 'lineage link exists', 'no JS errors'],
  reports: results
}, null, 2)+'\n');
console.log('PASS: three reports, difference and ambiguity views, search/selection');
