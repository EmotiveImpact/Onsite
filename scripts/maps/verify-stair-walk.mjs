// Physical route fixture: actual WWB capsule, Rapier, layered nav and runtime art.
// Scripted movement, frozen opponents; never label these captures combat/input evidence.
import {chromium} from '@playwright/test'
import assert from 'node:assert/strict'
import {mkdir,writeFile} from 'node:fs/promises'
import {createHash} from 'node:crypto'

const core=process.env.CORE||'S1',base=Number(process.env.BASE??(core==='S7'?-3:0)),origin=process.env.ONSITE_URL||'http://127.0.0.1:5173'
const out=process.env.OUT||`test-results/stair-walk-${core.toLowerCase()}-${base<0?'b1':'g'}`
await mkdir(out,{recursive:true})
const browser=await chromium.launch({executablePath:process.env.CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']})
const context=await browser.newContext({viewport:{width:1280,height:800},recordVideo:{dir:out,size:{width:1280,height:800}}}),page=await context.newPage()
const errors=[],failed=[],warnings=[],checks=[],captures=[],started=Date.now()
page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());if(m.type()==='warning')warnings.push(m.text())})
page.on('requestfailed',r=>failed.push(`${r.failure()?.errorText} ${r.url()}`));page.on('response',r=>{if(r.status()>=400)failed.push(`${r.status()} ${r.url()}`)})
const snapshot=()=>page.evaluate(()=>window.__stairRoute?.state??{error:document.body.dataset.error??null})
let finalState=null,asset=null,error=null
try{
  const url=new URL('/tests/stair-route-harness.html',origin);url.searchParams.set('core',core);url.searchParams.set('base',String(base))
  await page.goto(url.href)
  await page.waitForFunction(()=>window.__stairRoute?.state.ready||document.body.dataset.error,null,{timeout:180000,polling:100})
  const initial=await snapshot();assert.equal(initial.error,null);assert.equal(initial.botsDisabled,true);assert.equal(initial.spawnCount,1);assert(initial.art.loaded&&initial.art.retiredTriangles>0)
  assert.equal(initial.metrics.pixelRatio,.5,'Normal software fallback retained; no inspection DPR override')
  checks.push('Actual constructed stair asset loaded; original WWB player/nav/Rapier; opponents disabled')
  const response=await fetch(new URL('/models/heron-reach/stair-detail.glb',origin));assert(response.ok,'Stair asset must remain available');const bytes=Buffer.from(await response.arrayBuffer());asset={url:response.url,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')}
  for(const [index,target]of initial.plan.entries()){
    await page.waitForFunction(name=>window.__stairRoute?.state.checkpoints.some(p=>p.name===name)||window.__stairRoute?.state.error,target.name,{timeout:180000,polling:50})
    const state=await snapshot();assert.equal(state.error,null);const checkpoint=state.checkpoints.find(p=>p.name===target.name)
    assert(checkpoint,`Missing ${target.name}`);assert(Math.abs(checkpoint.position.y-target.expectedY)<=target.tolerance,`${target.name} expected feet height ${target.expectedY}`);assert.equal(checkpoint.grounded,true)
    assert.equal(state.stage,target.name,`Missed screenshot hold for ${target.name}`);assert.equal(state.phase,'checkpoint',`Capture must show the held ${target.name} position`)
    const image=`${String(index+1).padStart(2,'0')}-${target.name}.png`
    await page.screenshot({path:`${out}/${image}`})
    captures.push({image,label:target.label,checkpoint});checks.push(`${target.name}: feet y=${checkpoint.position.y.toFixed(3)} m, grounded`)
    console.log(checks.at(-1))
  }
  await page.waitForFunction(()=>window.__stairRoute?.state.done||window.__stairRoute?.state.error,null,{timeout:60000,polling:100})
  finalState=await snapshot();assert.equal(finalState.error,null);assert.equal(finalState.done,true);assert.equal(finalState.checkpoints.length,7);assert.equal(finalState.spawnCount,1)
  assert(finalState.maximumPhysicsStep<=.6,'Every recorded physics step remained continuous')
  assert(Math.hypot(finalState.position.x-finalState.initial.x,finalState.position.z-finalState.initial.z)<.5,'Returned to original entry');assert(Math.abs(finalState.position.y-base)<.18)
  assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);checks.push('Continuous ascent, dogleg turn and descent completed without any post-spawn teleport')
}catch(e){error=String(e);process.exitCode=1;finalState=await snapshot().catch(()=>null);await page.screenshot({path:`${out}/failure.png`}).catch(()=>{});console.error(e)}
finally{
  const video=page.video();await context.close();const videoPath=await video?.path();await browser.close()
  const report={context:'Physical stair traversal fixture; scripted steering, bots disabled; not combat evidence',core,base,concurrentFixtureCount:Number(process.env.FIXTURE_CONCURRENCY||1),rendering:'Chromium / ANGLE SwiftShader, normal software fallback; not a real-GPU benchmark',checks,captures,asset,errors,failed,warnings,error,elapsedWallSeconds:(Date.now()-started)/1000,video:videoPath?.split('/').at(-1),state:finalState}
  await writeFile(`${out}/${error?'failure':'report'}.json`,JSON.stringify(report,null,2));console.log(JSON.stringify({core,base,checks:checks.length,error,elapsedWallSeconds:report.elapsedWallSeconds}))
}
