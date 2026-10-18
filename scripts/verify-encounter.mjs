import {chromium} from '@playwright/test';import assert from 'node:assert/strict';import{mkdir,writeFile}from'node:fs/promises';
const out='test-results/encounter';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const context=await browser.newContext({viewport:{width:1100,height:700},recordVideo:{dir:out,size:{width:960,height:600}}});const page=await context.newPage();const errors=[],failed=[],checks=[];page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push(`${r.failure()?.errorText} ${r.url()}`));page.on('response',r=>{if(r.status()>=400)failed.push(`${r.status()} ${r.url()}`)});
const snap=()=>page.evaluate(()=>__onsite.snapshot());const check=m=>{checks.push(m);console.log(m)};let mouse={x:550,y:350};
async function ticks(n){const t=(await snap()).tick;await page.waitForFunction(t=>__onsite.snapshot().tick>=t||['won','lost'].includes(__onsite.snapshot().status),t+n,{timeout:90000,polling:100})}
async function aim(yaw,pitch=0){for(let attempt=0;attempt<1;attempt++){const s=await snap(),dx=Math.atan2(Math.sin(yaw-s.player.yaw),Math.cos(yaw-s.player.yaw)),dy=pitch-s.player.pitch;const n=Math.ceil(Math.max(Math.abs(dx),Math.abs(dy))/.45)||1;for(let i=0;i<n;i++){mouse.x-=dx/.0019/n;mouse.y-=dy/.0019/n;await page.mouse.move(mouse.x,mouse.y)}await ticks(1)}}
async function moveTo(x,z){let count=0;while(count++<60){const s=await snap(),p=s.player.position;if(Math.hypot(x-p.x,z-p.z)<.65)return;if(s.status!=='active')throw Error('Round ended while walking');await aim(Math.atan2(-(x-p.x),-(z-p.z)));await page.keyboard.down('KeyW');await ticks(3);await page.keyboard.up('KeyW')}throw Error(`Could not walk to ${x},${z}: ${JSON.stringify((await snap()).player)}`)}
try{
 await page.goto(process.env.ONSITE_URL||'http://127.0.0.1:5173');await page.waitForFunction(()=>window.__onsite?.ready,null,{timeout:90000});check('All materials/models loaded');await page.click('#start');await page.waitForFunction(()=>document.pointerLockElement);await page.mouse.move(mouse.x,mouse.y);await aim(0);check('Pointer lock and mouse look');
 await ticks(15);await page.screenshot({path:out+'/first-person.png'});
 await page.mouse.down({button:'right'});await ticks(25);assert((await snap()).weapon.ads>.9);await page.screenshot({path:out+'/aiming.png'});await page.mouse.up({button:'right'});check('Aim-down-sights reaches full blend');
 const old=(await snap()).weapon.ammo;await page.mouse.down();await ticks(15);await page.mouse.up();assert((await snap()).weapon.ammo<old);await page.keyboard.press('KeyR');await ticks(140);assert.equal((await snap()).weapon.ammo,30);check('WWB automatic fire, recoil and timed reload');
 await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.pointerLockElement);const t=(await snap()).tick;await page.waitForTimeout(500);assert.equal((await snap()).tick,t);await page.click('#resume');await page.waitForFunction(()=>document.pointerLockElement);check('Pause/resume freezes simulation');
 await page.keyboard.press('Escape');await page.click('#restart-pause');await page.waitForFunction(()=>document.pointerLockElement);
 await page.keyboard.down('Space');await ticks(8);assert((await snap()).player.position.y>.3);await page.keyboard.up('Space');await ticks(45);check('Jump and landing');
 await aim(0);await moveTo(-9,6.5);check('Walk through lobby doorway into court');
 for(let i=0;i<70;i++){
  const s=await snap();if(s.status!=='active')break;if(s.bots.every(b=>!b.alive))break;
  const target=s.bots.find(b=>s.visible.includes(b.id));if(!target){await ticks(20);continue}
  const p=s.player.position,b={...target.position};b.x+=target.velocity.x*.15;b.z+=target.velocity.z*.15;await aim(Math.atan2(-(b.x-p.x),-(b.z-p.z)),Math.atan2(b.y+1.4-p.y-1.62,Math.hypot(b.x-p.x,b.z-p.z)));
  await page.mouse.down({button:'right'});await page.mouse.down();await ticks(10);await page.mouse.up();if((await snap()).weapon.ammo<6){await page.keyboard.press('KeyR');await ticks(140)}
 }
 await page.mouse.up({button:'right'});await page.screenshot({path:out+'/combat.png'});const s=await snap();check(`Combat result: ${s.bots.filter(b=>!b.alive).length} opponents down, health ${s.player.health}`);assert(s.stats.hits>0,'Actual shots must damage a bot');
 if(s.bots.every(b=>!b.alive)){await moveTo(-3,2);await ticks(180);assert.equal((await snap()).status,'won');check('Clear and capture victory');await page.screenshot({path:out+'/victory.png'})}
 if((await snap()).status==='lost'){check('Player damage and death screen');await page.screenshot({path:out+'/death.png'})}
 await page.keyboard.press('Escape');if(await page.locator('#result').isVisible())await page.click('#restart');else await page.click('#restart-pause');await page.waitForFunction(()=>document.pointerLockElement);assert.equal((await snap()).player.health,100);check('Round reset restores player and opponents');
 const report={checks,errors,failed,metrics:await page.evaluate(()=>__onsite.metrics()),state:await snap()};await writeFile(out+'/report.json',JSON.stringify(report,null,2));assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);console.log(JSON.stringify(report.metrics));
}catch(e){console.error(e);await page.screenshot({path:out+'/failure.png'});await writeFile(out+'/failure.json',JSON.stringify({checks,errors,failed,state:await snap().catch(()=>null)},null,2));process.exitCode=1}finally{await context.close();await browser.close()}
