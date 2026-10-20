import {chromium} from '@playwright/test';import assert from 'node:assert/strict';import{mkdir,writeFile,rm}from'node:fs/promises';
const out=process.env.OUT||'test-results/encounter';await mkdir(out,{recursive:true});await rm(out+'/report.json',{force:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const context=await browser.newContext({viewport:{width:1100,height:700},recordVideo:{dir:out,size:{width:960,height:600}}});const page=await context.newPage();const errors=[],failed=[],checks=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error'||/Heron Reach art unavailable|Constructed stairs unavailable|Building construction unavailable|Ground plan unavailable|Ground detail unavailable|Ground grass mask unavailable|World dressing kit unavailable|World dressing asset unavailable|Heron Reach kits: no model/.test(m.text()))errors.push(m.text())});page.on('requestfailed',r=>failed.push(`${r.failure()?.errorText} ${r.url()}`));page.on('response',r=>{if(r.status()>=400)failed.push(`${r.status()} ${r.url()}`)});
const snap=()=>page.evaluate(()=>__onsite.snapshot());const check=m=>{checks.push(m);console.log(m)};let mouse={x:550,y:350};
async function ticks(n){const t=(await snap()).tick;await page.waitForFunction(t=>__onsite.snapshot().tick>=t||['won','lost'].includes(__onsite.snapshot().status),t+n,{timeout:90000,polling:100})}
async function aim(yaw,pitch=0,settle=true){const s=await snap(),dx=Math.atan2(Math.sin(yaw-s.player.yaw),Math.cos(yaw-s.player.yaw)),dy=pitch-s.player.pitch;const n=Math.ceil(Math.max(Math.abs(dx),Math.abs(dy))/.45)||1;for(let i=0;i<n;i++){mouse.x-=dx/.0019/n;mouse.y-=dy/.0019/n;await page.mouse.move(mouse.x,mouse.y)}if(settle)await ticks(1)}
async function moveTo(x,z){let count=0;while(count++<60){const s=await snap(),p=s.player.position;if(Math.hypot(x-p.x,z-p.z)<.65)return;if(s.status!=='active')throw Error('Round ended while walking');await aim(Math.atan2(-(x-p.x),-(z-p.z)));await page.keyboard.down('KeyW');await ticks(3);await page.keyboard.up('KeyW')}throw Error(`Could not walk to ${x},${z}: ${JSON.stringify((await snap()).player)}`)}
async function advanceToward(x,y,z){
 const s=await snap(),p=s.player.position,path=await page.evaluate(({x,y,z})=>__onsite.route(x,y,z),{x,y,z});
 if(!path?.length)throw Error('No physical route to '+JSON.stringify({x,y,z}));
 const w=path.find(q=>Math.hypot(q.x-p.x,q.z-p.z)>.6)||path.at(-1);
 await page.mouse.up({button:'right'});await aim(Math.atan2(-(w.x-p.x),-(w.z-p.z)));await page.keyboard.down('KeyW');await ticks(4);await page.keyboard.up('KeyW');
}
// Capture can finish anywhere inside its 4 m zone, before the chosen waypoint.
// The game freezes movement on victory; the final won assertion still applies.
async function routeTo(x,y,z){for(let i=0;i<240;i++){const s=await snap(),p=s.player.position;if(s.status==='won')return;if(Math.hypot(x-p.x,z-p.z)<.7&&Math.abs(y-p.y)<.4)return;if(s.status!=='active')throw Error('Round ended during route');await advanceToward(x,y,z)}throw Error('Route movement limit exceeded')}
try{
 await page.goto(process.env.ONSITE_URL||'http://127.0.0.1:5173');await page.waitForFunction(()=>window.__onsite?.ready,null,{timeout:90000});check('All materials/models loaded');await page.click('#start');await page.waitForFunction(()=>document.pointerLockElement);await page.mouse.move(mouse.x,mouse.y);await aim(0);check('Pointer lock and mouse look');
 await ticks(15);await page.screenshot({path:out+'/first-person.png'});
 await page.mouse.down({button:'right'});await ticks(25);assert((await snap()).weapon.ads>.9);const visual=await page.evaluate(()=>__onsite.weaponVisual());assert(visual?.finite);assert(visual.name.includes('IRONLINE'));assert(Math.abs(visual.sightNdc[0])<.03&&Math.abs(visual.sightNdc[1])<.03,'Imported rear sight stays within 1.5% of screen centre');await page.screenshot({path:out+'/aiming.png'});await page.mouse.up({button:'right'});check('Imported rifle and hands loaded; ADS sight aligns to centre');
 const old=(await snap()).weapon.ammo;await page.mouse.down();await ticks(15);await page.mouse.up();assert((await snap()).weapon.ammo<old);await page.keyboard.press('KeyR');await ticks(140);assert.equal((await snap()).weapon.ammo,30);check('WWB automatic fire, recoil and timed reload');
 await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.pointerLockElement);const t=(await snap()).tick;await page.waitForTimeout(500);assert.equal((await snap()).tick,t);await page.click('#resume');await page.waitForFunction(()=>document.pointerLockElement);check('Pause/resume freezes simulation');
 await page.keyboard.press('Escape');await page.click('#restart-pause');await page.waitForFunction(()=>document.pointerLockElement);
 await page.keyboard.down('Space');await ticks(8);assert((await snap()).player.position.y>.3);await page.keyboard.up('Space');await ticks(45);check('Jump and landing');
 await aim(0);await moveTo(-9,6.5);check('Walk through lobby doorway into court');
 for(let i=0;i<200;i++){
  const s=await snap();if(s.status!=='active')break;if(s.bots.every(b=>!b.alive))break;
  const target=s.bots.filter(b=>s.visible.includes(b.id)).sort((a,b)=>a.health-b.health)[0];if(!target){await page.mouse.up();const goal=s.bots.find(b=>b.alive).position;await advanceToward(goal.x,goal.y,goal.z);continue}
  // Track through normal mouse input once per rendered update. A separate aim wait
  // followed by a fire wait leaves a moving target ~0.5 s stale on SwiftShader.
  const p=s.player.position,b={...target.position};b.x+=target.velocity.x*.15;b.z+=target.velocity.z*.15;await aim(Math.atan2(-(b.x-p.x),-(b.z-p.z)),Math.atan2(b.y+1.25-p.y-1.62,Math.hypot(b.x-p.x,b.z-p.z)),false);
  await page.mouse.down({button:'right'});await page.mouse.down();await ticks(1);
  if((await snap()).weapon.ammo<3){await page.mouse.up();await page.keyboard.press('KeyR');await ticks(140)}
  if(i%10===0)console.log('Tracking',JSON.stringify({tick:s.tick,health:s.player.health,target:target.id,targetHealth:target.health,hits:s.stats.hits,shots:s.stats.shots}));
 }
 await page.mouse.up();await page.mouse.up({button:'right'});await page.screenshot({path:out+'/combat.png'});const s=await snap();check(`Combat result: ${s.bots.filter(b=>!b.alive).length} opponents down, health ${s.player.health}`);assert(s.stats.hits>0,'Actual shots must damage a bot');
 if(s.bots.every(b=>!b.alive)){await routeTo(-2.5,0,1.5);await ticks(180);assert.equal((await snap()).status,'won');check('Clear and capture victory');await page.screenshot({path:out+'/victory.png'})}
 if((await snap()).status==='lost'){check('Player damage and death screen');await page.screenshot({path:out+'/death.png'})}
 assert.equal((await snap()).status,'won','Complete the encounter, rather than passing on partial kills');const combatState=await snap(),metrics=await page.evaluate(()=>__onsite.metrics());
 const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('onsite.player.v1')));assert.equal(saved.records['heron-court'].last.outcome,'won','Actual capture must persist');assert.equal(saved.records['heron-court'].played,1,'Only completed rounds count');
 await page.keyboard.press('Escape');if(await page.locator('#result').isVisible())await page.click('#restart');else await page.click('#restart-pause');await page.waitForFunction(()=>document.pointerLockElement);assert.equal((await snap()).player.health,100);check('Round reset restores player and opponents');
 const report={checks,errors,failed,combatState,metrics,state:await snap()};await writeFile(out+'/report.json',JSON.stringify(report,null,2));assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);console.log(JSON.stringify(report.metrics));
}catch(e){console.error(e);await page.screenshot({path:out+'/failure.png'});await writeFile(out+'/failure.json',JSON.stringify({checks,errors,failed,state:await snap().catch(()=>null)},null,2));process.exitCode=1}finally{await context.close();await browser.close()}
