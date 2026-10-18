import test from 'node:test';
import assert from 'node:assert/strict';
import { Simulation, DT } from '../src/sim/Simulation.js';
import { findRoute, nearestNode } from '../src/sim/navigation.js';
import { reloadMagazine, accuracy } from '../src/adapted/gameplay.js';
import { FixedStepper } from '../src/adapted/loop.js';
const ticks=(s,n,c={})=>{let r;for(let i=0;i<n;i++)r=s.tick(c);return r;};
function place(s,actor,p){actor.body.setTranslation(p,true);actor.body.setNextKinematicTranslation(p);s.world.step();}
const setup=async t=>{const s=await Simulation.create();t.after(()=>s.dispose());return s;};
test('floor, wall and fence collision stop a sprinting capsule',async t=>{
  const s=await setup(t);ticks(s,60);assert(s.grounded);assert(Math.abs(s.player.body.translation().y-.865)<.03);
  place(s,s.player,{x:18,y:1,z:12});ticks(s,240,{moveX:1,sprint:true});assert(s.player.body.translation().x<19.22);
  place(s,s.player,{x:12,y:1,z:-7});ticks(s,120,{moveX:1});assert(s.player.body.translation().x<15.82);
});
test('real stairs ascend to the elevated landing and descend without falling through',async t=>{
  const s=await setup(t);s.botHealth=0;s.bot.collider.setEnabled(false);
  place(s,s.player,{x:-13.8,y:1,z:5.4});ticks(s,170,{moveZ:1});
  const top=s.player.body.translation();assert(top.y>3.95,JSON.stringify(top));assert(top.z< -3,JSON.stringify(top));
  ticks(s,200,{moveZ:-1});assert(s.player.body.translation().y<1.2);assert(s.player.body.translation().y>.8);
});
test('jump is edge-triggered and gravity returns the player to ground',async t=>{
 const s=await setup(t);ticks(s,30);let high=0;for(let i=0;i<100;i++){s.tick({jump:true});high=Math.max(high,s.player.body.translation().y);}
 assert(high>1.8);assert(s.grounded);assert(s.player.body.translation().y<1);
});
test('diagonal normalization and command sequence rejection prevent extra movement',async t=>{
 const a=await setup(t),b=await setup(t);ticks(a,30);ticks(b,30);
 const p=a.player.body.translation();ticks(a,30,{moveZ:1});ticks(b,30,{moveZ:1,moveX:1});
 const da=Math.hypot(a.player.body.translation().x-p.x,a.player.body.translation().z-p.z),db=Math.hypot(b.player.body.translation().x-p.x,b.player.body.translation().z-p.z);assert(db<=da+.05 && db>da*.85);
 const before=a.snapshot();a.tick({sequence:before.lastSequence,moveZ:1,fire:true});assert.deepEqual(a.snapshot().player,before.player);assert.equal(a.tickNumber,before.tick);
});
test('cover blocks hitscan damage and bot sight; clear line of sight allows both',async t=>{
 const s=await setup(t);place(s,s.player,{x:1,y:.87,z:0});place(s,s.bot,{x:1,y:.87,z:-8});s.botYaw=Math.PI;
 // Low aiming line passes through the concrete cover at z=-4.
 ticks(s,1,{fire:true,pitch:-.09});assert.equal(s.botHealth,100);
 // Full fence blocks rays and bot damage.
 place(s,s.player,{x:12,y:.87,z:5});place(s,s.bot,{x:12,y:.87,z:-7});ticks(s,150,{fire:true});assert.equal(s.botHealth,100);assert.equal(s.health,100);
 s.reset();place(s,s.player,{x:7,y:.87,z:0});place(s,s.bot,{x:7,y:.92,z:-7});ticks(s,100);assert(s.health<100);
 ticks(s,30,{fire:true});assert.equal(s.botHealth,0);assert(s.stats.hits>=2);
});
test('reload blocks fire, conserves ammunition, and respects limited reserve',async t=>{
 const s=await setup(t);ticks(s,20,{fire:true});const used=24-s.ammo;assert(used>=2&&used<=3);
 s.tick({reload:true,fire:true});const ammo=s.ammo;ticks(s,50,{fire:true});assert.equal(s.ammo,ammo);
 ticks(s,60);assert.equal(s.ammo,24);assert.equal(s.reserve,96-used);assert.deepEqual(reloadMagazine(22,1),{mag:23,reserve:0});
});
test('eliminate, capture, finish and restart reset all gameplay state',async t=>{
 const s=await setup(t);place(s,s.player,{x:7,y:.87,z:0});place(s,s.bot,{x:7,y:.92,z:-7});ticks(s,30,{fire:true});assert.equal(s.botHealth,0);
 place(s,s.player,{x:7,y:.92,z:-7});ticks(s,181);assert.equal(s.status,'won');assert(accuracy(s.stats)>0);
 const tick=s.tickNumber;s.tick({fire:true});assert.equal(s.tickNumber,tick);s.reset();assert.equal(s.botHealth,100);assert.equal(s.health,100);assert.equal(s.ammo,24);assert.equal(s.status,'active');assert.equal(s.stats.shots,0);
});
test('bot can end encounter, and timeout is terminal',async t=>{
 const s=await setup(t);place(s,s.player,{x:7,y:.87,z:0});place(s,s.bot,{x:7,y:.92,z:-7});ticks(s,700);assert.equal(s.status,'lost');
 s.reset();s.tickNumber=10800;s.tick({});assert.equal(s.status,'lost');
});
test('navigation keeps both floors and routes upward through all stair nodes',()=>{
 const lower=nearestNode({x:-16,y:1,z:-12}),upper=nearestNode({x:-16,y:4,z:-12});assert.notEqual(lower.id,upper.id);
 const route=findRoute({x:7,y:1,z:-7},{x:-16,y:4,z:-12});assert(route.some(n=>n.id==='step-0'));assert(route.some(n=>n.id==='step-15'));assert.equal(route.at(-1).id,'upper-mid');
 for(let i=1;i<route.length;i++)assert(Math.abs(route[i].y-route[i-1].y)<.3);
});
test('fixed-step clock is render-rate independent and reset discards paused time',()=>{
 const run=(fps)=>{const l=new FixedStepper();let n=0;for(let i=0;i<fps*2;i++)l.advance(1/fps,()=>{n++;});return n;};
 assert(Math.abs(run(30)-run(144))<=1);const l=new FixedStepper();l.advance(.01,()=>{});l.resetAccumulator();assert.equal(l.accumulator,0);
});
