import * as THREE from 'three'
import type {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js'
import {applyWetGround,surfaceBelow,wetGroundNames} from './wetGround'
import type {Solid} from './level'

/** Heron Reach presentation built in Blender (assets/blender/heron-reach). Render-only: collision stays in heronReach.ts. */
type Entry={map?:string|null;normalMap?:string|null;ormMap?:string|null;emissiveMap?:string|null;repeat?:number;color?:number[];emissive?:number[];emissiveIntensity?:number;roughness?:number;metalness?:number;shadow?:boolean;doubleSided?:boolean;wet?:number;opacity?:number}

export class HeronReachMaterials {
 readonly mats=new Map<string,THREE.MeshStandardMaterial>();readonly shadow=new Map<string,boolean>();
 private readonly textures=new Map<string,Promise<THREE.Texture>>();private readonly loader=new THREE.TextureLoader();private pending:Promise<unknown>[]=[];
 constructor(private readonly lib:Record<string,Entry>,private readonly anisotropy:number){}
 static async load(anisotropy:number){return new HeronReachMaterials(await (await fetch('/materials/heron/runtime-materials.json')).json(),anisotropy)}
 private texture(url:string,srgb:boolean,repeat:number){
  const key=url+'@'+repeat;let t=this.textures.get(key);
  if(!t){t=this.loader.loadAsync(url).then(tex=>{tex.wrapS=tex.wrapT=THREE.RepeatWrapping;tex.repeat.set(repeat,repeat);tex.anisotropy=this.anisotropy;tex.colorSpace=srgb?THREE.SRGBColorSpace:THREE.NoColorSpace;return tex});this.textures.set(key,t)}
  return t;
 }
 get(name:string){
  let m=this.mats.get(name);if(m)return m;
  const e=this.lib[name]??{color:[.5,.5,.5],roughness:.8},repeat=e.repeat??1;
  m=new THREE.MeshStandardMaterial({name,vertexColors:true,roughness:e.roughness??1,metalness:e.metalness??(e.ormMap?1:0),side:e.doubleSided?THREE.DoubleSide:THREE.FrontSide});
  if(e.color)m.color.setRGB(e.color[0],e.color[1],e.color[2],THREE.LinearSRGBColorSpace);
  if(e.emissive){m.emissive.setRGB(e.emissive[0],e.emissive[1],e.emissive[2],THREE.LinearSRGBColorSpace);m.emissiveIntensity=e.emissiveIntensity??1}
  if(name==='hr_lamp_emit')m.emissiveIntensity=4;
  const mat=m;
  if(e.map)this.pending.push(this.texture(e.map,true,repeat).then(t=>{mat.map=t;mat.needsUpdate=true}));
  if(e.emissiveMap)this.pending.push(this.texture(e.emissiveMap,true,repeat).then(t=>{mat.emissiveMap=t;mat.needsUpdate=true}));
  if(e.normalMap)this.pending.push(this.texture(e.normalMap,false,repeat).then(t=>{mat.normalMap=t;mat.normalScale.set(.8,.8);mat.needsUpdate=true}));
  // ORM: R occlusion, G roughness, B metalness (glTF packing), so one texture drives all three.
  if(e.ormMap)this.pending.push(this.texture(e.ormMap,false,repeat).then(t=>{mat.aoMap=t;mat.roughnessMap=t;mat.metalnessMap=t;mat.roughness=e.wet??1;mat.metalness=1;mat.needsUpdate=true}));
  if(e.wet)m.envMapIntensity=1.6;
  if(wetGroundNames.has(name))this.pending.push(this.texture('/materials/heron/decals/wetness-mask.webp',false,1).then(t=>{applyWetGround(mat,t);mat.needsUpdate=true}));
  if(e.opacity!==undefined){m.transparent=true;m.opacity=e.opacity;m.depthWrite=false;m.envMapIntensity=2.2}
  this.mats.set(name,m);this.shadow.set(name,e.shadow!==false);return m;
 }
 ready(){return Promise.all(this.pending)}
 names(){return new Set(Object.keys(this.lib))}
}

/** Load the authored architecture and give every mesh its named material. */
export async function loadHeronReachArch(gltf:GLTFLoader,mats:HeronReachMaterials){
 const arch=await gltf.loadAsync('/models/heron-reach/heron-reach-arch.glb');
 arch.scene.name='ONSITE / Heron Reach (Blender)';
 arch.scene.traverse(o=>{if(o instanceof THREE.Mesh){
  const name=(o.material as THREE.Material).name,m=mats.get(name);(o.material as THREE.Material).dispose();
  o.material=m;o.castShadow=mats.shadow.get(name)!==false;o.receiveShadow=true;
 }});
 await mats.ready();
 return arch.scene;
}

export type LightAnchor={x:number;y:number;z:number;kind:string;head?:boolean};

function radial(size:number,stops:[number,string][]){
 const c=document.createElement('canvas');c.width=c.height=size;const g=c.getContext('2d')!,gr=g.createRadialGradient(size/2,size/2,0,size/2,size/2,size/2);
 for(const [o,col]of stops)gr.addColorStop(o,col);g.fillStyle=gr;g.fillRect(0,0,size,size);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;
}

/**
 * Blue-hour dusk for Heron Reach: graded sky, cool sky light, warm 2700 K lamps. Real point lights are a
 * small pool given to the lamps nearest the camera; every lamp also gets a glow sprite and a stretched
 * wet-ground reflection streak, which is what carries the look of the concept frames at little cost.
 */
export class HeronReachAtmosphere {
 readonly group=new THREE.Group();private readonly pool:THREE.PointLight[]=[];private readonly streaks:{x:number;y:number;z:number;big:boolean}[]=[];private streakMesh!:THREE.InstancedMesh;private readonly m=new THREE.Matrix4();private readonly q=new THREE.Quaternion();private readonly up=new THREE.Vector3(0,1,0);private next=0;
 constructor(private readonly scene:THREE.Scene,renderer:THREE.WebGLRenderer,private readonly anchors:LightAnchor[],software:boolean,surfaces:readonly Solid[]){
  this.group.name='ONSITE / Heron Reach blue hour';scene.add(this.group);
  const top=new THREE.Color('#263b50'),mid=new THREE.Color('#53697d'),horizon=new THREE.Color('#929ca4'),glow=new THREE.Color('#bda18c');
  scene.background=mid.clone();scene.fog=new THREE.FogExp2('#687b8d',.007);
  const sky=new THREE.SphereGeometry(520,48,24),cols:number[]=[],p=sky.attributes.position;
  for(let i=0;i<p.count;i++){
   const y=p.getY(i)/520,az=Math.atan2(p.getZ(i),p.getX(i)),warm=Math.max(0,Math.cos(az-2.4))**3*Math.max(0,1-Math.abs(y)*6);
   const c=y<0?horizon.clone().multiplyScalar(.55):y<.12?horizon.clone().lerp(mid,y/.12):mid.clone().lerp(top,Math.min(1,(y-.12)/.6));
   c.lerp(glow,warm*.65);cols.push(c.r,c.g,c.b);
  }
  sky.setAttribute('color',new THREE.Float32BufferAttribute(cols,3));
  const dome=new THREE.Mesh(sky,new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.BackSide,depthWrite:false,fog:false}));dome.name='blue hour sky';dome.renderOrder=-10;this.group.add(dome);
  // The far city: a wrap-around panorama (a ChatGPT image) between the tower skyline and the dome,
  // three mirrored repeats round a 470 m ring (seen from inside), its horizon a few degrees above the eye and its top fading out.
  const pano=new THREE.TextureLoader().load('/materials/heron/backdrop/skyline-panorama.webp',t=>{t.colorSpace=THREE.SRGBColorSpace;t.wrapS=THREE.RepeatWrapping;t.repeat.set(-3,1);t.needsUpdate=true});
  const panoramaMaterial=new THREE.MeshBasicMaterial({map:pano,side:THREE.BackSide,transparent:true,depthWrite:false,fog:true,color:'#aeb7c1'});
  panoramaMaterial.onBeforeCompile=shader=>{shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
   diffuseColor.rgb=mix(vec3(dot(diffuseColor.rgb,vec3(.2126,.7152,.0722))),diffuseColor.rgb,.3);`)};
  const ring=new THREE.Mesh(new THREE.CylinderGeometry(470,470,246,96,1,true),panoramaMaterial);
  ring.position.y=83;ring.name='far city';ring.renderOrder=-9;this.group.add(ring);
  // Reflections come from the same graded sky so glass and wet paving pick up the dusk.
  const envScene=new THREE.Scene();envScene.add(dome.clone());const pm=new THREE.PMREMGenerator(renderer);
  scene.environment=pm.fromScene(envScene,.02).texture;scene.environmentIntensity=.7;pm.dispose();
  const halo=radial(128,[[0,'rgba(255,214,160,1)'],[.18,'rgba(255,170,90,.55)'],[.5,'rgba(255,140,60,.12)'],[1,'rgba(255,120,40,0)']]);
  const streak=new THREE.TextureLoader().load('/materials/heron/decals/lamp-streak.webp');streak.colorSpace=THREE.SRGBColorSpace;streak.anisotropy=software?2:8;
  const haloMat=(size:number)=>new THREE.PointsMaterial({map:halo,size,sizeAttenuation:true,blending:THREE.AdditiveBlending,depthWrite:false,transparent:true,fog:true});
  const streakMat=new THREE.MeshBasicMaterial({map:streak,blending:THREE.AdditiveBlending,depthWrite:false,transparent:true,polygonOffset:true,polygonOffsetFactor:-4});
  const plane=new THREE.PlaneGeometry(1,1).rotateX(-Math.PI/2);
  // Glows and streaks are batched: two point clouds and one instanced mesh, whatever the lamp count.
  const glows:Record<'big'|'small',number[]>={big:[],small:[]};
  for(const a of anchors){
   const big=a.kind==='street'||a.kind==='court';
   glows[big?'big':'small'].push(a.x,a.y,a.z);
   const floor=surfaceBelow(a.x,a.y,a.z,surfaces);
   if(floor!==null)this.streaks.push({x:a.x,y:floor+.018,z:a.z,big});
  }
  for(const [k,size]of [['big',3.4],['small',1.7]] as const)if(glows[k].length){ // point size is in world units before the fov term, so 1/tan(37°) larger than the old sprites
   const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(glows[k],3));
   const pts=new THREE.Points(g,haloMat(size));pts.name=`lamp glow ${k}`;this.group.add(pts);
  }
  this.streakMesh=new THREE.InstancedMesh(plane,streakMat,Math.max(1,this.streaks.length));this.streakMesh.count=this.streaks.length;this.streakMesh.frustumCulled=false;this.group.add(this.streakMesh);
  for(let i=0;i<(software?4:10);i++){const l=new THREE.PointLight('#ffd09a',0,20,2);this.pool.push(l);this.group.add(l)}
 }
 /** Hand the light pool to the nearest lamps, and turn reflection streaks towards the viewer. */
 update(camera:THREE.Camera,t:number){
  const c=camera.position;
  if(t>=this.next){
   this.next=t+.25;
   // Rank by estimated contribution, so a low doorway lamp cannot evict every court column.
   const near=this.anchors.map(a=>({a,d:((a.x-c.x)**2+(a.y-c.y)**2*2+(a.z-c.z)**2+4)/(a.kind==='street'||a.kind==='court'?6:1)})).sort((p,q)=>p.d-q.d);
   this.pool.forEach((l,i)=>{const n=near[i];if(!n){l.intensity=0;return}const big=n.a.kind==='street'||n.a.kind==='court',ceiling=n.a.kind==='ceiling';l.position.set(n.a.x,n.a.y-.35,n.a.z);l.color.set(ceiling?'#e4e9df':'#ffd09a');l.intensity=big?175:ceiling?11:14;l.distance=big?25:9});
  }
  const p=new THREE.Vector3(),sc=new THREE.Vector3();
  this.streaks.forEach((s,i)=>{
   const d=Math.hypot(c.x-s.x,c.z-s.z);this.q.setFromAxisAngle(this.up,Math.atan2(c.x-s.x,c.z-s.z));
   // Reflection stretches towards the viewer, on its own supporting floor.
   const length=(s.big?4:1.8)+Math.min(d,24)*(s.big?.38:.16),towards=Math.min(d*.25,length*.3);
   sc.set(s.big?1.7:.8,1,length);this.streakMesh.setMatrixAt(i,this.m.compose(p.set(s.x+(c.x-s.x)/Math.max(d,1)*towards,s.y,s.z+(c.z-s.z)/Math.max(d,1)*towards),this.q,sc));
  });
  this.streakMesh.instanceMatrix.needsUpdate=true;
 }
}

export type KitPlacement={asset:string;x:number;y:number;z:number;ry:number;sx?:number};
const OX=72,OZ=60;
const placeMatrix=(p:KitPlacement,m=new THREE.Matrix4())=>m.compose(new THREE.Vector3(p.x-OX,p.y,p.z-OZ),new THREE.Quaternion().setFromAxisAngle(new THREE.Object3D().up,p.ry),new THREE.Vector3(p.sx??1,1,1));

/** Instance the props and foliage kits from the dressing plan: one InstancedMesh per asset part. */
/** The South London gap-fill kits name their shared surfaces mat_*; they take the texture kit's sets. */
/** Perforated steel void sheet (1.2 x 2.4 m map) over the kit's metric UVs; windows use its top half. */
const voidSheets=new Map<string,THREE.MeshStandardMaterial>();
function voidSheet(asset:string){
 let m=voidSheets.get(asset);if(m)return m;
 const t=new THREE.TextureLoader().load('/materials/heron/props/hr_void_sheet-color.webp');t.colorSpace=THREE.SRGBColorSpace;
 if(asset.includes('window')){t.repeat.set(1/1.3,.5/1.3);t.offset.set(.5,.5+.05*.5/1.3)}else{t.repeat.set(1/1.2,1/2.4);t.offset.set(.5,.05/2.4)}
 m=new THREE.MeshStandardMaterial({name:'hr_void_sheet',map:t,roughness:.55,metalness:.7});voidSheets.set(asset,m);return m;
}
const SL_SHARED:Record<string,string>={mat_brick_london_stock:'hr_brick_stock',mat_brick_red:'hr_brick_red',mat_concrete_cast:'hr_concrete_cast',mat_roof_felt:'hr_roof_felt',mat_steel_black_painted:'hr_steel_black',mat_galvanised_steel:'hr_steel_galv'};
export async function loadHeronReachKits(gltf:GLTFLoader,mats:HeronReachMaterials,placements:KitPlacement[],shared:Set<string>){
 const group=new THREE.Group();group.name='ONSITE / Heron Reach kits';
 const kits=await Promise.all(['props','foliage','sl-signs','sl-lights','sl-structures','sl-extras'].map(k=>gltf.loadAsync(`/models/heron-reach/heron-reach-${k}.glb`).then(g=>g.scene).catch(()=>null)));
 const byAsset=new Map<string,KitPlacement[]>();for(const p of placements)byAsset.set(p.asset,[...(byAsset.get(p.asset)??[]),p]);
 const missing:string[]=[];
 for(const [asset,list]of byAsset){
  const root=kits.map(k=>k?.getObjectByName(asset)).find(Boolean);if(!root){missing.push(asset);continue}
  root.updateMatrixWorld(true);const inv=new THREE.Matrix4().copy(root.matrixWorld).invert();
  root.traverse(o=>{
   if(!(o instanceof THREE.Mesh))return;
   const local=new THREE.Matrix4().multiplyMatrices(inv,o.matrixWorld),src=o.material as THREE.MeshStandardMaterial;
   const base=src.name.replace(/\.\d+$/,''),name=SL_SHARED[base]??src.name,material=base==='mat_void_sheet'?voidSheet(asset):shared.has(name)?mats.get(name):src;
   if(base==='hr_prop_sign_letters')src.emissiveIntensity=1.3;
   if(base==='hr_prop_fridge_light')src.emissiveIntensity=2.5;
   const im=new THREE.InstancedMesh(o.geometry,material,list.length);im.name=`${asset}/${src.name}`;
   const m=new THREE.Matrix4();list.forEach((p,i)=>im.setMatrixAt(i,placeMatrix(p,m).multiply(local)));
   im.instanceMatrix.needsUpdate=true;im.computeBoundingSphere();
   const foliage=/leaf|grass|weed|litter|hedge|shrub/.test(src.name);
   im.castShadow=!/litter|grass|weed|lamp_emit|glass/.test(src.name)&&!asset.startsWith('CRISP')&&!asset.startsWith('CRUSHED');im.receiveShadow=true;
   if(foliage&&src.alphaTest===0&&src.transparent){src.alphaTest=.5;src.transparent=false}
   group.add(im);
  });
 }
 if(missing.length)console.warn('Heron Reach kits: no model yet for',missing.join(', '));
 await mats.ready();
 return group;
}

/**
 * Grass: clumps from the foliage kit scattered over the Blender ground's grass cells, in 8 m tiles
 * that are frustum-culled and hidden beyond a draw distance, so the field stays dense near the player.
 */
export class GrassField {
 readonly group=new THREE.Group();private tiles:THREE.InstancedMesh[]=[];
 constructor(private readonly reach=40){this.group.name='ONSITE / Heron Reach grass'}
 async build(gltf:GLTFLoader,density:number){
  const [scene,cells]=await Promise.all([gltf.loadAsync('/models/heron-reach/heron-reach-foliage.glb').then(g=>g.scene).catch(()=>null),fetch('/models/heron-reach/grass-cells.json').then(r=>r.json()).catch(()=>null)]);
  if(!scene||!cells)return this.group;
  const parts:{geo:THREE.BufferGeometry;mat:THREE.Material;local:THREE.Matrix4}[][]=[];
  for(const name of ['GRASS_CLUMP_A','GRASS_CLUMP_B','GRASS_CLUMP_C','GRASS_CLUMP_D']){
   const root=scene.getObjectByName(name);if(!root)continue;root.updateMatrixWorld(true);const inv=new THREE.Matrix4().copy(root.matrixWorld).invert(),list:typeof parts[number]=[];
   root.traverse(o=>{if(o instanceof THREE.Mesh)list.push({geo:o.geometry,mat:o.material as THREE.Material,local:new THREE.Matrix4().multiplyMatrices(inv,o.matrixWorld)})});parts.push(list);
  }
  if(!parts.length)return this.group;
  const size:number=cells.cell,tiles=new Map<string,[number,number][]>();
  let seed=7;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647};
  for(const [x,z]of cells.cells as [number,number][]){
   const n=Math.round(size*size*density*(.7+rnd()*.6));
   for(let i=0;i<n;i++){const px=x+rnd()*size,pz=z+rnd()*size,key=`${Math.floor(px/8)},${Math.floor(pz/8)}`;(tiles.get(key)??tiles.set(key,[]).get(key)!).push([px,pz])}
  }
  const m=new THREE.Matrix4(),q=new THREE.Quaternion(),up=new THREE.Vector3(0,1,0);
  for(const pts of tiles.values())parts.forEach((list,k)=>{
   const mine=pts.filter((_,i)=>i%parts.length===k);if(!mine.length)return;
   for(const part of list){
    const im=new THREE.InstancedMesh(part.geo,part.mat,mine.length);im.receiveShadow=true;
    mine.forEach(([px,pz],i)=>{const s=.8+rnd()*.6;m.compose(new THREE.Vector3(px-OX,0,pz-OZ),q.setFromAxisAngle(up,rnd()*6.283),new THREE.Vector3(s,s*(.8+rnd()*.5),s)).multiply(part.local);im.setMatrixAt(i,m)});
    im.computeBoundingSphere();this.tiles.push(im);this.group.add(im);
   }
  });
  return this.group;
 }
 update(camera:THREE.Camera){const c=camera.position;for(const t of this.tiles){const s=t.boundingSphere!;t.visible=s.center.distanceTo(c)<this.reach+s.radius}}
}

/** Rain: streaks that live in world space and wrap around the camera, faded out under cover. */
export class Rain {
 readonly mesh:THREE.LineSegments;private readonly uniforms={uCam:{value:new THREE.Vector3()},uTime:{value:0},uAlpha:{value:.12},uLamps:{value:Array.from({length:8},()=>new THREE.Vector3())}};private fade=1;private next=0;
 constructor(count:number,private readonly covered:(x:number,y:number,z:number)=>boolean,private readonly anchors:readonly LightAnchor[]=[]){
  const seeds=new Float32Array(count*2*3),ends=new Float32Array(count*2);
  for(let i=0;i<count;i++){const s=[Math.random(),Math.random(),Math.random()];for(const k of [0,1]){seeds.set(s,(i*2+k)*3);ends[i*2+k]=k}}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(count*2*3),3));g.setAttribute('seed',new THREE.BufferAttribute(seeds,3));g.setAttribute('tail',new THREE.BufferAttribute(ends,1));
  const m=new THREE.ShaderMaterial({uniforms:this.uniforms,transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,
   vertexShader:`attribute vec3 seed;attribute float tail;uniform vec3 uCam;uniform float uTime;uniform vec3 uLamps[8];varying float vA;varying float vLamp;
    const vec3 S=vec3(36.,18.,36.);
    void main(){vec3 p=uCam+(fract((seed*S-uCam)/S+.5)-.5)*S;p.y=uCam.y-6.+fract(seed.y-uTime*.62)*S.y;
     p+=vec3(.025,-.24,.012)*tail;vA=(1.-tail*.7)*smoothstep(0.,6.,distance(p.xz,uCam.xz)+2.)*(1.-smoothstep(12.,18.,distance(p.xz,uCam.xz)));
     vLamp=0.;for(int i=0;i<8;i++){vLamp=max(vLamp,(1.-smoothstep(0.,7.,distance(p,uLamps[i])))*step(p.y,uLamps[i].y+.2));}
     gl_Position=projectionMatrix*viewMatrix*vec4(p,1.);}`,
   fragmentShader:`uniform float uAlpha;varying float vA;varying float vLamp;void main(){gl_FragColor=vec4(mix(vec3(.34,.44,.56),vec3(1.,.67,.32),vLamp),uAlpha*vA*(.3+vLamp));}`});
  this.mesh=new THREE.LineSegments(g,m);this.mesh.frustumCulled=false;this.mesh.name='ONSITE / rain';this.mesh.renderOrder=5;
 }
 update(camera:THREE.Camera,t:number,dt:number){
  const c=camera.position;this.fade+=((this.covered(c.x,c.y,c.z)?.18:1)-this.fade)*Math.min(1,dt*3);
  if(t>=this.next){this.next=t+.5;const near=[...this.anchors].sort((a,b)=>(a.x-c.x)**2+(a.z-c.z)**2-((b.x-c.x)**2+(b.z-c.z)**2));this.uniforms.uLamps.value.forEach((p,i)=>{const a=near[i];p.set(a?.x??0,a?.y??-1000,a?.z??0)})}
  this.uniforms.uCam.value.copy(c);this.uniforms.uTime.value=t;this.uniforms.uAlpha.value=.23*this.fade;
 }
}

export type Decal={kind:'puddle'|'graffiti'|'tag'|'throwup'|'buffed'|'gum';x:number;y:number;z:number;w:number;h:number;ry:number;cell?:number};
// Wall decal sheets: UV rectangles [u0, v0, u1, v1] (v up) for each cell of the South London thread's
// tag set (12 tags, 2 throw-ups) and buffed-out patches (2 x 2).
const TAG_COLS=[[16,688],[704,1344],[1360,2032]],TAG_ROWS=[[16,390],[400,760],[776,1160],[1648,2024]];
const px=(x0:number,y0:number,x1:number,y1:number):number[]=>[x0/2048,1-y1/2048,x1/2048,1-y0/2048];
const SHEETS={
 graffiti:{url:'/materials/heron/decals/graffiti-photo-atlas.webp',cells:[0,1,2,3,4,5].map(c=>[(c%2)/2,(2-Math.floor(c/2))/3,(c%2+1)/2,(3-Math.floor(c/2))/3])},
 tag:{url:'/materials/heron/decals/sl-tags.webp',cells:TAG_ROWS.flatMap(([y0,y1])=>TAG_COLS.map(([x0,x1])=>px(x0,y0,x1,y1)))},
 throwup:{url:'/materials/heron/decals/sl-tags.webp',cells:[px(32,1168,1024,1640),px(1040,1168,2016,1640)]},
 buffed:{url:'/materials/heron/decals/sl-buffed.webp',cells:[[0,.5,.5,1],[.5,.5,1,1],[0,0,.5,.5],[.5,0,1,.5]]},
};
/** Puddles on the ground and tags on the walls, as alpha-cut planes over the Blender surfaces: one
 * instanced mesh for the puddles and one merged mesh for the tags. */
export function buildDecals(decals:Decal[],anisotropy:number){
 const group=new THREE.Group();group.name='ONSITE / Heron Reach decals';const tl=new THREE.TextureLoader();
 const tex=(u:string,srgb=true)=>{const t=tl.load(u);t.anisotropy=anisotropy;t.colorSpace=srgb?THREE.SRGBColorSpace:THREE.NoColorSpace;return t};
 const puddle=new THREE.MeshStandardMaterial({map:tex('/materials/heron/decals/puddle-color.webp'),normalMap:tex('/materials/heron/decals/puddle-normal.webp',false),roughness:.03,metalness:.15,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-3,envMapIntensity:2.4});
 const tags=new THREE.MeshStandardMaterial({map:tex('/materials/heron/decals/graffiti-photo-atlas.webp'),roughness:.8,transparent:true,alphaTest:.05,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-2});
 const flat=new THREE.PlaneGeometry(1,1).rotateX(-Math.PI/2),puddles=decals.filter(d=>d.kind==='puddle');
 const pm=new THREE.InstancedMesh(flat,puddle,Math.max(1,puddles.length)),o=new THREE.Object3D();pm.count=puddles.length;pm.receiveShadow=true;
 puddles.forEach((d,i)=>{o.position.set(d.x-OX,d.y+.008,d.z-OZ);o.rotation.set(0,d.ry,0);o.scale.set(d.w,1,d.h);o.updateMatrix();pm.setMatrixAt(i,o.matrix)});
 pm.computeBoundingSphere();group.add(pm);
 // Chewing gum on the paving where people stand: one more instanced, alpha-blended layer.
 const gum=decals.filter(d=>d.kind==='gum'),gm=new THREE.InstancedMesh(flat,new THREE.MeshStandardMaterial({map:tex('/materials/heron/decals/sl-gum.webp'),roughness:.7,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-2}),Math.max(1,gum.length));
 gm.count=gum.length;gm.receiveShadow=true;
 gum.forEach((d,i)=>{o.position.set(d.x-OX,d.y+.006,d.z-OZ);o.rotation.set(0,d.ry,0);o.scale.set(d.w,1,d.h);o.updateMatrix();gm.setMatrixAt(i,o.matrix)});
 gm.computeBoundingSphere();group.add(gm);
 // Wall pieces: one merged mesh per sheet. Buffed patches sit behind fresh tags (lower polygon offset).
 const wall=new Map<string,THREE.BufferGeometry[]>();
 for(const d of decals){
  const sheet=d.kind==='tag'||d.kind==='throwup'?'tag':d.kind;if(!(d.kind in SHEETS))continue;
  const cells=SHEETS[d.kind as keyof typeof SHEETS].cells,[u0,v0,u1,v1]=cells[(d.cell??0)%cells.length];
  const g=new THREE.PlaneGeometry(1,1),uv=g.attributes.uv;
  for(let i=0;i<uv.count;i++)uv.setXY(i,u0+(u1-u0)*uv.getX(i),v0+(v1-v0)*uv.getY(i));
  o.position.set(d.x-OX,d.y,d.z-OZ);o.rotation.set(0,d.ry,0);o.scale.set(d.w,d.h,1);o.updateMatrix();
  wall.set(sheet,[...(wall.get(sheet)??[]),g.applyMatrix4(o.matrix)]);
 }
 for(const [sheet,list]of wall){
  const material=sheet==='graffiti'?tags:new THREE.MeshStandardMaterial({map:tex(SHEETS[sheet as keyof typeof SHEETS].url),roughness:sheet==='buffed'?.9:.8,transparent:true,alphaTest:.05,depthWrite:false,polygonOffset:true,polygonOffsetFactor:sheet==='buffed'?-1:-2});
  const mesh=new THREE.Mesh(mergeGeometries(list),material);mesh.renderOrder=sheet==='buffed'?0:1;group.add(mesh);
 }
 return group;
}
