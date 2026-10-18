import {chromium} from '@playwright/test';
import {readFile,writeFile,mkdir,rename} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';

const out=resolve('docs/maps/heron-reach-32/blueprints');
const sheets=JSON.parse(await readFile(out+'/sheets.json','utf8'));
const temp=resolve('test-results/blueprints');await mkdir(temp,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const svgs=[];const errors=[];const overflow=[];
try{
 const page=await browser.newPage({viewport:{width:2000,height:1413},deviceScaleFactor:1});
 page.on('pageerror',e=>errors.push(e.message));
 for(const sheet of sheets){
  const svg=await readFile(out+'/'+sheet.file+'.svg','utf8');svgs.push(svg);
  await page.setContent('<style>body{margin:0}svg{display:block;width:2000px;height:auto}</style>'+svg);
  const problems=await page.locator('svg').evaluate(svg=>[...svg.querySelectorAll('text')].flatMap(t=>{
   const b=t.getBoundingClientRect(),s=svg.getBoundingClientRect();
   return b.left<s.left||b.top<s.top||b.right>s.right+1||b.bottom>s.bottom+1?[t.textContent]:[];
  }));
  if(problems.length)overflow.push({sheet:sheet.id,problems});
  await page.locator('svg').screenshot({path:out+'/'+sheet.file+'.png'});
  await page.setContent('<style>@page{size:841mm 594mm;margin:0}body{margin:0}svg{display:block;width:841mm;height:594mm}</style>'+svg);
  await page.pdf({path:temp+'/'+sheet.id+'.pdf',preferCSSPageSize:true,printBackground:true});
 }
 const html=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ONSITE / Heron Reach / B01 blueprints</title><style>
 *{box-sizing:border-box}body{margin:0;background:#102333;color:#eef4f7;font:16px Arial,sans-serif}header{padding:24px;border-bottom:1px solid #486172}h1{margin:0 0 10px;font-size:26px}header p{max-width:1000px;line-height:1.5}a{color:#9cdeea}nav{display:flex;gap:8px;flex-wrap:wrap;padding:16px}button{padding:10px;border:1px solid #6f8798;background:#1d3d52;color:white;cursor:pointer}button[aria-pressed=true]{background:#e5b15c;color:#102333}main{padding:16px}article{display:none}article.active{display:block}article svg{width:100%;height:auto;background:white}footer{padding:24px;font-size:14px}@media print{@page{size:841mm 594mm;margin:0}header,nav,footer{display:none}body,main{padding:0;margin:0}article{display:block;break-after:page}article:last-child{break-after:auto}article svg{width:841mm;height:594mm}}
 </style><header><h1>ONSITE / HERON REACH — B01 BLUEPRINTS</h1><p>17 dimensioned A1 sheets for Blender construction. Proposed game environment; current playable unchanged. Print PDF at 100% on A1. Use the machine-readable contract for exact coordinates.</p><a href="ONSITE-HERON-REACH-B01-BLUEPRINTS.pdf">Download drawing book</a> · <a href="CLAUDE-BUILD-BRIEF.md">Claude build brief</a> · <a href="build-spec.json">Metric specification</a></header><nav aria-label="Drawing sheets">${sheets.map((s,i)=>`<button data-page="${i}" aria-pressed="${i===0}">${s.id} ${s.title}</button>`).join('')}</nav><main>${svgs.map((s,i)=>`<article data-page="${i}" class="${i===0?'active':''}">${s}</article>`).join('')}</main><footer>Dimensions in metres. Vector sheets preserve printed scale. Original map and earlier massing remain separate. Revision B01 / 18 October 2026.</footer><script>document.querySelectorAll('button[data-page]').forEach(b=>b.onclick=()=>{document.querySelectorAll('button[data-page]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.querySelectorAll('article').forEach(x=>x.classList.toggle('active',x.dataset.page===b.dataset.page));});</script></html>`;
 await writeFile(out+'/index.html',html);
 await page.setContent(html);
 for(let i=0;i<sheets.length;i++){
  await page.locator(`button[data-page="${i}"]`).click();
  assert.equal(await page.locator('article.active').getAttribute('data-page'),String(i));
 }
 await page.setViewportSize({width:390,height:844});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'390 px viewer overflow');
 assert.deepEqual(errors,[]);assert.deepEqual(overflow,[],'Text clipped by sheet edge');
 await writeFile(out+'/drawing-check.json',JSON.stringify({scope:'Static drawings and viewer only',sheets:sheets.length,paperMm:[841,594],vectorPdf:true,pngWidth:2000,pageSelections:sheets.length,mobileWidth:390,pageErrors:errors,edgeClippedText:overflow},null,2)+'\n');
}finally{await browser.close();}
execFileSync('python3',['-c',`import fitz,json
from pathlib import Path
root=Path(${JSON.stringify(out)})
items=json.loads((root/'sheets.json').read_text())
doc=fitz.open()
for item in items:
 p=fitz.open(Path(${JSON.stringify(temp)})/(item['id']+'.pdf'))
 assert len(p)==1,(item['id'],len(p))
 doc.insert_pdf(p)
doc.set_toc([[1,item['id']+' '+item['title'],i+1]for i,item in enumerate(items)])
doc.set_metadata({'title':'ONSITE Heron Reach B01 dimensioned blueprints','author':'ONSITE','subject':'Game environment modelling contract; proposed, not as-built'})
doc.save(root/'ONSITE-HERON-REACH-B01-BLUEPRINTS.pdf',garbage=4,deflate=True)
assert all(abs(p.rect.width*25.4/72-841)<0.5 and abs(p.rect.height*25.4/72-594)<0.5 for p in doc)
print(str(len(doc))+' vector A1 PDF pages verified.')`],{stdio:'inherit'});
console.log('17 sheet exports, viewer selections, mobile layout and edge clipping checks passed.');
// Lossless PDF rewrite: preserve vector paths, searchable text, page sizes and bookmarks.
execFileSync('gs',['-q','-dBATCH','-dNOPAUSE','-sDEVICE=pdfwrite','-dCompatibilityLevel=1.6','-dDetectDuplicateImages=true','-dCompressFonts=true','-sOutputFile='+temp+'/compact.pdf',out+'/ONSITE-HERON-REACH-B01-BLUEPRINTS.pdf']);
await rename(temp+'/compact.pdf',out+'/ONSITE-HERON-REACH-B01-BLUEPRINTS.pdf');
execFileSync('python3',['-c',`import fitz,json
from pathlib import Path
root=Path(${JSON.stringify(out)});p=fitz.open(root/'ONSITE-HERON-REACH-B01-BLUEPRINTS.pdf')
assert len(p)==17 and len(p.get_toc())==17
assert all(abs(s.rect.width*25.4/72-841)<.5 and abs(s.rect.height*25.4/72-594)<.5 for s in p)
assert all(len(s.get_drawings())>30 and len(s.get_text())>200 for s in p)
r=json.loads((root/'drawing-check.json').read_text());r.update(pdfPages=len(p),bookmarks=len(p.get_toc()),pdfBytes=(root/'ONSITE-HERON-REACH-B01-BLUEPRINTS.pdf').stat().st_size,pdfOptimisation='Ghostscript vector-preserving rewrite; no raster/downsample preset')
(root/'drawing-check.json').write_text(json.dumps(r,indent=2)+'\\n')
print('Final PDF retains 17 A1 pages, bookmarks, searchable text and vector geometry.')`],{stdio:'inherit'});
