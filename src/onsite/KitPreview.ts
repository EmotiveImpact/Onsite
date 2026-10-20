// The kit menu renders the exact authored bot asset. It has no simulation or physics.
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {OPERATOR_ASSET,DEFAULT_OPERATOR_KIT,createOperatorVisual,setOperatorKit,OperatorAnimator,type OperatorKit} from './OperatorVisual'

export class KitPreview{
 readonly ready:Promise<void>
 private readonly renderer:THREE.WebGLRenderer
 private readonly scene=new THREE.Scene()
 private readonly camera=new THREE.PerspectiveCamera(32,1,.1,10)
 private readonly stage=new THREE.Group()
 private readonly observer:ResizeObserver
 private model:THREE.Object3D|null=null
 private animator:OperatorAnimator|null=null
 private kit:OperatorKit={...DEFAULT_OPERATOR_KIT}
 private active=false
 private disposed=false
 private frame=0
 private last=0
 private turn=.38
 private dragging=false
 private pointerX=0
 constructor(private readonly container:HTMLElement){
  this.renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power'})
  this.renderer.setPixelRatio(Math.min(window.devicePixelRatio,1.5))
  this.renderer.outputColorSpace=THREE.SRGBColorSpace
  this.renderer.toneMapping=THREE.ACESFilmicToneMapping
  this.renderer.toneMappingExposure=1.25
  this.renderer.domElement.setAttribute('aria-label','Three-dimensional operator kit preview. Drag to rotate.')
  this.renderer.domElement.style.cssText='width:100%;height:100%;display:block;touch-action:none;cursor:grab'
  container.append(this.renderer.domElement)
  this.scene.add(this.stage,new THREE.HemisphereLight(0xa4bdcc,0x32322e,2.2))
  const key=new THREE.DirectionalLight(0xffd7aa,4);key.position.set(-2,3,3);this.scene.add(key)
  const edge=new THREE.DirectionalLight(0x88b8db,3);edge.position.set(2,2,-2);this.scene.add(edge)
  const floor=new THREE.Mesh(new THREE.CircleGeometry(.60,40),new THREE.MeshStandardMaterial({color:0x222a2d,roughness:.9}))
  floor.rotation.x=-Math.PI/2;floor.position.y=-.006;this.scene.add(floor)
  this.camera.position.set(0,.98,3.5);this.camera.lookAt(0,.9,0)
  this.observer=new ResizeObserver(()=>this.resize());this.observer.observe(container)
  const canvas=this.renderer.domElement
  canvas.addEventListener('pointerdown',this.onDown)
  canvas.addEventListener('pointermove',this.onMove)
  canvas.addEventListener('pointerup',this.onUp)
  canvas.addEventListener('pointercancel',this.onUp)
  this.ready=new GLTFLoader().loadAsync(OPERATOR_ASSET).then(({scene})=>{
   if(this.disposed){this.release(scene);return}
   const {model}=createOperatorVisual(scene,this.kit)
   // Preview faces the camera; bot adapter keeps its existing -Z facing contract.
   model.rotation.y=0;this.model=model;this.stage.add(model);this.animator=new OperatorAnimator(model)
   this.resize();if(this.active)this.start()
  })
 }
 setKit(kit:OperatorKit){this.kit={...kit};if(this.model)setOperatorKit(this.model,this.kit);if(this.active)this.render(performance.now())}
 setActive(active:boolean){
  if(this.disposed)return
  this.active=active
  if(active){this.resize();this.start()}else{cancelAnimationFrame(this.frame);this.frame=0;this.last=0;this.dragging=false}
 }
 private resize(){
  if(this.disposed)return
  const box=this.container.getBoundingClientRect(),w=Math.max(1,box.width),h=Math.max(1,box.height)
  this.renderer.setSize(w,h,false);this.camera.aspect=w/h
  this.camera.position.z=Math.max(3.5,1.2/this.camera.aspect)
  this.camera.updateProjectionMatrix()
 }
 private start(){if(this.frame||!this.active||!this.model)return;this.last=performance.now();this.frame=requestAnimationFrame(this.tick)}
 private tick=(now:number)=>{this.frame=0;if(!this.active||this.disposed)return;this.render(now);this.frame=requestAnimationFrame(this.tick)}
 private render(now:number){
  if(this.disposed||!this.model)return
  const dt=Math.min(.05,Math.max(0,(now-this.last)/1000));this.last=now
  this.animator?.update(dt,0,0,0,0,0,now/1000)
  this.stage.rotation.y=this.turn
  this.renderer.render(this.scene,this.camera)
 }
 private onDown=(event:PointerEvent)=>{this.dragging=true;this.pointerX=event.clientX;this.renderer.domElement.setPointerCapture(event.pointerId)}
 private onMove=(event:PointerEvent)=>{if(this.dragging){this.turn+=(event.clientX-this.pointerX)*.012;this.pointerX=event.clientX}}
 private onUp=()=>{this.dragging=false}
 private release(object:THREE.Object3D){
  const geometries=new Set<THREE.BufferGeometry>(),materials=new Set<THREE.Material>()
  object.traverse(o=>{if(o instanceof THREE.Mesh){geometries.add(o.geometry);for(const m of Array.isArray(o.material)?o.material:[o.material])materials.add(m)}})
  for(const g of geometries)g.dispose();for(const m of materials)m.dispose()
 }
 dispose(){
  if(this.disposed)return
  this.setActive(false);this.disposed=true;this.observer.disconnect()
  const canvas=this.renderer.domElement
  canvas.removeEventListener('pointerdown',this.onDown);canvas.removeEventListener('pointermove',this.onMove)
  canvas.removeEventListener('pointerup',this.onUp);canvas.removeEventListener('pointercancel',this.onUp)
  this.release(this.scene);this.renderer.dispose();canvas.remove()
 }
}
