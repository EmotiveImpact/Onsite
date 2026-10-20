// Small browser-side consumer of the offline accepted plan. No planner/manifests enter this path.
import type {GroundPatch,GroundPlan} from './heronGroundPlan'
export type GroundDensityMask=(x:number,z:number)=>number;

/** Optional presentation fetch: failure preserves original placements and the original grass field. */
export async function loadHeronGroundPlan(fetchPlan:typeof fetch=fetch):Promise<GroundPlan|null>{
 try{
  const response=await fetchPlan('/models/heron-reach/ground-plan.json');
  if(!response.ok)throw new Error(`HTTP ${response.status}`);
  const plan=await response.json() as GroundPlan;
  const finite=(values:unknown[])=>values.every(v=>typeof v==='number'&&Number.isFinite(v));
  if(plan.version!==1||!Array.isArray(plan.patches)||!Array.isArray(plan.plants)||!Array.isArray(plan.perimeterTrees))throw new Error('Unsupported ground plan');
  if(plan.patches.some(p=>!['soil','pit','moss','leaves'].includes(p.kind)||!finite([p.x,p.y,p.z])||!Array.isArray(p.outline)||p.outline.length<3||p.outline.some(v=>!Array.isArray(v)||v.length!==2||!finite(v))))throw new Error('Invalid ground patch');
  if([...plan.plants,...plan.perimeterTrees].some(p=>typeof p.asset!=='string'||!finite([p.x,p.y,p.z,p.ry,p.scale??1,p.sx??1])||(p.scale??1)<=0))throw new Error('Invalid ground planting');
  return plan;
 }catch(e){console.warn('Ground plan unavailable; retaining original planting and grass',e);return null}
}

const densityIndexes=new WeakMap<GroundPlan,GroundDensityMask>();
/** One 8m spatial lookup feeds the existing GrassField; no second grass system or frame updates. */
export function createGroundGrassDensity(plan:GroundPlan):GroundDensityMask{
 let cached=densityIndexes.get(plan);if(cached)return cached;
 const cells=new Map<string,GroundPatch[]>();
 for(const p of plan.patches){if(p.kind!=='soil'&&p.kind!=='pit')continue;
  const xs=p.outline.map(v=>v[0]),zs=p.outline.map(v=>v[1]);
  for(let x=Math.floor(Math.min(...xs)/8);x<=Math.floor(Math.max(...xs)/8);x++)for(let z=Math.floor(Math.min(...zs)/8);z<=Math.floor(Math.max(...zs)/8);z++){
   const key=`${x},${z}`,list=cells.get(key);if(list)list.push(p);else cells.set(key,[p]);
  }
 }
 cached=(x,z)=>{
  let density=1;
  for(const p of cells.get(`${Math.floor(x/8)},${Math.floor(z/8)}`)??[]){
   let inside=false;for(let i=0,j=p.outline.length-1;i<p.outline.length;j=i++){
    const a=p.outline[i],b=p.outline[j];if((a[1]>z)!==(b[1]>z)&&x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0])inside=!inside;
   }if(inside)density=Math.min(density,p.kind==='pit'?.04:.13);
  }return density;
 };densityIndexes.set(plan,cached);return cached;
}
export function groundGrassDensity(plan:GroundPlan,x:number,z:number){return createGroundGrassDensity(plan)(x,z)}

/** A separate coordinate hash never consumes the established grass transform RNG. */
export function acceptGrassCandidate(x:number,z:number,density:number){
 if(!Number.isFinite(density)||density>=1)return true;
 if(density<=0)return false;
 let h=Math.imul(Math.round(x*1e5),0x45d9f3b)^Math.imul(Math.round(z*1e5),0x27d4eb2d);
 h=Math.imul(h^(h>>>16),0x45d9f3b);h=Math.imul(h^(h>>>16),0x45d9f3b);
 return((h^(h>>>16))>>>0)/4294967296<density;
}
