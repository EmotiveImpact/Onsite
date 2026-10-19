import '../style.css'
import * as THREE from 'three'
import {Input} from '../wwb/engine/input'
import {GameLoop} from '../wwb/engine/loop'
import {initPhysics} from '../wwb/engine/physics'
import {Audio} from '../wwb/engine/audio'
import {formatClock} from '../wwb/game/rules'
import {View} from './View'
import {Encounter} from './Encounter'
import {levelFor} from './levels'
const $=(id:string)=>document.getElementById(id)!;
async function boot(){
 const level=levelFor(location.search),view=new View($('game') as HTMLCanvasElement,level);await initPhysics();const model=await view.ready;
 const audio=new Audio(),input=new Input($('game') as HTMLCanvasElement),game=new Encounter(audio,view.scene,view.camera,model,level);
 view.installWeapon(game);
 if(view.software)game.fx.group.traverse(o=>{if(o instanceof Object&&'isPointLight' in o)o.visible=false});
 let started=false,paused=true,look={x:0,y:0},last=performance.now();const frames:number[]=[];
 const pause=()=>{paused=true;input.unlockPointer();input.clear();$('pause').hidden=false;loop.paused=true};
 const resume=()=>{paused=false;input.clear();$('pause').hidden=true;loop.resetAccumulator();loop.paused=false;input.lockPointer();audio.unlock()};
 const restart=()=>{game.reset();$('result').hidden=true;resume()};
 const loop=new GameLoop({step:dt=>{
 if(paused)return;input.update();look=input.takeLook();game.step(dt,{...input.move,jump:input.consume('jump'),sprint:input.held('sprint'),ads:input.held('ads'),slide:input.consume('slide'),crouch:input.held('slide'),fire:input.held('fire'),firePressed:input.consume('fire'),reload:input.consume('reload'),yaw:game.player.yaw-look.x,pitch:game.player.pitch-look.y});
 input.endFrame();if(game.state==='won'||game.state==='lost'){paused=true;loop.paused=true;input.unlockPointer();$('result').hidden=false;$('result-title').textContent=game.state==='won'?'Site secured.':'Run it back.';$('result-detail').textContent=`${game.match.stats.shots} shots · ${game.match.stats.hits} hits · ${Math.floor(game.time)} seconds`}
 },render:(alpha,dt)=>{
 const now=performance.now(),raw=now-last;last=now;if(started&&!paused){frames.push(raw);if(frames.length>360)frames.shift()}
 view.render(game,alpha,dt,look,!started);look={x:0,y:0};hud();
 }});loop.paused=true;loop.start();
 function hud(){const p=game.player,a=game.arsenal,n=game.bots.filter(b=>b.alive).length;
 $('health').textContent=String(Math.ceil(p.health));$('health-bar').style.width=`${p.health}%`;$('ammo').textContent=String(a.slot.mag).padStart(2,'0');$('reserve').textContent=String(a.slot.reserve);$('weapon-state').textContent=a.reloading>0?'RELOADING':'ONS-01 / CARBINE';$('score').innerHTML=`${String(game.bots.length-n).padStart(2,'0')} <i>:</i> <em>${String(n).padStart(2,'0')}</em>`;$('timer').textContent=formatClock(game.match.timeLeft);$('task').textContent=n?'CLEAR THE ESTATE':'HOLD THE COURT';$('task-detail').textContent=n?`${n} opponents · ground + gallery`:`Secure ${level.capture.label.toLowerCase()} · ${Math.round(game.capture/2.5*100)}%`;$('hitmarker').style.opacity=game.hit>0?'1':'0';$('damage').style.opacity=String(game.hurt*.8);$('crosshair').style.opacity=String(1-a.ads);
 const ctx=($('map') as HTMLCanvasElement).getContext('2d')!;ctx.clearRect(0,0,160,160);ctx.save();ctx.translate(80,80);ctx.scale(4,4);if(level.id==='heron-reach'){ctx.scale(.75,.75);ctx.translate(-p.position.x,-p.position.z)}
 for(const s of level.solids){if(level.id==='heron-reach'?level.surfaceIds.includes(s.id):['ground','room-floor','gallery'].includes(s.id))continue;if(level.id==='heron-reach'?s.y-s.h/2>p.position.y+1.5||s.y+s.h/2<p.position.y+.5:p.position.y>2.5?s.y<3:s.y>2)continue;ctx.fillStyle='#68727a';ctx.fillRect(s.x-s.w/2,s.z-s.d/2,s.w,s.d)}ctx.translate(p.position.x,p.position.z);ctx.rotate(-p.yaw);ctx.fillStyle='#edb253';ctx.beginPath();ctx.moveTo(0,-1);ctx.lineTo(-.6,.6);ctx.lineTo(.6,.6);ctx.fill();ctx.restore();
 }
 $('start').onclick=()=>{started=true;$('menu').hidden=true;$('hud').hidden=false;restart()};$('resume').onclick=resume;$('restart').onclick=restart;$('restart-pause').onclick=restart;
 window.addEventListener('keydown',e=>{if(e.code==='Escape'&&started&&!paused)pause()});window.addEventListener('blur',()=>{if(started&&!paused)pause()});document.addEventListener('pointerlockchange',()=>{if(!input.locked&&started&&!paused&&game.state==='active')pause()});
 $('sensitivity').oninput=()=>{input.sensitivity=Number(($('sensitivity') as HTMLInputElement).value)};
 $('sound').onchange=()=>audio.setVolumes(0,.6,!($('sound') as HTMLInputElement).checked);
 Object.defineProperty(window,'__onsite',{value:Object.freeze({ready:true,weaponVisual:()=>view.weaponProbe(),snapshot:()=>({...game.snapshot(),visible:game.bots.filter(b=>b.alive&&game.lineOfSight(game.player.eye(1,view.camera.position.clone()),b.eye)).map(b=>b.id)}),route:(x:number,y:number,z:number)=>game.nav.findPath(game.player.position.x,game.player.position.z,x,z,game.player.position.y,y),metrics:()=>({softwareRenderer:view.software,renderer:view.renderer.getContext().getParameter(view.renderer.getContext().RENDERER),frames:frames.length,meanFrameMs:frames.reduce((a,b)=>a+b,0)/Math.max(1,frames.length),drawCalls:view.renderer.info.render.calls,triangles:view.renderer.info.render.triangles}),nav:()=>({nodes:game.nav.nodes.length}),
  // Inspection fixtures only (?inspect): stills from fixed viewpoints, never gameplay evidence.
  ...(new URLSearchParams(location.search).has('inspect')?{place:(x:number,y:number,z:number,yaw=0,pitch=0)=>{game.player.spawn(new THREE.Vector3(x,y,z),yaw);game.player.pitch=pitch}}:{})})});
 $('start').removeAttribute('disabled');$('start').innerHTML='ENTER THE ESTATE <span>↗</span>';$('load-status').textContent='Ready · RMB aim · LMB fire · R reload · C crouch';
}
boot().catch(e=>{console.error(e);$('load-status').textContent=`Load failed: ${e.message}`});
