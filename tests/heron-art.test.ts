import test from 'node:test'
import assert from 'node:assert/strict'
import {surfaceBelow} from '../src/onsite/wetGround.ts'
import type {Solid} from '../src/onsite/level.ts'
import {readFileSync} from 'node:fs'
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js'
import {createHash} from 'node:crypto'

const floor=(y:number):Solid=>({id:'slab',x:0,y:y-.1,z:0,w:8,h:.2,d:8,mat:'concrete'});
test('Compressed Blender architecture preserves metre-scale wall, roof and paving UVs',async()=>{
 const bytes=Uint8Array.from(readFileSync('public/models/heron-reach/heron-reach-arch.glb'));
 const {scene}=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes.buffer,'');scene.updateMatrixWorld(true);
 const checked:Record<string,number>={hr_brick_stock:0,hr_roof_felt:0,hr_paving:0};
 scene.traverse(o=>{
  if(!(o instanceof THREE.Mesh))return;const name=(o.material as THREE.Material).name;if(!(name in checked))return;
  const g=o.geometry,p=g.attributes.position,uv=g.attributes.uv,index=g.index;
  for(let i=0;i<(index?.count??p.count)&&checked[name]<100;i+=3){
   const a=index?index.getX(i):i,b=index?index.getX(i+1):i+1;
   const va=new THREE.Vector3().fromBufferAttribute(p,a).applyMatrix4(o.matrixWorld),vb=new THREE.Vector3().fromBufferAttribute(p,b).applyMatrix4(o.matrixWorld);
   const metres=va.distanceTo(vb);if(metres<1.5)continue;
   const texels=Math.hypot(uv.getX(a)-uv.getX(b),uv.getY(a)-uv.getY(b));
   assert(Math.abs(texels/metres-1)<.06,`${name}: ${texels} UV units across ${metres} metres`);checked[name]++;
  }
 });
 for(const [name,n]of Object.entries(checked))assert(n>=20,'Insufficient exported samples for '+name);
});
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

test('Compressed PBR library covers each source, preserves hashes and contains complete KTX2 mip chains',()=>{
 const lib=JSON.parse(readFileSync('public/materials/heron/runtime-materials.json','utf8'));
 const manifest=JSON.parse(readFileSync('public/materials/heron/ktx2/manifest.json','utf8'));
 const urls=new Set<string>();
 for(const e of Object.values(lib) as Record<string,unknown>[]){for(const key of ['map','normalMap','ormMap','emissiveMap'])if(e[key])urls.add(String(e[key]))}
 assert.equal(Object.keys(manifest.entries).length,urls.size);
 for(const url of urls){
  const e=manifest.entries[url];assert.ok(e,url);
  const source=readFileSync('public'+url),packed=readFileSync('public'+e.url);
  assert.equal(createHash('sha256').update(source).digest('hex'),e.sourceSHA256,url+' stale source');
  assert.equal(createHash('sha256').update(packed).digest('hex'),e.sha256,url+' stale output');
  assert.equal(packed.subarray(0,12).toString('hex'),'ab4b5458203230bb0d0a1a0a',url+' signature');
  assert.equal(packed.readUInt32LE(20),e.width);assert.equal(packed.readUInt32LE(24),e.height);
  assert.equal(packed.readUInt32LE(40),Math.floor(Math.log2(Math.max(e.width,e.height)))+1,url+' mip chain');
 }
});
