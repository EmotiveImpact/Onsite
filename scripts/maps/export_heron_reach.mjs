import {chromium} from '@playwright/test';
import {readFile,writeFile,rename} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const out=resolve('docs/maps/heron-reach-32');
const pages=JSON.parse(await readFile(out+'/sheets.json','utf8'));
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
try {
 const page=await browser.newPage({viewport:{width:1600,height:1200},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 for(const sheet of pages){
  await page.setContent(await readFile(out+'/'+sheet+'.svg','utf8'));
  await page.locator('svg').screenshot({path:out+'/'+sheet+'.png'});
 }
 await page.setContent(await readFile(out+'/index.html','utf8'));
 assert.equal(await page.locator('article').count(),9);
 for(let i=0;i<9;i++){
  await page.locator(`button[data-page="${i}"]`).click();
  assert.equal(await page.locator('article.active').count(),1);
  assert.equal(await page.locator('article.active').getAttribute('data-page'),String(i));
 }
 for(const layer of ['routes','cover','landscape','lighting','wet']){
  await page.locator(`input[data-layer="${layer}"]`).uncheck();
  assert.equal(await page.locator(`g[data-layer="${layer}"]:not(.off)`).count(),0);
  await page.locator(`input[data-layer="${layer}"]`).check();
 }
 await page.locator('button[data-page="0"]').click();
 await page.pdf({path:out+'/ONSITE-HERON-REACH-32.pdf',preferCSSPageSize:true,printBackground:true});
 execFileSync('gs',['-q','-dBATCH','-dNOPAUSE','-sDEVICE=pdfwrite','-dCompatibilityLevel=1.6','-dPDFSETTINGS=/ebook','-dDetectDuplicateImages=true','-dCompressFonts=true','-sOutputFile='+out+'/compact.pdf',out+'/ONSITE-HERON-REACH-32.pdf']);
 await rename(out+'/compact.pdf',out+'/ONSITE-HERON-REACH-32.pdf');
 await page.setViewportSize({width:390,height:844});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No mobile horizontal overflow');
 assert.deepEqual(errors,[]);
 await writeFile(out+'/viewer-check.json',JSON.stringify({scope:'Static design viewer, not the FPS runtime',pages:9,layerToggles:5,mobileWidth:390,pageErrors:errors,pngExport:true,pdfExport:true,pdfOptimisation:'Ghostscript ebook profile; original SVGs and PNGs retained'},null,2)+'\n');
 console.log('9 PNG sheets + PDF exported; 9 page selections, 5 layer toggles and 390 px layout passed.');
}finally{await browser.close();}
