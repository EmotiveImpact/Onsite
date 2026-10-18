import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync,existsSync}from'node:fs'
import {createHash}from'node:crypto'
import * as THREE from 'three'
import {Physics,initPhysics}from'../src/wwb/engine/physics'
import {Player}from'../src/wwb/game/player'
import {solids}from'../src/onsite/level'
function glb(path:string){const b=readFileSync(path);assert.equal(b.toString('ascii',0,4),'glTF');return JSON.parse(b.toString('utf8',20,20+b.readUInt32LE(12)))}
test('Blender export contains render architecture and baked occlusion, no collision/nav guides',()=>{
 const g=glb('public/models/onsite-heron-court.glb');assert(g.meshes.length<=26,'Architecture, homes and dressing stay batched by material');assert.equal(g.images?.length??0,0);
 for(const name of ['grass','litter','mud','leak'])assert(g.materials.some((m:any)=>m.name===name),'Missing dressing material '+name);
 for(const n of g.nodes)assert(!/COLLIDER|NAV \/|DONOR \/|Review/.test(n.name??''));
 for(const m of g.meshes)for(const p of m.primitives)assert('COLOR_0'in p.attributes);
 const meta=JSON.parse(readFileSync('public/models/onsite-heron-court.json','utf8'));
 assert.equal(meta.layoutSha256,createHash('sha256').update(readFileSync('docs/development/evidence/layout.json')).digest('hex'));
 assert(meta.dressing.grassBlades>2000&&meta.dressing.grassBlades<10000);
 assert.equal(meta.homes.accessibleHomes,1);assert(meta.homes.privateBalconies>0);
 // The decorative slabs must face the player, not leave only their bevels visible.
 const bytes=readFileSync('public/models/onsite-heron-court.glb'),bin=28+bytes.readUInt32LE(12);
 const vector=(index:number,i:number)=>{const a=g.accessors[index],v=g.bufferViews[a.bufferView],at=bin+(v.byteOffset??0)+(a.byteOffset??0)+i*(v.byteStride??12);assert.equal(a.componentType,5126);return[bytes.readFloatLE(at),bytes.readFloatLE(at+4),bytes.readFloatLE(at+8)]};
 let upwardSlabVertices=0;
 for(const m of g.meshes)for(const p of m.primitives)if(g.materials[p.material].name==='paving')for(let i=0;i<g.accessors[p.attributes.POSITION].count;i++)if(vector(p.attributes.POSITION,i)[1]>.02&&vector(p.attributes.NORMAL,i)[1]>.9)upwardSlabVertices++;
 assert(upwardSlabVertices>1000,'Paving top faces must point upward');
 // Stock-brick tint is neutral AO; its yellow colour comes from the image.
 // This catches stale Blender UV/colour handles corrupting facade vertex data.
 for(const m of g.meshes)for(const p of m.primitives)if(g.materials[p.material].name==='stock'){
  const a=g.accessors[p.attributes.COLOR_0],v=g.bufferViews[a.bufferView],size=a.componentType===5126?4:2;
  assert([5123,5126].includes(a.componentType));
  for(let i=0;i<a.count;i++){const at=bin+(v.byteOffset??0)+(a.byteOffset??0)+i*(v.byteStride??4*size);const rgba=[0,1,2,3].map(k=>size===4?bytes.readFloatLE(at+k*size):bytes.readUInt16LE(at+k*size)/65535);
   assert(Math.max(...rgba.slice(0,3))-Math.min(...rgba.slice(0,3))<.002,'Stock facade UV data must not corrupt vertex colour');assert(rgba[3]>.99,'Untinted walls must stay opaque');
  }
 }
 for(const m of g.meshes)for(const p of m.primitives)if(['mud','grass'].includes(g.materials[p.material].name))assert.equal(g.accessors[p.attributes.COLOR_0].type,'VEC4','Dressing tint/fade alpha survives export');
});
test('Imported rifle external textures exist and imported payloads match provenance',()=>{
 const records=JSON.parse(readFileSync('public/models/donors/provenance.json','utf8'));
 for(const r of records)assert.equal(createHash('sha256').update(readFileSync('public/'+r.file)).digest('hex'),r.sha256,r.file);
 const materials=JSON.parse(readFileSync('public/materials/detail/provenance.json','utf8'));
 const stock=JSON.parse(readFileSync('public/materials/homes/provenance.json','utf8'));assert.equal(createHash('sha256').update(readFileSync(stock.runtime)).digest('hex'),stock.sha256);
 for(const r of materials.assets)assert.equal(createHash('sha256').update(readFileSync('public/'+r.file)).digest('hex'),r.sha256,r.file);
 const g=glb('public/models/donors/m4a1-hands.glb');
 for(const i of g.images??[])if(i.uri)assert(existsSync('public/models/donors/'+i.uri),i.uri);
 assert.deepEqual(g.animations.map((a:any)=>a.name),['grip_vgrip']);
 const derived=glb('public/models/onsite-carbine.glb'),record=JSON.parse(readFileSync('public/models/onsite-carbine.json','utf8'));
 assert.equal(createHash('sha256').update(readFileSync('public/models/onsite-carbine.glb')).digest('hex'),record.sha256);
 assert.equal(derived.skins.length,1);assert.equal(derived.animations?.length??0,0,'No third-party motion tracks introduced');
 assert(derived.images?.length>=6,'Blender finishing must retain the licensed PBR images');
 for(const material of derived.materials){assert(material.pbrMetallicRoughness?.baseColorTexture,'Missing base colour for '+material.name);assert(material.normalTexture,'Missing normal map for '+material.name)}
 for(const n of ['Hand_L','Hand_R','MuzzleSocket','MagazineGripSocket','RearIronSight'])assert(derived.nodes.some((o:any)=>o.name===n),n);
});
test('Donor car collision blocks an actual WWB player capsule',async()=>{
 await initPhysics();const p=new Physics();for(const s of solids)p.addStaticBox(new THREE.Vector3(s.x,s.y,s.z),new THREE.Vector3(s.w,s.h,s.d));
 const player=new Player(p);player.spawn(new THREE.Vector3(7,.04,2.1),0);p.step(1/60);
 for(let i=0;i<100;i++){player.step(1/60,{x:0,y:1,jump:false,sprint:false,ads:false});p.step(1/60)}
 const car=solids.find(s=>s.id==='dress-covered_car')!;assert(player.position.z>car.z+car.d/2+.3);assert(player.position.y<.2);p.world.free();
});
