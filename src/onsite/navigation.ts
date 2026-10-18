// Original height-aware navigation for ONSITE. One node per walkable floor per x/z,
// never one height per cell. Rapier remains the sole owner of actor movement.
import {solids} from './level'
type Point={x:number;y:number;z:number}
type Node=Point&{id:number;cx:number;cz:number;edges:number[]}
export class LayeredNav {
 readonly nodes:Node[]=[];readonly cell=.375;private cells=new Map<string,Node[]>();
 constructor(){
 const surfaces=solids.filter(s=>['ground','gallery','room-floor','stair','half-landing','top-landing'].includes(s.id));
 for(let cx=0;cx<96;cx++)for(let cz=0;cz<80;cz++){
 const x=-18+(cx+.5)*this.cell,z=-15+(cz+.5)*this.cell,heights=new Set<number>();
 for(const s of surfaces)if(Math.abs(x-s.x)<=s.w/2&&Math.abs(z-s.z)<=s.d/2)heights.add(Math.round((s.y+s.h/2)*1000)/1000);
 for(const y of heights){
 // Clearance for a 0.38m radius, 1.86m tall walker. Horizontal expansion is slightly
 // smaller than the capsule so door cells remain connected; Rapier resolves exact contact.
 if(solids.some(s=>s.y-s.h/2<y+1.86&&s.y+s.h/2>y+.36&&Math.abs(x-s.x)<s.w/2+.3&&Math.abs(z-s.z)<s.d/2+.3))continue;
 const n:Node={id:this.nodes.length,x,y,z,cx,cz,edges:[]};this.nodes.push(n);const k=`${cx},${cz}`;this.cells.set(k,[...(this.cells.get(k)||[]),n]);
 }}
 for(const n of this.nodes)for(const [dx,dz]of [[1,0],[-1,0],[0,1],[0,-1]])for(const q of this.cells.get(`${n.cx+dx},${n.cz+dz}`)||[])if(Math.abs(n.y-q.y)<=.36)n.edges.push(q.id);
 }
 nearest(x:number,z:number,y=0){let best:Node|undefined,score=Infinity;for(const n of this.nodes){const d=(n.x-x)**2+(n.z-z)**2+16*(n.y-y)**2;if(d<score){score=d;best=n}}return best!}
 walkable(x:number,z:number,y=0){const n=this.nearest(x,z,y);return Math.hypot(n.x-x,n.z-z)<.65&&Math.abs(n.y-y)<.4}
 heightAt(x:number,z:number,y=0){return this.nearest(x,z,y).y}
 clearLine(_sx:number,_sz:number,_tx:number,_tz:number){return false} // No unsafe 2D string-pulling across voids/floors.
 findPath(sx:number,sz:number,tx:number,tz:number,sy=0,ty=sy):Point[]|null{
 const start=this.nearest(sx,sz,sy),end=this.nearest(tx,tz,ty);const costs=new Map([[start.id,0]]),parents=new Map<number,number>(),open=new Set([start.id]);
 while(open.size){let id=-1,best=Infinity;for(const i of open){const n=this.nodes[i],h=Math.hypot(n.x-end.x,n.z-end.z)+Math.abs(n.y-end.y);const f=costs.get(i)!+h;if(f<best){best=f;id=i}}
 if(id===end.id){const path:Point[]=[];while(id!==start.id){const n=this.nodes[id];path.push({x:n.x,y:n.y,z:n.z});id=parents.get(id)!}return path.reverse()}
 open.delete(id);const n=this.nodes[id];for(const j of n.edges){const q=this.nodes[j],cost=costs.get(id)!+Math.hypot(n.x-q.x,n.z-q.z,n.y-q.y);if(cost<(costs.get(j)??Infinity)){costs.set(j,cost);parents.set(j,id);open.add(j)}}
 }return null;
 }
}
