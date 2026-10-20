import * as THREE from 'three'
import type {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {layout} from './heronReach'
import type {HeronReachMaterials} from './heronReachArt'
import {applyHeronSurfaceResponse} from './heronSurfaceResponse'

type Bounds={x0:number;x1:number;y0:number;y1:number;z0:number;z1:number}
export type StairRetirement={trianglesRemoved:number;treadTrianglesRemoved:number;railTrianglesRemoved:number;meshesChanged:number;perCore:Record<string,number>}
// Original architecture quantises a 984m skyline together with the estate. Its
// half-step position error is 7.51mm; the new isolated asset uses finer positions.
const epsilon=.008
const concrete=new Set(['hr_concrete_cast','hr_concrete_board','hr_stair_tread'])
const contains=(b:Bounds,x0:number,x1:number,y0:number,y1:number,z0:number,z1:number)=>
 b.x0>=x0-epsilon&&b.x1<=x1+epsilon&&b.y0>=y0-epsilon&&b.y1<=y1+epsilon&&b.z0>=z0-epsilon&&b.z1<=z1+epsilon

/** Retire only public-core tread boxes and the original incorrectly directed
 * rails. Keep the original file, landings, private stairs, walls and glazing.
 * Called only after the replacement asset/materials have loaded successfully. */
export function removeLegacyCoreStairs(arch:THREE.Object3D):StairRetirement{
 const previous=arch.userData.stairRetirement as StairRetirement|undefined
 if(previous)return previous
 const report:StairRetirement={trianglesRemoved:0,treadTrianglesRemoved:0,railTrianglesRemoved:0,meshesChanged:0,perCore:{}}
 arch.updateMatrixWorld(true)
 const p=new THREE.Vector3(),b:Bounds={x0:0,x1:0,y0:0,y1:0,z0:0,z1:0}
 arch.traverse(o=>{
  if(!(o instanceof THREE.Mesh)||Array.isArray(o.material))return
  const material=o.material.name,isConcrete=concrete.has(material)
  if(!isConcrete&&material!=='hr_steel_black')return
  const geometry=o.geometry,index=geometry.index,position=geometry.getAttribute('position')
  if(!position)return
  const mapped=new Float64Array(position.count*3)
  for(let i=0;i<position.count;i++){
   p.fromBufferAttribute(position,i).applyMatrix4(o.matrixWorld)
   mapped[i*3]=p.x+72;mapped[i*3+1]=p.y;mapped[i*3+2]=p.z+60
  }
  const retained:number[]=[],count=index?.count??position.count
  let removed=0
  for(let i=0;i<count;i+=3){
   const a=index?index.getX(i):i,c=index?index.getX(i+1):i+1,d=index?index.getX(i+2):i+2
   const x0=Math.min(mapped[a*3],mapped[c*3],mapped[d*3]),x1=Math.max(mapped[a*3],mapped[c*3],mapped[d*3])
   const y0=Math.min(mapped[a*3+1],mapped[c*3+1],mapped[d*3+1]),y1=Math.max(mapped[a*3+1],mapped[c*3+1],mapped[d*3+1])
   const z0=Math.min(mapped[a*3+2],mapped[c*3+2],mapped[d*3+2]),z1=Math.max(mapped[a*3+2],mapped[c*3+2],mapped[d*3+2])
   let owner:string|undefined
   for(const core of layout.cores){
    const [cx,cz]=core.rect,base=core.levels[0],top=core.levels.at(-1)!
    b.x0=x0-cx;b.x1=x1-cx;b.y0=y0;b.y1=y1
    b.z0=core.mirror?6-(z1-cz):z0-cz;b.z1=core.mirror?6-(z0-cz):z1-cz
    const retired=isConcrete?
     (contains(b,.4,1.9,base-.151,top,1.7,4.22)||contains(b,4.1,5.6,base-.151,top,1.7,4.22)):
     (contains(b,1.902,1.958,base-.03,top+2.53,1.68,4.24)||
      contains(b,4.042,4.098,base-.03,top+2.53,1.68,4.24)||
      contains(b,.19,4.11,base-.03,top+2.53,4.162,4.218))
    if(retired){owner=core.id;break}
   }
   if(owner){removed++;report.perCore[owner]=(report.perCore[owner]??0)+1}
   else retained.push(a,c,d)
  }
  if(!removed)return
  // Avoid modifying a shared source geometry. Attributes remain exact; only the
  // replacement's index changes. Other material batches are untouched.
  const replacement=geometry.clone();replacement.setIndex(retained)
  o.geometry=replacement;if(!retained.length)o.visible=false
  report.meshesChanged++;report.trianglesRemoved+=removed
  if(isConcrete)report.treadTrianglesRemoved+=removed;else report.railTrianglesRemoved+=removed
 })
 arch.userData.stairRetirement=report
 return report
}

/** Original Blender render geometry; one existing material library/lighting owner. */
export async function loadStairArt(gltf:GLTFLoader,mats:HeronReachMaterials,arch:THREE.Object3D){
 const {scene}=await gltf.loadAsync('/models/heron-reach/stair-detail.glb')
 scene.name='ONSITE / constructed public stairs'
 const sources=new Map<string,THREE.MeshStandardMaterial>()
 scene.traverse(o=>{if(o instanceof THREE.Mesh&&!Array.isArray(o.material)){
  const name=o.material.name;sources.set(name,mats.get(name==='hr_stair_concrete'?'hr_concrete_cast':name))
 }})
 await mats.ready()
 const dry=sources.get('hr_stair_concrete')?.clone()
 if(dry){
  // MeshStandardMaterial.clone shares textures but does not copy shader hooks.
  // These sheltered flights therefore omit the outdoor wet-ground patch.
  dry.name='hr_stair_concrete';dry.roughness=.88;dry.metalness=0;dry.envMapIntensity=.7
  applyHeronSurfaceResponse(dry);sources.set('hr_stair_concrete',dry)
 }
 scene.traverse(o=>{if(o instanceof THREE.Mesh&&!Array.isArray(o.material)){
  const imported=o.material;o.material=sources.get(imported.name)!;imported.dispose()
  o.castShadow=mats.shadow.get(o.material.name)!==false;o.receiveShadow=true
 }})
 scene.userData.retired=removeLegacyCoreStairs(arch)
 return scene
}
