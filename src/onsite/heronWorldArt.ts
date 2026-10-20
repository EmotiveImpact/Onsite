import * as THREE from 'three'
import type {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'

export type WorldAssetBounds={min:[number,number,number];max:[number,number,number]}
export type WorldArtPlacement={asset:string;x:number;y:number;z:number;ry:number;rx?:number;scale:number}
type Primitive={geometry:THREE.BufferGeometry;material:THREE.Material;local:THREE.Matrix4}
export type WorldAsset={bounds:WorldAssetBounds;primitives:Primitive[];soilSurfaceY?:number;soilRadius?:number;stemXZ?:[number,number];stemBasalY?:number}
export type WorldAssetLibrary=Map<string,WorldAsset>
export const worldAssetKits=[
 {url:'/models/heron-reach/heron-reach-world-props.glb',roots:['WORLD_TRASH_BAG','WORLD_BIN_RUST','WORLD_AIRCON_RUST','WORLD_CARDBOARD_BOX','WORLD_WOODEN_CRATE','WORLD_TYRE']},
 {url:'/models/heron-reach/heron-reach-world-plants.glb',roots:['WORLD_FERN_A','WORLD_FERN_B','WORLD_FERN_C','WORLD_FERN_D','WORLD_CLAY_POT']},
] as const

/** Individual, metre-scale Blender roots. Failed optional assets never retire original art. */
export async function loadWorldAssetLibrary(loader:Pick<GLTFLoader,'loadAsync'>):Promise<WorldAssetLibrary>{
 const library:WorldAssetLibrary=new Map()
 await Promise.all(worldAssetKits.map(async kit=>{
  try{
   const {scene}=await loader.loadAsync(kit.url)
   scene.updateMatrixWorld(true)
   for(const name of kit.roots){
    const root=scene.getObjectByName(name)
    if(!root){console.warn('World dressing asset unavailable; retaining original art',name);continue}
    const inverse=root.matrixWorld.clone().invert(),bounds=new THREE.Box3(),primitives:Primitive[]=[]
    let valid=true
    root.traverse(o=>{
     if(!(o instanceof THREE.Mesh))return
     const geometry=o.geometry,local=new THREE.Matrix4().multiplyMatrices(inverse,o.matrixWorld)
     if(o instanceof THREE.SkinnedMesh||Array.isArray(o.material)||!geometry.attributes.position||!local.elements.every(Number.isFinite)){valid=false;return}
     geometry.computeBoundingBox()
     if(!geometry.boundingBox||geometry.boundingBox.isEmpty()){valid=false;return}
     bounds.union(geometry.boundingBox.clone().applyMatrix4(local))
     primitives.push({geometry,material:o.material,local})
    })
    const size=bounds.getSize(new THREE.Vector3())
    if(!valid||!primitives.length||![...bounds.min,...bounds.max].every(Number.isFinite)||Math.min(size.x,size.y,size.z)<=0){
     console.warn('World dressing asset unavailable; retaining original art',name);continue
    }
    const soil=root.userData.soilSurfaceY
    const soilSurfaceY=typeof soil==='number'&&Number.isFinite(soil)&&soil>bounds.min.y&&soil<bounds.max.y?soil:undefined
    const radius=root.userData.soilRadius,stem=root.userData.stemXZ
    const soilRadius=typeof radius==='number'&&Number.isFinite(radius)&&radius>0&&radius<=Math.min(size.x,size.z)/2?radius:undefined
    const stemXZ=Array.isArray(stem)&&stem.length===2&&stem.every(v=>typeof v==='number'&&Number.isFinite(v))&&
     stem[0]>=bounds.min.x&&stem[0]<=bounds.max.x&&stem[1]>=bounds.min.z&&stem[1]<=bounds.max.z?stem as [number,number]:undefined
    const basal=root.userData.stemBasalY
    const stemBasalY=typeof basal==='number'&&Number.isFinite(basal)&&basal>=bounds.min.y-1e-6&&basal<=bounds.max.y?basal:undefined
    library.set(name,{bounds:{min:bounds.min.toArray(),max:bounds.max.toArray()},primitives,soilSurfaceY,soilRadius,stemXZ,stemBasalY})
   }
  }catch(error){console.warn('World dressing kit unavailable; retaining original art',kit.url,error)}
 }))
 return library
}

/** Map metres: +X east, +Y up, +Z south. The planner has already placed the native root. */
export function worldArtMatrix(p:WorldArtPlacement,target=new THREE.Matrix4()){
 return target.makeTranslation(p.x-72,p.y,p.z-60)
  .multiply(new THREE.Matrix4().makeRotationY(p.ry))
  .multiply(new THREE.Matrix4().makeRotationX(p.rx??0))
  .scale(new THREE.Vector3(p.scale,p.scale,p.scale))
}

/** Share source geometry/materials; bound each draw to one floor and a 24 m spatial tile. */
export function buildWorldArt(library:WorldAssetLibrary,placements:readonly WorldArtPlacement[]){
 const group=new THREE.Group();group.name='ONSITE / scanned estate objects and living planting'
 const tiles=new Map<string,WorldArtPlacement[]>()
 for(const p of placements){
  if(!library.has(p.asset)||!Object.values(p).filter(v=>typeof v==='number').every(Number.isFinite)||p.scale<=0)continue
  const key=`${p.asset}/${Math.floor(p.x/24)}/${Math.floor(p.z/24)}/${Math.floor(p.y/3)}`
  const list=tiles.get(key)??[];list.push(p);tiles.set(key,list)
 }
 for(const [key,list]of tiles){
  const asset=library.get(list[0].asset)!
  asset.primitives.forEach((part,index)=>{
   const instances=new THREE.InstancedMesh(part.geometry,part.material,list.length)
   instances.name=`${key}/${index}`;instances.castShadow=true;instances.receiveShadow=true
   const matrix=new THREE.Matrix4()
   list.forEach((p,i)=>instances.setMatrixAt(i,worldArtMatrix(p,matrix).multiply(part.local)))
   instances.instanceMatrix.needsUpdate=true
   instances.computeBoundingBox();instances.computeBoundingSphere()
   group.add(instances)
  })
 }
 group.userData.placementCount=[...tiles.values()].reduce((n,list)=>n+list.length,0)
 return group
}
