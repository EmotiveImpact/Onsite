import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createHash} from 'node:crypto'
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js'
import {isReplacedShopShelf,loadShopDepth} from '../src/onsite/heronLivedDetail.ts'
import type {HeronReachMaterials} from '../src/onsite/heronReachArt.ts'
import {layout,solids,OX,OZ} from '../src/onsite/heronReach.ts'

type Bounds={min:number[];max:number[]};
const manifest=JSON.parse(readFileSync('assets/blender/heron-reach/shop-depth-manifest.json','utf8'));
const hash=(path:string)=>createHash('sha256').update(readFileSync(path)).digest('hex');

/** Load the actual compressed geometry in Node, without asking a DOM to decode its WebP.
 * Only image references in an in-memory GLB copy are removed; shipped buffers/transforms stay exact. */
async function geometry(name:string){
 const original=readFileSync(`public/models/heron-reach/heron-reach-${name}.glb`),jsonLength=original.readUInt32LE(12);
 const json=JSON.parse(original.subarray(20,20+jsonLength).toString());
 json.materials=json.materials.map((m:{name:string})=>({name:m.name}));delete json.images;delete json.textures;delete json.samplers;
 for(const field of ['extensionsUsed','extensionsRequired'])if(json[field])json[field]=json[field].filter((x:string)=>x!=='EXT_texture_webp');
 const encoded=Buffer.from(JSON.stringify(json)),padding=Buffer.alloc((4-encoded.length%4)%4,32),body=Buffer.concat([encoded,padding]);
 const tail=original.subarray(20+jsonLength),header=Buffer.alloc(20);header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4);
 header.writeUInt32LE(20+body.length+tail.length,8);header.writeUInt32LE(body.length,12);header.writeUInt32LE(0x4e4f534a,16);
 const bytes=Uint8Array.from(Buffer.concat([header,body,tail]));
 const {scene}=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes.buffer,'');scene.updateMatrixWorld(true);return scene;
}

const mapBounds=(s:typeof solids[number]):Bounds=>({min:[s.x+OX-s.w/2,s.y-s.h/2,s.z+OZ-s.d/2],max:[s.x+OX+s.w/2,s.y+s.h/2,s.z+OZ+s.d/2]});
const shelfPlacements=layout.dressing.filter(isReplacedShopShelf);
const boundsFor=(x:number,z:number,height:number)=>{
 const solid=solids.find(s=>s.id==='dress'&&Math.abs(s.x+OX-x)<.05&&Math.abs(s.z+OZ-z)<.05&&Math.abs(s.h-height)<.01);
 assert(solid,`authoritative collider at ${x},${z}`);return mapBounds(solid);
};

test('shop replacement selects exactly the four existing Corner shelves and retains their colliders',()=>{
 assert.equal(shelfPlacements.length,4);
 assert.deepEqual(shelfPlacements.map(p=>[p.x,p.z]),manifest.hideOriginalShelfRenderPlacements.map((p:{x:number;z:number})=>[p.x,p.z]));
 for(const p of shelfPlacements){
  const b=boundsFor(p.x,p.z,2.07);assert(Math.abs(b.max[0]-b.min[0]-1.2)<1e-6);assert(Math.abs(b.max[2]-b.min[2]-.5)<1e-6);
  assert(!isReplacedShopShelf({...p,asset:'SHOP_FRIDGE'}));assert(!isReplacedShopShelf({...p,y:3}));assert(!isReplacedShopShelf({...p,x:p.x+.01}));
 }
 assert(!isReplacedShopShelf({asset:'SHOP_SHELF_UNIT',x:30,y:0,z:52.5}));
});

test('shipped stock triangles remain inside existing furniture footprints and clear both doors and the centre aisle',async()=>{
 const scene=await geometry('shop-depth');
 const allowed=shelfPlacements.map(p=>boundsFor(p.x,p.z,2.07));
 for(const shop of layout.shops.filter(s=>['LAUNDERETTE','WASHHOUSE'].includes(s.name))){
  const [x,z,w,d]=shop.rect;
  for(const p of layout.dressing.filter(p=>p.asset==='WASHING_MACHINE'&&p.x>x&&p.x<x+w&&p.z>z&&p.z<z+d)){
   const b=boundsFor(p.x,p.z,1.1);b.min[1]=1.1;b.max[1]=1.29;allowed.push(b);
  }
 }
 const routes:Bounds[]=[{min:[110.14,.035,47.55],max:[111.86,2.4,50.15]},
  {min:[110,.035,50.15],max:[112,2.4,55.8]},{min:[110.31,.035,55.8],max:[111.69,2.4,57.45]}];
 const tolerance=.006;let triangles=0,meshes=0,colourMin=1,colourMax=0,northStock=0,southStock=0;
 scene.traverse(o=>{if(!(o instanceof THREE.Mesh))return;meshes++;
  const g=o.geometry,p=g.attributes.position,uv=g.attributes.uv,colour=g.attributes.color,index=g.index;
  assert(uv&&colour,'exported UVs and contact shading');
  for(let i=0;i<p.count;i++){
   assert(Number.isFinite(uv.getX(i))&&Number.isFinite(uv.getY(i)));colourMin=Math.min(colourMin,colour.getX(i));colourMax=Math.max(colourMax,colour.getX(i));
  }
  for(let i=0;i<(index?.count??p.count);i+=3){
   const points=[0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld).add(new THREE.Vector3(OX,0,OZ)));
   const lo=[0,1,2].map(j=>Math.min(...points.map(p=>p.getComponent(j)))),hi=[0,1,2].map(j=>Math.max(...points.map(p=>p.getComponent(j))));
   assert(allowed.some(b=>[0,1,2].every(j=>lo[j]>=b.min[j]-tolerance&&hi[j]<=b.max[j]+tolerance)),`triangle outside collider footprints: ${lo}/${hi}`);
   for(const r of routes)assert(![0,1,2].every(j=>hi[j]>r.min[j]+tolerance&&lo[j]<r.max[j]-tolerance),'stock intersects an existing route');
   if((o.material as THREE.Material).name==='hr_lived_atlas'&&lo[0]>112&&hi[0]<113.2&&lo[1]>.15&&hi[1]<1.9){
    if(hi[2]<52.44)northStock++;if(lo[2]>52.56)southStock++;
   }
   triangles++;
  }
 });
 assert.equal(triangles,manifest.triangles);assert(triangles<20000);assert(meshes<=10);
 assert(colourMin<.5&&colourMax>.9,'contact shades survive mesh compression');
 assert(northStock>100&&southStock>100,'centre stock has depth on both sides, replacing the plain backboard');
});

test('retired lived shelf panels cannot overlap the replacement stock',async()=>{
 const scene=await geometry('lived');const centres=shelfPlacements.filter(p=>Math.abs(p.z-52.5)<.1);
 scene.traverse(o=>{if(!(o instanceof THREE.Mesh))return;const p=o.geometry.attributes.position;
  for(let i=0;i<p.count;i++){
   const v=new THREE.Vector3().fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld).add(new THREE.Vector3(OX,0,OZ));
   assert(!centres.some(c=>Math.abs(v.x-c.x)<.61&&Math.abs(v.z-c.z)<.26&&v.y<2.31),'old shelf decoration remains');
  }
 });
});

test('depth loader shares the atlas and hides only authored photographic panels',async()=>{
 const atlas=new THREE.MeshStandardMaterial({name:'hr_lived_atlas',vertexColors:true}),texture=new THREE.Texture();atlas.map=texture;atlas.emissiveMap=texture;
 const lived=new THREE.Group();lived.add(new THREE.Mesh(new THREE.BoxGeometry(),atlas));
 const duplicate=new THREE.MeshStandardMaterial({name:atlas.name}),oldTexture=new THREE.Texture();duplicate.map=oldTexture;duplicate.emissiveMap=oldTexture;
 let disposedTexture=0,disposedMaterial=0;oldTexture.addEventListener('dispose',()=>disposedTexture++);duplicate.addEventListener('dispose',()=>disposedMaterial++);
 const replacement=new THREE.Group(),stock=new THREE.Mesh(new THREE.BoxGeometry(),duplicate);replacement.add(stock);
 const shops=new THREE.Group();const nodes=manifest.hideCardNodes.map((name:string,i:number)=>{const o=new THREE.Object3D();if(i===0)o.name=name;else{o.name='sanitised_'+i;o.userData.name=name}shops.add(o);return o});
 const fitting=new THREE.Object3D();fitting.userData.name='E-shop/interior / hr_shop_fitting';shops.add(fitting);
 const loader={loadAsync:async()=>({scene:replacement})} as unknown as GLTFLoader;
 const materials={names:()=>new Set<string>(['unused-library-material']),get:()=>{throw new Error('Unused library materials must not allocate textures')}} as unknown as HeronReachMaterials;
 await loadShopDepth(loader,materials,lived,shops);
 assert.equal(stock.material,atlas);assert.equal(disposedTexture,1);assert.equal(disposedMaterial,1);
 assert.equal(atlas.map,texture);assert(nodes.every((o:THREE.Object3D)=>!o.visible));assert(fitting.visible);
});

test('stock artifact provenance and cost manifest match the shipped source and texture',()=>{
 assert.equal(hash(manifest.builder),manifest.builderSHA256);
 assert.equal(hash('public/models/heron-reach/heron-reach-shop-depth.glb'),manifest.compressedGLBSHA256);
 assert.equal(hash('public/materials/heron/lived/shop-lived-color.webp'),manifest.textureSHA256);
 assert.equal(readFileSync('public/models/heron-reach/heron-reach-shop-depth.glb').byteLength,manifest.compressedGLBBytes);
 assert.equal(manifest.routeChecks,'passed');assert.equal(manifest.footprintChecks,'passed');
});
