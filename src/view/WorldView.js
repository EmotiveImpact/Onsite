import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { solids, lamps, OBJECTIVE } from '../sim/level.js';
import { batchStatic, chainLinkTexture } from '../adapted/environment.js';
import { spring } from '../adapted/gameplay.js';
export class WorldView {
  constructor(canvas) {
    this.renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'high-performance'});
    const gl=this.renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');
    this.software=!!ext&&/swiftshader|llvmpipe/i.test(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL));
    this.renderer.setPixelRatio(this.software?.55:Math.min(devicePixelRatio,1.25));
    this.renderer.shadowMap.enabled=!this.software;this.renderer.shadowMap.type=THREE.PCFSoftShadowMap;
    this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.25;
    this.scene=new THREE.Scene();this.scene.background=new THREE.Color('#293c52');this.scene.fog=new THREE.FogExp2('#334456',.011);
    this.camera=new THREE.PerspectiveCamera(74,1,.06,220);this.camera.rotation.order='YXZ';
    this.scene.add(this.camera);
    const pmrem=new THREE.PMREMGenerator(this.renderer);const room=new RoomEnvironment();
    this.environment=pmrem.fromScene(room,.04);this.scene.environment=this.environment.texture;this.scene.environmentIntensity=.2;room.dispose();pmrem.dispose();
    this.scene.add(new THREE.HemisphereLight('#b1c7e3','#252323',1.5));
    const sun=new THREE.DirectionalLight('#b0c5e5',2.2);sun.position.set(-20,35,15);sun.castShadow=true;
    sun.shadow.mapSize.set(this.software?512:1024,this.software?512:1024);Object.assign(sun.shadow.camera,{left:-32,right:32,top:32,bottom:-32,near:1,far:100});sun.shadow.bias=-.0004;this.scene.add(sun);
    this.staticBoxes=[];this.kick={x:0,v:0};this.materials={};this.pending=[];this.loader=new THREE.TextureLoader();
    for(const name of ['brick','stock','concrete','asphalt','paving','steel']) {
      const maps={};
      for(const kind of ['color','normal','roughness']) {
        let resolveTexture,rejectTexture;
        this.pending.push(new Promise((resolve,reject)=>{resolveTexture=resolve;rejectTexture=reject;}));
        const texture=this.loader.load(`/materials/${name}-${kind}.png`,resolveTexture,undefined,rejectTexture);
        if(kind==='color')texture.colorSpace=THREE.SRGBColorSpace;
        texture.wrapS=texture.wrapT=THREE.RepeatWrapping;texture.anisotropy=Math.min(8,this.renderer.capabilities.getMaxAnisotropy());
        maps[kind]=texture;
      }
      this.materials[name]=new THREE.MeshStandardMaterial({map:maps.color,normalMap:maps.normal,roughnessMap:maps.roughness,roughness:1,metalness:0});
    }
    for(const [name,mat]of Object.entries(this.materials))mat.name=name;
    this.materials.court=this.materials.asphalt;
    this.materials.glass=new THREE.MeshStandardMaterial({color:'#203444',metalness:.4,roughness:.24});
    this.materials.warm=new THREE.MeshStandardMaterial({color:'#eed0a0',emissive:'#e5a451',emissiveIntensity:1.2,roughness:.7});
    this.materials.dark=new THREE.MeshStandardMaterial({color:'#121a20',roughness:.8});
    this.materials.paint=new THREE.MeshStandardMaterial({color:'#c9c5b0',roughness:.8});
    this.effects=[];this.botRoot=new THREE.Group();this.scene.add(this.botRoot);
    this.weaponRoot=new THREE.Group();this.camera.add(this.weaponRoot);this.weaponRoot.position.set(.23,-.22,-.5);
    for(const s of solids) {
      if(s.material==='invisible')continue;
      if(s.material==='fence'){this.fence(s);continue;}
      if(s.id.includes('rail')){this.railing(s);continue;}
      const mesh=this.box(s.position.x,s.position.y,s.position.z,s.size.x,s.size.y,s.size.z,s.material);
      if(this.materials[s.material]?.map)this.setUVScale(mesh,s.size);
    }
    this.architecture();this.court();this.dressing();batchStatic(this.scene,this.staticBoxes);this.staticBoxes=[];
    this.objective=new THREE.Mesh(new THREE.OctahedronGeometry(.28),new THREE.MeshBasicMaterial({color:'#f4aa32',wireframe:true}));this.objective.position.set(OBJECTIVE.x,2.5,OBJECTIVE.z);this.scene.add(this.objective);
    this.flash=new THREE.PointLight('#ffbd5b',0,4);this.flash.position.set(0,0,-1);this.camera.add(this.flash);
    this.ready=Promise.all([...this.pending,this.loadModels()]);
    this.resize();
  }
  box(x,y,z,w,h,d,mat='concrete') {
    const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),typeof mat==='string'?this.materials[mat]:mat);
    mesh.position.set(x,y,z);mesh.castShadow=h>.3;mesh.receiveShadow=true;this.scene.add(mesh);this.staticBoxes.push(mesh);return mesh;
  }
  setUVScale(mesh,size){
    const uv=mesh.geometry.attributes.uv;
    for(let i=0;i<uv.count;i++){
      const face=Math.floor(i/4);const u=face<2?size.z:size.x;const v=face<2?size.y:face<4?size.z:size.y;
      uv.setXY(i,uv.getX(i)*u/2,uv.getY(i)*v/2);
    }
  }
  instances(geometry,material,items){
    const m=new THREE.InstancedMesh(geometry,material,items.length),o=new THREE.Object3D();
    items.forEach((p,i)=>{o.position.set(p.x,p.y,p.z);o.scale.set(p.sx??1,p.sy??1,p.sz??1);o.rotation.set(0,p.ry??0,0);o.updateMatrix();m.setMatrixAt(i,o.matrix);});
    m.receiveShadow=true;m.castShadow=false;this.scene.add(m);return m;
  }
  fence(s){
    const alongX=s.size.x>s.size.z,len=Math.max(s.size.x,s.size.z),items=[];
    const wire=chainLinkTexture();wire.repeat.set(len/.14,3/.14);
    const panel=new THREE.Mesh(new THREE.PlaneGeometry(len,3),new THREE.MeshStandardMaterial({map:wire,alphaTest:.35,side:THREE.DoubleSide,color:'#4a5154',roughness:.7}));
    panel.position.set(s.position.x,1.5,s.position.z);panel.rotation.y=alongX?0:Math.PI/2;this.scene.add(panel);
    for(let t=-len/2;t<=len/2+.01;t+=2.25)items.push({x:s.position.x+(alongX?t:0),y:1.5,z:s.position.z+(alongX?0:t),sx:.065,sy:3.1,sz:.065});
    this.instances(new THREE.BoxGeometry(1,1,1),this.materials.steel,items);
  }
  railing(s){
    const alongX=s.size.x>s.size.z,len=Math.max(s.size.x,s.size.z),items=[];
    items.push({x:s.position.x,y:4.28,z:s.position.z,sx:alongX?len:.06,sy:.06,sz:alongX?.06:len});
    for(let t=-len/2;t<=len/2;t+=.3)items.push({x:s.position.x+(alongX?t:0),y:3.73,z:s.position.z+(alongX?0:t),sx:.035,sy:1.1,sz:.035});
    this.instances(new THREE.BoxGeometry(1,1,1),this.materials.steel,items);
  }
  architecture(){
    const windows=[],lit=[],frames=[],balconies=[];
    const window=(x,y,z,ry,seed)=>{
      frames.push({x,y,z,ry,sx:1.65,sy:1.85,sz:.16});
      (seed%7===0||seed%11===0?lit:windows).push({x:x+Math.sin(ry)*.1,y,z:z+Math.cos(ry)*.1,ry,sx:1.38,sy:1.55,sz:.04});
    };
    for(let row=0;row<5;row++)for(let col=0;col<13;col++)window(-21+col*3.5,1.8+row*2.95,-21.43,0,row*13+col);
    for(let row=0;row<5;row++)for(let col=0;col<13;col++)window(-19.43,1.7+row*2.85,-20+col*3.3,Math.PI/2,row*17+col);
    for(let row=0;row<6;row++)for(let col=0;col<11;col++)window(19.43,1.8+row*2.85,-21+col*3.3,-Math.PI/2,row*19+col);
    this.instances(new THREE.BoxGeometry(),this.materials.dark,frames);
    this.instances(new THREE.BoxGeometry(),this.materials.glass,windows);
    this.instances(new THREE.BoxGeometry(),this.materials.warm,lit);
    for(let row=1;row<5;row++)balconies.push({x:0,y:row*2.95-.2,z:-21.15,sx:47,sy:.18,sz:.6});
    this.instances(new THREE.BoxGeometry(),this.materials.concrete,balconies);
    // Distant skyline establishes the estate without extending playable collision space.
    const towerMat=new THREE.MeshStandardMaterial({color:'#394553',roughness:1});
    for(let i=0;i<10;i++) {
      const x=-65+i*14,z=-43-(i%3)*8,h=20+(i%4)*6;
      this.box(x,h/2,z,9,h,9,towerMat);
      const dots=[];for(let r=0;r<h/3;r++)for(let c=0;c<3;c++)if((r*3+c+i)%4===0)dots.push({x:x-2.7+c*2.7,y:r*3+1.5,z:z+4.55,sx:.7,sy:1.1,sz:.02});
      this.instances(new THREE.BoxGeometry(),this.materials.warm,dots);
    }
    for(const z of [-6,-12,-18]){
      this.box(-19.3,1.25,z, .12,2.4,1.1,'dark');
      this.sign('HERON HOUSE',-19.28,2.75,z,1.3,.22,Math.PI/2);
    }
    this.sign('HERON ESTATE',0,4.2,-21.22,7,.7);
    this.sign('THE CORNER',16.8,3.5,-18.45,4.6,.65);
    this.box(16.8,1.65,-18.43,4.4,2.3,.06,'warm');
    this.box(16.8,1.6,-18.32,.08,2.8,.1,'steel');
    this.sign('STAIRS  /  01',-13.8,3.05,4.24,2.3,.4);
    this.sign('COURT 01',7,3.15,2.53,2.1,.38);
    // Handrail follows the real staircase.
    const a=new THREE.Vector3(-12.3,1,4.1),b=new THREE.Vector3(-12.3,4.2,-2.55);
    const rail=new THREE.Mesh(new THREE.CylinderGeometry(.035,.035,a.distanceTo(b),8),this.materials.steel);rail.position.copy(a).add(b).multiplyScalar(.5);rail.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),b.clone().sub(a).normalize());this.scene.add(rail);
    for(let i=0;i<8;i++)this.box(-12.3,.6+i*.2,4-i*.84,.035,1.1+i*.4,.035,'steel');
  }
  sign(text,x,y,z,w,h,ry=0){
    const c=document.createElement('canvas');c.width=1024;c.height=128;const ctx=c.getContext('2d');ctx.fillStyle='#1b2429';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='#d8d8cc';ctx.font='bold 68px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,512,68);
    const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
    const m=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshStandardMaterial({map:t,roughness:.8}));m.position.set(x,y,z);m.rotation.y=ry;this.scene.add(m);
  }
  court(){
    const line=(x,z,w,d)=>this.box(x,.083,z,w,.01,d,'paint');
    for(const x of [-.7,14.7])line(x,-7,.045,16.8);
    for(const z of [-15.4,1.4,-7])line(7,z,15.4,.045);
    const ring=new THREE.Mesh(new THREE.RingGeometry(2.05,2.1,64),this.materials.paint);ring.rotation.x=-Math.PI/2;ring.position.set(7,.092,-7);this.scene.add(ring);
    for(const z of [-14.8,.8]){
      for(const x of [5.5,8.5])this.box(x,1.05,z,.065,2.1,.065,'paint');
      this.box(7,2.08,z,3.05,.065,.065,'paint');
    }
  }
  dressing(){
    for(const p of lamps){
      const l=new THREE.PointLight('#ffbc69',32,13,2);l.position.set(p.x,3.8,p.z);this.scene.add(l);
      const glow=new THREE.Mesh(new THREE.SphereGeometry(.16,12,8),new THREE.MeshBasicMaterial({color:'#ffcb88'}));glow.position.copy(l.position);this.scene.add(glow);
    }
    for(const z of [-3,-10,-17]) {
      const l=new THREE.PointLight('#ffd197',13,8,2);l.position.set(-17,2.6,z);this.scene.add(l);
      this.box(-18.7,2.55,z,.16,.12,.6,'warm');
    }
    const leaf=new THREE.MeshStandardMaterial({color:'#273b2d',roughness:1});
    for(const p of [{x:-5,z:8},{x:17.8,z:7}])for(let i=0;i<6;i++){
      const m=new THREE.Mesh(new THREE.IcosahedronGeometry(.65,1),leaf);m.position.set(p.x+(i%3-1)*.6,1.4,p.z+(Math.floor(i/3)-.5)*.5);m.scale.y=.7;this.scene.add(m);
    }
    for(const x of [-9,18]){
      const trunk=new THREE.Mesh(new THREE.CylinderGeometry(.09,.17,5,8),new THREE.MeshStandardMaterial({color:'#352e27'}));trunk.position.set(x,2.5,14);this.scene.add(trunk);
      for(let i=0;i<6;i++){
        const m=new THREE.Mesh(new THREE.IcosahedronGeometry(1.2,1),leaf);m.position.set(x+Math.sin(i*2)*1.1,4.5+(i%2),14+Math.cos(i*2));this.scene.add(m);
      }
    }
    const puddleMat=new THREE.MeshStandardMaterial({color:'#455367',metalness:.55,roughness:.16,transparent:true,opacity:.45,depthWrite:false});
    for(let i=0;i<20;i++){
      const m=new THREE.Mesh(new THREE.CircleGeometry(.5+(i%4)*.25,20),puddleMat);m.rotation.x=-Math.PI/2;m.scale.x=2.3;m.position.set(-9+(i*7)%26,.012,5+(i*3)%16);this.scene.add(m);
    }
    // Original geometric litter bins, no third-party props.
    for(const z of [-4,10])this.box(-18, .55,z,.55,1.1,.55,'steel');
  }
  async loadModels(){
    const loader=new GLTFLoader();
    const [lamp,bench,bot,weapon]=await Promise.all(['estate-lamp','estate-bench','hooded-opponent','first-person-prop'].map(n=>loader.loadAsync(`/models/${n}.glb`)));
    for(const p of lamps){const m=lamp.scene.clone(true);m.position.set(p.x,0,p.z);this.scene.add(m);}
    for(const p of [{x:-8,z:5,ry:0},{x:17.7,z:-4,ry:-Math.PI/2}]){const m=bench.scene.clone(true);m.position.set(p.x,0,p.z);m.rotation.y=p.ry;this.scene.add(m);}
    this.botRoot.add(bot.scene);this.botModel=bot.scene;
    this.botParts=[];bot.scene.traverse(o=>{if(o.isMesh){o.castShadow=true;if(/Leg_|Trainer_/.test(o.name))this.botParts.push({object:o,z:o.position.z,name:o.name});}});
    this.weaponRoot.add(weapon.scene);weapon.scene.rotation.y=Math.PI;weapon.scene.scale.setScalar(.85);
    // Viewmodel stays on top of close walls, and never affects world hit tests.
    weapon.scene.traverse(o=>{if(o.isMesh){o.material=o.material.clone();o.material.depthTest=false;o.material.depthWrite=false;o.renderOrder=10;}});
  }
  event(e){
    if(e.type==='shot'){this.flash.intensity=10;this.kick.v+=.8;}
    if(e.type==='shot'||e.type==='bot-shot'){
      const origin=e.type==='shot'?new THREE.Vector3(.2,-.18,-.95).applyMatrix4(this.camera.matrixWorld):new THREE.Vector3(e.origin.x,e.origin.y,e.origin.z);
      const g=new THREE.BufferGeometry().setFromPoints([origin,new THREE.Vector3(e.end.x,e.end.y,e.end.z)]);
      const m=new THREE.Line(g,new THREE.LineBasicMaterial({color:e.type==='shot'?'#ffcd87':'#ff7249',transparent:true,opacity:.8}));this.scene.add(m);this.effects.push({m,life:.06});
    }
  }
  update(snapshot,dt,time,active){
    const p=snapshot.player.position;
    this.camera.position.set(p.x,p.y+.7,p.z);this.camera.rotation.set(snapshot.player.pitch,snapshot.player.yaw,0,'YXZ');
    this.botRoot.position.set(snapshot.bot.position.x,snapshot.bot.position.y-.85,snapshot.bot.position.z);this.botRoot.rotation.y=snapshot.bot.yaw+Math.PI;
    this.botRoot.visible=snapshot.bot.health>0;
    if(this.botModel)for(const part of this.botParts)part.object.position.z=part.z+(snapshot.bot.mode==='patrol'||snapshot.bot.mode==='search'?Math.sin(time*8+(part.name.endsWith('L')?0:Math.PI))*.08:0);
    this.weaponRoot.visible=active;this.weaponRoot.rotation.x=snapshot.weapon.reloadRemaining>0?-.55:0;
    this.weaponRoot.position.z=-.5+spring(this.kick,0,160,18,dt);this.weaponRoot.position.y=-.22+Math.sin(time*2)*.002;this.flash.intensity=Math.max(0,this.flash.intensity-dt*120);
    this.objective.rotation.y=time;this.objective.visible=snapshot.status!=='won';
    for(let i=this.effects.length-1;i>=0;i--){const e=this.effects[i];e.life-=dt;if(e.life<=0){this.scene.remove(e.m);e.m.geometry.dispose();e.m.material.dispose();this.effects.splice(i,1);}}
    this.renderer.render(this.scene,this.camera);
  }
  surfaceAt(x,y){const ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2(x,y),this.camera);return ray.intersectObjects(this.scene.children,true).slice(0,5).map(h=>({name:h.object.name,material:h.object.material?.name,point:h.point.toArray(),distance:h.distance}));}
  resize(){this.renderer.setSize(innerWidth,innerHeight);this.camera.aspect=innerWidth/innerHeight;this.camera.updateProjectionMatrix();}
}
