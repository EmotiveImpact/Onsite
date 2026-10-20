import test from 'node:test'
import assert from 'node:assert/strict'
import * as THREE from 'three'
import {Physics,initPhysics} from '../src/wwb/engine/physics'
import {Player} from '../src/wwb/game/player'
import {Bot} from '../src/wwb/game/bots'
import {LayeredNav} from '../src/onsite/navigation'
import {solids} from '../src/onsite/level'
import {CONFIG} from '../src/wwb/game/config'
import {operatorFixture} from './operator-fixture'
await initPhysics();const nav=new LayeredNav(),operator=await operatorFixture();
function physics(){const p=new Physics();for(const s of solids)p.addStaticBox(new THREE.Vector3(s.x,s.y,s.z),new THREE.Vector3(s.w,s.h,s.d));p.step(1/60);return p}
test('layered routes connect both stairs and preserve overlapping floors',()=>{for(const [x,z]of [[-10,-5],[10,5]]){const path=nav.findPath(x,z,x,z,0,3)!;assert(path?.length);assert(path.some(p=>p.y>0&&p.y<3));assert(Math.abs(path.at(-1)!.y-3)<.01);assert.notEqual(nav.nearest(x,z,0).id,nav.nearest(x,z,3).id)}});
for(const [name,x,z]of [['A',-10,-5],['B',10,5]] as const)test(`WWB bot physically traverses stair ${name} up and down`,()=>{
 const p=physics();CONFIG.bots.speed=2.4;const target=new THREE.Vector3(x,3,z);const world:any={time:0,onslaught:true,lineOfSight:()=>false,audio:{play:()=>{}},fx:{},groundAt:()=>0};
 const bot=new Bot(1,'TEST','striker','#111','#111',p,nav,world,operator,{},'operator');bot.wave=true;bot.spawn(new THREE.Vector3(x,.03,z),0);
 const ctx:any={targets:[{id:0,pos:target,vel:new THREE.Vector3(),alive:true,isPlayer:true}],items:[],hotspots:[target],playerEye:target.clone().add(new THREE.Vector3(0,1.6,0)),playerId:0,frozen:false};
 for(const y of [3,0]){target.y=y;let reached=false;for(let i=0;i<4200;i++){world.time+=1/60;bot.update(1/60,ctx,[bot]);p.step(1/60);if(bot.pos.distanceTo(target)<.75){reached=true;break}}
 assert(reached,`${name} destination y=${y}, bot=${JSON.stringify(bot.pos)}, state=${bot.state} path=${JSON.stringify((bot as any).path.slice((bot as any).pathI,(bot as any).pathI+4))} vel=${JSON.stringify(bot.vel)}`)}p.world.free();
});
test('WWB player capsule climbs and descends both routes',()=>{for(const [x,z]of [[-10,-5],[10,5]]){
 const p=physics(),player=new Player(p);player.spawn(new THREE.Vector3(x,.03,z),0);p.step(1/60);
 for(const y of [3,0]){const path=nav.findPath(player.position.x,player.position.z,x,z,player.position.y,y)!;assert(path?.length);let i=0;
 for(let ticks=0;ticks<5000&&i<path.length;ticks++){const w=path[i],dx=w.x-player.position.x,dz=w.z-player.position.z;if(Math.hypot(dx,dz)<.2&&Math.abs(w.y-player.position.y)<.4){i++;continue}player.yaw=Math.atan2(-dx,-dz);player.step(1/60,{x:0,y:.45,jump:false,sprint:false,ads:false});p.step(1/60)}assert.equal(i,path.length,`player stuck ${JSON.stringify(player.position)}`);assert(Math.abs(player.position.y-y)<.3)}p.world.free();
 }});

test('WWB player crosses the lobby doorway and reaches court without clipping',()=>{const p=physics(),player=new Player(p);player.spawn(new THREE.Vector3(-9,.04,12),0);p.step(1/60);const path=nav.findPath(-9,12,-7,1,0,0)!;let i=0;for(let t=0;t<5000&&i<path.length;t++){const w=path[i],dx=w.x-player.position.x,dz=w.z-player.position.z;if(Math.hypot(dx,dz)<.2&&Math.abs(w.y-player.position.y)<.4){i++;continue}player.yaw=Math.atan2(-dx,-dz);player.step(1/60,{x:0,y:.5,jump:false,sprint:false,ads:false});p.step(1/60)}assert.equal(i,path.length,JSON.stringify({position:player.position,next:path[i]}));p.world.free()});

test('WWB player cannot pass the outer wall and damage respects spawn protection',()=>{const p=physics(),player=new Player(p);player.spawn(new THREE.Vector3(0,.04,-13),0);assert.equal(player.damage(30).dealt,0);p.step(1/60);for(let i=0;i<180;i++){player.step(1/60,{x:0,y:1,jump:false,sprint:true,ads:false});p.step(1/60)}assert(player.position.z>-14.5);assert(player.damage(30).dealt>0);p.world.free()});
test('continuous courtyard to stair A to gallery to stair B route',()=>{const p=physics(),player=new Player(p);player.spawn(new THREE.Vector3(-9,.04,12),0);CONFIG.player.walkSpeed=4.6;p.step(1/60);for(const [x,y,z]of [[-7,0,1],[-16,1,-5.5],[0,3,-7.5],[15,1.5,7.4],[8,0,5]]){const path=nav.findPath(player.position.x,player.position.z,x,z,player.position.y,y)!;assert(path?.length);let i=0;for(let t=0;t<5000&&i<path.length;t++){const w=path[i],dx=w.x-player.position.x,dz=w.z-player.position.z;if(Math.hypot(dx,dz)<.2&&Math.abs(w.y-player.position.y)<.45){i++;continue}player.yaw=Math.atan2(-dx,-dz);player.step(1/60,{x:0,y:.5,jump:false,sprint:false,ads:false});p.step(1/60)}assert.equal(i,path.length,JSON.stringify({goal:[x,y,z],position:player.position,next:path[i]}))}p.world.free()});

test('actual player enters Flat 01, reaches living area and bedroom, returns to court',()=>{
 const p=physics(),player=new Player(p);player.spawn(new THREE.Vector3(-9,.04,-7),0);p.step(1/60);
 for(const [x,z]of [[-8.5,-11],[-14,-13],[-9,-7]]){
  const path=nav.findPath(player.position.x,player.position.z,x,z,player.position.y,0)!;assert(path?.length);let i=0;
  for(let t=0;t<5000&&i<path.length;t++){const w=path[i],dx=w.x-player.position.x,dz=w.z-player.position.z;if(Math.hypot(dx,dz)<.2&&Math.abs(w.y-player.position.y)<.4){i++;continue}player.yaw=Math.atan2(-dx,-dz);player.step(1/60,{x:0,y:.45,jump:false,sprint:false,ads:false});p.step(1/60)}
  assert.equal(i,path.length,JSON.stringify({goal:[x,z],position:player.position,next:path[i]}));assert(player.position.y<.2);
 }
 player.spawn(new THREE.Vector3(-16.2,.04,-11.1),0);p.step(1/60);
 for(let i=0;i<120;i++){player.step(1/60,{x:0,y:1,jump:false,sprint:false,ads:false});p.step(1/60)}
 assert(player.position.z>-11.9,'Bed collision stops the capsule');p.world.free();
});

test('WWB bot brain routes through furnished Flat 01 without a second movement owner',()=>{
 const p=physics(),target=new THREE.Vector3(-14,0,-13),world:any={time:0,onslaught:true,lineOfSight:()=>false,audio:{play:()=>{}},fx:{},groundAt:()=>0};
 const bot=new Bot(1,'HOME ROUTE','striker','#111','#111',p,nav,world,operator,{},'operator');bot.wave=true;bot.spawn(new THREE.Vector3(-9,.03,-7),0);
 const ctx:any={targets:[{id:0,pos:target,vel:new THREE.Vector3(),alive:true,isPlayer:true}],items:[],hotspots:[target],playerEye:target.clone().add(new THREE.Vector3(0,1.6,0)),playerId:0,frozen:false};
 let reached=false;for(let i=0;i<4200;i++){world.time+=1/60;bot.update(1/60,ctx,[bot]);p.step(1/60);if(bot.pos.distanceTo(target)<.8){reached=true;break}}
 assert(reached,JSON.stringify({position:bot.pos,state:bot.state}));p.world.free();
});
