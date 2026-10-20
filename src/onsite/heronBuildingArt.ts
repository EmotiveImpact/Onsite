import * as THREE from 'three'
import type {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {layout, OX, OZ} from './heronReach'
import type {HeronReachMaterials} from './heronReachArt'
import {applyHeronSurfaceResponse} from './heronSurfaceResponse'

type Bounds={x0:number;x1:number;y0:number;y1:number;z0:number;z1:number}
export type PrivateStairRetirement={trianglesRemoved:number;meshesChanged:number;perHome:Record<string,number>;perMaterial:Record<string,number>}
export type NarrowJoineryRetirement={trianglesRemoved:number;jambTrianglesRemoved:number;leafTrianglesRemoved:number;meshesChanged:number;perDoor:Record<string,number>}
export type AdjacentLeafRetirement={trianglesRemoved:number;meshesChanged:number;perDoor:Record<string,number>}
export type UpperEntryLeafRetirement={trianglesRemoved:number;paintTrianglesRemoved:number;glassTrianglesRemoved:number;meshesChanged:number;perDoor:Record<string,number>}
// Match the source architecture's measured 7.51 mm half-step quantisation error.
const epsilon=.008
const inside=(b:Bounds,x0:number,x1:number,y0:number,y1:number,z0:number,z1:number)=>
 b.x0>=x0-epsilon&&b.x1<=x1+epsilon&&b.y0>=y0-epsilon&&b.y1<=y1+epsilon&&b.z0>=z0-epsilon&&b.z1<=z1+epsilon
const treadMaterials=new Set(['hr_concrete_cast','hr_concrete_board','hr_rubber'])

/** Retire only eight H2 maisonettes' old private treads, top guard and the two
 * finish sheets that incorrectly span their stair voids. Walls, slabs, public
 * stairs and all other home finishes remain. The original GLB is never edited. */
export function removeLegacyPrivateStairs(architecture:THREE.Object3D):PrivateStairRetirement {
 const previous=architecture.userData.privateStairRetirement as PrivateStairRetirement|undefined
 if(previous)return previous
 const homes=layout.homes.filter(h=>h.module==='H2-L')
 const report:PrivateStairRetirement={trianglesRemoved:0,meshesChanged:0,perHome:{},perMaterial:{}}
 const p=new THREE.Vector3(),b:Bounds={x0:0,x1:0,y0:0,y1:0,z0:0,z1:0}
 architecture.updateMatrixWorld(true)
 architecture.traverse(object=>{
  if(!(object instanceof THREE.Mesh)||Array.isArray(object.material))return
  const name=object.material.name,isTread=treadMaterials.has(name)
  if(!isTread&&!['hr_steel_black','hr_ceiling','hr_floor_laminate'].includes(name))return
  const geometry=object.geometry,positions=geometry.getAttribute('position'),index=geometry.index
  if(!positions)return
  const mapped=new Float64Array(positions.count*3)
  for(let i=0;i<positions.count;i++){
   p.fromBufferAttribute(positions,i).applyMatrix4(object.matrixWorld)
   mapped.set([p.x+OX,p.y,p.z+OZ],i*3)
  }
  const retained:number[]=[],count=index?.count??positions.count
  let removed=0
  for(let i=0;i<count;i+=3){
   const a=index?index.getX(i):i,c=index?index.getX(i+1):i+1,d=index?index.getX(i+2):i+2
   const lo=[0,1,2].map(k=>Math.min(mapped[a*3+k],mapped[c*3+k],mapped[d*3+k]))
   const hi=[0,1,2].map(k=>Math.max(mapped[a*3+k],mapped[c*3+k],mapped[d*3+k]))
   const owner=homes.find(h=>{
    b.x0=lo[0]-h.x;b.x1=hi[0]-h.x;b.y0=lo[1]-h.y;b.y1=hi[1]-h.y
    b.z0=h.mirror?8-(hi[2]-h.z):lo[2]-h.z;b.z1=h.mirror?8-(lo[2]-h.z):hi[2]-h.z
    if(isTread)return inside(b,6.18,7.38,-.151,1.356,3.4,5.92)||inside(b,7.53,8.73,1.349,2.856,3.4,5.92)
    if(name==='hr_steel_black')return inside(b,6.11,7.39,3,4.2,5.86,5.92)
    const plane=name==='hr_ceiling'?2.795:3.004
    return inside(b,.2,8.8,plane,plane,.2,7.8)
   })
   if(owner){removed++;report.perHome[owner.id]=(report.perHome[owner.id]??0)+1}
   else retained.push(a,c,d)
  }
  if(!removed)return
  const replacement=geometry.clone();replacement.setIndex(retained);object.geometry=replacement
  if(!retained.length)object.visible=false
  report.trianglesRemoved+=removed;report.meshesChanged++
  report.perMaterial[name]=(report.perMaterial[name]??0)+removed
 })
 architecture.userData.privateStairRetirement=report
 return report
}

/** The sixteen 0.8 m internal openings have 60 mm jambs and 45 mm open leaves
 * inside their physical clearance. Replace those exact faces, retaining the
 * coincident head/threshold end caps and all other internal doors. */
export function removeLegacyNarrowJoinery(architecture:THREE.Object3D):NarrowJoineryRetirement {
 const previous=architecture.userData.narrowJoineryRetirement as NarrowJoineryRetirement|undefined
 if(previous)return previous
 const doors=layout.openings.filter(o=>o.kind==='inner-door'&&Math.abs(o.width-.8)<1e-6).map(o=>{
  const home=layout.homes.find(h=>o.x>=h.x-.01&&o.x<=h.x+9.01&&o.z>=h.z-.01&&o.z<=h.z+8.01)!
  const side=(o.axis==='x'?o.x-home.x-4.5:o.z-home.z-4)<=0?-1:1
  const hinge=side*(o.width/2-.06),end=hinge-side*.045
  return {...o,side,key:`${o.owner}@${o.y}:${o.axis}:${o.x}:${o.z}`,leaf:{u0:Math.min(hinge,end),u1:Math.max(hinge,end),d0:-o.wall/2-.02-(o.width-.12)*Math.sin(92*Math.PI/180),d1:-o.wall/2-.02}}
 })
 const report:NarrowJoineryRetirement={trianglesRemoved:0,jambTrianglesRemoved:0,leafTrianglesRemoved:0,meshesChanged:0,perDoor:{}}
 const point=new THREE.Vector3()
 architecture.updateMatrixWorld(true)
 architecture.traverse(object=>{
  if(!(object instanceof THREE.Mesh)||Array.isArray(object.material))return
  const name=object.material.name;if(name!=='hr_timber'&&name!=='hr_plaster')return
  const geometry=object.geometry,position=geometry.getAttribute('position'),index=geometry.index
  if(!position)return
  const vertices=Array.from({length:position.count},(_,i)=>point.fromBufferAttribute(position,i).applyMatrix4(object.matrixWorld).add(new THREE.Vector3(OX,0,OZ)).toArray())
  const retained:number[]=[],count=index?.count??position.count;let removed=0
  for(let i=0;i<count;i+=3){
   const ids=[0,1,2].map(j=>index?index.getX(i+j):i+j),points=ids.map(id=>vertices[id])
   const owner=doors.find(o=>{
    const local=points.map(p=>[o.axis==='x'?p[0]-o.x:p[2]-o.z,p[1]-o.y,o.normal*(o.axis==='x'?p[2]-o.z:p[0]-o.x)])
    const b:Bounds={x0:Math.min(...local.map(p=>p[0])),x1:Math.max(...local.map(p=>p[0])),y0:Math.min(...local.map(p=>p[1])),y1:Math.max(...local.map(p=>p[1])),z0:Math.min(...local.map(p=>p[2])),z1:Math.max(...local.map(p=>p[2]))}
    if(name==='hr_plaster')return inside(b,o.leaf.u0,o.leaf.u1,.01,o.height-.06,o.leaf.d0,o.leaf.d1)
    const jamb=inside(b,-o.width/2,-o.width/2+.06,0,o.height,-o.wall/2,o.wall/2)||inside(b,o.width/2-.06,o.width/2,0,o.height,-o.wall/2,o.wall/2)
    // Full-height jamb faces or its broad top/bottom cap. The small end caps of
    // the retained horizontal head and threshold are deliberately excluded.
    const face=b.y1-b.y0>o.height-.03
    const cap=b.y1-b.y0<.001&&b.x1-b.x0>.04&&b.z1-b.z0>o.wall-.02&&(Math.abs(b.y0)<epsilon||Math.abs(b.y0-o.height)<epsilon)
    return jamb&&(face||cap)
   })
   if(owner){removed++;report.perDoor[owner.key]=(report.perDoor[owner.key]??0)+1}
   else retained.push(...ids)
  }
  if(!removed)return
  const replacement=geometry.clone();replacement.setIndex(retained);object.geometry=replacement
  if(!retained.length)object.visible=false
  report.meshesChanged++;report.trianglesRemoved+=removed
  if(name==='hr_timber')report.jambTrianglesRemoved+=removed;else report.leafTrianglesRemoved+=removed
 })
 architecture.userData.narrowJoineryRetirement=report
 return report
}

/** Sixteen adjacent P1 D02 leaves cross the physically clear bathroom approach.
 * Their replacement is held against the existing P1 wall. All frames stay. */
export function removeLegacyAdjacentLeaves(architecture:THREE.Object3D):AdjacentLeafRetirement {
 const previous=architecture.userData.adjacentLeafRetirement as AdjacentLeafRetirement|undefined
 if(previous)return previous
 const doors=layout.homes.filter(h=>h.module==='H2-L').flatMap(h=>layout.openings.filter(o=>
  o.kind==='inner-door'&&o.owner===h.id.replace(/-L$/,'')&&o.axis==='z'&&o.normal===-1&&Math.abs(o.width-.9)<1e-6&&
  Math.abs(o.x-h.x-4.44)<1e-6&&Math.abs(o.z-h.z-(h.mirror?6.5:1.5))<1e-6&&(o.y===h.y||o.y===h.y+3)
 ).map(o=>({...o,side:h.mirror?1:-1,key:`${o.owner}@${o.y}:P1-D02`})))
 const report:AdjacentLeafRetirement={trianglesRemoved:0,meshesChanged:0,perDoor:{}}
 const point=new THREE.Vector3(),offset=new THREE.Vector3(OX,0,OZ)
 architecture.updateMatrixWorld(true)
 architecture.traverse(object=>{
  if(!(object instanceof THREE.Mesh)||Array.isArray(object.material)||object.material.name!=='hr_plaster')return
  const geometry=object.geometry,position=geometry.getAttribute('position'),index=geometry.index
  if(!position)return
  const vertices=Array.from({length:position.count},(_,i)=>point.fromBufferAttribute(position,i).applyMatrix4(object.matrixWorld).add(offset).toArray())
  const retained:number[]=[],count=index?.count??position.count;let removed=0
  for(let i=0;i<count;i+=3){
   const ids=[0,1,2].map(j=>index?index.getX(i+j):i+j),points=ids.map(id=>vertices[id])
   const owner=doors.find(o=>{
    const hinge=o.side*(o.width/2-.06),end=hinge-o.side*.045,u0=Math.min(hinge,end),u1=Math.max(hinge,end)
    const d0=-o.wall/2-.02-(o.width-.12)*Math.sin(92*Math.PI/180),d1=-o.wall/2-.02
    return points.every(p=>{
     const u=p[2]-o.z,v=p[1]-o.y,d=o.normal*(p[0]-o.x)
     return u>=u0-epsilon&&u<=u1+epsilon&&v>=.01-epsilon&&v<=o.height-.06+epsilon&&d>=d0-epsilon&&d<=d1+epsilon
    })
   })
   if(owner){removed++;report.perDoor[owner.key]=(report.perDoor[owner.key]??0)+1}
   else retained.push(...ids)
  }
  if(!removed)return
  const replacement=geometry.clone();replacement.setIndex(retained);object.geometry=replacement
  if(!retained.length)object.visible=false
  report.meshesChanged++;report.trianglesRemoved+=removed
 })
 architecture.userData.adjacentLeafRetirement=report
 return report
}

/** Eight upper maisonette entrance leaves and their glass inserts project into
 * the bathroom route. The replacement folds onto the existing exterior wall;
 * keep every original frame, threshold, window and physical opening unchanged. */
export function removeLegacyUpperEntryLeaves(architecture:THREE.Object3D):UpperEntryLeafRetirement {
 const previous=architecture.userData.upperEntryLeafRetirement as UpperEntryLeafRetirement|undefined
 if(previous)return previous
 const doors=layout.homes.filter(h=>h.module==='H2-U').flatMap(h=>layout.openings.filter(o=>
  o.kind==='door'&&o.owner===h.id.replace(/-U$/,'')&&o.y===h.y&&o.axis==='x'&&Math.abs(o.width-1.1)<1e-6&&
  Math.abs(o.x-h.x-5.25)<1e-6&&Math.abs(o.z-h.z-(h.mirror?7.9:.1))<1e-6
 ).map(o=>({...o,key:`${o.owner}@${o.y}:upper-D01`})))
 const report:UpperEntryLeafRetirement={trianglesRemoved:0,paintTrianglesRemoved:0,glassTrianglesRemoved:0,meshesChanged:0,perDoor:{}}
 const point=new THREE.Vector3(),offset=new THREE.Vector3(OX,0,OZ)
 architecture.updateMatrixWorld(true)
 architecture.traverse(object=>{
  if(!(object instanceof THREE.Mesh)||Array.isArray(object.material))return
  const glass=object.material.name==='hr_glass'
  if(!glass&&object.material.name!=='hr_door_paint')return
  const geometry=object.geometry,position=geometry.getAttribute('position'),index=geometry.index
  if(!position)return
  const vertices=Array.from({length:position.count},(_,i)=>point.fromBufferAttribute(position,i).applyMatrix4(object.matrixWorld).add(offset).toArray())
  const retained:number[]=[],count=index?.count??position.count;let removed=0
  for(let i=0;i<count;i+=3){
   const ids=[0,1,2].map(j=>index?index.getX(i+j):i+j),points=ids.map(id=>vertices[id])
   const owner=doors.find(o=>{
    const hinge=o.width/2-.06,height=o.height-.06,near=-o.wall/2-.02,far=near-(o.width-.12)*Math.sin(92*Math.PI/180)
    const u0=hinge-.045-(glass ? .002 : 0),u1=hinge+(glass ? .002 : 0)
    const v0=glass?height*.45:.01,v1=glass?height-.15:height,d0=glass?far+.12:far,d1=glass?near-.12:near
    return points.every(p=>{
     const u=p[0]-o.x,v=p[1]-o.y,d=o.normal*(p[2]-o.z)
     return u>=u0-epsilon&&u<=u1+epsilon&&v>=v0-epsilon&&v<=v1+epsilon&&d>=d0-epsilon&&d<=d1+epsilon
    })
   })
   if(owner){removed++;report.perDoor[owner.key]=(report.perDoor[owner.key]??0)+1}
   else retained.push(...ids)
  }
  if(!removed)return
  const replacement=geometry.clone();replacement.setIndex(retained);object.geometry=replacement
  if(!retained.length)object.visible=false
  report.meshesChanged++;report.trianglesRemoved+=removed
  if(glass)report.glassTrianglesRemoved+=removed;else report.paintTrianglesRemoved+=removed
 })
 architecture.userData.upperEntryLeafRetirement=report
 return report
}

/** Additive original Blender construction; retire old art only after a complete
 * load. Shared PBR textures retain their provenance and allocation. */
export async function loadBuildingArt(loader:GLTFLoader,materials:HeronReachMaterials,architecture:THREE.Object3D){
 const {scene}=await loader.loadAsync('/models/heron-reach/building-detail.glb')
 scene.name='ONSITE / building joints and private stairs (Blender)'
 const mapped=new Map<string,THREE.MeshStandardMaterial>()
 scene.traverse(object=>{if(object instanceof THREE.Mesh&&!Array.isArray(object.material)){
  const name=object.material.name;mapped.set(name,materials.get(name==='hr_stair_concrete'?'hr_concrete_cast':name))
 }})
 await materials.ready()
 const dry=mapped.get('hr_stair_concrete')?.clone()
 if(dry){
  dry.name='hr_stair_concrete';dry.roughness=.88;dry.metalness=0;dry.envMapIntensity=.7
  applyHeronSurfaceResponse(dry);mapped.set(dry.name,dry)
 }
 scene.traverse(object=>{if(object instanceof THREE.Mesh&&!Array.isArray(object.material)){
  const imported=object.material;object.material=mapped.get(imported.name)!;imported.dispose()
  object.castShadow=materials.shadow.get(object.material.name)!==false;object.receiveShadow=true
 }})
 scene.userData.retired=removeLegacyPrivateStairs(architecture)
 scene.userData.joineryRetired=removeLegacyNarrowJoinery(architecture)
 scene.userData.adjacentLeavesRetired=removeLegacyAdjacentLeaves(architecture)
 scene.userData.upperEntryLeavesRetired=removeLegacyUpperEntryLeaves(architecture)
 return scene
}
