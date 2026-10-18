// Explicit 3D walk graph: surfaces sharing x/z retain distinct node IDs and heights.
// Deliberately replaces WWB's single-height grid. Coordinates are capsule centres.
const node=(id,x,y,z)=>({id,x,y,z});
export const navNodes=[node('court',7,.92,-7),node('court-gate',5.5,.92,-2),node('entry',5.5,.86,5.5),node('west-approach',-9,.86,5.5),node('stair-foot',-13.8,.86,5.1)];
for(let i=0;i<16;i++)navNodes.push(node(`step-${i}`,-13.8,.86+(i+1)*.2,4-i*.42));
navNodes.push(node('landing',-13.8,4.06,-3.4),node('upper-west',-16,4.06,-6),node('upper-mid',-16,4.06,-12),node('upper-north',-16,4.06,-18),node('upper-east',-5,4.06,-19),node('lower-mid',-16,.98,-12),node('lower-west',-16,.98,-6),node('lower-entry',-17,.98,5.5));
export const navEdges=[];
for(let i=0;i<25;i++)navEdges.push([navNodes[i].id,navNodes[i+1].id]);
navEdges.push(['west-approach','lower-entry'],['lower-entry','lower-west'],['lower-west','lower-mid']);
export function nearestNode(p){return navNodes.reduce((best,n)=>Math.hypot(n.x-p.x,(n.y-p.y)*3,n.z-p.z)<Math.hypot(best.x-p.x,(best.y-p.y)*3,best.z-p.z)?n:best);}
export function findRoute(start,end){
  const from=nearestNode(start),to=nearestNode(end),distance=new Map([[from.id,0]]),previous=new Map(),open=new Set(navNodes.map(n=>n.id));
  while(open.size){
    const id=[...open].reduce((a,b)=>(distance.get(a)??Infinity)<(distance.get(b)??Infinity)?a:b);
    if(!distance.has(id))break;open.delete(id);if(id===to.id)break;
    const a=navNodes.find(n=>n.id===id);
    for(const edge of navEdges){if(!edge.includes(id))continue;const next=edge[0]===id?edge[1]:edge[0];if(!open.has(next))continue;
      const b=navNodes.find(n=>n.id===next);const d=distance.get(id)+Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
      if(d<(distance.get(next)??Infinity)){distance.set(next,d);previous.set(next,id);}
    }
  }
  if(!distance.has(to.id))return [];
  const route=[to];let id=to.id;while(id!==from.id){id=previous.get(id);if(!id)return [];route.unshift(navNodes.find(n=>n.id===id));}
  return route.map(n=>({...n}));
}
