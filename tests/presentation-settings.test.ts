import test from 'node:test'
import assert from 'node:assert/strict'
import {presentationProfile,cameraPresentation} from '../src/onsite/PresentationSettings'

test('quality choices cannot enable expensive effects on the software fallback',()=>{
 for(const quality of ['auto','balanced','detail'] as const){
  const p=presentationProfile({quality,reducedMotion:true},true,2);
  assert.equal(p.pixelRatio,.5);assert.equal(p.bloom,false);assert.equal(p.reducedMotion,true);
 }
 assert.equal(presentationProfile({quality:'detail',reducedMotion:false},true,2,1).pixelRatio,1);
});
test('balanced rendering caps native resolution and removes bloom without changing gameplay settings',()=>{
 assert.deepEqual(presentationProfile({quality:'balanced',reducedMotion:false},false,2),{pixelRatio:1,bloom:false,reducedMotion:false});
 assert.deepEqual(presentationProfile({quality:'detail',reducedMotion:false},false,2),{pixelRatio:1.5,bloom:true,reducedMotion:false});
});
test('reduced camera kick preserves the actual aim and Arsenal punch state',()=>{
 const punch=Object.freeze({pitch:.08,yaw:.04,roll:.02});
 assert.deepEqual(cameraPresentation(.5,1,punch,true),{pitch:.52,yaw:1.01,roll:.005});
 assert.deepEqual(cameraPresentation(.5,1,punch,false),{pitch:.58,yaw:1.04,roll:.02});
 assert.deepEqual(punch,{pitch:.08,yaw:.04,roll:.02});
});
