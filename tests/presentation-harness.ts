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
 const locations:Record<string,[number,number,number,number,number]>={court:[-7,.04,2,-.55,-.08],stair:[-16,.4,-4.6,0,-.28],rubbish:[-8,.04,5.5,.72,-.24],gallery:[0,3.04,-7.5,Math.PI,-.18],homes:[-3,.04,3,.15,.35],living:[-7,.04,-10.4,.55,-.13],bedroom:[-13.5,.04,-11.5,.78,-.15],neighbourhood:[25,20,28,.75,-.35]};
 const setLocation=(name:string)=>{const [x,y,z,yaw,pitch]=locations[name]??locations.court;g.player.spawn(new THREE.Vector3(x,y,z),yaw);g.player.pitch=pitch;g.physics.step(1/60)};
 setLocation(params.get('location')??'court');
 g.arsenal.reloadTotal=1.85;g.arsenal.reloading=phase<0?0:1.85*(1-phase);
 $('menu').hidden=true;$('hud').hidden=false;$('task').textContent='PRESENTATION CHECK';$('task-detail').textContent=phase<0?'Idle pose · bots disabled':`Reload ${Math.round(phase*100)}% · frozen simulation`;$('ammo').textContent='30';$('reserve').textContent='150';
 const frames:number[]=[];let renderedPhase=-999,last=performance.now();function frame(now:number){frames.push(now-last);last=now;view.render(g,1,1/60,{x:0,y:0});renderedPhase=phase;requestAnimationFrame(frame)}frame(last);
 Object.defineProperty(window,'__presentation',{value:{ready:true,get renderedPhase(){return renderedPhase},setLocation(name:string){phase=-1;g.arsenal.reloading=0;setLocation(name);view.renderer.setPixelRatio(1);view.renderer.shadowMap.enabled=true;view.resize();$('task-detail').textContent=name+' · fixed inspection view · bots disabled'},setPhase(n:number){phase=n;g.arsenal.reloading=n<0?0:1.85*(1-n);view.renderer.setPixelRatio(.5);view.renderer.shadowMap.enabled=false;view.resize();$('task-detail').textContent=`Reload ${Math.round(n*100)}% · frozen simulation`},probe:()=>view.weaponProbe(),metrics:()=>({software:view.software,meanFrameMs:frames.slice(5).reduce((a,b)=>a+b,0)/Math.max(1,frames.length-5),frames:frames.length,drawCalls:view.renderer.info.render.calls,triangles:view.renderer.info.render.triangles})}})
}
run().catch(e=>{console.error(e);document.body.dataset.error=e.message})
