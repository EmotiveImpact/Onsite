import test from 'node:test'
import assert from 'node:assert/strict'
import spec from '../docs/maps/heron-reach-32/blueprints/build-spec.json'
import {solids,surfaceIds} from '../src/onsite/heronReach.ts'
import {buildStairLightAnchors,stairCorePhotometry} from '../src/onsite/heronStairLighting.ts'
import {lightReceiverBelow,lightReceiverFloor,lightSegmentBlocked,prepareLightOccluders,prepareReceiverLights,selectReceiverLights} from '../src/onsite/heronLightSelection.ts'

const surfaces=solids.filter(s=>surfaceIds.includes(s.id)),occluders=prepareLightOccluders(solids),anchors=buildStairLightAnchors();
const lights=prepareReceiverLights(anchors,surfaces).map(l=>({...l,intensity:stairCorePhotometry.intensity,range:stairCorePhotometry.range}));
const stair=spec.stairs['ST-P'];
const samples=[
 ['entry',1.15,5,0],
 ['first-middle',1.15,stair.flightZ+stair.flightRun-4.5*stair.going,5*stair.rise],
 ['half-left',1.15,.95,1.5],['half-middle',3,.95,1.5],['half-right',4.85,.95,1.5],
 ['second-middle',4.85,stair.flightZ+4.5*stair.going,1.5+5*stair.rise],
 ['second-top',4.85,stair.flightZ+8.5*stair.going,1.5+9*stair.rise],
 ['upper-landing',4.85,5,3],
] as const;

test('Stair fixture plan retains full landings and adds one properly mirrored half-landing per flight pair',()=>{
 assert.equal(anchors.filter(a=>a.landing==='full').length,32);
 assert.equal(anchors.filter(a=>a.landing==='half').length,24);
 for(const core of spec.cores){
  const own=anchors.filter(a=>a.coreId===core.id);
  for(const y of core.levels){
   const full=own.find(a=>a.landing==='full'&&a.floorY===y)!;
   assert.equal(full.x,core.rect[0]+1.75-72);
   assert.equal(full.z,core.rect[1]+(core.mirrorZ?1:5)-60);
   assert.equal(full.y,y+2.65);
  }
  assert.equal(own.filter(a=>a.landing==='half').length,core.levels.length-1);
  for(const half of own.filter(a=>a.landing==='half')){
   assert.equal(half.floorY,half.fixtureFloorY-1.5);
   assert.equal(lightReceiverFloor(half,surfaces),half.floorY,'explicit lower-storey receiver wins');
   const point=prepareReceiverLights([half],surfaces)[0].position;
   assert.equal(occluders.some(o=>point.x>o.min.x&&point.x<o.max.x&&point.y>o.min.y&&point.y<o.max.y&&point.z>o.min.z&&point.z<o.max.z),false,'source stays outside existing opaque geometry');
  }
 }
});

test('All mirrored/B1 routes retain a visible own-core fixture at standing and crouched eye heights',()=>{
 let checked=0;
 for(const core of spec.cores)for(const base of core.levels.slice(0,-1))for(const eye of [1.62,1.04])for(const [name,x,z,y]of samples){
  const camera={x:core.rect[0]+x-72,y:base+y+eye,z:core.rect[1]+(core.mirrorZ?6-z:z)-60};
  const floor=lightReceiverBelow(camera,surfaces),selected=selectReceiverLights(lights,camera,floor,occluders,4);
  assert(selected.some(l=>l.anchor.coreId===core.id),`${core.id} ${base} ${name} eye ${eye}`);
  assert(selected.every(l=>l.floorY===base+(name==='upper-landing'?3:0)),`${core.id} ${name}: adjacent floor rejected`);
  assert(selected.length<=4,'software light pool remains bounded');checked++;
 }
 assert.equal(checked,384);
});

test('Half-landing anchors fill the return-flight gap without relaxing opaque spine or slab visibility',()=>{
 const core=spec.cores.find(c=>c.id==='S1')!,fullOnly=lights.filter(l=>l.anchor.landing==='full');
 for(const [name,x,z,y]of samples.filter(p=>p[0]==='half-right'||p[0]==='second-middle')){
  const camera={x:core.rect[0]+x-72,y:y+1.62,z:core.rect[1]+z-60},floor=lightReceiverBelow(camera,surfaces);
  assert.equal(selectReceiverLights(fullOnly,camera,floor,occluders,4).length,0,`${name}: existing gap`);
  const selected=selectReceiverLights(lights,camera,floor,occluders,4);
  assert(selected.some(l=>l.anchor.coreId==='S1'&&l.anchor.landing==='half'));
  assert(selected.every(l=>!lightSegmentBlocked(l.position,camera,occluders)));
 }
 const spine=occluders.find(o=>o.id==='S1-balustrade')!;
 const centre={x:(spine.min.x+spine.max.x)/2,y:1,z:(spine.min.z+spine.max.z)/2};
 assert.equal(lightSegmentBlocked({...centre,x:centre.x-.5},{...centre,x:centre.x+.5},[spine]),true,'well spine still blocks');
 const slab=occluders.find(o=>o.id==='landing')!;
 const middle={x:(slab.min.x+slab.max.x)/2,y:(slab.min.y+slab.max.y)/2,z:(slab.min.z+slab.max.z)/2};
 assert.equal(lightSegmentBlocked({...middle,y:middle.y-.5},{...middle,y:middle.y+.5},[slab]),true,'landing still blocks');
});
