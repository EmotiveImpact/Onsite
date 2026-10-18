// Heron Reach step-1 stills. These are INSPECTION FIXTURES (?inspect places the player at fixed
// viewpoints); they show the blockout in the actual browser runtime but are not gameplay evidence.
import {chromium} from '@playwright/test';import {mkdir,writeFile} from 'node:fs/promises';
const out=process.env.OUT||'test-results/heron-reach';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1280,height:720}});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>m.type()==='error'&&errors.push(m.text()));
const at=(x,y,z)=>[x-72,y+.04,z-60],face=(dx,dz)=>Math.atan2(-dx,-dz);
const ticks=async n=>{const t=await page.evaluate(()=>__onsite.snapshot().tick);await page.waitForFunction(t=>__onsite.snapshot().tick>=t,t+n,{timeout:120000,polling:100})};
await page.goto((process.env.ONSITE_URL||'http://127.0.0.1:5173')+'/?map=heron-reach&inspect');await page.waitForFunction(()=>window.__onsite?.ready,null,{timeout:180000});
await page.evaluate(()=>{document.getElementById('menu').hidden=true});await page.waitForTimeout(1500);await page.screenshot({path:`${out}/00-overview.png`});
await page.evaluate(()=>{document.getElementById('menu').hidden=false});await page.click('#start');await ticks(10);
const views=[
 ['01-arrival-courtyard',at(50,0,47),face(-8,-15),.08],
 ['02-ground-arcade',at(42,0,34),face(0,-1),.02],
 ['03-s1-stair-from-ground',at(25.15,0,41.2),face(0,-1),.32],
 ['04-l1-gallery',at(46,3,37.6),face(-1,0),-.02],
 ['05-h1-flat-living-room',at(56.6,0,27.6),face(-1,-.35),-.05],
 ['06-h2-private-stair',at(32.75,3,28.9),face(0,-1),.3],
 ['07-l2-rear-landing',at(36,6,19.6),face(1,0),-.02],
 ['08-rowan-roof',at(38,9,34),face(1,-1),-.06],
];
const metrics=[];
for(const [name,[x,y,z],yaw,pitch]of views){await page.evaluate(({x,y,z,yaw,pitch})=>__onsite.place(x,y,z,yaw,pitch),{x,y,z,yaw,pitch});await ticks(6);await page.screenshot({path:`${out}/${name}.png`});const s=await page.evaluate(()=>__onsite.snapshot());metrics.push({name,player:s.player.position,status:s.status});console.log(name,JSON.stringify(s.player.position))}
await writeFile(`${out}/stills.json`,JSON.stringify({kind:'inspection fixtures',errors,metrics,runtime:await page.evaluate(()=>__onsite.metrics())},null,2));
console.log('errors',errors);await browser.close();
