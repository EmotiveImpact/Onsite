import './style.css';
import { FixedStepper } from './adapted/loop.js';
import { movementIntent } from './adapted/input.js';
import { accuracy, formatClock } from './adapted/gameplay.js';
import { Simulation, DT } from './sim/Simulation.js';
import { solids, OBJECTIVE } from './sim/level.js';
import { WorldView } from './view/WorldView.js';
const $=id=>document.getElementById(id);
const stepper=new FixedStepper();
const keys=new Set();let yaw=0,pitch=0,fire=false,jump=false,reload=false,sequence=0,active=false,started=false,sensitivity=1;
let sim,view,snapshot,last=performance.now(),accumulator=0,hitTime=0,damageTime=0,noticeTime=0,audio;
const performanceSamples=[];let frameCount=0;
function clearInput(){keys.clear();fire=false;jump=false;reload=false;accumulator=0;stepper.resetAccumulator();}
function tone(freq,duration,volume,type='triangle'){
  if(!$('sound').checked||!audio)return;
  const o=audio.createOscillator(),g=audio.createGain();o.type=type;o.frequency.setValueAtTime(freq,audio.currentTime);o.frequency.exponentialRampToValueAtTime(Math.max(30,freq*.35),audio.currentTime+duration);g.gain.setValueAtTime(volume,audio.currentTime);g.gain.exponentialRampToValueAtTime(.001,audio.currentTime+duration);o.connect(g);g.connect(audio.destination);o.start();o.stop(audio.currentTime+duration);
}
function notice(text){$('notice').textContent=text;noticeTime=2.5;}
function handleEvent(e){
  view.event(e);
  if(e.type==='shot')tone(135,.09,.12,'sawtooth');
  if(e.type==='hit'){hitTime=.18;tone(780,.08,.05);}
  if(e.type==='bot-shot'){damageTime=.35;tone(75,.15,.1,'sawtooth');}
  if(e.type==='reload')tone(300,.15,.04,'square');
  if(e.type==='bot-down')notice('OPPONENT DOWN / SECURE THE COURT');
}
function hud(){
  $('health').textContent=snapshot.player.health;$('health-bar').style.width=`${snapshot.player.health}%`;
  $('ammo').textContent=String(snapshot.weapon.ammo).padStart(2,'0');$('reserve').textContent=snapshot.weapon.reserve;
  $('weapon-state').textContent=snapshot.weapon.reloadRemaining>0?'RELOADING':snapshot.weapon.ammo===0?'EMPTY / PRESS R':'ONS-01 / AUTO';
  $('score').innerHTML=snapshot.bot.health>0?'00 <i>:</i> <em>01</em>':'01 <i>:</i> <em>00</em>';
  $('timer').textContent=formatClock(180-snapshot.tick*DT);
  $('task').textContent=snapshot.bot.health>0?'CLEAR THE COURT':snapshot.capture>0?'SECURING THE SITE':'HOLD THE COURT';
  const p=snapshot.player.position,dist=Math.round(Math.hypot(p.x-OBJECTIVE.x,p.z-OBJECTIVE.z));
  $('task-detail').textContent=snapshot.bot.health>0?`One opponent on site · ${dist} m`:snapshot.capture>0?`${Math.round(snapshot.capture/3*100)}% secured`:`Reach the amber marker · ${dist} m`;
  const ctx=$('map').getContext('2d');ctx.clearRect(0,0,160,160);ctx.save();ctx.translate(80,80);ctx.scale(3,3);
  for(const s of solids){if(s.id==='ground'||s.id==='court'||s.id.includes('pavement'))continue;ctx.fillStyle=s.material==='fence'?'#50606a':'#68727a';ctx.fillRect(s.position.x-s.size.x/2,s.position.z-s.size.z/2,s.size.x,s.size.z);}
  ctx.fillStyle='#edae48';ctx.beginPath();ctx.arc(OBJECTIVE.x,OBJECTIVE.z,1.2,0,Math.PI*2);ctx.fill();
  ctx.translate(p.x,p.z);ctx.rotate(-snapshot.player.yaw);ctx.fillStyle='#f5f3eb';ctx.beginPath();ctx.moveTo(0,-1.5);ctx.lineTo(-1,1);ctx.lineTo(1,1);ctx.closePath();ctx.fill();ctx.restore();
}
async function lock(){
  try{audio??=new AudioContext();await audio.resume();}catch{}
  try{await $('game').requestPointerLock();}catch{notice('Click the game to capture your mouse.');}
}
function restart(){sim.reset();snapshot=sim.snapshot();yaw=0;pitch=0;sequence=0;clearInput();$('result').hidden=true;$('pause').hidden=true;lock();}
$('start').addEventListener('click',()=>{started=true;lock();});$('resume').addEventListener('click',lock);$('restart').addEventListener('click',restart);$('restart-pause').addEventListener('click',restart);
$('sensitivity').addEventListener('input',e=>sensitivity=+e.target.value);
document.addEventListener('pointerlockchange',()=>{
  active=document.pointerLockElement===$('game');clearInput();
  if(active){$('menu').hidden=true;$('pause').hidden=true;$('hud').hidden=false;}
  else if(started&&snapshot?.status==='active')$('pause').hidden=false;
});
document.addEventListener('pointerlockerror',()=>{$('load-status').textContent='Mouse capture unavailable. Click Enter Estate to retry.';});
window.addEventListener('blur',()=>{clearInput();if(document.pointerLockElement)document.exitPointerLock();});
document.addEventListener('visibilitychange',()=>{if(document.hidden){clearInput();document.exitPointerLock();}});
document.addEventListener('mousemove',e=>{if(!active)return;yaw-=e.movementX*.002*sensitivity;pitch=Math.max(-1.45,Math.min(1.45,pitch-e.movementY*.002*sensitivity));});
document.addEventListener('keydown',e=>{if(!active)return;if(e.code==='Escape'){document.exitPointerLock();return;}if(['KeyW','KeyA','KeyS','KeyD','Space','ShiftLeft','KeyR'].includes(e.code))e.preventDefault();keys.add(e.code);if(e.code==='KeyR'&&!e.repeat)reload=true;});
document.addEventListener('keyup',e=>keys.delete(e.code));
document.addEventListener('mousedown',e=>{if(active&&e.button===0)fire=true;});document.addEventListener('mouseup',()=>fire=false);document.addEventListener('contextmenu',e=>e.preventDefault());
window.addEventListener('resize',()=>view?.resize());
function frame(now){
  const frameSeconds=(now-last)/1000;const elapsed=Math.min(frameSeconds,.1);last=now;
  if(active&&snapshot.status==='active'){
    stepper.advance(elapsed,()=>{
      snapshot=sim.tick({sequence:sequence++,yaw,pitch,...movementIntent(keys),fire,reload});
      reload=false;for(const e of snapshot.events)handleEvent(e);
      if(snapshot.status!=='active'){
        active=false;clearInput();document.exitPointerLock();$('pause').hidden=true;$('result').hidden=false;
        $('result-title').textContent=snapshot.status==='won'?'Site secured.':'You went down.';
        $('result-detail').textContent=snapshot.status==='won'?`Court held. Encounter completed in ${Math.floor(snapshot.tick*DT)} seconds. Accuracy: ${Math.round(accuracy(snapshot.stats)*100)}%.`:'Use the planters for cover, reload between shots, and watch the court entrance.';return false;
      }
    });
  }
  hitTime=Math.max(0,hitTime-elapsed);damageTime=Math.max(0,damageTime-elapsed);noticeTime=Math.max(0,noticeTime-elapsed);
  $('hitmarker').style.opacity=hitTime>0?1:0;$('damage').style.opacity=damageTime;$('notice').style.opacity=noticeTime>0?1:0;
  hud();view.update(snapshot,elapsed,now/1000,started);
  if(frameCount++>60){performanceSamples.push(frameSeconds*1000);if(performanceSamples.length>300)performanceSamples.shift();}
  requestAnimationFrame(frame);
}
try{
  sim=await Simulation.create();view=new WorldView($('game'));snapshot=sim.snapshot();
  await view.ready;$('start').disabled=false;$('start').innerHTML='ENTER ESTATE <span>↗</span>';$('load-status').textContent='Desktop · headphones recommended';
  // Read-only diagnostics: no teleport, damage or aim controls exposed to the browser.
  window.__onsite={snapshot:()=>sim.snapshot(),metrics:()=>({softwareRenderer:view.software,frames:frameCount,meanFrameMs:performanceSamples.reduce((a,b)=>a+b,0)/Math.max(1,performanceSamples.length),drawCalls:view.renderer.info.render.calls,triangles:view.renderer.info.render.triangles}),surfaceAt:(x,y)=>view.surfaceAt(x,y),ready:true};
  last=performance.now();requestAnimationFrame(frame);
}catch(error){console.error(error);$('load-status').textContent=`Could not load the estate: ${error.message}. Reload to retry.`;$('start').textContent='LOAD FAILED';}
