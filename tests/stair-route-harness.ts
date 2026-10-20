// Test-only physical traversal, with actual render assets and the existing WWB capsule.
// One initial spawn; every subsequent position comes from Player.step and Rapier.
// Scripted steering is route evidence, not mouse/keyboard or combat evidence.
import '../src/style.css'
import * as THREE from 'three'
import {initPhysics} from '../src/wwb/engine/physics'
import {Audio} from '../src/wwb/engine/audio'
import {Encounter} from '../src/onsite/Encounter'
import {View} from '../src/onsite/View'
import {heronReach} from '../src/onsite/levels'
import {fromMap, toMap} from '../src/onsite/heronReach'
import spec from '../docs/maps/heron-reach-32/blueprints/build-spec.json'

type Point = {x:number;y:number;z:number}
type Target = Point & {name:string;label:string;expectedY:number;tolerance:number;look:Point}
type Checkpoint = {name:string;label:string;tick:number;position:Point;mapPosition:Point;expectedY:number;tolerance:number;grounded:boolean;target:Point;pathNodes:number}
const $ = (id:string) => document.getElementById(id)!
const xyz = (p:Point):Point => ({x:p.x,y:p.y,z:p.z})
const query = new URLSearchParams(location.search), coreId = query.get('core') || 'S1'
const core = spec.cores.find(c => c.id === coreId)
const requestedBase = Number(query.get('base') ?? (coreId === 'S7' ? -3 : 0))
let ready = false, done = false, error:string|null = null, ticks = 0, stage = '', phase = 'loading', currentPath:Point[] = [], node = 0
let game:Encounter|undefined, view:View|undefined, initial:Point|undefined
const evidence:Checkpoint[] = [], samples:number[] = []
let planned:Target[] = [], stairArtLoaded = false, retiredTriangles = 0, maximumPhysicsStep = 0
const fail = (e:unknown) => {
  error = e instanceof Error ? e.message : String(e); phase = 'failed'
  document.body.dataset.error = error
  document.querySelector('.route-caption')?.setAttribute('data-error','true')
  $('route-label').textContent = 'Route verification failed'
  $('route-coordinate').textContent = error
  console.error(e)
}
Object.defineProperty(window,'__stairRoute',{value:Object.freeze({get state(){
  const p = game?.player.position
  return {ready,done,error,core:coreId,base:requestedBase,mirror:core?.mirrorZ,stage,phase,ticks,
    position:p?xyz(p):null,mapPosition:p?toMap(p.x,p.y,p.z):null,grounded:game?.player.grounded,
    initial:initial?xyz(initial):null,spawnCount:game?1:0,maximumPhysicsStep,botsDisabled:game?game.bots.every(bot=>!bot.alive):true,
    checkpoints:evidence.map(e=>({...e,position:xyz(e.position),mapPosition:xyz(e.mapPosition),target:xyz(e.target)})),
    plan:planned.map(t=>({name:t.name,label:t.label,target:xyz(t),expectedY:t.expectedY,tolerance:t.tolerance})),
    path:{index:node,length:currentPath.length,next:currentPath[node]?xyz(currentPath[node]):null},
    art:{loaded:stairArtLoaded,retiredTriangles},
    metrics:view?{softwareRenderer:view.software,pixelRatio:view.renderer.getPixelRatio(),drawCalls:view.renderer.info.render.calls,triangles:view.renderer.info.render.triangles,
      frames:samples.length,meanFrameMs:samples.reduce((a,b)=>a+b,0)/Math.max(1,samples.length),note:'Software/fixture timing, not a real-GPU benchmark'}:null}
}})})

async function run(){
  if(!core)throw Error(`Unknown public core: ${coreId}`)
  if(!Number.isFinite(requestedBase)||!core.levels.includes(requestedBase)||!core.levels.includes(requestedBase+3))throw Error(`${coreId} does not serve the requested ${requestedBase} → ${requestedBase+3} storey`)
  const s=spec.stairs['ST-P'],[cx,cz]=core.rect,base=requestedBase
  const at=(x:number,y:number,z:number):Point=>fromMap(cx+x,base+y,cz+(core.mirrorZ?6-z:z))
  const x1=s.firstFlightX+s.flightWidth/2,x2=s.secondFlightX+s.flightWidth/2,mid=s.flightZ+s.flightRun/2,halfZ=s.halfLanding[1]+s.halfLanding[3]/2
  const target=(name:string,label:string,x:number,y:number,z:number,look:Point,tolerance=.18):Target=>({...at(x,y,z),name,label,expectedY:base+y,tolerance,look})
  planned=[
    target('entry','Entry / first flight ahead',3,0,5.05,at(x1,.75,mid)),
    target('first-flight','Ascending / first flight',x1,.75,mid,at(x1,1.5,halfZ),.35),
    target('half-landing','Half landing / dogleg turn',x2,1.5,halfZ,at(x2,2.25,mid)),
    target('return-flight','Ascending / return flight',x2,2.25,mid,at(x2,3,4.9),.35),
    target('upper-landing','Upper landing / +3 m reached',3,3,5.05,at(x2,2.25,mid)),
    target('descending-half','Descending / half landing',x1,1.5,halfZ,at(x1,.75,mid)),
    target('returned-entry','Returned / original floor',3,0,6.75,at(3,0,5.05)),
  ]
  initial=at(3,.04,6.75)
  $('route-title').textContent=`ONSITE / ${coreId} · ${base.toFixed(1)} → ${(base+3).toFixed(1)} → ${base.toFixed(1)} m`
  view=new View($('game') as HTMLCanvasElement,heronReach)
  await initPhysics();const model=await view.ready
  const art=view.scene.getObjectByName('ONSITE / constructed public stairs')
  stairArtLoaded=!!art;retiredTriangles=Number(art?.userData.retired?.trianglesRemoved??0)
  if(!stairArtLoaded||retiredTriangles<=0)throw Error('Constructed public stair asset or its legacy retirement was not loaded')
  const audio=new Audio();audio.setVolumes(0,0,true);audio.setPaused(true)
  // The fixture changes only the constructor spawn. Solids, floors and nav are the actual map.
  game=new Encounter(audio,view.scene,view.camera,model,{...heronReach,spawn:{...initial,yaw:core.mirrorZ?Math.PI:0}})
  const g=game,v=view;v.installWeapon(g);g.bots.forEach(bot=>bot.hide())
  // A .375 m nav cell does not coincide exactly with a .28 m tread. Assert the
  // selected mid-flight node's actual floor, rather than a fictitious smooth ramp.
  for(const t of planned)if(t.tolerance>.2)t.expectedY=g.nav.nearest(t.x,t.z,t.y).y
  if(v.software)g.fx.group.traverse(o=>{if('isPointLight' in o)o.visible=false})
  $('route-context').textContent=`PHYSICAL WALK FIXTURE · BOTS DISABLED · NO TELEPORTS AFTER SPAWN · ${v.software?'SOFTWARE RENDERER':'HARDWARE RENDERER — NOT BENCHMARKED'}`
  let targetIndex=0,hold=0,settle=12,stageNodes=0,stuckTicks=0,lastNode=0,lastPosition=g.player.position.clone(),last=performance.now(),accumulator=0,holdStarted=0
  const dt=1/60
  function beginPath(){
    const p=g.player.position,t=planned[targetIndex]
    const path=g.nav.findPath(p.x,p.z,t.x,t.z,p.y,t.y)
    if(!path)throw Error(`No layered route to ${t.name}`)
    // Do not silently pass via a different core or an exterior route around the stair.
    for(const point of path){const m=toMap(point.x,point.y,point.z),lx=m.x-cx,lz=core!.mirrorZ?6-(m.z-cz):m.z-cz
      if(lx<-.2||lx>6.2||lz<-.2||lz>7.3)throw Error(`Path to ${t.name} escaped ${coreId}: ${JSON.stringify(m)}`)
    }
    currentPath=path;stageNodes=path.length;node=0;lastNode=0;stuckTicks=0;lastPosition.copy(p);phase='walking'
    $('route-label').textContent=t.label
  }
  function stepPlayer(speed:number){
    g.time+=dt;g.steps++;ticks++
    const previous=xyz(g.player.position)
    g.player.step(dt,{x:0,y:speed,jump:false,sprint:false,ads:false})
    g.arsenal.step(dt,{fire:false,firePressed:false,ads:false,reload:false},g.player.eye(1,new THREE.Vector3()),false)
    g.physics.step(dt)
    const movement=Math.hypot(g.player.position.x-previous.x,g.player.position.y-previous.y,g.player.position.z-previous.z)
    maximumPhysicsStep=Math.max(maximumPhysicsStep,movement)
    if(movement>.6)throw Error(`Discontinuous capsule movement: ${movement.toFixed(3)} m in one physics step`)
    if(g.player.position.y<base-.4||g.player.position.y>base+3.45)throw Error(`Player left the intended storey: y=${g.player.position.y.toFixed(3)}`)
    if(ticks>12000)throw Error(`Physical route exceeded 12000 simulation ticks at ${planned[targetIndex]?.name}`)
  }
  function checkpoint(){
    const p=g.player.position,t=planned[targetIndex]
    if(Math.abs(p.y-t.expectedY)>t.tolerance)throw Error(`${t.name} expected feet y=${t.expectedY}±${t.tolerance}; got ${p.y}`)
    if(!g.player.grounded)throw Error(`${t.name} did not settle onto the actual floor`)
    const dx=t.look.x-p.x,dz=t.look.z-p.z
    g.player.yaw=Math.atan2(-dx,-dz);g.player.pitch=THREE.MathUtils.clamp(Math.atan2(t.look.y-p.y,Math.hypot(dx,dz))*.5,-.3,.3)
    stage=t.name;phase='checkpoint';hold=60;holdStarted=performance.now()
    evidence.push({name:t.name,label:t.label,tick:ticks,position:xyz(p),mapPosition:toMap(p.x,p.y,p.z),expectedY:t.expectedY,tolerance:t.tolerance,grounded:g.player.grounded,target:xyz(t),pathNodes:stageNodes})
    $('route-label').textContent=t.label
  }
  ready=true
  function frame(now:number){
    if(error)return
    try{
      const raw=Math.max(0,(now-last)/1000);last=now;accumulator+=Math.min(raw,.1)
      if(phase==='walking'){samples.push(raw*1000);if(samples.length>360)samples.shift()}
      while(accumulator>=dt&&!done){
        accumulator-=dt
        if(settle>0){stepPlayer(0);settle--;if(!settle){if(phase==='loading')beginPath();else checkpoint()}continue}
        if(hold>0){stepPlayer(0);hold--;continue}
        if(phase==='checkpoint'){
          // 60 physics ticks and at least 750 ms let the external reader capture this view.
          if(now-holdStarted<750){stepPlayer(0);continue}
          targetIndex++;if(targetIndex===planned.length){done=true;phase='complete';$('route-label').textContent='Route complete / ascent and descent';break}
          beginPath()
        }
        const p=g.player.position,w=currentPath[node]
        if(!w){settle=12;phase='settling';stepPlayer(0);continue}
        const dx=w.x-p.x,dz=w.z-p.z
        if(Math.hypot(dx,dz)<.2&&Math.abs(w.y-p.y)<.45){node++;stepPlayer(0);continue}
        g.player.yaw=Math.atan2(-dx,-dz);g.player.pitch=w.y>p.y+.1?.12:w.y<p.y-.1?-.15:0
        stepPlayer(.5)
        if(node!==lastNode||p.distanceTo(lastPosition)>.03){stuckTicks=0;lastPosition.copy(p);lastNode=node}else stuckTicks++
        if(stuckTicks>240)throw Error(`Stuck at ${planned[targetIndex].name}, node ${node}/${currentPath.length}: ${JSON.stringify(toMap(p.x,p.y,p.z))}`)
      }
      const p=g.player.position
      $('route-coordinate').textContent=`FEET ${p.y.toFixed(2)} m · WORLD ${p.x.toFixed(2)}, ${p.z.toFixed(2)} · ${phase.toUpperCase()} · ${ticks} TICKS`
      v.render(g,1,Math.min(raw,.033),{x:0,y:0})
      requestAnimationFrame(frame)
    }catch(e){fail(e)}
  }
  requestAnimationFrame(frame)
}
run().catch(fail)
