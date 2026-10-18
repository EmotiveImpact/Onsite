/** Selective adaptations from WWB 4cf34e8 (MIT, Jeevesh Singale, 2026).
 * Sources: player.ts, weapons.ts, rules.ts. See public/licenses/WWB-MIT.txt.
 * ONSITE changes: plain numeric state, one rifle, no armour, no slides/network/cloud.
 */
export function accelerate(velocity, intent, yaw, grounded, dt) {
  const len=Math.max(1,Math.hypot(intent.moveX,intent.moveZ));
  const moving=Math.abs(intent.moveX)+Math.abs(intent.moveZ)>.01;
  const sprinting=intent.sprint && intent.moveZ>.3 && grounded;
  const speed=sprinting?6.4:4;
  const wx=(intent.moveX*Math.cos(yaw)-intent.moveZ*Math.sin(yaw))/len;
  const wz=(-intent.moveX*Math.sin(yaw)-intent.moveZ*Math.cos(yaw))/len;
  const dx=wx*speed-velocity.x,dz=wz*speed-velocity.z,dl=Math.hypot(dx,dz);
  const accel=grounded?32:10,friction=grounded?(moving?1:1.6):.05;
  const maxDv=accel*dt*(moving?1:friction);
  if(dl>0&&(grounded||moving)) {const k=Math.min(1,maxDv/dl);velocity.x+=dx*k;velocity.z+=dz*k;}
  return sprinting;
}
export function reloadMagazine(mag,reserve,capacity=24){
  const n=Math.min(capacity-mag,reserve);
  return {mag:mag+n,reserve:reserve-n};
}
export function applyDamage(health,armor,amount,absorb=.6){
  const soaked=Math.min(armor,amount*absorb);
  return {health:Math.max(0,health-(amount-soaked)),armor:armor-soaked};
}
export function createStats(){return {shots:0,hits:0,damageDealt:0};}
export function recordShot(stats,shots,hits,damage=0){return {...stats,shots:stats.shots+shots,hits:stats.hits+hits,damageDealt:stats.damageDealt+damage};}
export function accuracy(stats){return stats.shots>0?stats.hits/stats.shots:0;}
export function formatClock(seconds){const t=Math.max(0,Math.ceil(seconds));return `${Math.floor(t/60)}:${String(t%60).padStart(2,'0')}`;}
export function spring(s,target,k,d,dt){s.v+=(target-s.x)*k*dt;s.v*=Math.exp(-d*dt);s.x+=s.v*dt;return s.x;}
