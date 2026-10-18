// Visual regression fixture: freeze WWB's actual reload clock at a selected phase.
// Does not ship in index.html and does not add mutable hooks to the game.
import '../src/style.css'
import * as THREE from 'three'
import {View} from '../src/onsite/View'
import {Encounter} from '../src/onsite/Encounter'
import {Audio} from '../src/wwb/engine/audio'
import {initPhysics} from '../src/wwb/engine/physics'
const $=(s:string)=>document.getElementById(s)!
async function run(){
 const view=new View($('game') as HTMLCanvasElement);await initPhysics();const character=await view.ready;
 const g=new Encounter(new Audio(),view.scene,view.camera,character);view.installWeapon(g);g.bots.forEach(b=>b.hide());
 g.player.spawn(new THREE.Vector3(-7,.04,2),-.55);g.player.eye(1,view.camera.position);g.physics.step(1/60);
 const params=new URLSearchParams(location.search);let phase=Number(params.get('phase')??-1);
 if(params.get('quality')==='high'){view.renderer.setPixelRatio(1);view.renderer.shadowMap.enabled=true;view.resize()}
 for(let i=0;i<60;i++)g.arsenal.step(1/60,{fire:false,firePressed:false,ads:false,reload:false},view.camera.position,false);
 if(params.get('location')==='stair'){g.player.spawn(new THREE.Vector3(-16,.4,-4.6),0);g.player.pitch=-.28;g.physics.step(1/60)}
 g.arsenal.reloadTotal=1.85;g.arsenal.reloading=phase<0?0:1.85*(1-phase);
 $('menu').hidden=true;$('hud').hidden=false;$('task').textContent='PRESENTATION CHECK';$('task-detail').textContent=phase<0?'Idle pose · bots disabled':`Reload ${Math.round(phase*100)}% · frozen simulation`;
 const frames:number[]=[];let renderedPhase=-999,last=performance.now();function frame(now:number){frames.push(now-last);last=now;view.render(g,1,1/60,{x:0,y:0});renderedPhase=phase;requestAnimationFrame(frame)}frame(last);
 Object.defineProperty(window,'__presentation',{value:{ready:true,get renderedPhase(){return renderedPhase},setPhase(n:number){phase=n;g.arsenal.reloading=n<0?0:1.85*(1-n);view.renderer.setPixelRatio(.5);view.renderer.shadowMap.enabled=false;view.resize();$('task-detail').textContent=`Reload ${Math.round(n*100)}% · frozen simulation`},probe:()=>view.weaponProbe(),metrics:()=>({software:view.software,meanFrameMs:frames.slice(5).reduce((a,b)=>a+b,0)/Math.max(1,frames.length-5),frames:frames.length,drawCalls:view.renderer.info.render.calls,triangles:view.renderer.info.render.triangles})}})
}
run().catch(e=>{console.error(e);document.body.dataset.error=e.message})
