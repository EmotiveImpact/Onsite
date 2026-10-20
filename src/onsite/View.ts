import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {RGBELoader} from 'three/addons/loaders/RGBELoader.js'
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js'
import dressing from './dressing.json'
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js'
import {donorRifle} from './DonorRifle'
import {heronCourt,type Level} from './levels'
import * as reach from './heronReach'
import {buildDecals,GrassField,HeronReachAtmosphere,HeronReachMaterials,loadHeronReachArch,loadHeronReachKits,Rain} from './heronReachArt'
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js'
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js'
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js'
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js'
import type {Encounter} from './Encounter'
import {loadShopArt,shopLightAnchors} from './heronShopArt'
import {stairLightAnchors} from './heronStairLighting'
import {loadStairArt} from './heronStairArt'
import {loadBuildingArt} from './heronBuildingArt'
import {loadGalleryArt} from './heronGalleryArt'
import {installHeronDepthFog} from './HeronDepthFog'
import {loadLivedDetail,loadScannedDetail,loadShopDepth,isReplacedShopShelf} from './heronLivedDetail'
import {HeronContactShadows} from './HeronContactShadows'
import {presentationProfile,cameraPresentation} from './PresentationSettings'
import type {PlayerSettings} from './profile'

/** Blender-authored estate presentation. Collision and simulation remain in Encounter. */
export class View {
 readonly renderer:THREE.WebGLRenderer; readonly scene=new THREE.Scene(); readonly camera=new THREE.PerspectiveCamera(74,1,.06,160);
 readonly vmScene=new THREE.Scene(); readonly vmCamera=new THREE.PerspectiveCamera(52,1,.025,8);
 readonly software:boolean; readonly mats:Record<string,THREE.MeshStandardMaterial>={}; readonly ready:Promise<THREE.Object3D>;
 private readonly coverageSamples:number;
 private rifle!:THREE.Object3D;private sky!:THREE.Mesh;private hemi!:THREE.HemisphereLight;private sun!:THREE.DirectionalLight;
 private atmosphere?:HeronReachAtmosphere;private composer?:EffectComposer;private readonly clock=new THREE.Clock();private readonly grass=new GrassField();private rain?:Rain;
 private settings:Pick<PlayerSettings,'quality'|'reducedMotion'>;private inspectionRatio?:number;private bloom?:UnrealBloomPass;private contacts?:HeronContactShadows;
 private activeRifle?:ReturnType<typeof donorRifle>;
 artTextureStats:HeronReachMaterials['textureStats']|null=null;
 constructor(canvas:HTMLCanvasElement,readonly level:Level=heronCourt,settings:Pick<PlayerSettings,'quality'|'reducedMotion'>={quality:'auto',reducedMotion:false}){
  this.settings={...settings};
  const probe=document.createElement('canvas').getContext('webgl2'),ext=probe?.getExtension('WEBGL_debug_renderer_info');
  this.software=!!probe&&!!ext&&/swiftshader|llvmpipe/i.test(probe.getParameter(ext.UNMASKED_RENDERER_WEBGL));
  probe?.getExtension('WEBGL_lose_context')?.loseContext();
  this.renderer=new THREE.WebGLRenderer({canvas,antialias:!this.software});
  const gl=this.renderer.getContext() as WebGL2RenderingContext;
  const samples=this.software?[]:Array.from(gl.getInternalformatParameter(gl.RENDERBUFFER,gl.RGBA16F,gl.SAMPLES) as Int32Array);
  this.coverageSamples=samples.includes(2)?2:samples.includes(4)?4:0;
  // Inspection-only resolution override for readable art review on a software renderer.
  // It does not enable GPU-only effects or change normal gameplay's reduced profile.
  const query=new URLSearchParams(location.search),requestedDpr=Number(query.get('dpr')??.5);
  this.inspectionRatio=query.has('inspect')&&Number.isFinite(requestedDpr)?requestedDpr:undefined;
  this.renderer.info.autoReset=false;this.renderer.setPixelRatio(presentationProfile(this.settings,this.software,devicePixelRatio,this.inspectionRatio).pixelRatio);
  this.renderer.shadowMap.enabled=!this.software;this.renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.12;
  this.scene.background=new THREE.Color('#60778c');this.scene.fog=new THREE.FogExp2('#516b81',.013);
  // Keep the credited HDRI for lighting; its rural field is not London's skyline.
  const skyGeo=new THREE.SphereGeometry(120,24,12),skyColors:number[]=[];
  const skyTop=new THREE.Color('#344d68'),skyHorizon=new THREE.Color('#939b9e');
  for(let i=0;i<skyGeo.attributes.position.count;i++){const y=skyGeo.attributes.position.getY(i)/120,c=skyHorizon.clone().lerp(skyTop,Math.max(0,y));skyColors.push(c.r,c.g,c.b)}
  skyGeo.setAttribute('color',new THREE.Float32BufferAttribute(skyColors,3));
  this.sky=new THREE.Mesh(skyGeo,new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.BackSide,depthWrite:false,fog:false}));this.scene.add(this.sky);
  this.camera.rotation.order='YXZ';this.scene.add(this.camera);
  this.hemi=new THREE.HemisphereLight('#b4d0ee','#323e43',1.35);this.scene.add(this.hemi);
  const sun=new THREE.DirectionalLight('#b7cce2',1.35);this.sun=sun;sun.position.set(-18,25,-14);sun.castShadow=true;
  sun.shadow.mapSize.set(2048,2048);sun.shadow.normalBias=.025;Object.assign(sun.shadow.camera,{left:-25,right:25,top:25,bottom:-25,near:1,far:90});this.scene.add(sun);
  if(level.id==='heron-reach'){const c=reach.capture;sun.target.position.set(c.x,0,c.z);sun.position.set(c.x-18,25,c.z-14);Object.assign(sun.shadow.camera,{left:-38,right:38,top:38,bottom:-38});this.scene.add(sun.target)}
  this.vmScene.add(this.vmCamera,new THREE.HemisphereLight('#bbd4ed','#222c36',1.4));
  const key=new THREE.DirectionalLight('#d9e5ef',1.7);key.position.set(-1,2,3);this.vmScene.add(key);
  this.ready=this.load();this.resize();window.addEventListener('resize',()=>this.resize());
 }
 private async load(){
  const loader=new THREE.TextureLoader(),pending:Promise<unknown>[]=[];
  for(const name of ['brick','stock','concrete','asphalt','paving','steel']){
   const mat=new THREE.MeshStandardMaterial({roughness:1,vertexColors:true});this.mats[name]=mat;
   if(name==='stock'){
    pending.push(loader.loadAsync('/materials/homes/stock-color.webp').then(t=>{t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=this.software?2:4;t.colorSpace=THREE.SRGBColorSpace;mat.map=t;mat.roughness=.93;mat.needsUpdate=true}));continue;
   }
   for(const kind of ['color','normal','arm'])pending.push(loader.loadAsync(name==='asphalt'&&kind==='color'?'/materials/detail/generated-asphalt-color.webp':`/materials/pbr/${name==='stock'?'brick':name}-${kind}.webp`).then(t=>{
    t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=this.software?2:4;
    if(kind==='color'){t.colorSpace=THREE.SRGBColorSpace;mat.map=t}else if(kind==='normal'){mat.normalMap=t;mat.normalScale.set(.45,.45)}else{mat.roughnessMap=t;mat.aoMap=t;if(name==='steel'){mat.metalnessMap=t;mat.metalness=.75}}
    if(name==='stock')mat.color.set('#b9ad8e');if(name==='asphalt')mat.roughness=.55;mat.needsUpdate=true;
   }));
  }
  const colors:Record<string,string>={dark:'#26323b',glass:'#364f64',lit:'#ffe3ad',trim:'#c0c2b7',soil:'#30271b',leaves:'#3e502b',wood:'#554335',paint:'#284952',wet:'#314454',amber:'#a47125',grass:'#657044',litter:'#b6a88b',rubbish_metal:'#808785',mud:'#ffffff',leak:'#ffffff',paint_worn:'#c6ac72',contact:'#20221b',plaster:'#c4bb9d',fabric:'#aaaa9f',roof:'#3b444b'};
  for(const [name,color]of Object.entries(colors))this.mats[name]=new THREE.MeshStandardMaterial({color,vertexColors:true,roughness:name==='wet'?.12:name==='glass'?.18:.8,metalness:name==='glass'||name==='wet'?.45:0});
  this.mats.lit.emissive.set('#ffb35b');this.mats.lit.emissiveIntensity=1.2;
  this.mats.grass.side=THREE.DoubleSide;this.mats.litter.side=THREE.DoubleSide;
  this.mats.rubbish_metal.metalness=.65;this.mats.rubbish_metal.roughness=.65;
  this.mats.contact.transparent=true;this.mats.contact.depthWrite=false;this.mats.contact.side=THREE.DoubleSide;this.mats.contact.polygonOffset=true;this.mats.contact.polygonOffsetFactor=-2;
  for(const [name,asset]of [['mud','Ground110'],['leak','Leaking003']]){
   const mat=this.mats[name];mat.transparent=true;mat.depthWrite=false;mat.alphaTest=.025;mat.polygonOffset=true;mat.polygonOffsetFactor=-1;mat.side=THREE.DoubleSide;
   for(const channel of ['Color','NormalGL','Roughness'])pending.push(loader.loadAsync(`/materials/detail/${asset}-${channel==='Color'&&name==='leak'?'ColorA':channel}.webp`).then(t=>{t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=4;if(channel==='Color'){t.colorSpace=THREE.SRGBColorSpace;mat.map=t}else if(channel==='NormalGL'){mat.normalMap=t;mat.normalScale.set(.3,.3)}else mat.roughnessMap=t;mat.needsUpdate=true}));
  }
  const gltf=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  if(this.level.id==='heron-reach'){
   // ?art=0 shows the collision blockout instead of the Blender build, for checking the two against each other.
   const useArt=new URLSearchParams(location.search).get('art')!=='0';
   const arch=useArt?HeronReachMaterials.load(this.renderer,this.software).then(async m=>{
    // Render replacements only. The original dressing plan still owns every collider.
    const courtLamps=reach.lampAnchors.filter(a=>a.kind==='court');
    const dressing=reach.dressing.items.filter(p=>!isReplacedShopShelf(p)).map(p=>p.asset==='WALL_LAMP'&&Math.hypot(p.x-111,p.z-47.99)<.1?{...p,x:103}:p.asset==='LAMP_COLUMN'&&courtLamps.some(a=>Math.hypot(a.x-(p.x-72),a.z-(p.z-60))<.2)?{...p,asset:'CAGE_FLOODLIGHT',ry:Math.atan2(72-p.x,60-p.z)}:p);
    const [built,kits,grass,shops,gallery,lived]=await Promise.all([loadHeronReachArch(gltf,m),fetch('/models/heron-reach/facade-dressing.json').then(r=>r.json()).catch(()=>[]).then(facade=>loadHeronReachKits(gltf,m,[...dressing,{asset:'CAGE_MARKINGS',x:72,y:0,z:60,ry:0},...facade],m.names(),this.software,this.coverageSamples>0)),this.grass.build(gltf,this.software?1.5:5),loadShopArt(gltf),loadGalleryArt(gltf,this.software,this.coverageSamples>0),loadLivedDetail(gltf,m)]);
    const [scanned,shopDepth,stairs,buildings]=await Promise.all([loadScannedDetail(gltf,shops),loadShopDepth(gltf,m,lived,shops),
     loadStairArt(gltf,m,built).catch(e=>{console.warn('Constructed stairs unavailable; retaining original stair art',e);return new THREE.Group()}),
     loadBuildingArt(gltf,m,built).catch(e=>{console.warn('Building construction unavailable; retaining original building art',e);return new THREE.Group()})]);
    await m.ready();this.artTextureStats=m.textureStats;m.disposeTranscoder();
    const root=new THREE.Group();root.name='ONSITE / Heron Reach';root.add(built,kits,grass,shops,gallery,lived,scanned,shopDepth,stairs,buildings);return root;
   }).catch(e=>{console.warn('Heron Reach art unavailable; showing the blockout',e);return null}):Promise.resolve(null);
   const [character,rifle,art]=await Promise.all([gltf.loadAsync('/models/onsite-operator.glb'),gltf.loadAsync('/models/onsite-carbine.glb'),arch,...pending,this.environment()]);
   if(art){this.scene.add(art);this.blueHour();for(const t of reach.signs)this.sign(t.text,t.x,t.y,t.z,t.w,t.ry);installHeronDepthFog(this.scene);this.contacts=new HeronContactShadows(this.scene,this.level)}else this.blockout();
   this.rifle=rifle.scene;return character.scene;
  }
  const [estate,character,rifle]=await Promise.all([
   gltf.loadAsync('/models/onsite-heron-court.glb'),gltf.loadAsync('/models/onsite-operator.glb'),gltf.loadAsync('/models/onsite-carbine.glb'),
   ...pending,this.props(gltf),this.environment()
  ]);
  estate.scene.name='ONSITE / Blender Heron Estate';
  estate.scene.traverse(o=>{if(o instanceof THREE.Mesh){
   const old=o.material as THREE.MeshStandardMaterial,name=old.name;
   o.material=this.mats[name]??old;o.castShadow=true;o.receiveShadow=true;
   if(name==='wet')o.castShadow=false;
  }});
  this.scene.add(estate.scene);this.rifle=rifle.scene;this.signage();return character.scene;
 }
 /** Heron Reach blockout: one merged mesh per material, built from the collision boxes themselves. */
 private blockout(){
  const metres:Record<string,number>={brick:1.2,stock:1.2,concrete:3,asphalt:4,steel:2},groups=new Map<string,THREE.BufferGeometry[]>();
  // Guards read as dark perforated metal panels so floors stay legible; collision is unchanged.
  this.mats.guard=new THREE.MeshStandardMaterial({color:'#2a3137',metalness:.6,roughness:.45,transparent:true,opacity:.55,vertexColors:true,depthWrite:false});
  for(const s of this.level.solids){
   const g=new THREE.BoxGeometry(s.w,s.h,s.d);g.translate(s.x,s.y,s.z);const pos=g.attributes.position,nor=g.attributes.normal,uv=g.attributes.uv,k=1/(metres[s.mat]??1);
   for(let i=0;i<pos.count;i++){const [x,y,z]=[pos.getX(i),pos.getY(i),pos.getZ(i)],ax=Math.abs(nor.getX(i)),ay=Math.abs(nor.getY(i));uv.setXY(i,(ay>.5?x:ax>.5?z:x)*k,(ay>.5?z:y)*k)}
   g.setAttribute('color',new THREE.Float32BufferAttribute(new Array(pos.count*3).fill(1),3));
   const key=s.mat==='steel'&&(s.id==='guard'||s.id.endsWith('-guard')||s.id.endsWith('-balustrade'))?'guard':s.mat;groups.set(key,[...(groups.get(key)||[]),g]);
  }
  const root=new THREE.Group();root.name='ONSITE / Heron Reach blockout (B01 Rowan)';
  for(const [mat,geos]of groups){const m=new THREE.Mesh(mergeGeometries(geos),this.mats[mat]??this.mats.concrete);m.name=mat;m.castShadow=!['glass','lit','guard'].includes(mat);m.receiveShadow=true;root.add(m);geos.forEach(g=>g.dispose())}
  this.scene.add(root);this.reachDetails();
 }
 /** Heron Reach at blue hour: graded dusk sky, cool sky light, lamp pool, glow and bloom. */
 private blueHour(){
  this.scene.remove(this.sky);this.camera.near=.1;this.camera.far=600;this.camera.updateProjectionMatrix();
  this.hemi.color.set('#b3c5d8');this.hemi.groundColor.set('#343a3d');this.hemi.intensity=1.8;
  this.sun.color.set('#c0cad4');this.sun.intensity=.65;
  this.renderer.toneMappingExposure=1.12;
  const artAnchors=[...reach.lampAnchors.map(a=>a.kind==='court'?{...a,y:6.35,floorY:0}:a.kind==='wall'&&Math.hypot(a.x-39,a.z+12.78)<.1?{...a,x:31}:a),...shopLightAnchors,...stairLightAnchors,...[52,61].map(x=>({x:x-72,y:5.8,z:38.1-60,kind:'gallery',floorY:3}))];
  this.atmosphere=new HeronReachAtmosphere(this.scene,this.renderer,artAnchors,this.software,this.level.solids.filter(s=>this.level.surfaceIds.includes(s.id)),this.level.solids);
  this.scene.add(buildDecals(reach.dressing.decals,this.software?2:8));
  // Rain thins out under any slab or roof above the camera (decks, arcades, cores, the undercroft).
  const roofs=this.level.solids.filter(s=>['slab','roof','landing','ground'].includes(s.id)||s.id.endsWith('-cap'));
  const covered=(x:number,y:number,z:number)=>roofs.some(s=>s.y>y&&s.y-y<12&&Math.abs(x-s.x)<s.w/2&&Math.abs(z-s.z)<s.d/2);
  // Rain's exterior colour proxies have no floor/occlusion selection. Sheltered
  // stair strips must not consume those slots or colour outside rain orange.
  if(new URLSearchParams(location.search).get('rain')!=='0'){this.rain=new Rain(this.software?1500:6000,covered,artAnchors.filter(a=>a.kind!=='core'));this.scene.add(this.rain.mesh)}
  if(!this.software){
   const size=this.renderer.getSize(new THREE.Vector2());this.composer=new EffectComposer(this.renderer);
   // Canvas antialiasing does not multisample the composer's offscreen scene target.
   // Enable coverage only when this half-float format supports it; otherwise nets blend alpha.
   this.composer.renderTarget1.samples=this.composer.renderTarget2.samples=this.coverageSamples;
   this.composer.addPass(new RenderPass(this.scene,this.camera));this.bloom=new UnrealBloomPass(size.multiplyScalar(.5),.32,.45,1.15);this.composer.addPass(this.bloom);this.composer.addPass(new OutputPass());
   this.applySettings(this.settings);
  }
 }
 private reachDetails(){
  for(const t of reach.signs)this.sign(t.text,t.x,t.y,t.z,t.w,t.ry);
  for(const l of reach.lights){const p=new THREE.PointLight('#ffb366',l.kind==='street'||l.kind==='court'?30:14,l.kind==='street'||l.kind==='court'?12:6,2);p.position.set(l.x,l.y,l.z);this.scene.add(p)}
 }
 installWeapon(g:Encounter){this.activeRifle=donorRifle(this.rifle,g.fx.flashTexture,g.fx.flameTexture);g.arsenal.installRifle(this.activeRifle);this.vmCamera.add(g.arsenal.holder,g.arsenal.muzzleLight);if(this.level.id==='heron-reach')installHeronDepthFog(this.scene)}
 weaponProbe(){const vm=this.activeRifle;if(!vm)return null;const sight=vm.root.getObjectByName('RearIronSight')!.getWorldPosition(new THREE.Vector3()).project(this.vmCamera),hand=vm.root.getObjectByName('Hand_L')!.getWorldPosition(new THREE.Vector3()),grip=vm.mag!.getObjectByName('MagazineGripSocket')!.getWorldPosition(new THREE.Vector3());return {name:vm.root.name,sightNdc:sight.toArray(),magazine:vm.mag!.position.toArray(),handToMagazine:hand.distanceTo(grip),finite:vm.root.matrixWorld.elements.every(Number.isFinite)}}
 private async environment(){
  const hdr=await new RGBELoader().loadAsync('/models/donors/bambanani_sunset_2k.hdr');hdr.mapping=THREE.EquirectangularReflectionMapping;
  const pm=new THREE.PMREMGenerator(this.renderer),env=pm.fromEquirectangular(hdr).texture;
  this.scene.environment=env;this.scene.environmentIntensity=.42;
  this.scene.backgroundRotation.y=1.1;this.scene.environmentRotation.y=1.1;
  this.vmScene.environment=env;this.vmScene.environmentIntensity=.6;pm.dispose();
 }
 private async props(loader:GLTFLoader){
  const sources=new Map<string,THREE.Object3D>();
  await Promise.all([...new Set(dressing.map(p=>p.asset))].map(async name=>{sources.set(name,(await loader.loadAsync(`/models/donors/${name}.glb`)).scene)}));
  const place=(source:THREE.Object3D,x:number,y:number,z:number,height:number,ry:number)=>{
   const m=source.clone(true),bounds=new THREE.Box3().setFromObject(m),size=bounds.getSize(new THREE.Vector3()),center=bounds.getCenter(new THREE.Vector3()),k=height/size.y;
   m.scale.multiplyScalar(k);m.position.set(-center.x*k,-bounds.min.y*k,-center.z*k);
   const root=new THREE.Group();root.name='Donor / '+source.name;root.add(m);root.position.set(x,y,z);root.rotation.y=ry;this.scene.add(root);
   m.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=true;o.receiveShadow=true}});
  };
  dressing.forEach(p=>place(sources.get(p.asset)!,p.x,p.y,p.z,p.height,p.ry));
  const [box,light,bench]=await Promise.all(['ph-utility_box_02','ph-security_light','estate-bench'].map(n=>loader.loadAsync('/models/'+n+'.glb')));
  for(const [x,z,ry]of [[-11.5,-1.7,Math.PI/2],[11.5,1.7,-Math.PI/2]])place(box.scene,x,0,z,1.3,ry);
  for(const x of [-6,6])place(light.scene,x,2.1,-8.8,.4,0);
  for(const x of [-7,7])place(bench.scene,x,0,7.8,1.1,Math.PI);
 }
 private sign(text:string,x:number,y:number,z:number,w:number,ry=0){
  const c=document.createElement('canvas');c.width=1024;c.height=128;const ctx=c.getContext('2d')!;
  ctx.fillStyle='#18282d';ctx.fillRect(0,0,1024,128);ctx.fillStyle='#eee5d1';ctx.font='600 62px sans-serif';ctx.textAlign='center';ctx.fillText(text,512,85);
  const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
  const m=new THREE.Mesh(new THREE.PlaneGeometry(w,w/8),new THREE.MeshStandardMaterial({map:t,roughness:.8}));m.position.set(x,y,z);m.rotation.y=ry;this.scene.add(m);
 }
 private signage(){
  this.sign('HERON COURT / SE15',0,5.2,-8.84,5);this.sign('THE CORNER / OFF LICENCE',6,2.5,8.84,4.4,Math.PI);
  this.sign('01 / HERON COURT',-9,2.45,-8.84,1.6);
  this.sign('STAIR A / 01—12',-11.83,2.5,-4.1,1.4,Math.PI/2);this.sign('STAIR B / 13—24',11.83,2.5,4.1,1.4,-Math.PI/2);
  this.sign('HERON / MAINTENANCE',0,1.9,1.58,2.5);
  // Four local pools give readable warm/cool separation without 24 per-pixel lights.
  for(const [x,y,z]of [[-8,3.4,-4.9],[8,3.4,4.9],[-6,2.3,-8.5],[6,2.3,8.5]]){
   const l=new THREE.PointLight('#ffad52',22,9,2);l.position.set(x,y,z);this.scene.add(l);
  }
  for(const x of [-8.7,-16]){const lamp=new THREE.PointLight('#ffdcaa',14,5.5,2);lamp.position.set(x,2.35,-12.5);this.scene.add(lamp)}
 }
 render(g:Encounter,alpha:number,dt:number,look:{x:number;y:number},overview=false){
  g.player.eye(alpha,this.camera.position);g.audio.setListener(this.camera.position,g.player.forward(new THREE.Vector3()));
  const pose=cameraPresentation(g.player.pitch,g.player.yaw,g.arsenal.punch,this.settings.reducedMotion);
  this.camera.rotation.set(pose.pitch,pose.yaw,pose.roll,'YXZ');this.camera.fov=74*g.arsenal.fovScale();this.camera.updateProjectionMatrix();
  g.arsenal.animate(Math.min(dt,.033),look,this.settings.reducedMotion);for(const b of g.bots)b.render(alpha);this.contacts?.update(g.bots);g.fx.update(Math.min(dt,.05));this.vmCamera.position.copy(this.camera.position);this.vmCamera.quaternion.copy(this.camera.quaternion);
  if(overview){const o=this.level.overview;this.camera.position.set(o.from.x,o.from.y,o.from.z);this.camera.lookAt(o.to.x,o.to.y,o.to.z);this.camera.fov=74;this.camera.updateProjectionMatrix()}
  const t=this.clock.getElapsedTime();this.atmosphere?.update(this.camera,t);this.grass.update(this.camera);this.rain?.update(this.camera,t,dt);
  this.renderer.info.reset();this.renderer.autoClear=true;if(this.composer)this.composer.render();else this.renderer.render(this.scene,this.camera);
  if(!overview){this.renderer.autoClear=false;this.renderer.clearDepth();this.renderer.render(this.vmScene,this.vmCamera)}this.renderer.autoClear=true;
 }
 applySettings(settings:Pick<PlayerSettings,'quality'|'reducedMotion'>){
  this.settings={...settings};const profile=presentationProfile(settings,this.software,devicePixelRatio,this.inspectionRatio);
  if(this.renderer.getPixelRatio()!==profile.pixelRatio){this.renderer.setPixelRatio(profile.pixelRatio);this.composer?.setPixelRatio(profile.pixelRatio);this.resize()}
  if(this.bloom)this.bloom.enabled=profile.bloom;
 }
 presentation(){return {...this.settings,pixelRatio:this.renderer.getPixelRatio(),bloom:!!this.bloom?.enabled,contactInstances:this.contacts?.mesh.count??0}}
 resize(){this.renderer.setSize(innerWidth,innerHeight);this.composer?.setSize(innerWidth,innerHeight);this.camera.aspect=innerWidth/innerHeight;this.camera.updateProjectionMatrix();this.vmCamera.aspect=this.camera.aspect;this.vmCamera.updateProjectionMatrix()}
}
