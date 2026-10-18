// Test-only physical traversal fixture. Bots disabled; no teleports after spawn.
// Uses the shipped WWB Player/Physics and the same level and renderer as the game.
import '../src/style.css';import * as THREE from 'three';import {initPhysics} from '../src/wwb/engine/physics';import {Audio} from '../src/wwb/engine/audio';import {Encounter} from '../src/onsite/Encounter';import {View} from '../src/onsite/View';
const $=(id:string)=>document.getElementById(id)!;
async function run(){const view=new View($('game') as HTMLCanvasElement);await initPhysics();const model=await view.ready;const g=new Encounter(new Audio(),view.scene,view.camera,model);view.installWeapon(g);if(view.software)g.fx.group.traverse(o=>{if('isPointLight'in o)o.visible=false});g.bots.forEach(b=>b.hide());$('menu').hidden=true;$('hud').hidden=false;$('task').textContent='ROUTE VERIFICATION';$('task-detail').textContent='Scripted walking · bots disabled';$('ammo').textContent='30';$('reserve').textContent='150';
const targets=[{name:'courtyard',x:-7,y:0,z:1},{name:'stairs',x:-16,y:1,z:-5.5},{name:'upper-route',x:0,y:3,z:-7.5},{name:'stair-b',x:15,y:1.5,z:7.4},{name:'return',x:8,y:0,z:5}];let stage=0,path:any[]=[],node=0,hold=0,ticks=0,last=performance.now(),acc=0,done=false;const evidence:any[]=[];let shot='';
function route(){const p=g.player.position,t=targets[stage];path=g.nav.findPath(p.x,p.z,t.x,t.z,p.y,t.y)||[];node=0;if(!path.length)throw Error('No route to '+t.name)}route();
const frames:number[]=[];Object.defineProperty(window,'__route',{value:{get state(){return {stage:shot,done,ticks,position:g.player.position.clone(),evidence,metrics:{softwareRenderer:view.software,frames:frames.length,meanFrameMs:frames.reduce((a,b)=>a+b,0)/Math.max(1,frames.length),calls:view.renderer.info.render.calls,triangles:view.renderer.info.render.triangles}}}}});
function frame(now:number){const raw=(now-last)/1000;last=now;acc+=Math.min(raw,.1);if(ticks>120&&hold===0)frames.push(raw*1000);if(frames.length>180)frames.shift();
while(acc>=1/60&&!done){acc-=1/60;ticks++;g.time+=1/60;g.arsenal.step(1/60,{fire:false,firePressed:false,ads:false,reload:false},g.player.eye(1,new THREE.Vector3()),false);if(hold>0){hold--;if(!hold){stage++;if(stage>=targets.length){done=true;break}route()}continue}
const p=g.player.position,w=path[node];if(!w){const t=targets[stage];shot=t.name;evidence.push({name:shot,position:p.clone(),tick:ticks});hold=180;g.player.yaw=stage===2?Math.PI:stage===0?-.8:stage===1?0:Math.PI;g.player.pitch=.08;continue}
const dx=w.x-p.x,dz=w.z-p.z;if(Math.hypot(dx,dz)<.2&&Math.abs(w.y-p.y)<.45){node++;continue}
g.player.yaw=Math.atan2(-dx,-dz);g.player.pitch=0;g.player.step(1/60,{x:0,y:.5,jump:false,sprint:false,ads:false});g.physics.step(1/60);
}
view.render(g,1,Math.min(raw,.033),{x:0,y:0});requestAnimationFrame(frame)}requestAnimationFrame(frame);
}
run().catch(e=>{console.error(e);document.body.dataset.error=e.message});
