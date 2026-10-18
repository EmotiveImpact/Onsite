import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
const out='test-results/homes';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1280,height:800}});const errors=[],failed=[];
page.on('requestfailed',r=>failed.push(r.failure()?.errorText+' '+r.url()));
page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failed.push(r.status()+' '+r.url())});
try {
 await page.goto('http://127.0.0.1:5173/tests/presentation-harness.html?phase=-1&quality=high');
 await page.waitForFunction(()=>window.__presentation?.ready||document.body.dataset.error,null,{timeout:180000});assert.equal(await page.evaluate(()=>document.body.dataset.error),undefined);
 const evidence=[];
 for(const location of ['homes','living','bedroom','gallery','neighbourhood']){
  await page.evaluate(name=>__presentation.setLocation(name),location);await page.waitForTimeout(1500);
  await page.screenshot({path:`${out}/${location}.png`});const probe=await page.evaluate(()=>__presentation.probe());assert(probe.finite);evidence.push({location,probe});console.log('Captured',location);
 }
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);await writeFile(out+'/report.json',JSON.stringify({context:'Fixed inspection cameras and frozen reload phases; actual runtime renderer; bots disabled; high-resolution stills are not a performance measurement',errors,failed,evidence},null,2));
}finally{await browser.close()}
