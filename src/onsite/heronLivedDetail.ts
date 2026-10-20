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

/** Only these four render units are replaced. Their existing dressing colliders stay intact. */
export function isReplacedShopShelf(p:{asset:string;x:number;y:number;z:number}){
 return p.asset==='SHOP_SHELF_UNIT'&&Math.abs(p.y)<.001&&[[107.24,56.52],[108.52,56.52],[109.4,52.5],[112.6,52.5]].some(([x,z])=>Math.hypot(p.x-x,p.z-z)<.001);
}

/** Actual stock and double-sided gondolas, authored inside the original furniture footprints. */
export async function loadShopDepth(loader:GLTFLoader,materials:HeronReachMaterials,lived:THREE.Object3D,shops:THREE.Object3D){
 const {scene}=await loader.loadAsync('/models/heron-reach/heron-reach-shop-depth.glb');
 const shared=new Map<string,THREE.Material>(),sharedNames=materials.names();
 lived.traverse(o=>{if(o instanceof THREE.Mesh)for(const material of Array.isArray(o.material)?o.material:[o.material])shared.set(material.name,material)});
 scene.name='ONSITE / three-dimensional shop stock (Blender)';
 const retired=new Set<THREE.Material>();
 scene.traverse(o=>{if(o instanceof THREE.Mesh){
  const replace=(old:THREE.Material)=>{const material=shared.get(old.name)??(sharedNames.has(old.name)?materials.get(old.name):undefined);if(material){retired.add(old);return material}return old};
  o.material=Array.isArray(o.material)?o.material.map(replace):replace(o.material);o.castShadow=true;o.receiveShadow=true;
 }});
 // Discard duplicate embedded atlas resources after substituting the lived kit's same atlas.
 const retiredTextures=new Set<THREE.Texture>();
 retired.forEach(material=>{if(material instanceof THREE.MeshStandardMaterial){if(material.map)retiredTextures.add(material.map);if(material.emissiveMap)retiredTextures.add(material.emissiveMap)}material.dispose()});
 retiredTextures.forEach(texture=>texture.dispose());
 const cards=new Set(['E-shop/interior / hr_shop_image_corner','W-shops/interior / hr_shop_image_laundry','C-store/interior / hr_shop_image_laundry']);
 shops.traverse(o=>{if(cards.has(o.name)||cards.has(o.userData.name))o.visible=false});
 return scene;
}
