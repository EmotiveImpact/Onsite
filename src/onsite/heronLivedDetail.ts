import * as THREE from 'three'
import type {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import type {HeronReachMaterials} from './heronReachArt'

/** Blender-authored details already in metre-scale world coordinates. Render only. */
export async function loadLivedDetail(loader:GLTFLoader,materials:HeronReachMaterials){
 const {scene}=await loader.loadAsync('/models/heron-reach/heron-reach-lived.glb');
 scene.name='ONSITE / occupied shopfront and estate services (Blender)';
 const shared=materials.names();
 scene.traverse(o=>{if(o instanceof THREE.Mesh){
  const old=o.material as THREE.MeshStandardMaterial;
  if(shared.has(old.name)){o.material=materials.get(old.name);old.dispose()}
  o.castShadow=true;o.receiveShadow=true;
 }});
 return scene;
}

/** Individually cleared Poly Haven scans, adapted in Blender; embedded maps stay intact. */
export async function loadScannedDetail(loader:GLTFLoader,shopArt:THREE.Object3D){
 const {scene}=await loader.loadAsync('/models/heron-reach/heron-reach-scanned.glb');
 scene.name='ONSITE / Poly Haven ground covers and shop fittings (Blender)';
 scene.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=false;o.receiveShadow=true}});
 hideReplacedShopFittings(shopArt);
 return scene;
}

export function hideReplacedShopFittings(shopArt:THREE.Object3D){
 const replaced=new Set(['E-shop/interior / hr_shop_fitting','E-shop/interior / hr_shop_strip']);
 let hidden=0;
 // GLTFLoader sanitises node.name, retaining the authored name in userData.name.
 shopArt.traverse(o=>{if(replaced.has(o.userData.name)||replaced.has(o.name)){o.visible=false;hidden++}});
 return hidden;
}
