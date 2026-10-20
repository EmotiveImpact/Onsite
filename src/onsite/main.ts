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
import {ObjectiveMarker} from './ObjectiveMarker'
import {FrontEnd} from './FrontEnd'
import {loadProfile,type PlayerSettings} from './profile'
const $=(id:string)=>document.getElementById(id)!;
let frontEnd:FrontEnd|undefined;
async function boot(){
 const level=levelFor(location.search),preferences=loadProfile(undefined,matchMedia('(prefers-reduced-motion: reduce)').matches);
 const view=new View($('game') as HTMLCanvasElement,level,preferences.settings);
 let applySettings=(settings:PlayerSettings)=>view.applySettings(settings),returnToTitle=()=>{};
 const front=new FrontEnd({mapId:level.id,onSettings:s=>applySettings(s),onKit:()=>{},onReturnToTitle:()=>returnToTitle()});frontEnd=front;
 await initPhysics();const model=await view.ready;
 const audio=new Audio(),input=new Input($('game') as HTMLCanvasElement),game=new Encounter(audio,view.scene,view.camera,model,level);
 const objectiveMarker=new ObjectiveMarker(level);
 applySettings=settings=>{view.applySettings(settings);input.sensitivity=settings.sensitivity;audio.setVolumes(0,settings.volume,!settings.sound)};
 applySettings(front.settings);audio.setPaused(true);
 view.installWeapon(game);
 if(view.software)game.fx.group.traverse(o=>{if(o instanceof Object&&'isPointLight' in o)o.visible=false});
 let started=false,paused=true,look={x:0,y:0},last=performance.now();const frames:number[]=[];
 const frameMetrics=()=>{const sorted=[...frames].sort((a,b)=>a-b);return {frames:frames.length,meanFrameMs:frames.reduce((a,b)=>a+b,0)/Math.max(1,frames.length),medianFrameMs:sorted[Math.floor(sorted.length*.5)]??0,p95FrameMs:sorted[Math.min(sorted.length-1,Math.floor(sorted.length*.95))]??0}};
 const pause=()=>{paused=true;loop.paused=true;input.unlockPointer();input.clear();look={x:0,y:0};audio.setPaused(true);front.showPause()};
 const resume=()=>{paused=false;input.clear();front.enterGame();loop.resetAccumulator();loop.paused=false;input.lockPointer();audio.restoreWorld();audio.setPaused(false);audio.unlock()};
 const restart=()=>{started=true;game.reset();frames.length=0;last=performance.now();resume()};
 returnToTitle=()=>{paused=true;started=false;loop.paused=true;input.unlockPointer();input.clear();look={x:0,y:0};audio.silenceWorld(.05);audio.setPaused(true);game.reset()};
 const loop=new GameLoop({step:dt=>{
 if(paused)return;input.update();look=input.takeLook();game.step(dt,{...input.move,jump:input.consume('jump'),sprint:input.held('sprint'),ads:input.held('ads'),slide:input.consume('slide'),crouch:input.held('slide'),fire:input.held('fire'),firePressed:input.consume('fire'),reload:input.consume('reload'),yaw:game.player.yaw-look.x,pitch:game.player.pitch-look.y});
 input.endFrame();if(game.state==='won'||game.state==='lost'){paused=true;loop.paused=true;input.unlockPointer();input.clear();audio.silenceWorld();audio.setPaused(true);front.showResult({outcome:game.state,seconds:game.time,shots:game.match.stats.shots,hits:game.match.stats.hits,kills:game.bots.filter(b=>!b.alive).length})}
 },render:(alpha,dt)=>{
 const now=performance.now(),raw=now-last;last=now;if(started&&!paused){frames.push(raw);if(frames.length>360)frames.shift()}
 // Keep the last estate backdrop while the kit preview is active; only its small scene renders.
 if(started||$('kit-stage').hidden)view.render(game,alpha,dt,look,!started);look={x:0,y:0};hud();
 }});loop.paused=true;loop.start();
 function hud(){const p=game.player,a=game.arsenal,n=game.bots.filter(b=>b.alive).length;
 objectiveMarker.update(view.camera,p.position,n,game.state);
 $('health').textContent=String(Math.ceil(p.health));$('health-bar').style.width=`${p.health}%`;$('ammo').textContent=String(a.slot.mag).padStart(2,'0');$('reserve').textContent=String(a.slot.reserve);$('weapon-state').textContent=a.reloading>0?'RELOADING':'ONS-01 / CARBINE';$('score').innerHTML=`${String(game.bots.length-n).padStart(2,'0')} <i>:</i> <em>${String(n).padStart(2,'0')}</em>`;$('timer').textContent=formatClock(game.match.timeLeft);$('task').textContent=n?'CLEAR THE ESTATE':'HOLD THE COURT';$('task-detail').textContent=n?`${n} opponents · ${level.name.toLowerCase()}`:`Secure ${level.capture.label.toLowerCase()} · ${Math.round(game.capture/2.5*100)}%`;$('hitmarker').style.opacity=game.hit>0?'1':'0';$('damage').style.opacity=String(game.hurt*.8);$('crosshair').style.opacity=String(1-a.ads);
 const ctx=($('map') as HTMLCanvasElement).getContext('2d')!;ctx.clearRect(0,0,160,160);ctx.save();ctx.translate(80,80);ctx.scale(4,4);if(level.id==='heron-reach'){ctx.scale(.75,.75);ctx.translate(-p.position.x,-p.position.z)}
 for(const s of level.solids){if(level.id==='heron-reach'?level.surfaceIds.includes(s.id):['ground','room-floor','gallery'].includes(s.id))continue;if(level.id==='heron-reach'?s.y-s.h/2>p.position.y+1.5||s.y+s.h/2<p.position.y+.5:p.position.y>2.5?s.y<3:s.y>2)continue;ctx.fillStyle='#68727a';ctx.fillRect(s.x-s.w/2,s.z-s.d/2,s.w,s.d)}ctx.translate(p.position.x,p.position.z);ctx.rotate(-p.yaw);ctx.fillStyle='#edb253';ctx.beginPath();ctx.moveTo(0,-1);ctx.lineTo(-.6,.6);ctx.lineTo(.6,.6);ctx.fill();ctx.restore();
 }
 $('start').onclick=restart;$('resume').onclick=resume;$('restart').onclick=restart;$('restart-pause').onclick=restart;
 window.addEventListener('keydown',e=>{if(e.code==='Escape'&&started&&!paused)pause()});window.addEventListener('blur',()=>{if(started&&!paused)pause()});document.addEventListener('pointerlockchange',()=>{if(!input.locked&&started&&!paused&&game.state==='active')pause()});

 Object.defineProperty(window,'__onsite',{value:Object.freeze({ready:true,weaponVisual:()=>view.weaponProbe(),snapshot:()=>({...game.snapshot(),visible:game.bots.filter(b=>b.alive&&game.lineOfSight(game.player.eye(1,view.camera.position.clone()),b.eye)).map(b=>b.id)}),route:(x:number,y:number,z:number)=>game.nav.findPath(game.player.position.x,game.player.position.z,x,z,game.player.position.y,y),metrics:()=>({softwareRenderer:view.software,renderer:view.renderer.getContext().getParameter(view.renderer.getContext().RENDERER),...frameMetrics(),drawCalls:view.renderer.info.render.calls,triangles:view.renderer.info.render.triangles,architectureTextures:view.artTextureStats,presentation:view.presentation(),audioPaused:audio.isPaused}),nav:()=>({nodes:game.nav.nodes.length}),
  // Inspection fixtures only (?inspect): stills from fixed viewpoints, never gameplay evidence.
  ...(new URLSearchParams(location.search).has('inspect')?{place:(x:number,y:number,z:number,yaw=0,pitch=0)=>{game.player.spawn(new THREE.Vector3(x,y,z),yaw);game.player.pitch=pitch}}:{})})});
 front.markReady();
}
boot().catch(e=>{console.error(e);if(frontEnd)frontEnd.markLoadError(e.message);else $('load-status').textContent=`Load failed: ${e.message}`});
