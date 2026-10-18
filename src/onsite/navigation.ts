// Original height-aware navigation for ONSITE. One node per walkable floor per x/z,
// never one height per cell. Rapier remains the sole owner of actor movement.
import {heronCourt,type Level} from './levels'
type Point={x:number;y:number;z:number}
type Node=Point&{id:number;cx:number;cz:number;edges:number[]}
export class LayeredNav {
 readonly nodes:Node[]=[];readonly cell=.375;private cells=new Map<string,Node[]>();private origin={x:0,z:0};
 constructor(level:Level=heronCourt){
 const {solids,bounds}=level,surfaces=new Set(solids.filter(s=>level.surfaceIds.includes(s.id)));
 // Bucket solids by 4 m column so larger levels do not test every box per cell.
 const B=4,buckets=new Map<string,typeof solids>(),key=(x:number,z:number)=>`${Math.floor(x/B)},${Math.floor(z/B)}`;
 for(const s of solids)for(let bx=Math.floor((s.x-s.w/2-.4)/B);bx<=Math.floor((s.x+s.w/2+.4)/B);bx++)for(let bz=Math.floor((s.z-s.d/2-.4)/B);bz<=Math.floor((s.z+s.d/2+.4)/B);bz++){const k=`${bx},${bz}`;buckets.set(k,[...(buckets.get(k)||[]),s])}
 this.origin={x:bounds.minX,z:bounds.minZ};const nx=Math.round((bounds.maxX-bounds.minX)/this.cell),nz=Math.round((bounds.maxZ-bounds.minZ)/this.cell);
 for(let cx=0;cx<nx;cx++)for(let cz=0;cz<nz;cz++){
 const x=bounds.minX+(cx+.5)*this.cell,z=bounds.minZ+(cz+.5)*this.cell,heights=new Set<number>(),near=buckets.get(key(x,z))||[];
 for(const s of near)if(surfaces.has(s)&&Math.abs(x-s.x)<=s.w/2&&Math.abs(z-s.z)<=s.d/2)heights.add(Math.round((s.y+s.h/2)*1000)/1000);
 for(const y of heights){
 // Clearance for a 0.38m radius, 1.86m tall walker. Horizontal expansion is slightly
 // smaller than the capsule so door cells remain connected; Rapier resolves exact contact.
 if(near.some(s=>s.y-s.h/2<y+1.86&&s.y+s.h/2>y+.36&&Math.abs(x-s.x)<s.w/2+.3&&Math.abs(z-s.z)<s.d/2+.3))continue;
 const n:Node={id:this.nodes.length,x,y,z,cx,cz,edges:[]};this.nodes.push(n);const k=`${cx},${cz}`;this.cells.set(k,[...(this.cells.get(k)||[]),n]);
 }}
 for(const n of this.nodes)for(const [dx,dz]of [[1,0],[-1,0],[0,1],[0,-1]])for(const q of this.cells.get(`${n.cx+dx},${n.cz+dz}`)||[])if(Math.abs(n.y-q.y)<=.36)n.edges.push(q.id);
 }
 nearest(x:number,z:number,y=0){
 // Ring search over the cell index; stops once no farther ring can beat the best score.
 const cx=Math.floor((x-this.origin.x)/this.cell),cz=Math.floor((z-this.origin.z)/this.cell);let best:Node|undefined,score=Infinity;
 for(let r=0;r<400;r++){if(best&&((r-1)*this.cell)**2>score)break;
 for(let i=-r;i<=r;i++)for(const [dx,dz]of r?[[i,-r],[i,r],[-r,i],[r,i]]:[[0,0]])for(const n of this.cells.get(`${cx+dx},${cz+dz}`)||[]){const d=(n.x-x)**2+(n.z-z)**2+16*(n.y-y)**2;if(d<score){score=d;best=n}}}
 return best!}
 walkable(x:number,z:number,y=0){const n=this.nearest(x,z,y);return Math.hypot(n.x-x,n.z-z)<.65&&Math.abs(n.y-y)<.4}
 heightAt(x:number,z:number,y=0){return this.nearest(x,z,y).y}
 clearLine(_sx:number,_sz:number,_tx:number,_tz:number){return false} // No unsafe 2D string-pulling across voids/floors.
 findPath(sx:number,sz:number,tx:number,tz:number,sy=0,ty=sy):Point[]|null{
 const start=this.nearest(sx,sz,sy),end=this.nearest(tx,tz,ty);const costs=new Map([[start.id,0]]),parents=new Map<number,number>(),closed=new Set<number>();
 const h=(n:Node)=>Math.hypot(n.x-end.x,n.z-end.z)+Math.abs(n.y-end.y),heap:[number,number][]=[[h(start),start.id]];
 const push=(e:[number,number])=>{heap.push(e);let i=heap.length-1;while(i){const p=(i-1)>>1;if(heap[p][0]<=e[0])break;heap[i]=heap[p];i=p}heap[i]=e};
 const pop=()=>{const top=heap[0],last=heap.pop()!;if(heap.length){let i=0;for(;;){const l=2*i+1,r=l+1;let m=i;const v=(k:number)=>k===i?last[0]:heap[k][0];if(l<heap.length&&heap[l][0]<v(m))m=l;if(r<heap.length&&heap[r][0]<v(m))m=r;if(m===i)break;heap[i]=heap[m];i=m}heap[i]=last}return top};
 while(heap.length){const [,id]=pop();if(closed.has(id))continue;closed.add(id);
 if(id===end.id){const path:Point[]=[];let k=id;while(k!==start.id){const n=this.nodes[k];path.push({x:n.x,y:n.y,z:n.z});k=parents.get(k)!}return path.reverse()}
 const n=this.nodes[id];for(const j of n.edges){if(closed.has(j))continue;const q=this.nodes[j],cost=costs.get(id)!+Math.hypot(n.x-q.x,n.z-q.z,n.y-q.y);if(cost<(costs.get(j)??Infinity)){costs.set(j,cost);parents.set(j,id);push([cost+h(q),j])}}
 }return null;
 }
}
