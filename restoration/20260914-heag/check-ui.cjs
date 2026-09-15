const fs=require('node:fs'),assert=require('node:assert/strict');
const {JSDOM,VirtualConsole}=require('/tmp/lab-dom-check/node_modules/jsdom');
const file='examples/evidence-acquisition/verified/index.html';
const errors=[],virtualConsole=new VirtualConsole();virtualConsole.on('jsdomError',e=>errors.push(e.message));
const dom=new JSDOM(fs.readFileSync(file,'utf8'),{runScripts:'dangerously',virtualConsole});
const {document,Event}=dom.window,$=s=>document.querySelector(s);
assert.equal(document.querySelectorAll('#rows tr').length,3);
assert.match($('#conclusion').textContent,/seçimi değiştiriyor/);
assert.match($('#rows').textContent,/0\.162868/);
assert.match($('#rows').textContent,/0\.115165/);
$('#cost').value=0;$('#cost').dispatchEvent(new Event('input'));
assert.match($('#conclusion').textContent,/aynı seçimi/);
assert.equal(document.querySelectorAll('#rows .pick').length,3);
$('#cost').value=.3;$('#cost').dispatchEvent(new Event('input'));
assert.equal(document.querySelectorAll('#rows .stop').length,3);
$('#case').value=1;$('#case').dispatchEvent(new Event('change'));
assert.match($('#scope').textContent,/varsayımsal/);
assert.match($('#rows').textContent,/0\.184722/);
assert.match($('#rows').textContent,/0\.127597/);
assert.match($('#interval').textContent,/3\.306e-7/);
assert.match($('#conclusion').textContent,/seçimi değiştiriyor/);
for(const id of ['input','result'])assert.ok(fs.existsSync('examples/evidence-acquisition/verified/'+$('#'+id).getAttribute('href')));
assert.deepEqual(errors,[]);dom.window.close();
fs.writeFileSync('restoration/20260914-heag/ui-check.json',JSON.stringify({status:'PASS',file,
  checks:['three model rows','cost slider changes choices','public dataset selection','hypothetical-utility disclosure',
          'small positive decision threshold preserved','input/output links','no JS errors'],
  scope:'jsdom interactions, not real-browser visual or user testing'},null,2)+'\n');
console.log('PASS: cost sensitivity and public/synthetic case selector');
