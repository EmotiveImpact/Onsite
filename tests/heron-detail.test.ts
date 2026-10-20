import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js'
import {hideReplacedShopFittings} from '../src/onsite/heronLivedDetail.ts'

test('Scanned fixture replacement finds real sanitised GLB nodes and preserves the shop backdrop',async()=>{
 const source=readFileSync('public/models/heron-reach/heron-reach-shops.glb'),length=source.readUInt32LE(12);
 const json=JSON.parse(source.subarray(20,20+length).toString());
 // Keep actual node hierarchy/meshopt geometry; omit browser image decoding for this Node test.
 delete json.images;delete json.textures;delete json.materials;
 for(const mesh of json.meshes)for(const primitive of mesh.primitives)delete primitive.material;
 const encoded=Buffer.from(JSON.stringify(json)),padded=Buffer.alloc(Math.ceil(encoded.length/4)*4,32);encoded.copy(padded);
 const bin=source.subarray(20+length),head=Buffer.alloc(20);
 head.writeUInt32LE(0x46546c67,0);head.writeUInt32LE(2,4);head.writeUInt32LE(20+padded.length+bin.length,8);
 head.writeUInt32LE(padded.length,12);head.writeUInt32LE(0x4e4f534a,16);
 const bytes=Uint8Array.from(Buffer.concat([head,padded,bin]));
 const {scene}=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes.buffer,'');
 assert.equal(scene.getObjectByName('E-shop/interior / hr_shop_fitting'),undefined,'Raw authored names are sanitised by the loader');
 assert.equal(hideReplacedShopFittings(scene),2);
 let backdropVisible=false,otherShopFittings=0;
 scene.traverse(o=>{
  if(o.userData.name==='E-shop/interior / hr_shop_image_corner')backdropVisible=o.visible;
  if(typeof o.userData.name==='string'&&o.userData.name.endsWith(' / hr_shop_fitting')&&!o.userData.name.startsWith('E-shop/')){assert(o.visible);otherShopFittings++}
 });
 assert(backdropVisible);assert(otherShopFittings>=1);
});
