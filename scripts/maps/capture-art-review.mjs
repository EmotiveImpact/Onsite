// Repeatable runtime inspection fixtures, never input-driven gameplay evidence.
import {chromium} from '@playwright/test';
import {readFile, mkdir, writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
const out=process.env.OUT||'test-results/art-review';
const views=JSON.parse(await readFile(new URL('./art-review-views.json',import.meta.url),'utf8'));
const selected=process.env.VIEWS?.split(',');
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try {
 const page=await browser.newPage({viewport:{width:1280,height:720}}),errors=[],failed=[],captures=[];
 page.setDefaultTimeout(120000);
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error'||/Heron Reach art unavailable|Heron Reach kits: no model/.test(m.text()))errors.push(m.text())});
 page.on('requestfailed',r=>failed.push(`${r.failure()?.errorText} ${r.url()}`));
 page.on('response',r=>{if(r.status()>=400)failed.push(`${r.status()} ${r.url()}`)});
 await page.addInitScript(()=>{let seed=741;Math.random=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296)});
 await page.goto((process.env.ONSITE_URL||'http://127.0.0.1:4173')+'/?map=heron-reach&inspect'+(process.env.QUERY||''));
 await page.waitForFunction(()=>window.__onsite?.ready,null,{timeout:240000});
 await page.click('#start');await page.waitForFunction(()=>document.pointerLockElement);
 for(const [name,x,y,z,dx,dz,pitch] of views){
  if(selected&&!selected.includes(name))continue;
  const pose={x:x-72,y:y+.04,z:z-60,yaw:Math.atan2(-dx,-dz),pitch};
  await page.evaluate(p=>__onsite.place(p.x,p.y,p.z,p.yaw,p.pitch),pose);
  const tick=await page.evaluate(()=>__onsite.snapshot().tick);
  await page.waitForFunction(t=>__onsite.snapshot().tick>=t+12,tick,{timeout:120000,polling:100});
  await page.screenshot({path:`${out}/${name}.png`});
  captures.push({name,requestedPose:pose,actualPlayer:await page.evaluate(()=>__onsite.snapshot().player),metrics:await page.evaluate(()=>__onsite.metrics())});
  console.log('Captured',name);
 }
 const renderer=await page.evaluate(()=>{const gl=document.querySelector('#game').getContext('webgl2'),e=gl.getExtension('WEBGL_debug_renderer_info');return e?gl.getParameter(e.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)});
 const pixelRatio=await page.evaluate(()=>document.querySelector('#game').width/innerWidth);
 const report={kind:'Fixed-camera inspection fixtures; bots frozen; not gameplay evidence',renderer,software:true,viewport:{width:1280,height:720},pixelRatio,commit:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),workingTree:execFileSync('git',['diff','--stat'],{encoding:'utf8'}).trim(),captures,errors,failed};
 await writeFile(`${out}/report.json`,JSON.stringify(report,null,2)+'\n');
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);assert.equal(captures.length,selected?.length??views.length);
}finally{await browser.close()}
