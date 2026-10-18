import {chromium}from'@playwright/test';
import assert from'node:assert/strict';
import{mkdir,writeFile,rm}from'node:fs/promises';
const out='test-results/home-route';await mkdir(out,{recursive:true});await rm(out+'/route-report.json',{force:true});
const b=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const context=await b.newContext({viewport:{width:1280,height:800},recordVideo:{dir:out,size:{width:960,height:600}}});
const page=await context.newPage(),errors=[],failed=[];
page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push(r.failure()?.errorText+' '+r.url()));page.on('response',r=>{if(r.status()>=400)failed.push(r.status()+' '+r.url())});
try{
 await page.goto('http://127.0.0.1:5173/tests/route-harness.html?homes');
 for(const stage of ['entry','living','bedroom','return']){
  await page.waitForFunction(s=>window.__route?.state.stage===s,stage,{timeout:180000});
  await page.screenshot({path:`${out}/${stage}.png`});console.log(stage,await page.evaluate(()=>__route.state.position));
 }
 await page.waitForFunction(()=>__route.state.done,null,{timeout:60000});const state=await page.evaluate(()=>__route.state);
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);assert(state.done);
 await writeFile(out+'/route-report.json',JSON.stringify({context:'Continuous WWB capsule traversal, bots disabled, no teleport after spawn; not ordinary mouse/keyboard gameplay',errors,failed,...state},null,2));console.log(JSON.stringify(state.metrics));
}finally{await context.close();await b.close()}
