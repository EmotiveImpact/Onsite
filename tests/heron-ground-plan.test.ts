import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js'
import {solids,surfaceIds,layout,dressing} from '../src/onsite/heronReach.ts'
import cells from '../public/models/heron-reach/grass-cells.json'
import {buildHeronGroundPlan,GroundAcceptance,plantBounds,type GroundInput} from '../src/onsite/heronGroundPlan.ts'
import {groundGrassDensity} from '../src/onsite/heronGroundRuntime.ts'

const input:GroundInput={solids,surfaceIds,layout,grassCells:cells,existingPlacements:dressing.items};
const before=JSON.stringify({solids,layout,dressing}),plan=buildHeronGroundPlan(input),accept=new GroundAcceptance(input);

test('Ground additions are deterministic and never mutate physics, navigation inputs or dressing',()=>{
 assert.deepEqual(buildHeronGroundPlan(input),plan);
 assert.equal(JSON.stringify({solids,layout,dressing}),before);
 assert.equal(plan.patches.filter(p=>p.kind==='pit').length,layout.trees.length);
 for(const t of layout.trees){const p=plan.patches.find(p=>p.kind==='pit'&&p.source===t.id)!;assert.equal(p.x,t.x);assert.equal(p.z,t.z)}
});

test('Every irregular patch footprint has the same G finish, clear doors/objectives/gates and no B1 opening',()=>{
 for(const p of plan.patches)for(const [x,z]of [[p.x,p.z],...p.outline]){
  assert(accept.supported(x,z),`${p.id}: missing G support`);
  assert.equal(p.y,accept.finishY(x,z)+.002,`${p.id}: crosses raised grass edge`);
  assert(accept.routeClear(x,z),`${p.id}: route clearance`);
 }
 for(const c of layout.cores){const [x,z,w,d]=c.rect;assert.equal(accept.routeClear(x+w/2,z+d/2),false)}
 for(const [x,z]of [[72,48],[72,72],[55,60],[89,60],[72,14],[62,24],[72,24]])assert.equal(accept.routeClear(x,z),false,`protected path ${x},${z}`);
 for(const d of layout.openings.filter(d=>d.y===0&&d.kind.includes('door')))assert.equal(accept.routeClear(d.x,d.z),false);
});

test('Raised shrubs fit the existing interior rims after rotation/scale and root exactly on Blender soil',()=>{
 const shrubs=plan.plants.filter(p=>p.source?.startsWith('planter:'));
 assert.equal(new Set(shrubs.map(p=>p.source)).size,8);
 assert.equal(shrubs.length,10);
 for(const p of shrubs){
  const c=layout.cover.find(c=>`planter:${c.id}`===p.source)!,b=plantBounds(p),[x,z,w,d]=c.rect;
  assert(p.x-b.radius>=x+.12&&p.x+b.radius<=x+w-.12);
  assert(p.z-b.radius>=z+.12&&p.z+b.radius<=z+d-.12);
  assert(Math.abs(b.bottom-(c.y+c.height-.15))<1e-9);
  assert(b.top<=c.y+c.height+.25,'cosmetic foliage stays low above existing cover');
 }
});

test('Extra trunks are outside the sealed site and clear existing lamps/vehicles and context facades',()=>{
 assert.equal(plan.perimeterTrees.length,16);
 for(const p of plan.perimeterTrees){
  assert(p.z<=-1.9||p.z>=121.9);
  assert.equal(p.y,.12,'existing context pavement finish');
  assert(p.asset.endsWith('_LOD1'));
  assert(input.existingPlacements!.every(q=>Math.hypot(q.x-p.x,q.z-p.z)>=1.5));
  // Context facades start 17.2 m beyond the wall; conservative 5m tree canopy stays clear.
  assert(p.z<0?p.z-5>-17.2:p.z+5<137.2);
 }
 assert.equal(plan.stats.treeTriangles,17452);
});

test('Support rejects upper floors, stairs and holes instead of projecting foliage onto another storey',()=>{
 const empty={...layout,cores:[],openings:[],spawns:[],objectives:[]};
 const make=(geometry:typeof solids)=>new GroundAcceptance({...input,layout:empty,solids:geometry,grassCells:{cell:2,cells:[]}});
 const base={id:'slab',x:0,y:2.9,z:0,w:8,h:.2,d:8,mat:'concrete'};
 assert.equal(make([base]).supported(72,60),false,'overhead +3 slab is not G support');
 assert.equal(make([{...base,id:'stair',y:-.1}]).supported(72,60),false,'a tread never becomes a planting surface');
 const A=make([{...base,x:-2,y:-.1,w:2},{...base,x:2,y:-.1,w:2}]);
 assert.equal(A.supported(72,60),false,'gap between slabs remains a hole');
 assert.equal(A.supported(70,60),true);
 assert.equal(A.accept([[70,60],[72,60]],0),false,'supported centre cannot hide unsupported extent');
});

test('Bare pockets thin only the existing grass owner and the Blender/plant total remains below 30k triangles',()=>{
 const p=plan.patches.find(p=>p.kind==='soil'&&accept.grassAt(p.x,p.z))!;
 assert.equal(groundGrassDensity(plan,p.x,p.z),.13);
 assert.equal(groundGrassDensity(plan,-100,-100),1);
 const manifest=JSON.parse(readFileSync(new URL('../assets/blender/heron-reach/ground-detail-manifest.json',import.meta.url),'utf8'));
 assert(manifest.triangles+plan.stats.plantTriangles<=30000);
 assert.equal(manifest.plantTriangles,plan.stats.plantTriangles);
});

test('Exported Blender vertices sit millimetres above their own G finish with upward faces and no embedded textures',async()=>{
 const bytes=readFileSync(new URL('../public/models/heron-reach/heron-reach-ground-detail.glb',import.meta.url));
 const json=JSON.parse(bytes.toString('utf8',20,20+bytes.readUInt32LE(12)));
 assert.equal(json.images?.length??0,0);assert.equal(json.textures?.length??0,0);
 assert(json.meshes.length<=90,'spatial batches stay bounded');
 const gltf=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
 gltf.scene.updateMatrixWorld(true);let triangles=0,vertices=0;
 const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3(),ab=new THREE.Vector3(),ac=new THREE.Vector3();
 gltf.scene.traverse(o=>{if(!(o instanceof THREE.Mesh))return;
  const g=o.geometry,p=g.getAttribute('position'),ix=g.index;
  for(let i=0;i<p.count;i++){
   a.fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld);const x=a.x+72,z=a.z+60,finish=accept.finishY(x,z);
   assert(accept.supported(x,z),`${o.name}: exported unsupported vertex`);
   assert(a.y>=finish+.0015&&a.y<=finish+.008,`${o.name}: floating/buried finish ${a.y} vs ${finish}`);vertices++;
  }
  for(let i=0;i<(ix?.count??p.count);i+=3){
   a.fromBufferAttribute(p,ix?ix.getX(i):i).applyMatrix4(o.matrixWorld);
   b.fromBufferAttribute(p,ix?ix.getX(i+1):i+1).applyMatrix4(o.matrixWorld);
   c.fromBufferAttribute(p,ix?ix.getX(i+2):i+2).applyMatrix4(o.matrixWorld);
   assert(ab.subVectors(b,a).cross(ac.subVectors(c,a)).y>=-1e-8,`${o.name}: reversed ground face`);triangles++;
  }
 });
 assert(vertices>1000);assert.equal(triangles,5240);
});
