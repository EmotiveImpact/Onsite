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
 const g=glb('public/models/onsite-heron-court.glb');assert.equal(g.meshes.length,14);assert.equal(g.images?.length??0,0);
 for(const n of g.nodes)assert(!/COLLIDER|NAV \/|DONOR \/|Review/.test(n.name??''));
 for(const m of g.meshes)for(const p of m.primitives)assert('COLOR_0'in p.attributes);
 const meta=JSON.parse(readFileSync('public/models/onsite-heron-court.json','utf8'));
 assert.equal(meta.layoutSha256,createHash('sha256').update(readFileSync('docs/development/evidence/layout.json')).digest('hex'));
});
test('Imported rifle external textures exist and imported payloads match provenance',()=>{
 const records=JSON.parse(readFileSync('public/models/donors/provenance.json','utf8'));
 for(const r of records)assert.equal(createHash('sha256').update(readFileSync('public/'+r.file)).digest('hex'),r.sha256,r.file);
 const g=glb('public/models/donors/m4a1-hands.glb');
 for(const i of g.images??[])if(i.uri)assert(existsSync('public/models/donors/'+i.uri),i.uri);
 assert.deepEqual(g.animations.map((a:any)=>a.name),['grip_vgrip']);
});
test('Donor car collision blocks an actual WWB player capsule',async()=>{
 await initPhysics();const p=new Physics();for(const s of solids)p.addStaticBox(new THREE.Vector3(s.x,s.y,s.z),new THREE.Vector3(s.w,s.h,s.d));
 const player=new Player(p);player.spawn(new THREE.Vector3(7,.04,2.1),0);p.step(1/60);
 for(let i=0;i<100;i++){player.step(1/60,{x:0,y:1,jump:false,sprint:false,ads:false});p.step(1/60)}
 const car=solids.find(s=>s.id==='dress-covered_car')!;assert(player.position.z>car.z+car.d/2+.3);assert(player.position.y<.2);p.world.free();
});
