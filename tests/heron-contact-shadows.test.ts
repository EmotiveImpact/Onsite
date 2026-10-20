import test from 'node:test'
import assert from 'node:assert/strict'
import * as THREE from 'three'
import {ContactSupportIndex,contactHeightFade,HeronContactShadows,staticContactPatches} from '../src/onsite/HeronContactShadows.ts'
import {heronReach,heronCourt,type Level} from '../src/onsite/levels.ts'
import type {Solid} from '../src/onsite/level.ts'

const floor=(y:number,x=0,z=0,w=8,d=8):Solid=>({id:'slab',x,y:y-.1,z,w,h:.2,d,mat:'concrete'});
const prop=(base:number):Solid=>({id:'dress',x:0,y:base+.5,z:0,w:.7,h:1,d:.8,mat:'steel'});

test('Supporting contacts select B1, ground, gallery and roof independently at the same x/z',()=>{
 const surfaces=[floor(-3),floor(0),floor(3),floor(9)],index=new ContactSupportIndex(surfaces,['slab']);
 for(const y of [-3,0,3,9])assert.equal(index.below(0,y+.04,0)?.y,y);
 assert.equal(index.below(0,1.8,0),null,'an airborne foot gets no long floating projection');
 assert.equal(index.below(0,2.90,0),null,'a higher slab cannot receive from below');
 assert.equal(index.below(0,2.98,0)?.y,3,'small interpolation penetration is tolerated');
 assert.equal(index.below(8,0,0),null,'no surface is invented outside the receiver');
 assert.equal(index.below(0,-3.1,0),null);
});

test('Stair contacts use the actual tread footprint and fade smoothly with clearance',()=>{
 const treads=[floor(.15,0,0,1.2,.3),floor(.3,0,-.3,1.2,.3),floor(.45,0,-.6,1.2,.3)];
 const index=new ContactSupportIndex(treads,['slab']);
 for(let i=0;i<treads.length;i++){
  const surface=index.below(0,.15*(i+1)+.02,-.3*i)!;
  assert.equal(surface.surface,treads[i]);assert.equal(surface.y,.15*(i+1));
 }
 assert.equal(contactHeightFade(0),1);assert.equal(contactHeightFade(.04),1);
 assert(contactHeightFade(.2)>contactHeightFade(.4));assert.equal(contactHeightFade(.55),0);
 for(const x of [.04,.55])assert(Math.abs(contactHeightFade(x-1e-6)-contactHeightFade(x+1e-6))<1e-8);
});

test('Static footprints follow measured props on their own floors and leave source collision unchanged',()=>{
 const solids=[floor(-3),floor(0),floor(3),prop(-3),prop(0),prop(3),{...prop(0),id:'wall',w:8}];
 const before=JSON.stringify(solids),index=new ContactSupportIndex(solids,['slab']),patches=staticContactPatches(solids,index);
 assert.equal(patches.length,3);
 assert.deepEqual(patches.map(p=>p.y),[-2.986,.014,3.014]);
 assert(patches.every(p=>Math.abs(p.width-.96)<1e-12&&Math.abs(p.depth-1.06)<1e-12&&p.opacity<=.16));
 assert.equal(JSON.stringify(solids),before);
});

test('Real Heron Reach floors support all six current spawn levels and static contacts stay local',()=>{
 const before=JSON.stringify(heronReach.solids),index=new ContactSupportIndex(heronReach.solids,heronReach.surfaceIds);
 for(const spawn of heronReach.botSpawns){
  const support=index.below(spawn.x,spawn.y,spawn.z);
  assert(support,`missing bot receiver at ${JSON.stringify(spawn)}`);
  assert(Math.abs(support.y-(spawn.y-.04))<1e-9);
 }
 const patches=staticContactPatches(heronReach.solids,index);
 assert(patches.length>100&&patches.length<800,'bounded static contact set');
 assert(patches.some(p=>Math.abs(p.y-9.014)<.001),'roof plant receives on its roof');
 assert(patches.every(p=>p.y-(p.support.y+p.support.h/2)<.015));
 assert.equal(JSON.stringify(heronReach.solids),before);
});

test('One fixed instanced batch follows rendered bot feet and removes dead, hidden or airborne actors',()=>{
 const level:Level={...heronReach,solids:[floor(0),floor(3),prop(0)],surfaceIds:['slab']};
 const scene=new THREE.Scene(),contacts=new HeronContactShadows(scene,level),root=new THREE.Group();
 root.position.set(0,3.04,0);root.rotation.y=Math.PI/2;
 const actor={alive:true,parts:{root},scale:1};
 const capacity=contacts.mesh.instanceMatrix.count,staticMatrix=Array.from(contacts.mesh.instanceMatrix.array.slice(0,contacts.staticCount*16));
 assert.equal(scene.children.length,1);assert(contacts.mesh.isInstancedMesh);
 assert.equal(contacts.update([actor]),2);assert.equal(contacts.mesh.count,contacts.staticCount+2);
 const first=new THREE.Matrix4();contacts.mesh.getMatrixAt(contacts.staticCount,first);
 const point=new THREE.Vector3().setFromMatrixPosition(first);
 assert(Math.abs(point.x)<1e-6&&Math.abs(point.y-3.014)<1e-6&&Math.abs(point.z-.14)<1e-6);
 const bounds=contacts.mesh.geometry.getAttribute('onsiteContactBounds');
 assert.deepEqual([bounds.getX(contacts.staticCount),bounds.getY(contacts.staticCount),bounds.getZ(contacts.staticCount),bounds.getW(contacts.staticCount)],[-4,-4,4,4]);
 for(let i=0;i<100;i++){root.position.x=Math.sin(i)*.5;contacts.update([actor])}
 assert.equal(contacts.mesh.instanceMatrix.count,capacity);assert.equal(scene.children.length,1);
 assert.deepEqual(Array.from(contacts.mesh.instanceMatrix.array.slice(0,contacts.staticCount*16)),staticMatrix);
 root.position.y=3.7;assert.equal(contacts.update([actor]),0);
 root.position.y=3.04;actor.alive=false;assert.equal(contacts.update([actor]),0);
 actor.alive=true;root.visible=false;assert.equal(contacts.update([actor]),0);
 root.visible=true;assert.equal(contacts.update(new Array(40).fill(actor)),contacts.actorCapacity*2);
 const material=contacts.mesh.material;
 assert.equal(material.fog,false);assert.equal(material.depthWrite,false);assert.equal(material.depthTest,true);
 assert.equal(contacts.mesh.castShadow,false);
 const shader={...THREE.ShaderLib.basic,uniforms:{}} as Parameters<THREE.Material['onBeforeCompile']>[0];
 material.onBeforeCompile(shader,{} as THREE.WebGLRenderer);
 assert(shader.fragmentShader.includes('contactReceiver'));
 assert(shader.fragmentShader.includes('diffuseColor.a *= vContactOpacity'));
 contacts.dispose();assert.equal(scene.children.length,0);
});

test('Heron Court gets no contact batch or dynamic instances',()=>{
 const scene=new THREE.Scene(),contacts=new HeronContactShadows(scene,heronCourt);
 assert.equal(scene.children.length,0);assert.equal(contacts.staticCount,0);
 assert.equal(contacts.update([{alive:true,parts:{root:new THREE.Group()}}]),0);contacts.dispose();
});
