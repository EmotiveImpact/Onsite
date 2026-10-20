import * as THREE from 'three'
import type {Level} from './levels'

/** HUD projection only; the encounter retains all capture and floor-selection rules. */
export class ObjectiveMarker {
 private readonly el=document.createElement('div');private readonly point=new THREE.Vector3();
 private readonly label=document.createElement('strong');private readonly distance=document.createElement('span');
 constructor(private readonly level:Level){
  this.el.id='objective-marker';this.el.hidden=true;this.el.setAttribute('aria-hidden','true');
  const diamond=document.createElement('i');this.el.append(diamond,this.label,this.distance);document.getElementById('hud')!.append(this.el);
 }
 update(camera:THREE.Camera,player:THREE.Vector3,remaining:number,state:string){
  const c=this.level.capture;
  this.point.set(c.x,1.7,c.z).project(camera);
  const visible=this.level.id==='heron-reach'&&state==='active'&&this.point.z>-1&&this.point.z<1&&Math.abs(this.point.x)<.85&&Math.abs(this.point.y)<.72;
  this.el.hidden=!visible;if(!visible)return;
  this.el.style.left=`${(this.point.x*.5+.5)*100}%`;this.el.style.top=`${(-this.point.y*.5+.5)*100}%`;
  this.label.textContent=remaining?c.label.toUpperCase():'HOLD THE COURT';
  const metres=Math.round(Math.hypot(player.x-c.x,player.y,player.z-c.z));
  this.distance.textContent=`${metres} m${Math.abs(player.y)>2?' · GROUND FLOOR':''}`;
 }
}
