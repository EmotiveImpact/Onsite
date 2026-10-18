// Heron Reach step 1 (Rowan House): the generated level is checked with the real WWB player and
// bot capsules in one Rapier world, plus layered navigation. Southern mirrored blocks are not built yet.
import test from 'node:test'
import assert from 'node:assert/strict'
import * as THREE from 'three'
import {Physics,initPhysics} from '../src/wwb/engine/physics'
import {Player} from '../src/wwb/game/player'
import {Bot} from '../src/wwb/game/bots'
import {LayeredNav} from '../src/onsite/navigation'
import {heronReach as level,inCapture} from '../src/onsite/levels'
import {fromMap as at,toMap,surfaceIds} from '../src/onsite/heronReach'
import {CONFIG} from '../src/wwb/game/config'
await initPhysics();const nav=new LayeredNav(level);
function physics(){const p=new Physics();for(const s of level.solids)p.addStaticBox(new THREE.Vector3(s.x,s.y,s.z),new THREE.Vector3(s.w,s.h,s.d));p.step(1/60);return p}
const inRect=(p:{x:number;z:number},x:number,z:number,w:number,d:number)=>{const m=toMap(p.x,0,p.z);return m.x>x&&m.x<x+w&&m.z>z&&m.z<z+d};
type P={x:number;y:number;z:number};
/** Steer the actual player capsule along nav waypoints; returns the furthest waypoint reached. */
function walk(p:Physics,player:Player,to:P,speed=.45){
 const path=nav.findPath(player.position.x,player.position.z,to.x,to.z,player.position.y,to.y)!;assert(path?.length,`no route to ${JSON.stringify(toMap(to.x,to.y,to.z))}`);let i=0;
 for(let t=0;t<9000&&i<path.length;t++){const w=path[i],dx=w.x-player.position.x,dz=w.z-player.position.z;if(Math.hypot(dx,dz)<.2&&Math.abs(w.y-player.position.y)<.45){i++;continue}player.yaw=Math.atan2(-dx,-dz);player.step(1/60,{x:0,y:speed,jump:false,sprint:false,ads:false});p.step(1/60)}
 assert.equal(i,path.length,JSON.stringify({goal:toMap(to.x,to.y,to.z),at:toMap(player.position.x,player.position.y,player.position.z),next:path[i]&&toMap(path[i].x,path[i].y,path[i].z)}));return path;
}
const cores={S1:[24,36],S2:[54,36]} as const;

test('every Rowan floor is on the layered graph and each core serves G, L1, L2 and R',()=>{
 for(const [name,[cx,cz]]of Object.entries(cores)){
  const a=at(cx+3,0,43.5),b=at(cx+3,9,43.5),path=nav.findPath(a.x,a.z,b.x,b.z,0,9)!;assert(path?.length,name);
  for(const y of [1.5,3,4.5,6,7.5])assert(path.some(p=>Math.abs(p.y-y)<.01&&inRect(p,cx,cz,6,6)),`${name} passes y=${y} inside the core`);
  assert(Math.abs(path.at(-1)!.y-9)<.01);
 }
 for(const [x,y,z]of [[42,3,19.5],[45,3,37.5],[42,6,32],[42,6,19.5],[42,9,27],[31,3,25],[31,6,25],[30,0,25]]){const a=at(x,y,z),n=nav.nearest(a.x,a.z,a.y);assert(Math.hypot(n.x-a.x,n.z-a.z)<.6&&Math.abs(n.y-y)<.01,`floor at ${[x,y,z]}`)}
 assert.notEqual(nav.nearest(at(42,0,25).x,at(42,0,25).z,0).id,nav.nearest(at(42,0,25).x,at(42,0,25).z,3).id,'stacked floors keep separate nodes');
});

for(const name of ['S1','S2'] as const)test(`actual player climbs ${name} from G to the roof and back down`,()=>{
 const [cx]=cores[name],p=physics(),player=new Player(p);player.spawn(new THREE.Vector3(at(cx+3,0,44).x,.04,at(cx+3,0,44).z),0);p.step(1/60);
 for(const y of [3,6,9,0]){walk(p,player,at(cx+3,y,43.5));assert(Math.abs(player.position.y-y)<.3,`${name} level ${y}: ${player.position.y}`)}
 p.world.free();
});

test('H2 maisonette: front door at +3, private stair, rear door at +6, and back again',()=>{
 const p=physics(),player=new Player(p),front=at(31.25,3,30.5),upper=at(33.4,6,28),rear=at(31.25,6,19.5);
 player.spawn(new THREE.Vector3(front.x,3.04,front.z),0);p.step(1/60);
 for(const [goal,y]of [[upper,6],[rear,6],[upper,6],[front,3]] as const){
  const path=walk(p,player,goal);assert(Math.abs(player.position.y-y)<.3);
  assert(!path.some(q=>inRect(q,24,36,6,6)||inRect(q,54,36,6,6)),'route stays inside the home, not a public core');
 }
 p.world.free();
});

for(const name of ['S1','S2'] as const)test(`WWB bot physically traverses ${name} to L2 and back to G`,()=>{
 const [cx]=cores[name],p=physics();CONFIG.bots.speed=2.4;const target=new THREE.Vector3();const world:any={time:0,onslaught:true,lineOfSight:()=>false,audio:{play:()=>{}},fx:{},groundAt:()=>0};
 const bot=new Bot(1,'TEST','striker','#111','#111',p,nav,world,{scene:new THREE.Group(),clips:[]},{},'operator');bot.wave=true;const s=at(cx+3,0,44);bot.spawn(new THREE.Vector3(s.x,.03,s.z),0);
 const ctx:any={targets:[{id:0,pos:target,vel:new THREE.Vector3(),alive:true,isPlayer:true}],items:[],hotspots:[target],playerEye:target.clone(),playerId:0,frozen:false};
 for(const y of [6,0]){const g=at(cx+3,y,43.5);target.set(g.x,y,g.z);ctx.playerEye=target.clone().add(new THREE.Vector3(0,1.6,0));let reached=false;
  for(let i=0;i<7000;i++){world.time+=1/60;bot.update(1/60,ctx,[bot]);p.step(1/60);if(bot.pos.distanceTo(target)<.75){reached=true;break}}
  assert(reached,`${name} y=${y} bot=${JSON.stringify(toMap(bot.pos.x,bot.pos.y,bot.pos.z))} state=${bot.state}`)}
 p.world.free();
});

test('guards hold the player on the L1 rear gallery, the L2 front concourse and the roof edge',()=>{
 for(const [x,y,z,yaw]of [[42,3,19.2,0],[40,6,35,Math.PI],[30,9,19,0],[59,9,27,-Math.PI/2],[45,3,38.5,Math.PI]]){
  const p=physics(),player=new Player(p),s=at(x,y,z);player.spawn(new THREE.Vector3(s.x,y+.04,s.z),yaw);p.step(1/60);
  for(let i=0;i<150;i++){player.step(1/60,{x:0,y:1,jump:false,sprint:true,ads:false});p.step(1/60)}
  assert(Math.abs(player.position.y-y)<.2,`fell from ${[x,y,z]} to ${JSON.stringify(toMap(player.position.x,player.position.y,player.position.z))}`);p.world.free();
 }
});

test('stair and landing headroom is at least 2.4 m under every slab, tread and cap',()=>{
 const floors=level.solids.filter(s=>s.id==='stair'||s.id==='landing'),overhead=level.solids.filter(s=>surfaceIds.includes(s.id)||s.id.endsWith('-cap'));
 let worst=Infinity;
 for(const f of floors){const top=f.y+f.h/2;for(const o of overhead){if(o===f)continue;const ox=Math.min(f.x+f.w/2,o.x+o.w/2)-Math.max(f.x-f.w/2,o.x-o.w/2),oz=Math.min(f.z+f.d/2,o.z+o.d/2)-Math.max(f.z-f.d/2,o.z-o.d/2);const bottom=o.y-o.h/2;if(ox>.02&&oz>.02&&bottom>top+.01)worst=Math.min(worst,bottom-top)}}
 assert(worst>=2.4,`minimum headroom ${worst}`);
});

test('capture volume is floor-aware: the arcade counts, the galleries above do not',()=>{
 const c=level.capture;assert(inCapture(c,{x:c.x,y:.04,z:c.z}));assert(!inCapture(c,{x:c.x,y:3.04,z:c.z}));assert(!inCapture(c,{x:c.x,y:6.04,z:c.z}));assert(!inCapture(c,{x:c.x+c.radius+.1,y:0,z:c.z}));
});
