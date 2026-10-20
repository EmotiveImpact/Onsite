// Original ONSITE Blender-authored, render-only ground detail; see GROUND-GROWTH.md.
import * as THREE from 'three'
import type {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import type {HeronReachMaterials} from './heronReachArt'

/** Optional additive asset. Failure keeps the existing full ground/grass presentation. */
export async function loadHeronGroundArt(gltf:GLTFLoader,mats:HeronReachMaterials,kits:THREE.Object3D){
 try{
  const {scene}=await gltf.loadAsync('/models/heron-reach/heron-reach-ground-detail.glb');
  scene.name='ONSITE / Heron Reach ground detail';
  // Reuse the existing material/texture owners; moss tint is baked in vertex colours.
  const names=new Set<string>();scene.traverse(o=>{if(o instanceof THREE.Mesh)names.add((o.material as THREE.Material).name.replace(/\.\d+$/,''))});
  if(!names.has('hr_soil'))throw new Error('Ground detail contains no soil surface');
  const kitMaterials=new Map<string,THREE.Material>();kits.traverse(o=>{if(o instanceof THREE.Mesh&&!Array.isArray(o.material))kitMaterials.set(o.material.name.replace(/\.\d+$/,''),o.material)});
  for(const name of names)if(name!=='hr_leaf_litter')mats.get(name==='hr_ground_moss'?'hr_grass_ground':name);
  await mats.ready();
  scene.traverse(o=>{if(o instanceof THREE.Mesh){
   const old=o.material as THREE.MeshStandardMaterial;
   const name=old.name.replace(/\.\d+$/,'');
   if(name==='hr_leaf_litter'){
    const material=kitMaterials.get(name);if(material)o.material=material;else{o.visible=false;old.dispose();return}
   }else o.material=mats.get(name==='hr_ground_moss'?'hr_grass_ground':name);
   old.dispose();o.castShadow=false;o.receiveShadow=true;
  }});
  return {group:scene,loaded:true};
 }catch(e){console.warn('Ground detail unavailable; retaining existing ground and grass',e);return {group:new THREE.Group(),loaded:false}}
}
