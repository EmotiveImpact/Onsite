import test from 'node:test'
import assert from 'node:assert/strict'
import type {Solid} from '../src/onsite/level.ts'
import {lampAnchors,solids,surfaceIds} from '../src/onsite/heronReach.ts'
import {shopLightAnchors} from '../src/onsite/heronShopArt.ts'
import {coreLightAnchors} from '../src/onsite/heronCoreArt.ts'
import {lightReceiverBelow,lightReceiverFloor,lightSegmentBlocked,prepareLightOccluders,
 prepareReceiverLights,selectReceiverLights} from '../src/onsite/heronLightSelection.ts'

const box=(id:string,x:number,y:number,z:number,w:number,h:number,d:number,mat='concrete'):Solid=>({id,x,y,z,w,h,d,mat});
const surfaces=solids.filter(s=>surfaceIds.includes(s.id));
const anchors=[...lampAnchors.map(a=>a.kind==='court'?{...a,y:6.35}:a),...shopLightAnchors,...coreLightAnchors];
const lights=prepareReceiverLights(anchors,surfaces),occluders=prepareLightOccluders(solids);
const at=(x:number,y:number,z:number)=>selectReceiverLights(lights,{x,y,z},lightReceiverBelow({x,y,z},surfaces),occluders,4);

test('Court receivers stay at ground under an overlapping upper deck; cores keep their landing',()=>{
 const floors=[box('ground',0,-.1,0,10,.2,10),box('slab',0,5.9,0,10,.2,10)];
 assert.equal(lightReceiverFloor({x:0,y:6.35,z:0,kind:'court'},floors),0);
 assert.equal(lightReceiverFloor({x:0,y:5.65,z:0,kind:'core'},floors),3);
 assert.equal(lightReceiverFloor({x:0,y:-.35,z:0,kind:'core'},floors),-3);
 assert.equal(lightReceiverFloor({x:0,y:6.35,z:0,kind:'court',floorY:9},floors),9);
 for(const light of lights.filter(l=>l.anchor.kind==='court'))assert.equal(light.floorY,0);
});

test('Segment visibility rejects intervening walls and slabs, including a parallel ray',()=>{
 const wall=prepareLightOccluders([box('wall',0,1,0,.2,2,4)]);
 assert.equal(lightSegmentBlocked({x:-1,y:1,z:0},{x:1,y:1,z:0},wall),true);
 assert.equal(lightSegmentBlocked({x:-1,y:1,z:3},{x:1,y:1,z:3},wall),false);
 assert.equal(lightSegmentBlocked({x:0,y:1,z:-3},{x:0,y:1,z:3},wall),true);
 const slab=prepareLightOccluders([box('slab',0,3,0,6,.2,6)]);
 assert.equal(lightSegmentBlocked({x:0,y:3.04,z:0},{x:0,y:4,z:0},slab),true);
});

test('Only a shallow exit from a mounting wall is forgiven; glazing and cage mesh transmit light',()=>{
 const wall=prepareLightOccluders([box('wall',0,1,0,.2,2,4)]);
 assert.equal(lightSegmentBlocked({x:0,y:1,z:0},{x:1,y:1,z:0},wall),false);
 assert.equal(lightSegmentBlocked({x:0,y:1,z:0},{x:0,y:1,z:3},wall),true);
 const transparent=prepareLightOccluders([box('glass-shop',0,1,0,.2,2,4,'glass'),box('fence',.5,1,0,.2,2,4,'steel')]);
 assert.equal(lightSegmentBlocked({x:-1,y:1,z:0},{x:1,y:1,z:0},transparent),false);
});

test('Saved Cage camera spends no pool slots on B1 fixtures',()=>{
 const selected=at(-20,1.7,0);
 assert.ok(selected.length>0);
 assert.ok(selected.some(l=>l.anchor.kind==='court'));
 assert.ok(selected.every(l=>l.floorY===0));
});

test('Saved gallery camera selects its own storey rather than court or ground/core fixtures',()=>{
 const selected=at(-20,4.7,-22.9);
 assert.ok(selected.length>0,'Gallery should retain a visible local fixture');
 assert.ok(selected.every(l=>l.floorY===3));
 assert.ok(selected.every(l=>l.anchor.kind!=='court'));
});

test('Saved Corner camera gives both visible shop strips a pool slot',()=>{
 const selected=at(38,1.7,-17);
 const shop=selected.filter(l=>l.anchor.kind==='shop');
 assert.equal(shop.length,2,JSON.stringify(selected.map(l=>l.anchor)));
 assert.ok(selected.every(l=>l.floorY===0));
});
