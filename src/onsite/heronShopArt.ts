import * as THREE from 'three'
import type {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import spec from '../../docs/maps/heron-reach-32/blueprints/build-spec.json'
import type {LightAnchor} from './heronReachArt'

/** Presentation only: fixtures follow the existing shop shells, never supply collision. */
export const shopLightAnchors:LightAnchor[]=spec.shops.filter(s=>['THE CORNER','LAUNDERETTE','WASHHOUSE'].includes(s.name)).flatMap(s=>{
 const [x,z,w]=s.rect;
 return [.25,.75].map(u=>({x:x+w*u-72,y:2.5,z:z+.7-60,kind:'shop'}));
});

export async function loadShopArt(loader:GLTFLoader){
 const {scene}=await loader.loadAsync('/models/heron-reach/heron-reach-shops.glb');
 scene.name='ONSITE / illuminated shop interiors (Blender)';
 scene.traverse(o=>{if(o instanceof THREE.Mesh){
  const mat=o.material as THREE.MeshStandardMaterial;
  if(mat.name.startsWith('hr_shop_image_')){mat.emissive.set('#ffe0b5');mat.emissiveIntensity=1.1;mat.side=THREE.FrontSide;o.castShadow=false}
  else {o.castShadow=false;o.receiveShadow=true}
 }});
 return scene;
}
