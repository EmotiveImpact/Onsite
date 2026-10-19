import * as THREE from 'three'
import {Physics,RAPIER} from '../wwb/engine/physics'
import {Player,type MoveIntent} from '../wwb/game/player'
import {Arsenal} from '../wwb/game/weapons'
import {Bot} from '../wwb/game/bots'
import {Effects} from '../wwb/game/fx'
import {Audio} from '../wwb/engine/audio'
import type {CombatWorld,Hit,DamageInfo,DamageResult,ColliderTag} from '../wwb/game/combat'
import {createMatch,tick,registerKill,registerDeath,recordShot} from '../wwb/game/rules'
import {CONFIG} from '../wwb/game/config'
import {LayeredNav} from './navigation'
import {heronCourt,inCapture,type Level} from './levels'
import {createCaptureMatch} from './CaptureRound'
export type Command=MoveIntent&{fire:boolean;firePressed:boolean;reload:boolean;yaw:number;pitch:number}
export class Encounter implements CombatWorld{
 readonly physics=new Physics();readonly player=new Player(this.physics);readonly nav:LayeredNav;readonly bots:Bot[]=[];
 readonly tags=new Map<number,ColliderTag>();private readonly fences=new Set<number>();readonly fx:Effects;readonly arsenal:Arsenal;
 readonly onslaught=true;time=0;steps=0;state:'ready'|'active'|'won'|'lost'='ready';capture=0;match:ReturnType<typeof createMatch>;hit=0;hurt=0;
 constructor(readonly audio:Audio,scene:THREE.Scene,camera:THREE.PerspectiveCamera,character:THREE.Object3D,readonly level:Level=heronCourt){
 this.nav=new LayeredNav(level);
 CONFIG.player.walkSpeed=4.6;CONFIG.player.sprintSpeed=6.8;CONFIG.player.maxArmor=0;this.player.maxArmor=0;
 CONFIG.bots.speed=3;CONFIG.bots.viewRange=32;CONFIG.bots.reaction=.8;CONFIG.bots.damage=4;CONFIG.bots.fireInterval=.22;
 for(const s of level.solids){const c=this.physics.addStaticBox(new THREE.Vector3(s.x,s.y,s.z),new THREE.Vector3(s.w,s.h,s.d));if(level.fenceIds.includes(s.id))this.fences.add(c.handle);this.tags.set(c.handle,{kind:'world',surface:s.mat==='steel'?'metal':'concrete'})}
 this.tags.set(this.player.collider.handle,{kind:'player'});
 this.fx=new Effects((x,z,y)=>this.groundAt(x,z,y),scene.fog as THREE.FogExp2);scene.add(this.fx.group);
 this.arsenal=new Arsenal(this,this.player,camera,{hit:()=>{this.hit=.18},fired:()=>{},message:()=>{}},()=>({}));
 this.match=createCaptureMatch(level.botNames,level.seconds);
 for(let i=0;i<level.botSpawns.length;i++){const bot=new Bot(i+1,level.botNames[i],'striker','#111111','#181818',this.physics,this.nav,this,{scene:character,clips:[]},{},'operator');bot.wave=false;this.bots.push(bot);scene.add(bot.parts.root);this.tags.set(bot.collider.handle,{kind:'bot',id:i+1})}
 this.arsenal.isHead=(id,point)=>this.bots[id-1]?.isHead(point)??false;
 this.reset();this.state='ready';
 }
 reset(){this.time=0;this.steps=0;this.capture=0;this.state='active';this.match=createCaptureMatch(this.level.botNames,this.level.seconds);const {spawn,botSpawns}=this.level;this.player.spawn(new THREE.Vector3(spawn.x,spawn.y,spawn.z),spawn.yaw??0);this.arsenal.reset();this.arsenal.slots.shotgun.owned=false;this.bots.forEach((b,i)=>{const p=botSpawns[i];b.spawn(new THREE.Vector3(p.x,p.y,p.z),Math.PI)});this.physics.step(1/60)}
 step(dt:number,c:Command){if(this.state!=='active')return;this.time+=dt;this.steps++;this.hit=Math.max(0,this.hit-dt);this.hurt=Math.max(0,this.hurt-dt);
 const p=this.player;p.yaw=c.yaw;p.pitch=THREE.MathUtils.clamp(c.pitch,-1.48,1.48);p.step(dt,c);
 this.arsenal.step(dt,c,p.eye(1,new THREE.Vector3()),p.sprinting);
 this.match=recordShot(this.match,this.arsenal.shotsThisStep,this.arsenal.hitsThisStep,this.arsenal.damageThisStep);this.match=tick(this.match,dt);
 const targets=[{id:0,pos:p.position,vel:p.velocity,alive:p.alive,isPlayer:true}];
 for(const b of this.bots)b.update(dt,{targets,playerEye:p.eye(1,new THREE.Vector3()),playerId:0,frozen:false,items:[],hotspots:this.level.botSpawns.map(s=>new THREE.Vector3(s.x,s.y,s.z))},this.bots);
 this.physics.step(dt);
 if(!p.alive||this.match.timeLeft<=0)this.state='lost';
 if(this.bots.every(b=>!b.alive)&&inCapture(this.level.capture,p.position))this.capture+=dt;else this.capture=0;
 if(this.capture>=2.5)this.state='won';
 }
 raycast(origin:THREE.Vector3,dir:THREE.Vector3,maxDist:number,excludeHandle?:number,worldOnly=false):Hit|null{
 const ray=new RAPIER.Ray(origin,dir);const h=this.physics.world.castRayAndGetNormal(ray,maxDist,true,RAPIER.QueryFilterFlags.EXCLUDE_SENSORS,undefined,undefined,undefined,c=>c.handle!==excludeHandle&&!this.fences.has(c.handle)&&(!worldOnly||this.tags.get(c.handle)?.kind==='world'));
 return h?{point:origin.clone().addScaledVector(dir,h.timeOfImpact),normal:new THREE.Vector3(h.normal.x,h.normal.y,h.normal.z),distance:h.timeOfImpact,tag:this.tags.get(h.collider.handle),colliderHandle:h.collider.handle}:null;
 }
 lineOfSight(a:THREE.Vector3,b:THREE.Vector3){const d=b.clone().sub(a),len=d.length();return !this.raycast(a,d.normalize(),len-.1,undefined,true)}
 groundAt(x:number,z:number,fromY:number){return this.raycast(new THREE.Vector3(x,fromY,z),new THREE.Vector3(0,-1,0),40,undefined,true)?.point.y??0}
 damage(id:number,info:DamageInfo):DamageResult{
 if(id!==0&&info.attacker!==0)return {dealt:0,killed:false,armor:false};
 if(id===0){const r=this.player.damage(info.amount);if(r.dealt)this.hurt=.4;const killed=this.player.health<=0;if(killed){this.player.alive=false;this.match=registerDeath(this.match,0)}return {dealt:r.dealt,killed,armor:false}}
 const r=this.bots[id-1]?.takeDamage(info)??{dealt:0,killed:false,armor:false};if(r.killed){this.bots[id-1].shatter(info.from,.3);this.match=registerKill(this.match,{killer:info.attacker,victim:id,headshot:info.headshot,weapon:info.source}).state;}return r;
 }
 isHuman(){return true} noise(pos:THREE.Vector3,source:number,radius:number){for(const b of this.bots)if(b.id!==source&&b.pos.distanceTo(pos)<radius)b.hear(pos,source)}
 damageProp(){} explode(){} fireRocket(){} fireProjectile(){} damageDrone(){return {dealt:0,killed:false,armor:false}} bossPhase(){} bossSlam(){} summonDrones(){} stomp(){}
 snapshot(){return {tick:this.steps,status:this.state,time:this.time,capture:this.capture,player:{position:this.player.position.clone(),yaw:this.player.yaw,pitch:this.player.pitch,health:this.player.health,grounded:this.player.grounded},weapon:{ammo:this.arsenal.slot.mag,reserve:this.arsenal.slot.reserve,reloadRemaining:this.arsenal.reloading,ads:this.arsenal.ads},bots:this.bots.map(b=>({id:b.id,position:b.pos.clone(),health:b.health,alive:b.alive,state:b.state,velocity:b.vel.clone()})),stats:this.match.stats}}
}
