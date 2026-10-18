import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
const out='test-results';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:600}});const errors=[],failed=[],checks=[];let bytes=0;
page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push(`${r.failure()?.errorText || 'request failed'} ${r.url()}`));
page.on('response',async r=>{const n=Number(r.headers()['content-length']);if(Number.isFinite(n))bytes+=n;if(r.status()>=400)failed.push(`${r.status()} ${r.url()}`);});
const snap=()=>page.evaluate(()=>window.__onsite.snapshot());
async function ticks(n){const t=(await snap()).tick;await page.waitForFunction(t=>__onsite.snapshot().tick>=t,t+n,{timeout:60000,polling:100});}
let mouse={x:300,y:300};
async function look(yaw,pitch=0){
  const s=await snap();let delta=yaw-s.player.yaw;delta=Math.atan2(Math.sin(delta),Math.cos(delta));
  // Relative pointer motion through Chromium's normal input path, never mutate simulation.
  mouse.x+=-delta/.002;mouse.y+=-(pitch-s.player.pitch)/.002;
  await page.mouse.move(mouse.x,mouse.y);await ticks(2);
}
try{
 await page.goto(process.env.ONSITE_URL||'http://127.0.0.1:5173');await page.waitForFunction(()=>window.__onsite?.ready,null,{timeout:60000});
 await page.screenshot({path:`${out}/menu.png`});await page.click('#start');
 await page.waitForFunction(()=>!!document.pointerLockElement);await ticks(20);checks.push('Enter Estate captures pointer and starts simulation');
 await page.keyboard.down('KeyW');await ticks(30);await page.keyboard.up('KeyW');assert((await snap()).player.position.z<15);checks.push('W moves through courtyard');
 await page.keyboard.down('Space');await ticks(15);assert((await snap()).player.position.y>1.4);await page.keyboard.up('Space');await ticks(50);checks.push('Jump rises and lands');
 await page.mouse.down();await ticks(20);await page.mouse.up();const shot=await snap();assert(shot.weapon.ammo<24);checks.push('Fire consumes ammunition');
 await page.keyboard.press('KeyR');await ticks(110);assert.equal((await snap()).weapon.ammo,24);checks.push('Reload restores magazine');
 await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.pointerLockElement);await page.waitForFunction(()=>!document.getElementById('pause').hidden);const before=(await snap()).tick;await page.waitForTimeout(600);assert.equal((await snap()).tick,before);checks.push('Escape pauses simulation');
 await page.click('#resume');await page.waitForFunction(()=>!!document.pointerLockElement);await ticks(5);checks.push('Resume works');
 // Move to the court gateway using keyboard while looking down -Z.
 // Hold D until x~7, then W through the gate. No debug teleport or damage commands.
 await page.keyboard.down('KeyD');await page.waitForFunction(()=>__onsite.snapshot().player.position.x>=6.9,null,{timeout:60000,polling:50});await page.keyboard.up('KeyD');
 await page.keyboard.down('KeyW');await page.waitForFunction(()=>__onsite.snapshot().player.position.z<=.5,null,{timeout:60000,polling:50});await page.keyboard.up('KeyW');
 for(let i=0;i<8 && (await snap()).bot.health>0;i++){
   const s=await snap(),p=s.player.position,b=s.bot.position;
   const yaw=Math.atan2(-(b.x-p.x),-(b.z-p.z)),pitch=Math.atan2((b.y+.3)-(p.y+.7),Math.hypot(b.x-p.x,b.z-p.z));
   await look(yaw,pitch);await page.mouse.down();await ticks(20);await page.mouse.up();
 }
 assert.equal((await snap()).bot.health,0);checks.push('Normal mouse aim/fire eliminates bot');
 await page.screenshot({path:`${out}/courtyard.png`});
 await look(0,0);await page.keyboard.down('KeyW');await page.waitForFunction(()=>__onsite.snapshot().player.position.z<=-5,null,{timeout:60000,polling:50});await page.keyboard.up('KeyW');
 await page.waitForFunction(()=>__onsite.snapshot().status==='won',null,{timeout:60000});assert.equal(await page.locator('#result-title').textContent(),'Site secured.');checks.push('Capture completes round and shows victory');
 await page.screenshot({path:`${out}/victory.png`});await page.click('#restart');await page.waitForFunction(()=>!!document.pointerLockElement);await ticks(5);assert.equal((await snap()).bot.health,100);checks.push('Restart resets encounter');
 // Reach the stair lane without touching the planter at x=-5,z=8.
 await page.keyboard.down('KeyA');await page.waitForFunction(()=>__onsite.snapshot().player.position.x<=-13.6,null,{timeout:60000,polling:50});await page.keyboard.up('KeyA');
 await page.keyboard.down('KeyW');await page.waitForFunction(()=>__onsite.snapshot().player.position.y>4,null,{timeout:60000,polling:50});await page.keyboard.up('KeyW');checks.push('Keyboard traversal climbs physical stairs');
 await page.screenshot({path:`${out}/stairwell.png`});
 await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.pointerLockElement);
 const metrics=await page.evaluate(()=>__onsite.metrics());assert.equal(errors.length,0,errors.join('\n'));assert.equal(failed.length,0,failed.join('\n'));
 const report={checks,errors,failed,metrics,responseBytes:bytes};await writeFile(`${out}/browser-report.json`,JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}catch(e){await page.screenshot({path:`${out}/failure.png`});console.error('Completed checks:',checks);console.error('State:',await snap().catch(()=>null));throw e;}finally{await browser.close();}
