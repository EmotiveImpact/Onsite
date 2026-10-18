import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js'
import {batchStatic} from '../adapted/environment.js'
import {solids} from './level'
import type {Encounter} from './Encounter'
export class View{
 readonly renderer:THREE.WebGLRenderer;readonly scene=new THREE.Scene();readonly camera=new THREE.PerspectiveCamera(74,1,.06,150);
 readonly vmScene=new THREE.Scene();readonly vmCamera=new THREE.PerspectiveCamera(52,1,.025,8);readonly software:boolean;readonly mats:Record<string,THREE.MeshStandardMaterial>={};private boxes:THREE.Mesh[]=[];readonly ready:Promise<THREE.Object3D>;
 constructor(canvas:HTMLCanvasElement){
 this.renderer=new THREE.WebGLRenderer({canvas,antialias:false});const gl=this.renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');this.software=!!ext&&/swiftshader|llvmpipe/i.test(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL));
 this.renderer.info.autoReset=false;this.renderer.setPixelRatio(this.software?.5:Math.min(devicePixelRatio,1.5));this.renderer.shadowMap.enabled=!this.software;this.renderer.shadowMap.type=THREE.PCFSoftShadowMap;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.2;
 this.scene.background=new THREE.Color('#344554');this.scene.fog=new THREE.FogExp2('#344554',.012);this.camera.rotation.order='YXZ';this.scene.add(this.camera);
 this.scene.add(new THREE.HemisphereLight('#b8d3ef','#4a4440',2));const sun=new THREE.DirectionalLight('#b9cee5',2);sun.position.set(-20,35,12);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);Object.assign(sun.shadow.camera,{left:-25,right:25,top:25,bottom:-25,near:1,far:100});this.scene.add(sun);
 const pm=new THREE.PMREMGenerator(this.renderer),room=new RoomEnvironment();this.scene.environment=pm.fromScene(room,.04).texture;this.scene.environmentIntensity=.35;this.vmScene.environment=this.scene.environment;this.vmScene.environmentIntensity=.6;this.vmScene.add(this.vmCamera,new THREE.HemisphereLight('#d3deec','#383b40',2));const key=new THREE.DirectionalLight('#f4d6ab',2);key.position.set(-1,2,3);this.vmScene.add(key);room.dispose();pm.dispose();
 const loader=new THREE.TextureLoader(),pending:Promise<unknown>[]=[];
 for(const name of ['brick','stock','concrete','asphalt','paving','steel']){
 const mat=new THREE.MeshStandardMaterial({roughness:1});this.mats[name]=mat;
 for(const kind of ['color','normal','arm'])pending.push(loader.loadAsync(`/materials/pbr/${name==='stock'?'brick':name}-${kind}.webp`).then(t=>{t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=4;if(kind==='color'){t.colorSpace=THREE.SRGBColorSpace;mat.map=t}else if(kind==='normal'){mat.normalMap=t;mat.normalScale.set(.45,.45)}else {mat.roughnessMap=t;mat.aoMap=t;if(name==='steel'){mat.metalnessMap=t;mat.metalness=1}}if(name==='stock')mat.color.set('#c1bfa8');if(name==='asphalt')mat.roughness=.7;mat.needsUpdate=true}));
 }
 this.mats.dark=new THREE.MeshStandardMaterial({color:'#151b20',roughness:.7});this.mats.glass=new THREE.MeshStandardMaterial({color:'#273a49',roughness:.25,metalness:.5});this.mats.lit=new THREE.MeshStandardMaterial({color:'#e6cda1',emissive:'#e9b76c',emissiveIntensity:.8});this.mats.trim=new THREE.MeshStandardMaterial({color:'#838a87',roughness:.75});
 for(const s of solids){if(s.mat==='rail'){this.rail(s.x,s.y,s.z,s.w,s.d);continue}this.box(s.x,s.y,s.z,s.w,s.h,s.d,s.mat)}
 this.detail();batchStatic(this.scene,this.boxes);this.boxes=[];
 this.ready=Promise.all([...pending,this.props(),new GLTFLoader().loadAsync('/models/hooded-opponent.glb')]).then(a=>(a.at(-1) as {scene:THREE.Object3D}).scene);
 this.resize();window.addEventListener('resize',()=>this.resize());
 }
 box(x:number,y:number,z:number,w:number,h:number,d:number,name='concrete'){
 const g=new THREE.BoxGeometry(w,h,d),uv=g.attributes.uv;for(let i=0;i<uv.count;i++){const f=Math.floor(i/4),u=f<2?d:w,v=f<2?h:f<4?d:h;uv.setXY(i,uv.getX(i)*u/(name==='brick'||name==='stock'?.65:2),uv.getY(i)*v/(name==='brick'||name==='stock'?.65:2))}
 const m=new THREE.Mesh(g,this.mats[name]||this.mats.concrete);m.position.set(x,y,z);m.castShadow=true;m.receiveShadow=true;this.scene.add(m);this.boxes.push(m);return m;
 }
 rail(x:number,y:number,z:number,w:number,d:number){const along=w>d,len=Math.max(w,d);for(let i=0;i<=Math.ceil(len/.18);i++){const t=-len/2+i*len/Math.ceil(len/.18);this.box(x+(along?t:0),y,z+(along?0:t),.025,1.1,.025,'dark')}for(const h of [-.45,.5])this.box(x,y+h,z,along?w:.05,.05,along?.05:d,'dark')}
 sign(text:string,x:number,y:number,z:number,w:number,ry=0){const c=document.createElement('canvas');c.width=1024;c.height=128;const ctx=c.getContext('2d')!;ctx.fillStyle='#17232b';ctx.fillRect(0,0,1024,128);ctx.fillStyle='#e7deca';ctx.font='600 62px sans-serif';ctx.textAlign='center';ctx.fillText(text,512,85);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;const m=new THREE.Mesh(new THREE.PlaneGeometry(w,w/8),new THREE.MeshStandardMaterial({map:t,roughness:.8}));m.position.set(x,y,z);m.rotation.y=ry;this.scene.add(m)}
 detail(){
 // Inset facade bays, sills, structural bands and downpipes above the playable rooms.
 for(const side of [-1,1]){
 for(let row=0;row<3;row++)for(let col=0;col<12;col++){
 const x=-16.5+col*3,y=7.4+row*2.85,z=side*14.8;
 this.box(x,y,z,2.85,2.85,.32,'brick');this.box(x,y,z-side*.2,1.42,1.65,.16,'dark');this.box(x,y,z-side*.3,1.23,1.45,.04,(row*12+col)%5===0?'lit':'glass');this.box(x,y-.87,z-side*.3,1.62,.12,.3,'concrete');
 }
 for(let floor=0;floor<4;floor++)this.box(0,6+floor*2.85,side*14.6,36,.18,.6);
 for(let col=0;col<10;col++){const z=-13.5+col*3;for(let row=0;row<3;row++){
 const x=side*17.8,y=7.4+row*2.85;this.box(x,y,z,.32,2.85,2.85,'stock');this.box(x-side*.2,y,z,.16,1.65,1.42,'dark');this.box(x-side*.3,y,z,.04,1.45,1.23,(row+col)%5===0?'lit':'glass');}
 }
 for(const z of [-8.5,8.5])for(const x of [-10.5,-4.5,4.5,10.5]){this.box(x,1.4,z,.28,2.8,.28,'concrete');this.box(x,4.4,z,.28,2.8,.28,'concrete')}
 for(const x of [-11.8,11.8]){this.box(x,6.2,0,.16,.16,18,'dark');for(const z of [-8,0,8])this.box(x,3,z,.09,6,.09,'dark')}
 }
 for(const [x,z,rot]of [[-6,-8.85,0],[6,-8.85,0],[-11.85,0,Math.PI/2],[11.85,0,-Math.PI/2]]){
 for(const y of [2.4,5.4]){this.box(x,y,z,.3,.18,.2,'lit');const l=new THREE.PointLight('#ffbc68',5,5,2);l.position.set(x,y,z);if(!this.software)this.scene.add(l)}
 }
 this.sign('HERON ESTATE',0,5.2,-8.84,5);this.sign('THE CORNER / OFF LICENCE',6,2.5,8.84,4.4,Math.PI);this.sign('STAIR A',-11.83,2.5,-4.1,1.3,Math.PI/2);this.sign('STAIR B',11.83,2.5,4.1,1.3,-Math.PI/2);
 // Roof over perimeter rooms, with open court retained. Separate render-only cap.
 for(const z of [-12,12])this.box(0,6.08,z,36,.16,6);for(const x of [-15,15])this.box(x,6.08,0,6,.16,18);
 for(const x of [-8,8])for(const z of [-4,4]){this.box(x,.07,z,1,.12,1,'paving');this.box(x,1.1,z,.09,2.2,.09,'dark');this.box(x,2.2,z,.22,.18,.22,'lit')}
 // Bike stands, drain grates, edging, brick planters and black service cabinets.
 for(let i=0;i<6;i++){const x=-4+i*.65;this.box(x,.45,12,.04,.9,.04,'steel');this.box(x,.45,12.6,.04,.9,.04,'steel');this.box(x,.9,12.3,.04,.04,.6,'steel')}
 for(const z of [-5.7,5.7]){this.box(0,.015,z,17,.025,.2,'dark');for(let x=-8;x<8;x+=.25)this.box(x,.03,z,.04,.02,.2,'steel')}
 for(const x of [-11.5,11.5])for(const z of [-1.8,1.8]){this.box(x,.65,z,.6,1.3,.7,'steel');this.box(x,.9,z,.62,.04,.72,'dark')}
 for(const z of [-5,5])this.box(0,.015,z,16,.02,.06,'trim');
 }
 async props(){
 const loader=new GLTFLoader();
 const [box,light,bench]=await Promise.all(['ph-utility_box_02','ph-security_light','estate-bench'].map(n=>loader.loadAsync('/models/'+n+'.glb')));
 const place=(source:THREE.Object3D,x:number,y:number,z:number,height:number,ry=0)=>{const m=source.clone(true),bounds=new THREE.Box3().setFromObject(m),size=bounds.getSize(new THREE.Vector3()),center=bounds.getCenter(new THREE.Vector3());const k=height/size.y;m.scale.setScalar(k);m.position.set(-center.x*k,-bounds.min.y*k,-center.z*k);const root=new THREE.Group();root.add(m);root.position.set(x,y,z);root.rotation.y=ry;this.scene.add(root);m.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=true;o.receiveShadow=true}})};
 for(const [x,z,ry]of [[-11.5,-1.7,Math.PI/2],[11.5,1.7,-Math.PI/2]])place(box.scene,x,0,z,1.3,ry);
 for(const x of [-6,6])place(light.scene,x,2.1,-8.8,.4);
 for(const x of [-7,7])place(bench.scene,x,0,7.8,1.1,Math.PI);
 }
 render(g:Encounter,alpha:number,dt:number,look:{x:number;y:number}){
 g.player.eye(alpha,this.camera.position);g.audio.setListener(this.camera.position,g.player.forward(new THREE.Vector3()));this.camera.rotation.set(g.player.pitch+g.arsenal.punch.pitch,g.player.yaw+g.arsenal.punch.yaw,g.arsenal.punch.roll,'YXZ');
 this.camera.fov=74*g.arsenal.fovScale();this.camera.updateProjectionMatrix();g.arsenal.animate(Math.min(dt,.033),look,false);for(const b of g.bots)b.render(alpha);g.fx.update(Math.min(dt,.05));this.vmCamera.position.copy(this.camera.position);this.vmCamera.quaternion.copy(this.camera.quaternion);
 this.renderer.info.reset();this.renderer.autoClear=true;this.renderer.render(this.scene,this.camera);this.renderer.autoClear=false;this.renderer.clearDepth();this.renderer.render(this.vmScene,this.vmCamera);this.renderer.autoClear=true;
 }
 resize(){this.renderer.setSize(innerWidth,innerHeight);this.camera.aspect=innerWidth/innerHeight;this.camera.updateProjectionMatrix();this.vmCamera.aspect=this.camera.aspect;this.vmCamera.updateProjectionMatrix()}
}
