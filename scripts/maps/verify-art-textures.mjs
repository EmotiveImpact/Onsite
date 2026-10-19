// Software-only integration probe. Forcing KTX2 verifies transcoding, not real-GPU performance.
import {chromium} from '@playwright/test';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const base=process.env.ONSITE_URL||'http://127.0.0.1:4179',out=process.env.OUT||'test-results/art-textures';
const manifest=JSON.parse(await readFile('public/materials/heron/ktx2/manifest.json','utf8'));
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const report={software:true,renderer:'',runs:[],errors:[]};
try{
 for(const mode of ['webp','ktx2','ktx2-corrupt-fallback']){
  const page=await browser.newPage({viewport:{width:1280,height:720}});
  const network=await page.context().newCDPSession(page);await network.send('Network.enable');
  let transferredBytes=0;network.on('Network.loadingFinished',e=>transferredBytes+=e.encodedDataLength);
  page.on('pageerror',e=>report.errors.push(e.message));
  if(mode==='ktx2-corrupt-fallback'){
   const url=manifest.entries['/materials/heron/hr_brick_stock-normal.webp'].url;
   await page.route('**'+url,route=>route.fulfill({status:200,contentType:'image/ktx2',body:'deliberately invalid KTX2 fixture'}));
  }
  await page.goto(base+'/?map=heron-reach&inspect&textures='+(mode==='webp'?'webp':'ktx2'));
  await page.waitForFunction(()=>window.__onsite?.ready,null,{timeout:240000});
  const metrics=await page.evaluate(()=>__onsite.metrics()),t=metrics.architectureTextures;
  assert(metrics.softwareRenderer);assert(t);
  if(mode==='webp'){assert.equal(t.compressed,0);assert(t.webp>=80)}
  else {assert(t.compressed>=80);assert(t.estimatedMipBytes<report.runs[0].metrics.architectureTextures.estimatedMipBytes*.5)}
  if(mode==='ktx2-corrupt-fallback'){
   const good=report.runs[1].metrics.architectureTextures;
   assert.equal(t.compressed,good.compressed-1);assert.equal(t.webp,good.webp+1);
  }
  report.renderer=await page.evaluate(()=>{const g=document.querySelector('#game').getContext('webgl2'),e=g.getExtension('WEBGL_debug_renderer_info');return g.getParameter(e.UNMASKED_RENDERER_WEBGL)});
  report.runs.push({mode,metrics,transferredBytes});console.log(mode,JSON.stringify(t),'transferred bytes',transferredBytes);await page.close();
 }
 assert.deepEqual(report.errors,[]);
}finally{await writeFile(out+'/report.json',JSON.stringify(report,null,2)+'\n');await browser.close()}
