import * as THREE from 'three'
import type {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'

/** Cosmetic pigeon netting above existing parapets. Never supplies physics or navigation. */
export async function loadGalleryArt(loader:GLTFLoader,software:boolean,coverage:boolean){
 const {scene}=await loader.loadAsync('/models/heron-reach/heron-reach-gallery.glb');
 scene.name='ONSITE / gallery pigeon netting (Blender)';
 scene.traverse(o=>{if(o instanceof THREE.Mesh){
  const mat=o.material as THREE.MeshStandardMaterial;
  if(mat.name==='hr_pigeon_net'){
   mat.side=THREE.DoubleSide;mat.alphaTest=coverage?.15:.005;mat.transparent=!coverage;mat.depthWrite=coverage;mat.alphaToCoverage=coverage;
   if(mat.map){mat.map.anisotropy=software?2:8;mat.map.needsUpdate=true}
  }
  o.castShadow=false;o.receiveShadow=true;
 }});
 return scene;
}
