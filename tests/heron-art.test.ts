import test from 'node:test'
import assert from 'node:assert/strict'
import {surfaceBelow} from '../src/onsite/wetGround.ts'
import type {Solid} from '../src/onsite/level.ts'

const floor=(y:number):Solid=>({id:'slab',x:0,y:y-.1,z:0,w:8,h:.2,d:8,mat:'concrete'});
test('Lamp reflections select the supporting level, including overlapping floors',()=>{
 const surfaces=[floor(-3),floor(0),floor(3),floor(6)];
 assert.equal(surfaceBelow(0,2.72,0,surfaces),0);
 assert.equal(surfaceBelow(0,5.72,0,surfaces),3);
 assert.equal(surfaceBelow(0,-.48,0,surfaces),-3);
});
test('Street lamps reflect at ground level and unsupported positions stay empty',()=>{
 assert.equal(surfaceBelow(0,4.75,0,[floor(0)]),0);
 assert.equal(surfaceBelow(5,4.75,0,[floor(0)]),null);
 assert.equal(surfaceBelow(0,-4,0,[floor(-3)]),null);
});
