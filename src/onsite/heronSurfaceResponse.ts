import * as THREE from 'three'

/** Original ONSITE response tuning: the existing textures retain their provenance.
 * Fine normal noise must settle with distance, and concrete soffits stay dry. */
export function surfaceNormalScale(name:string):number {
 if(name.startsWith('hr_concrete'))return .24;
 if(name.startsWith('hr_brick'))return .36;
 if(name==='hr_paving'||name==='hr_pavers_red'||name==='hr_court')return .30;
 if(name==='hr_asphalt'||name==='hr_roof_felt')return .38;
 if(name==='hr_plaster'||name==='hr_render')return .22;
 return .65;
}

export function applyHeronSurfaceResponse(material:THREE.MeshStandardMaterial){
 const previous=material.onBeforeCompile,cache=material.customProgramCacheKey();
 material.onBeforeCompile=function(shader,renderer){
  previous.call(this,shader,renderer);
  shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
   // Distance-fade the authored normal, not a second resampled brick pattern.
   float onsiteFarNormal=smoothstep(7.0,35.0,length(vViewPosition));
   vec3 onsiteSurfaceUp=inverseTransformDirection(nonPerturbedNormal,viewMatrix);
   float onsiteSoffit=smoothstep(.45,.95,-onsiteSurfaceUp.y);
   normal=normalize(mix(normal,nonPerturbedNormal,max(onsiteFarNormal*.65,onsiteSoffit*.55)));
   roughnessFactor=max(roughnessFactor,onsiteSoffit*.9);`);
 };
 material.customProgramCacheKey=()=>cache+'|onsite-surface-response-v1';
}
