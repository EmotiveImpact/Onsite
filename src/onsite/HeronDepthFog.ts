/**
 * Adapted from Operation Blackout, src/lighting/AtmosphereFog.js, commit
 * 51816a061cac321e9fdd3e85f34db1969985dd77. Copyright (c) 2026 Rushindra Sinha.
 * SPDX-License-Identifier: MIT
 * Full notice: public/licenses/OPERATION-BLACKOUT-MIT.txt.
 * Provenance and integration: docs/research/OPERATION-BLACKOUT-NOTICE.md.
 */
import * as THREE from 'three'

/** Metre-scale blue-hour tuning. scene.fog.color/density remain the live controls. */
export const HERON_DEPTH_FOG = Object.freeze({
 aerialScale: .70,
 groundScale: .18,
 heightFalloff: .11,
 aerialHeightFalloff: .028,
 cameraHeightFloor: .55,
 baseHeight: 0,
 maxOpacity: .985,
});

const clamp = (x:number, low:number, high:number) => Math.min(high,Math.max(low,x));

/** Average exp(-height) along a ray; the series avoids cancellation at the horizon.
 * The exponent bound only affects extreme rays outside the estate's height range. */
function heightIntegral(delta:number):number {
 const x=clamp(delta,-16,16);
 return Math.abs(x)<.001 ? 1-x/2+x*x/6 : -Math.expm1(-x)/x;
}

/** CPU mirror of the shader: full ray length, camera/target world Y, FogExp2 density. */
export function heronFogOpticalDepth(distance:number,cameraY=1.75,targetY=cameraY,density=.007):number {
 const p=HERON_DEPTH_FOG,dist=Math.max(0,distance),d=Math.max(0,density);
 const cameraA=clamp(Math.exp(clamp(-(cameraY-p.baseHeight)*p.aerialHeightFalloff,-16,16)),p.cameraHeightFloor,4);
 const cameraH=clamp(Math.exp(clamp(-(cameraY-p.baseHeight)*p.heightFalloff,-16,16)),p.cameraHeightFloor*.5,4);
 const aerial=d*p.aerialScale*dist*cameraA*clamp(heightIntegral((targetY-cameraY)*p.aerialHeightFalloff),.35,2.5);
 const ground=d*p.groundScale*dist*cameraH*heightIntegral((targetY-cameraY)*p.heightFalloff);
 return aerial*aerial+ground;
}

/** Fog blend amount; useful for review without implying a rendered visual result. */
export function heronFogFactor(distance:number,cameraY=1.75,targetY=cameraY,density=.007):number {
 return clamp(-Math.expm1(-heronFogOpticalDepth(distance,cameraY,targetY,density)),0,HERON_DEPTH_FOG.maxOpacity);
}

const f=(value:number)=>value.toFixed(8);
const p=HERON_DEPTH_FOG;
const fogParsVertex=/* glsl */`
#include <fog_pars_vertex>
#if defined( USE_FOG ) && defined( FOG_EXP2 )
 varying vec3 vHeronFogWorldPosition;
#endif
`;
const fogVertex=/* glsl */`
#include <fog_vertex>
#if defined( USE_FOG ) && defined( FOG_EXP2 )
 // mvPosition already includes skinning, instancing and sprite billboarding.
 // Three's camera view rotation is orthonormal; its transpose is its inverse.
 vHeronFogWorldPosition = cameraPosition + transpose( mat3( viewMatrix ) ) * mvPosition.xyz;
#endif
`;
const fogParsFragment=/* glsl */`
#include <fog_pars_fragment>
#if defined( USE_FOG ) && defined( FOG_EXP2 )
 varying vec3 vHeronFogWorldPosition;
 float heronHeightIntegral( float delta ) {
  float x = clamp( delta, -16.0, 16.0 );
  return abs( x ) < 0.001 ? 1.0 - x * 0.5 + x * x / 6.0 : ( 1.0 - exp( -x ) ) / x;
 }
#endif
`;
const fogFragment=/* glsl */`
#if defined( USE_FOG ) && defined( FOG_EXP2 )
 {
  vec3 heronRay = vHeronFogWorldPosition - cameraPosition;
  float heronDistance = length( heronRay );
  vec3 heronDirection = heronRay / max( heronDistance, 0.0001 );
  float heronDeltaY = heronRay.y;
  float heronDensity = max( fogDensity, 0.0 );

  // Quadratic aerial extinction preserves near contrast; the weak linear layer
  // settles nearer the ground. Integrate both along the whole viewing ray.
  float heronCameraA = clamp( exp( clamp( -( cameraPosition.y - ${f(p.baseHeight)} ) * ${f(p.aerialHeightFalloff)}, -16.0, 16.0 ) ), ${f(p.cameraHeightFloor)}, 4.0 );
  float heronCameraH = clamp( exp( clamp( -( cameraPosition.y - ${f(p.baseHeight)} ) * ${f(p.heightFalloff)}, -16.0, 16.0 ) ), ${f(p.cameraHeightFloor*.5)}, 4.0 );
  float heronAerial = heronDensity * ${f(p.aerialScale)} * heronDistance * heronCameraA * clamp( heronHeightIntegral( heronDeltaY * ${f(p.aerialHeightFalloff)} ), 0.35, 2.5 );
  float heronGround = heronDensity * ${f(p.groundScale)} * heronDistance * heronCameraH * heronHeightIntegral( heronDeltaY * ${f(p.heightFalloff)} );
  float heronFactor = clamp( 1.0 - exp( -( heronAerial * heronAerial + heronGround ) ), 0.0, ${f(p.maxOpacity)} );

  // Four donor-derived colour lobes, restrained for ONSITE's cool blue hour.
  // The warm azimuth matches the existing sky dome (2.4 radians).
  vec3 heronColour = mix( fogColor, fogColor * vec3( 0.70, 0.74, 0.78 ), clamp( -heronDirection.y * 2.4, 0.0, 1.0 ) );
  heronColour = mix( heronColour, fogColor * vec3( 0.90, 1.02, 1.12 ), clamp( heronDirection.y * 1.7, 0.0, 1.0 ) );
  float heronWarmDot = max( dot( heronDirection, normalize( vec3( ${f(Math.cos(2.4))}, 0.08, ${f(Math.sin(2.4))} ) ) ), 0.0 );
  float heronWarmAmount = pow( heronWarmDot, 2.6 ) * 0.24 + pow( heronWarmDot, 16.0 ) * 0.08;
  heronColour = mix( heronColour, fogColor * vec3( 1.40, 1.12, 0.90 ), heronWarmAmount );
  gl_FragColor.rgb = mix( gl_FragColor.rgb, heronColour, heronFactor );
 }
#else
 // Preserve Three's linear Fog and no-fog behaviour exactly.
 #include <fog_fragment>
#endif
`;

const installed=new WeakSet<THREE.Material>();

/** Install after Reach's art/material hooks are ready. Safe to repeat for late additions.
 * Returns the number of newly wrapped materials. Only stock fogged materials are supported;
 * custom ShaderMaterial programs keep ownership of their fog. No ShaderChunk is mutated. */
export function installHeronDepthFog(scene:THREE.Scene):number {
 let count=0;
 scene.traverse(object=>{
  const materials=(object as THREE.Mesh).material;
  if(!materials)return;
  for(const material of Array.isArray(materials)?materials:[materials]){
   if((material as THREE.Material&{fog?:boolean}).fog!==true||material instanceof THREE.ShaderMaterial||installed.has(material))continue;
   const previousCompile=material.onBeforeCompile,previousKey=material.customProgramCacheKey;
   material.onBeforeCompile=function(shader,renderer){
    previousCompile.call(this,shader,renderer);
    // A previous hook may completely replace a shader. Leave it intact in that case.
    if(!shader.vertexShader.includes('#include <fog_pars_vertex>')||!shader.vertexShader.includes('#include <fog_vertex>')||
       !shader.fragmentShader.includes('#include <fog_pars_fragment>')||!shader.fragmentShader.includes('#include <fog_fragment>'))return;
    shader.vertexShader=shader.vertexShader.replace('#include <fog_pars_vertex>',fogParsVertex).replace('#include <fog_vertex>',fogVertex);
    shader.fragmentShader=shader.fragmentShader.replace('#include <fog_pars_fragment>',fogParsFragment).replace('#include <fog_fragment>',fogFragment);
   };
   material.customProgramCacheKey=function(){
    // Three's default key reads the *current* hook, so capture the original function
    // explicitly. Custom keys (including wet ground) still evaluate dynamically.
    const base=previousKey===THREE.Material.prototype.customProgramCacheKey?previousCompile.toString():previousKey.call(this);
    return base+'|onsite-heron-depth-fog-v1';
   };
   material.needsUpdate=true;
   installed.add(material);count++;
  }
 });
 return count;
}
