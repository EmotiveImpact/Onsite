// Heron Reach full shell: the generated level is checked with the real WWB player and bot capsules
// in one Rapier world, plus layered navigation, including the mirrored southern blocks and the undercroft.
import test from 'node:test'
import assert from 'node:assert/strict'
import * as THREE from 'three'
import {Physics,initPhysics} from '../src/wwb/engine/physics'
import {Player} from '../src/wwb/game/player'
import {Bot} from '../src/wwb/game/bots'
import {LayeredNav} from '../src/onsite/navigation'
import {heronReach as level,inCapture} from '../src/onsite/levels'
import {fromMap as at,toMap,surfaceIds,objectives} from '../src/onsite/heronReach'
import spec from '../docs/maps/heron-reach-32/blueprints/build-spec.json'
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
const cores=Object.fromEntries(spec.cores.map(c=>[c.id,c])) as Record<string,typeof spec.cores[number]>;
/** Map point just outside a core's door: south of northern cores, north of mirrored southern cores. */
const portal=(id:string,y:number)=>{const c=cores[id];return at(c.rect[0]+3,y,c.mirrorZ?c.rect[1]-1.5:c.rect[1]+7.5)};
const inCore=(p:P,id:string)=>{const [x,z,w,d]=cores[id].rect;return inRect(p,x,z,w,d)};

test('every core serves its levels on the layered graph, from B1 or G to its top',()=>{
 for(const [id,c]of Object.entries(cores)){
  const base=c.levels[0],top=c.levels.at(-1)!,a=portal(id,base),b=portal(id,top),path=nav.findPath(a.x,a.z,b.x,b.z,base,top)!;assert(path?.length,id);
  for(let y=base+1.5;y<top;y+=1.5)assert(path.some(p=>Math.abs(p.y-y)<.01&&inCore(p,id)),`${id} passes y=${y} inside the core`);
  assert(Math.abs(path.at(-1)!.y-top)<.01,`${id} reaches ${top}`);
 }
 assert.notEqual(nav.nearest(at(42,0,25).x,at(42,0,25).z,0).id,nav.nearest(at(42,0,25).x,at(42,0,25).z,3).id,'stacked floors keep separate nodes');
});

test('the shell connects: both staging yards, the +3 bridges, every +6 island, both roofs and the undercroft loop',()=>{
 const from=at(8,0,60);
 for(const [x,y,z,label]of [[136,0,60,'east yard'],[72,3,37.5,'north bridge'],[72,3,82.5,'south bridge'],[40.5,3,60,'west gallery'],[103.5,3,60,'east gallery'],
  [42,6,27,'Rowan +6'],[102,6,27,'Ash +6'],[42,6,93,'Birch +6'],[102,6,93,'Cedar +6'],[42,9,27,'Rowan roof'],[102,9,93,'Cedar roof'],
  [51,-3,60,'B1 west'],[93,-3,60,'B1 east'],[72,-3,63,'B1 cross'],[72,0,24,'Garden Court'],[72,0,60,'the Cage'],[72,0,96,'Washhouse Square']] as const){
  const t=at(x,y,z),n=nav.nearest(t.x,t.z,y);assert(Math.hypot(n.x-t.x,n.z-t.z)<.6&&Math.abs(n.y-y)<.01,`${label} is walkable`);
  assert(nav.findPath(from.x,from.z,t.x,t.z,0,y)?.length,`route from the west yard to ${label}`);
 }
 // Ash and Birch roofs are closed: no node on them.
 for(const [x,z]of [[102,27],[42,93]]){const t=at(x,9,z),n=nav.nearest(t.x,t.z,9);assert(Math.abs(n.y-9)>.5||Math.hypot(n.x-t.x,n.z-t.z)>3,'non-playable roof stays closed')}
});

for(const id of Object.keys(cores))test(`actual player climbs ${id} through every served level and back`,()=>{
 const c=cores[id],p=physics(),player=new Player(p),s=portal(id,c.levels[0]);player.spawn(new THREE.Vector3(s.x,c.levels[0]+.04,s.z),0);p.step(1/60);
 const order=[...c.levels.slice(1),c.levels[0]];
 for(const y of order){walk(p,player,portal(id,y));assert(Math.abs(player.position.y-y)<.3,`${id} level ${y}: ${player.position.y}`)}
 p.world.free();
});

for(const home of ['NW-H2-1','SE-H2-2'])test(`H2 maisonette ${home}: front door at +3, private stair, rear door at +6, and back again`,()=>{
 const h=spec.homeInstances.find(i=>i.id===home+'-L')!,z=(lz:number)=>h.mirrorZ?h.z+8-lz:h.z+lz;
 const p=physics(),player=new Player(p),front=at(h.x+5.25,3,z(9.5)),upper=at(h.x+7.4,6,z(7)),rear=at(h.x+5.25,6,z(-1.5));
 player.spawn(new THREE.Vector3(front.x,3.04,front.z),0);p.step(1/60);
 for(const [goal,y]of [[upper,6],[rear,6],[upper,6],[front,3]] as const){
  const path=walk(p,player,goal);assert(Math.abs(player.position.y-y)<.3);
  assert(!path.some(q=>Object.keys(cores).some(id=>inCore(q,id))),'route stays inside the home, not a public core');
 }
 p.world.free();
});

for(const [id,down]of [['S1',false],['S7',true]] as const)test(`WWB bot physically traverses ${id} ${down?'from G down to B1 and back':'to L2 and back to G'}`,()=>{
 const p=physics();CONFIG.bots.speed=2.4;const target=new THREE.Vector3();const world:any={time:0,onslaught:true,lineOfSight:()=>false,audio:{play:()=>{}},fx:{},groundAt:()=>0};
 const bot=new Bot(1,'TEST','striker','#111','#111',p,nav,world,{scene:new THREE.Group(),clips:[]},{},'operator');bot.wave=true;const s=portal(id,0);bot.spawn(new THREE.Vector3(s.x,.03,s.z),0);
 const ctx:any={targets:[{id:0,pos:target,vel:new THREE.Vector3(),alive:true,isPlayer:true}],items:[],hotspots:[target],playerEye:target.clone(),playerId:0,frozen:false};
 for(const y of down?[-3,0]:[6,0]){const g=portal(id,y);target.set(g.x,y,g.z);ctx.playerEye=target.clone().add(new THREE.Vector3(0,1.6,0));let reached=false;
  for(let i=0;i<7000;i++){world.time+=1/60;bot.update(1/60,ctx,[bot]);p.step(1/60);if(bot.pos.distanceTo(target)<.75){reached=true;break}}
  assert(reached,`${id} y=${y} bot=${JSON.stringify(toMap(bot.pos.x,bot.pos.y,bot.pos.z))} state=${bot.state}`)}
 p.world.free();
});

test('guards hold a sprinting player at gallery, bridge, island and roof edges',()=>{
 for(const [x,y,z,yaw]of [[42,3,19.2,0],[40,6,35,Math.PI],[30,9,19,0],[59,9,27,-Math.PI/2],[72,3,37.5,0],[72,3,82.5,Math.PI],[40.5,3,60,Math.PI/2],[102,6,100.8,Math.PI],[118,9,93,-Math.PI/2],[66,3,38.6,Math.PI]]){
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

test('objective volumes are floor-aware: ground counts, the undercroft below and galleries above do not',()=>{
 for(const c of objectives){assert(inCapture(c,{x:c.x,y:.04,z:c.z}),c.label);assert(!inCapture(c,{x:c.x,y:-2.96,z:c.z}),c.label);assert(!inCapture(c,{x:c.x,y:3.04,z:c.z}),c.label)}
 const c=level.capture;assert.equal(c.label,'THE CAGE');assert(!inCapture(c,{x:c.x+c.radius+.1,y:0,z:c.z}));
});
