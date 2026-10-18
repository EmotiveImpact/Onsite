import { accelerate, reloadMagazine, applyDamage, createStats, recordShot } from '../adapted/gameplay.js';
import { findRoute } from './navigation.js';
import { CombatQueries } from './combat.js';
import RAPIER from '@dimforge/rapier3d-compat';
import { solids, SPAWN, BOT_SPAWN, OBJECTIVE, PATROL } from './level.js';
export const DT = 1 / 60;
const copy = p => ({ x: p.x, y: p.y, z: p.z });
const clamp = (v, a, b) => Math.max(a, Math.min(b, Number.isFinite(v) ? v : 0));
let initialized;
export async function initPhysics() { initialized ??= RAPIER.init(); await initialized; }
export function direction(yaw, pitch = 0) {
  return { x: -Math.sin(yaw) * Math.cos(pitch), y: Math.sin(pitch), z: -Math.cos(yaw) * Math.cos(pitch) };
}
export class Simulation {
  static async create() { await initPhysics(); return new Simulation(); }
  constructor() {
    this.world = new RAPIER.World({ x: 0, y: -22, z: 0 });
    this.world.timestep = DT;this.combat=new CombatQueries(this.world);
    for (const s of solids) this.world.createCollider(RAPIER.ColliderDesc.cuboid(s.size.x/2,s.size.y/2,s.size.z/2).setTranslation(s.position.x,s.position.y,s.position.z));
    this.player = this.createActor(SPAWN);
    this.bot = this.createActor(BOT_SPAWN);
    this.controller = this.createController();
    this.botController = this.createController();
    this.world.step();
    this.reset();
  }
  createController() {
    const c=this.world.createCharacterController(.015);
    c.enableAutostep(.25,.15,true); c.enableSnapToGround(.25); c.setMaxSlopeClimbAngle(Math.PI/4); c.setMinSlopeSlideAngle(Math.PI/3);
    return c;
  }
  createActor(p) {
    const body=this.world.createRigidBody(RAPIER.RigidBodyDesc.kinematicPositionBased().setTranslation(p.x,p.y,p.z));
    const collider=this.world.createCollider(RAPIER.ColliderDesc.capsule(.55,.3),body);
    return {body,collider};
  }
  reset() {
    for(const [a,p] of [[this.player,SPAWN],[this.bot,BOT_SPAWN]]) {
      a.body.setTranslation(p,true); a.body.setNextKinematicTranslation(p); a.collider.setEnabled(true);
    }
    this.tickNumber=0; this.lastSequence=-1; this.health=100; this.botHealth=100;
    this.ammo=24; this.reserve=96; this.reloadRemaining=0; this.cooldown=0;
    this.velocity={x:0,z:0};this.coyote=0;this.jumpBuffer=0;this.stats=createStats();this.vertical=0; this.botVertical=0; this.grounded=false; this.yaw=0; this.pitch=0;
    this.botYaw=Math.PI; this.botMode='patrol'; this.waypoint=0; this.seenFor=0; this.memory=0; this.lastSeen=null;
    this.route=[];this.routeGoal=null;this.botCooldown=0; this.capture=0; this.status='active'; this.events=[]; this.jumpHeld=false;
    this.world.step();
  }
  eye() { const p=this.player.body.translation(); return {x:p.x,y:p.y+.7,z:p.z}; }
  cast(origin,dir,max,exclude) {
    return this.combat.raycast(origin,dir,max,exclude);
  }
  tick(raw={}) {
    this.events=[];
    if(this.status!=='active')return this.snapshot();
    // Commands carry intent only; health, positions, ammo and hit claims never come from a client.
    const sequence=Number.isSafeInteger(raw.sequence)?raw.sequence:this.lastSequence+1;
    if(sequence<=this.lastSequence)return this.snapshot();
    this.lastSequence=sequence; this.tickNumber++;
    const command={moveX:clamp(raw.moveX,-1,1),moveZ:clamp(raw.moveZ,-1,1),yaw:clamp(raw.yaw,-1e5,1e5),pitch:clamp(raw.pitch,-1.45,1.45),sprint:!!raw.sprint,jump:!!raw.jump,fire:!!raw.fire,reload:!!raw.reload};
    this.yaw=command.yaw;this.pitch=command.pitch;
    this.cooldown=Math.max(0,this.cooldown-DT);
    if(this.reloadRemaining>0) {
      this.reloadRemaining=Math.max(0,this.reloadRemaining-DT);
      if(this.reloadRemaining===0){ const r=reloadMagazine(this.ammo,this.reserve);this.ammo=r.mag;this.reserve=r.reserve;this.events.push({type:'reloaded'}); }
    }
    if(command.reload && this.reloadRemaining===0 && this.ammo<24 && this.reserve>0) {
      this.reloadRemaining=1.6; this.events.push({type:'reload'});
    }
    accelerate(this.velocity,command,this.yaw,this.grounded,DT);
    const dx=this.velocity.x*DT,dz=this.velocity.z*DT;
    this.coyote=this.grounded?.1:Math.max(0,this.coyote-DT);
    this.jumpBuffer=command.jump&&!this.jumpHeld?.12:Math.max(0,this.jumpBuffer-DT);
    if(this.jumpBuffer>0&&this.coyote>0){this.vertical=7;this.jumpBuffer=0;this.coyote=0;this.grounded=false;}
    this.jumpHeld=command.jump;this.vertical=Math.max(-30,this.vertical-22*DT);
    this.moveActor(this.player,this.controller,{x:dx,y:this.vertical*DT,z:dz});
    this.grounded=this.controller.computedGrounded();if(this.grounded&&this.vertical<0)this.vertical=0;
    if(this.botHealth>0) this.updateBot();
    this.world.step();
    if(command.fire&&this.cooldown===0&&this.reloadRemaining===0&&this.ammo>0) this.fire();
    if(this.health<=0){this.health=0;this.status='lost';this.events.push({type:'lost'});}
    const p=this.player.body.translation();
    if(this.tickNumber*DT>=180){this.health=0;this.status='lost';this.events.push({type:'timeout'});}
    if(p.y < -10){this.health=0;this.status='lost';}
    if(this.botHealth<=0 && Math.hypot(p.x-OBJECTIVE.x,p.z-OBJECTIVE.z)<OBJECTIVE.radius && p.y<2) this.capture=Math.min(3,this.capture+DT);
    else this.capture=0;
    if(this.capture>=3){this.status='won';this.events.push({type:'won'});}
    return this.snapshot();
  }
  moveActor(actor,controller,delta) {
    controller.computeColliderMovement(actor.collider,delta);
    const p=actor.body.translation(),m=controller.computedMovement();
    actor.body.setNextKinematicTranslation({x:p.x+m.x,y:p.y+m.y,z:p.z+m.z});
  }
  fire() {
    this.ammo--;this.cooldown=.16;this.stats=recordShot(this.stats,1,0);
    const origin=this.eye(),dir=direction(this.yaw,this.pitch),hit=this.cast(origin,dir,80,this.player.collider);
    const distance=hit?.timeOfImpact??80;
    const end={x:origin.x+dir.x*distance,y:origin.y+dir.y*distance,z:origin.z+dir.z*distance};
    this.events.push({type:'shot',origin,end});
    if(hit?.collider.handle===this.bot.collider.handle && this.botHealth>0) {
      const headshot=end.y>this.bot.body.translation().y+.45;
      const before=this.botHealth;this.botHealth=applyDamage(this.botHealth,0,headshot?60:34).health;this.stats=recordShot(this.stats,0,1,before-this.botHealth);
      this.events.push({type:'hit',headshot,health:this.botHealth});
      this.lastSeen=copy(this.player.body.translation());this.memory=30;
      if(this.botHealth===0){this.bot.collider.setEnabled(false);this.botMode='down';this.events.push({type:'bot-down'});}
    }
  }
  updateBot() {
    const p=this.bot.body.translation(),target=this.eye();
    const origin={x:p.x,y:p.y+.6,z:p.z};
    const distance=Math.hypot(target.x-origin.x,target.y-origin.y,target.z-origin.z);
    const dir={x:(target.x-origin.x)/distance,y:(target.y-origin.y)/distance,z:(target.z-origin.z)/distance};
    const forward=direction(this.botYaw);
    const inCone=dir.x*forward.x+dir.z*forward.z>Math.cos(Math.PI*.38);
    const hit=this.cast(origin,dir,Math.min(distance+.3,27),this.bot.collider);
    const visible=distance<19 && (inCone||this.memory>0) && hit?.collider.handle===this.player.collider.handle;
    this.botCooldown=Math.max(0,this.botCooldown-DT);
    if(visible){this.routeGoal=null;
      this.seenFor+=DT;this.memory=30;this.lastSeen=copy(target);this.botMode='engage';
      this.botYaw=Math.atan2(-dir.x,-dir.z);
      if(this.seenFor>1.2&&this.botCooldown===0){
        // The simulation verifies line of sight on every damage event.
        this.health=applyDamage(this.health,0,12).health;this.botCooldown=.9;this.events.push({type:'bot-shot',origin,end:copy(target)});
      }
    }else{this.seenFor=0;this.memory=Math.max(0,this.memory-DT);this.botMode=this.memory>0?'search':'patrol';}
    let dx=0,dz=0;
    if(!visible){
      let goal=PATROL[this.waypoint];
      if(this.memory>0&&this.lastSeen){
        if(!this.routeGoal||Math.hypot(this.routeGoal.x-this.lastSeen.x,this.routeGoal.y-this.lastSeen.y,this.routeGoal.z-this.lastSeen.z)>1){
          const dest={...this.lastSeen,y:this.lastSeen.y-.7};this.route=findRoute(p,dest);this.routeGoal=copy(this.lastSeen);
        }
        while(this.route.length&&Math.hypot(this.route[0].x-p.x,this.route[0].z-p.z)<.3&&Math.abs(this.route[0].y-p.y)<.4)this.route.shift();
        goal=this.route[0]??this.lastSeen;
      }
      const len=Math.hypot(goal.x-p.x,goal.z-p.z);
      if(len<.4){if(this.memory<=0)this.waypoint=(this.waypoint+1)%PATROL.length;}
      else{dx=(goal.x-p.x)/len*1.65*DT;dz=(goal.z-p.z)/len*1.65*DT;this.botYaw=Math.atan2(-dx,-dz);}
    }
    this.botVertical-=22*DT;
    this.moveActor(this.bot,this.botController,{x:dx,y:this.botVertical*DT,z:dz});
    if(this.botController.computedGrounded()&&this.botVertical<0)this.botVertical=0;
  }
  snapshot(){return {tick:this.tickNumber,lastSequence:this.lastSequence,status:this.status,stats:{...this.stats},player:{position:copy(this.player.body.translation()),yaw:this.yaw,pitch:this.pitch,health:this.health,grounded:this.grounded},weapon:{ammo:this.ammo,reserve:this.reserve,reloadRemaining:this.reloadRemaining},bot:{position:copy(this.bot.body.translation()),yaw:this.botYaw,health:this.botHealth,mode:this.botMode},capture:this.capture,events:this.events.map(e=>structuredClone(e))};}
  dispose(){this.world.free();}
}
