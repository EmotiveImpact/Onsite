// Original ONSITE render-only ground plan. Physics/navigation never consume this data.
import type {Solid} from './level'
import foliage from '../../assets/blender/heron-reach/foliage-manifest.json'

type Rect=readonly number[];
export type GroundPlacement={asset:string;x:number;y:number;z:number;ry:number;scale?:number;sx?:number;source?:string};
export type GroundPatch={id:string;kind:'soil'|'moss'|'pit'|'leaves';source:string;x:number;z:number;y:number;outline:[number,number][];seed:number};
export type GroundLayout={site:Rect;cores:readonly {rect:Rect}[];openings:readonly {kind:string;x:number;z:number;y:number;axis:string;normal:number;width:number}[];
 trees:readonly {id:string;x:number;z:number}[];planting:readonly {id:string;rect:Rect}[];cover:readonly {id:string;rect:Rect;height:number;y:number;kind:string}[];
 cage:{rect:Rect;gate:number};objectives:readonly {x:number;z:number;radius:number}[];spawns:readonly {rect:Rect;positions:readonly {x:number;z:number}[]}[]};
export type GroundInput={solids:readonly Solid[];surfaceIds:readonly string[];layout:GroundLayout;grassCells:{cell:number;cells:readonly (readonly number[])[]};existingPlacements?:readonly GroundPlacement[]};
export type GroundPlan={version:1;patches:GroundPatch[];plants:GroundPlacement[];perimeterTrees:GroundPlacement[];stats:{patches:number;plantTriangles:number;groundTriangleBudget:number;treeTriangles:number;rejected:Record<string,number>}};
const OX=72,OZ=60,EPS=1e-5;
const inRect=(x:number,z:number,r:Rect,pad=0)=>x>=r[0]-pad&&x<=r[0]+r[2]+pad&&z>=r[1]-pad&&z<=r[1]+r[3]+pad;
const noise=(s:number)=>{s=Math.imul(s^(s>>>16),0x45d9f3b);s=Math.imul(s^(s>>>16),0x45d9f3b);return((s^(s>>>16))>>>0)/4294967296};
const hash=(s:string)=>{let h=2166136261;for(const c of s)h=Math.imul(h^c.charCodeAt(0),16777619);return h>>>0};
const assets=new Map(foliage.assets.map(a=>[a.name,a]));

/** Conservative circle enclosing the rotated/scaled model footprint; Blender Z maps to runtime Y. */
export function plantBounds(p:GroundPlacement){
 const a=assets.get(p.asset);if(!a)throw new Error(`Unknown ground plant ${p.asset}`);
 const s=p.scale??1,mn=a.bounds_min,mx=a.bounds_max;
 const radius=Math.hypot(Math.max(Math.abs(mn[0]),Math.abs(mx[0])),Math.max(Math.abs(mn[1]),Math.abs(mx[1])))*s*Math.max(1,Math.abs(p.sx??1));
 return {radius,bottom:p.y+mn[2]*s,top:p.y+mx[2]*s,triangles:a.triangles};
}

/** G only: no stairs, ramps, adjacent storeys, or support inferred from a nearby origin. */
export class GroundAcceptance {
 readonly rejected:Record<string,number>={};private readonly floor:Solid[];private readonly blockers:Solid[];private readonly grass:Set<string>;
 constructor(readonly input:GroundInput){
  this.floor=input.solids.filter(s=>input.surfaceIds.includes(s.id)&&s.id!=='stair'&&Math.abs(s.y+s.h/2)<EPS);
  this.blockers=input.solids.filter(s=>!input.surfaceIds.includes(s.id)&&s.y-s.h/2<.7&&s.y+s.h/2>.03);
  this.grass=new Set(input.grassCells.cells.map(([x,z])=>`${x},${z}`));
 }
 grassAt(x:number,z:number){const c=this.input.grassCells.cell;return this.grass.has(`${Math.floor(x/c)*c},${Math.floor(z/c)*c}`)}
 finishY(x:number,z:number){return this.grassAt(x,z)?.01:0}
 supported(x:number,z:number){return this.floor.some(s=>Math.abs(x-OX-s.x)<=s.w/2+EPS&&Math.abs(z-OZ-s.z)<=s.d/2+EPS)}
 routeClear(x:number,z:number,r=0){
  const L=this.input.layout;
  if(L.cores.some(c=>inRect(x,z,c.rect,.8+r)))return false;
  if(L.objectives.some(o=>Math.hypot(x-o.x,z-o.z)<o.radius+1.2+r))return false;
  if(L.spawns.some(s=>inRect(x,z,s.rect,r)))return false;
  for(const d of L.openings)if(d.y===0&&d.kind.includes('door'))for(const sign of [-1,1]){
   const dx=d.axis==='x'?0:d.normal*sign,dz=d.axis==='x'?d.normal*sign:0;
   if(Math.hypot(x-d.x-dx,z-d.z-dz)<d.width/2+1.1+r)return false;
  }
  // Protect the garden's actual 3 m cross paths and central 8 m square.
  if(inRect(x,z,[60,12,24,24],r)&&(inRect(x,z,[70.5,12,3,24],r)||inRect(x,z,[60,22.5,24,3],r)||inRect(x,z,[68,20,8,8],r)))return false;
  const [cx,cz,cw,cd]=L.cage.rect,g=L.cage.gate;
  if(inRect(x,z,L.cage.rect,r))return false;
  for(const q of [[cx+cw/2-g/2,cz-3,g,3],[cx+cw/2-g/2,cz+cd,g,3],[cx-3,cz+cd/2-g/2,3,g],[cx+cw,cz+cd/2-g/2,3,g]])if(inRect(x,z,q,.35+r))return false;
  return true;
 }
 /** Check every sampled footprint point at the same flat finish, never just the centre. */
 accept(points:readonly (readonly number[])[],finish:number,allowTree=false){
  for(const [x,z]of points){
   let reason='';
   if(!this.supported(x,z)||Math.abs(this.finishY(x,z)-finish)>EPS)reason='support';
   else if(!this.routeClear(x,z))reason='route';
   else if(this.blockers.some(s=>!(allowTree&&s.id==='tree')&&Math.abs(x-OX-s.x)<s.w/2+.04&&Math.abs(z-OZ-s.z)<s.d/2+.04))reason='solid';
   if(reason){this.rejected[reason]=(this.rejected[reason]??0)+1;return false}
  }
  return true;
 }
}

function ellipse(x:number,z:number,a:number,b:number,angle:number,seed:number,n=16):[number,number][]{
 const c=Math.cos(angle),s=Math.sin(angle);
 return Array.from({length:n},(_,i)=>{const t=i/n*Math.PI*2,r=.76+noise(seed+i*37)*.24,px=Math.cos(t)*a*r,pz=Math.sin(t)*b*r;return[x+px*c-pz*s,z+px*s+pz*c]});
}
const samples=(x:number,z:number,outline:readonly [number,number][])=>[[x,z],...outline,...outline.map(([px,pz])=>[(x+px)/2,(z+pz)/2])];

/** Stable per-feature seeds keep earlier planting fixed when later features are added. */
export function buildHeronGroundPlan(input:GroundInput):GroundPlan{
 const A=new GroundAcceptance(input),patches:GroundPatch[]=[],plants:GroundPlacement[]=[],perimeterTrees:GroundPlacement[]=[];
 const existing=input.existingPlacements??[];
 const addPatch=(id:string,kind:GroundPatch['kind'],source:string,x:number,z:number,a:number,b:number,angle:number)=>{
  const seed=hash(id),outline=ellipse(x,z,a,b,angle,seed),y=A.finishY(x,z);
  if(!A.accept(samples(x,z,outline),y,kind==='pit'))return false;
  patches.push({id,kind,source,x,z,y:y+.002,outline,seed});return true;
 };
 // Organic bare pockets interrupt the current uniformly scattered grass without adding lawn area.
 for(const [x,z]of input.grassCells.cells){
  const seed=hash(`soil:${x}:${z}`);if(noise(seed)>.27)continue;
  addPatch(`soil:${x}:${z}`,'soil','grass-cell',x+1,z+1,.65+noise(seed+1)*1.1,.4+noise(seed+2)*.6,noise(seed+3)*6.283);
 }
 // Broken bands at grass/paving interfaces; no new kerbs or long continuous black strips.
 for(const [x,z]of input.grassCells.cells)for(const [dx,dz]of [[-1,0],[1,0],[0,-1],[0,1]]){
  const seed=hash(`edge:${x}:${z}:${dx}:${dz}`);if(noise(seed)>.24||A.grassAt(x+1+dx*2,z+1+dz*2))continue;
  const px=x+1+dx*.75,pz=z+1+dz*.75;
  addPatch(`edge:${seed}`,'moss','grass-edge',px,pz,.68,.16,dx?Math.PI/2:0);
  if(plants.filter(p=>p.source==='joint').length>=90||noise(seed+3)>.6)continue;
  const asset=noise(seed+4)<.65?'WEED_TUFT_A':'WEED_TUFT_B',p:GroundPlacement={asset,x:px,y:A.finishY(px,pz),z:pz,ry:noise(seed+5)*6.283,scale:.8,source:'joint'};
  const bounds=plantBounds(p),foot=ellipse(px,pz,bounds.radius,bounds.radius,0,0,12);
  if(A.accept(samples(px,pz,foot),p.y)&&A.routeClear(px,pz,bounds.radius)&&!existing.some(e=>/SHRUB|WEED/.test(e.asset)&&Math.hypot(px-e.x,pz-e.z)<.6))plants.push(p);
 }
 // All 20 existing interior tree centres stay exact. The soil/litter changes are centimetres deep.
 for(const t of input.layout.trees){
  addPatch(`pit:${t.id}`,'pit',t.id,t.x,t.z,.7,.65,noise(hash(t.id))*6.283);
  for(let i=0;i<3;i++){
   const seed=hash(`leaves:${t.id}:${i}`),x=t.x+.9+noise(seed)*.9,z=t.z+.4+noise(seed+1)*1.2;
   if(existing.some(e=>e.asset.startsWith('LEAF_LITTER')&&Math.hypot(x-e.x,z-e.z)<1))continue;
   addPatch(`leaves:${t.id}:${i}`,'leaves',t.id,x,z,.32,.16,noise(seed+2)*.7);
  }
 }
 // Existing Corner downpipe/grates and two manholes: short soil/moss deposits beside, never over, hardware.
 for(const [i,x,z]of [[0,119.72,47.61],[1,105.02,47.52],[2,117.56,57.34],[3,108,45],[4,92,61]]){
  addPatch(`drain:${i}`,'moss','existing-drain',x+.39,z+.14,.27,.08,.35);
  addPatch(`silt:${i}`,'soil','existing-drain',x-.35,z+.13,.22,.06,-.2);
 }
 // Six low, varied clumps per existing bed: leafy shrubs over broad rosettes and upright weeds.
 // Fit each measured footprint before placing it; all roots meet the same existing soil finish.
 const shrubAssets=['SHRUB_A','SHRUB_B','SHRUB_C'];
 const clumpScale:Record<string,number>={SHRUB_A:.62,SHRUB_B:.75,SHRUB_C:.54,WEED_TUFT_A:3.15,WEED_TUFT_B:1.35,WEED_TUFT_C:1.04};
 const planterSlots=[[-.55,-.30],[.50,.45],[-.68,.65],[.50,-.72],[.68,-.60],[-.15,.72]];
 for(const c of input.layout.cover.filter(c=>c.kind.includes('planter')&&c.y===0)){
  const [x,z,w,d]=c.rect,shrubCount=c.id==='K21'||c.id==='K22'?2:1,bedSeed=hash(`planter:${c.id}`),rim=.12;
  for(let i=0;i<planterSlots.length;i++){
   const seed=hash(`planter:${c.id}:${i}`);
   const asset=i<shrubCount?shrubAssets[(bedSeed+i)%shrubAssets.length]:['WEED_TUFT_A','WEED_TUFT_C','WEED_TUFT_A','WEED_TUFT_B'][(i-shrubCount)%4];
   const scale=clumpScale[asset]*(.91+.09*noise(seed+13));
   const p:GroundPlacement={asset,x:0,y:c.y+c.height-.15-assets.get(asset)!.bounds_min[2]*scale,z:0,ry:noise(seed)*6.283,scale,source:`planter:${c.id}`};
   const b=plantBounds(p),availableX=w/2-rim-b.radius-.035,availableZ=d/2-rim-b.radius-.035;
   if(availableX<=0||availableZ<=0||b.top>c.y+c.height+.25)continue;
   const [sx,sz]=planterSlots[i],mirror=bedSeed%2?-1:1;
   p.x=x+w/2+(sx*mirror+(noise(seed+41)-.5)*.12)*availableX;
   p.z=z+d/2+(sz+(noise(seed+73)-.5)*.12)*availableZ;
   plants.push(p);
  }
 }
 // The site wall prevents reaching these pavement trees. Trunks avoid roads; canopies avoid facades.
 // Alternate along the north/south near pavement, between existing street lamp positions.
 // Keep the first pass centres, yaw and plane choices; replace its sparse birch silhouettes only.
 const species=['TREE_PLANE_A_LOD1','TREE_PLANE_A_LOD1','TREE_PLANE_B_LOD1','TREE_PLANE_B_LOD1'];
 for(const z of [-1.9,121.9])for(const x of [16.5,34.5,52.5,70.5,88.5,106.5,124.5,142.5]){
  if(existing.some(p=>Math.hypot(x-p.x,z-p.z)<1.5))continue;
  const i=perimeterTrees.length;perimeterTrees.push({asset:species[i%4],x,y:.12,z,ry:noise(hash(`outer:${x}:${z}`))*6.283,source:'outside-boundary'});
 }
 const lodTriangles:Record<string,number>={TREE_PLANE_A_LOD1:1533,TREE_PLANE_B_LOD1:1393};
 const plantTriangles=plants.reduce((n,p)=>n+plantBounds(p).triangles,0);
 return {version:1,patches,plants,perimeterTrees,stats:{patches:patches.length,plantTriangles,groundTriangleBudget:patches.reduce((n,p)=>n+(p.kind==='leaves'?24:p.outline.length*2),0),treeTriangles:perimeterTrees.reduce((n,p)=>n+lodTriangles[p.asset],0),rejected:A.rejected}};
}
