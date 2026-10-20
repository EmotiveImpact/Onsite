// Repeatable runtime inspection fixtures, never input-driven gameplay evidence.
import {chromium} from '@playwright/test';
import {readFile, mkdir, writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const out=process.env.OUT||'test-results/art-review';
const views=JSON.parse(await readFile(new URL('./art-review-views.json',import.meta.url),'utf8'));
const selected=process.env.VIEWS?.split(',');
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try {
 const page=await browser.newPage({viewport:{width:1280,height:720}}),errors=[],failed=[],captures=[];
 page.setDefaultTimeout(120000);
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error'||/Heron Reach art unavailable|Heron Reach kits: no model|Constructed stairs unavailable/.test(m.text()))errors.push(m.text())});
 page.on('requestfailed',r=>failed.push(`${r.failure()?.errorText} ${r.url()}`));
 page.on('response',r=>{if(r.status()>=400)failed.push(`${r.status()} ${r.url()}`)});
 await page.addInitScript(()=>{let seed=741;Math.random=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296)});
 const frozenBuildUrl=process.env.ONSITE_URL||'http://127.0.0.1:4173';
 await page.goto(frozenBuildUrl+'/?map=heron-reach&inspect'+(process.env.QUERY||''));
 await page.waitForFunction(()=>window.__onsite?.ready,null,{timeout:240000});
 await page.click('#start');await page.waitForFunction(()=>document.pointerLockElement);
 for(const [name,x,y,z,dx,dz,pitch] of views){
  if(selected&&!selected.includes(name))continue;
  const pose={x:x-72,y:y+.04,z:z-60,yaw:Math.atan2(-dx,-dz),pitch};
  await page.evaluate(p=>__onsite.place(p.x,p.y,p.z,p.yaw,p.pitch),pose);
  const tick=await page.evaluate(()=>__onsite.snapshot().tick);
  await page.waitForFunction(t=>__onsite.snapshot().tick>=t+12,tick,{timeout:120000,polling:100});
  await page.screenshot({path:`${out}/${name}.png`});
  if(process.env.CHECK_MARKER==='1'&&['the-cage','gallery-edge'].includes(name)){
   assert(await page.locator('#objective-marker').isVisible(),'Objective diamond must be visible from '+name);
   const label=await page.locator('#objective-marker').innerText();assert.match(label,/THE CAGE/);assert.match(label,/\d+ m/);
   if(name==='gallery-edge')assert.match(label,/GROUND FLOOR/,'Upper gallery must identify the lower objective level');
  }
  captures.push({name,requestedPose:pose,actualPlayer:await page.evaluate(()=>__onsite.snapshot().player),actors:await page.evaluate(()=>__onsite.snapshot().bots),metrics:await page.evaluate(()=>__onsite.metrics())});
  console.log('Captured',name);
 }
 const renderer=await page.evaluate(()=>{const gl=document.querySelector('#game').getContext('webgl2'),e=gl.getExtension('WEBGL_debug_renderer_info');return e?gl.getParameter(e.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)});
 const pixelRatio=await page.evaluate(()=>document.querySelector('#game').width/innerWidth);
 const scripts=await page.locator('script[src]').evaluateAll(nodes=>nodes.map(n=>n.src));
 const servedScripts=await Promise.all(scripts.map(async url=>({url,sha256:createHash('sha256').update(Buffer.from(await (await fetch(url)).arrayBuffer())).digest('hex')})));
 const servedAssets=await Promise.all(['/models/heron-reach/heron-reach-arch.glb','/materials/heron/runtime-materials.json',...(process.env.EXTRA_ASSETS||'').split(',').filter(Boolean)].map(async path=>{const response=await fetch(frozenBuildUrl+path);assert(response.ok);const bytes=Buffer.from(await response.arrayBuffer());return {path,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')}}));
 const report={kind:'Fixed-camera inspection fixtures; actors remain active; not gameplay evidence',frozenBuildUrl,servedScripts,servedAssets,renderer,software:true,viewport:{width:1280,height:720},pixelRatio,harnessCommit:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),workingTree:execFileSync('git',['diff','--stat'],{encoding:'utf8'}).trim(),captures,errors,failed};
 await writeFile(`${out}/report.json`,JSON.stringify(report,null,2)+'\n');
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);assert.equal(captures.length,selected?.length??views.length);
}finally{await browser.close()}
