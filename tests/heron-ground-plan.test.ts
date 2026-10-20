import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createHash} from 'node:crypto'
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js'
import {solids,surfaceIds,layout,dressing} from '../src/onsite/heronReach.ts'
import cells from '../public/models/heron-reach/grass-cells.json'
import props from '../assets/blender/heron-reach/props-manifest.json'
import winter from '../assets/blender/heron-reach/winter-manifest.json'
import {buildHeronGroundPlan,GroundAcceptance,plantBounds,type GroundInput,type GroundPlacement} from '../src/onsite/heronGroundPlan.ts'
import {groundGrassDensity} from '../src/onsite/heronGroundRuntime.ts'

const input:GroundInput={solids,surfaceIds,layout,grassCells:cells,existingPlacements:dressing.items};
const before=JSON.stringify({solids,layout,dressing}),plan=buildHeronGroundPlan(input),accept=new GroundAcceptance(input);

const planeNames=['TREE_PLANE_A_LOD1','TREE_PLANE_B_LOD1'] as const;
// Captured from the original mixed-species plan: this correction changes species only.
const originalPerimeterTransforms=[
 [16.5,.12,-1.9,3.6328134777112866],[34.5,.12,-1.9,2.0708518802742475],
 [52.5,.12,-1.9,3.96646497012605],[70.5,.12,-1.9,1.4695310077129398],
 [88.5,.12,-1.9,.32241996290464886],[106.5,.12,-1.9,.47475181270274336],
 [124.5,.12,-1.9,.47525140936160465],[142.5,.12,-1.9,3.401166964194039],
 [16.5,.12,121.9,.9313656936381013],[34.5,.12,121.9,1.096278292738134],
 [52.5,.12,121.9,.8172052948628553],[70.5,.12,121.9,3.6640204898396043],
 [88.5,.12,121.9,.49838222251436676],[106.5,.12,121.9,4.259758396764751],
 [124.5,.12,121.9,1.2665383068153169],[142.5,.12,121.9,.8541841926849447],
];
// Decoded plane bounds from the original mixed-species GLB at 42471ab. gltfpack
// -vpf quantizes floating-point positions: Blender's unquantized maxY 7.512376785
// already shipped as 7.51220703125. Species selection must preserve that geometry.
const originalExportedPlaneBounds:Record<string,{min:number[];max:number[]}>= {
 TREE_PLANE_A_LOD1:{min:[-2.53369140625,-.07958984375,-2.020263671875],max:[2.238037109375,7.51220703125,3.169189453125]},
 TREE_PLANE_B_LOD1:{min:[-1.5478515625,-.0732421875,-2.42919921875],max:[2.451904296875,7.19580078125,2.661376953125]},
};
// Canonical decoded attributes and indices from 42471ab, independent of GLB packing.
const originalPlaneGeometry:Record<string,string>={
 TREE_PLANE_A_LOD1_bark:'e073cbe737a713c47f30ee2d200e034085bf0bbc3d9d5e0e9f78bfee56ecbb5e',
 TREE_PLANE_A_LOD1_leaves:'4153768521d48d4b24d71bbebb2b46a36c476d36cdeddfb7c2343fa6157b891d',
 TREE_PLANE_B_LOD1_bark:'06748811cdce708cda99ac3cabe180f9b90ae57b042524a3d14831c9b22a765b',
 TREE_PLANE_B_LOD1_leaves:'24323e27218729415c65c9153923a0ae2c474f64b5abb594bdcd7090785691b1',
};
function geometryFingerprint(g:THREE.BufferGeometry){
 const attributes=Object.keys(g.attributes).sort().map(name=>{
  const a=g.getAttribute(name),values:number[]=[];
  for(let i=0;i<a.count;i++)for(let c=0;c<a.itemSize;c++)values.push(a.getComponent(i,c));
  return {name,itemSize:a.itemSize,count:a.count,values};
 });
 assert(g.index);const indices=Array.from({length:g.index.count},(_,i)=>g.index!.getX(i));
 return createHash('sha256').update(JSON.stringify({attributes,indices})).digest('hex');
}
// Same placement transform as loadHeronReachKits, in map coordinates (common +72/+60 offset).
function placementMatrix(p:GroundPlacement){const s=p.scale??1;return new THREE.Matrix4().compose(
 new THREE.Vector3(p.x,p.y,p.z),new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),p.ry),new THREE.Vector3(s*(p.sx??1),s,s));}
async function loadGroundTrees(){
 const bytes=Uint8Array.from(readFileSync(new URL('../public/models/heron-reach/heron-reach-ground-trees.glb',import.meta.url)));
 const {scene}=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes.buffer,'');scene.updateMatrixWorld(true);
 return {scene,json:JSON.parse(new TextDecoder().decode(bytes.subarray(20,20+new DataView(bytes.buffer).getUint32(12,true))))};
}
let loadedTrees:ReturnType<typeof loadGroundTrees>|undefined;
const groundTrees=()=>loadedTrees??=loadGroundTrees();
function treeGeometry(root:THREE.Object3D,placement=new THREE.Matrix4()){
 const inv=new THREE.Matrix4().copy(root.matrixWorld).invert(),vertices:THREE.Vector3[]=[],triangles:THREE.Triangle[]=[];
 root.traverse(o=>{if(!(o instanceof THREE.Mesh))return;
  const matrix=placement.clone().multiply(inv).multiply(o.matrixWorld),position=o.geometry.getAttribute('position'),index=o.geometry.index;
  const points=Array.from({length:position.count},(_,i)=>new THREE.Vector3().fromBufferAttribute(position,i).applyMatrix4(matrix));vertices.push(...points);
  for(let i=0;i<(index?.count??position.count);i+=3)triangles.push(new THREE.Triangle(points[index?index.getX(i):i],points[index?index.getX(i+1):i+1],points[index?index.getX(i+2):i+2]));
 });
 return {vertices,triangles,bounds:new THREE.Box3().setFromPoints(vertices)};
}

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

test('The 16 perimeter trees retain their exact centres/yaws and select only existing plane LOD1 variants',()=>{
 assert.deepEqual(plan.perimeterTrees.map(p=>[p.x,p.y,p.z,p.ry]),originalPerimeterTransforms);
 assert.deepEqual(plan.perimeterTrees.map(p=>p.asset),Array.from({length:16},(_,i)=>planeNames[Math.floor(i/2)%2]));
 for(const p of plan.perimeterTrees){assert.equal(p.scale??1,1);assert.equal(p.sx??1,1);assert.equal(p.source,'outside-boundary')}
 assert.equal(plan.stats.treeTriangles,23408);
 for(const file of ['../assets/blender/heron-reach/ground-plan.json','../public/models/heron-reach/ground-plan.json']){
  const shipped=JSON.parse(readFileSync(new URL(file,import.meta.url),'utf8'));
  assert.deepEqual(shipped.perimeterTrees,plan.perimeterTrees,`${file}: regenerate both copies after changing species`);
  assert.equal(shipped.stats.treeTriangles,23408);
 }
});

test('The additive export preserves both plane LOD1 dimensions, source attributes and texture-free material names',async()=>{
 const {scene,json}=await groundTrees();
 assert.equal(json.images?.length??0,0);assert.equal(json.textures?.length??0,0);
 assert.deepEqual(json.materials.map((m:{name:string})=>m.name).sort(),['hr_bark_plane','hr_leaf_plane']);
 assert.deepEqual(scene.children.map(o=>o.name).sort(),[...planeNames]);
 assert.equal(json.meshes.length,4);
 assert.equal(json.meshes.reduce((n:number,m:{primitives:unknown[]})=>n+m.primitives.length,0),4);
 assert(json.extensionsRequired.includes('EXT_meshopt_compression'));
 let total=0;
 for(const name of planeNames){
  const root=scene.getObjectByName(name);assert(root,`missing named runtime root ${name}`);
  const geometry=treeGeometry(root),source=winter.assets.flatMap(a=>a.lods).find(lod=>lod.name===name);assert(source);
  assert.equal(geometry.triangles.length,source.triangles);total+=geometry.triangles.length;
  for(const side of ['min','max'] as const)assert.deepEqual(geometry.bounds[side].toArray(),originalExportedPlaneBounds[name][side],`${name}: original exported ${side} changed`);
  root.traverse(o=>{if(!(o instanceof THREE.Mesh))return;
   assert(!Array.isArray(o.material));const bark=o.material.name==='hr_bark_plane',g:THREE.BufferGeometry=o.geometry,p=g.getAttribute('position');
   assert.equal(geometryFingerprint(g),originalPlaneGeometry[o.name],`${o.name}: original positions, normals, UVs, colours or triangle indices changed`);
   assert.deepEqual(Object.keys(g.attributes).sort(),bark?['color','normal','position','uv']:['normal','position','uv']);
   for(const attribute of Object.values(g.attributes)){
    assert.equal(attribute.count,p.count);
    for(let i=0;i<attribute.count;i++)for(let c=0;c<attribute.itemSize;c++)assert(Number.isFinite(attribute.getComponent(i,c)),`${o.name}: non-finite authored attribute`);
   }
   const normals=g.getAttribute('normal'),uv=g.getAttribute('uv');
   for(let i=0;i<normals.count;i++)assert(Math.abs(Math.hypot(normals.getX(i),normals.getY(i),normals.getZ(i))-1)<.01,`${o.name}: invalid source normal`);
   assert(new Set(Array.from({length:uv.count},(_,i)=>`${uv.getX(i)},${uv.getY(i)}`)).size>=4,`${o.name}: source UVs lost`);
   if(bark){const colour=g.getAttribute('color');assert(Array.from({length:colour.count},(_,i)=>colour.getX(i)).some(v=>v<.9),`${o.name}: authored bark tint lost`)}
  });
 }
 assert.equal(total,2926);assert.equal(total*8,plan.stats.treeTriangles);
});

test('Rotated exported plane crowns clear context facades, full lamp envelopes, street props and each other',async()=>{
 const {scene}=await groundTrees(),[sx,sz,sw,sd]=layout.site;
 const exterior=(p:GroundPlacement)=>p.x<sx||p.x>sx+sw||p.z<sz||p.z>sz+sd;
 const visualBounds=new Map(props.assets.map(a=>[a.name,new THREE.Box3(
  new THREE.Vector3(a.bounds.min[0],a.bounds.min[2],-a.bounds.max[1]),new THREE.Vector3(a.bounds.max[0],a.bounds.max[2],-a.bounds.min[1]))]));
 // South London kits have no props manifest. These full visual bounds come from
 // south-london/build_structures.py:28–52, build_misc.py:92–94 and build_signs.py:19,41–45.
 for(const [name,min,max]of [
  ['hr_prop_bike_hangar',[-1.28,0,-.995],[1.28,1.365,.815]],
  ['hr_prop_speed_hump_rubber_3m',[-1.5,0,-.45],[1.5,.065,.45]],
  ['hr_prop_sign_estate_board_posts',[-.9,0,-.095],[.9,1.85,.004]],
 ] as const)visualBounds.set(name,new THREE.Box3(new THREE.Vector3(...min),new THREE.Vector3(...max)));
 const lamp=visualBounds.get('LAMP_COLUMN')!;
 assert.deepEqual(lamp.min.toArray(),[-.25,0,-.25]);assert.deepEqual(lamp.max.toArray(),[.25,5,.25],'include the half-metre lantern, not only its .12 m collider');
 const obstacles=dressing.items.filter(p=>exterior(p)||p.asset==='LAMP_COLUMN').map(p=>{
  const bounds=visualBounds.get(p.asset);assert(bounds,`${p.asset}: missing full visual envelope for an exterior placement`);
  return {placement:p,bounds:bounds.clone().applyMatrix4(placementMatrix(p)).expandByScalar(.05)};
 });
 assert.equal(obstacles.filter(o=>exterior(o.placement)&&o.placement.asset==='LAMP_COLUMN').length,32,'both actual street-lamp rows are checked');
 // heron_art_context.py streets()/terraces()/facade_cards(): wall .3 + two 3.2 m
 // pavements + 9 m road + 1.5 m setback, less .12 m projecting window cards.
 const facadeOffset=.3+3.2+9+3.2+1.5-.12;
 const placed=plan.perimeterTrees.map(p=>{const root=scene.getObjectByName(p.asset);assert(root);return {placement:p,...treeGeometry(root,placementMatrix(p))}});
 for(const tree of placed){
  const {placement:p,bounds}=tree,label=`${p.asset} at ${p.x},${p.z}`;
  assert(exterior(p));assert(input.existingPlacements!.every(q=>Math.hypot(q.x-p.x,q.z-p.z)>=1.5),`${label}: existing placement centre`);
  assert(bounds.min.x>sx-facadeOffset+10&&bounds.max.x<sx+sw+facadeOffset-10,`${label}: side facade clearance`);
  assert(bounds.min.z>sz-facadeOffset+10&&bounds.max.z<sz+sd+facadeOffset-10,`${label}: north/south facade clearance`);
  for(const obstacle of obstacles)if(bounds.intersectsBox(obstacle.bounds)){
   // A crown can overhang a low car. Test the real triangles against the full prop
   // envelope, so empty space below the crown does not create a false collision.
   assert(!tree.triangles.some(t=>obstacle.bounds.intersectsTriangle(t)),`${label}: overlaps ${obstacle.placement.asset} at ${obstacle.placement.x},${obstacle.placement.z}`);
  }
 }
 for(let i=0;i<placed.length;i++)for(let j=i+1;j<placed.length;j++)assert(!placed[i].bounds.clone().expandByScalar(.5).intersectsBox(placed[j].bounds),`perimeter crown envelopes ${i}/${j} overlap`);
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
 assert.equal(manifest.treeTriangles,plan.stats.treeTriangles);
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
