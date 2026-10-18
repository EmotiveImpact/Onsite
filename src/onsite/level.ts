// Original ONSITE layout transcribed from the user-supplied proposed floor plans.
// All dimensions metres, Y-up; render detail is separate from these collision solids.
import dressing from './dressing.json'
export type Solid={id:string;x:number;y:number;z:number;w:number;h:number;d:number;mat:string}
export const solids:Solid[]=[];
export const add=(id:string,x:number,y:number,z:number,w:number,h:number,d:number,mat='concrete')=>{const s={id,x,y,z,w,h,d,mat};solids.push(s);return s};
add('ground',0,-.2,0,36,.4,30,'asphalt');
// Outer enclosure and room partitions. North is -Z.
for(const x of [-18,18])add('outer-side',x,3.3,0,.3,6.6,30,'brick');
for(const z of [-15,15])add('outer-end',0,3.3,z,36,6.6,.3,'brick');
function doorway(id:string,x:number,z:number,length:number,axis:'x'|'z',floor=0,mat='brick',offset=0){
 for(const sign of [-1,1]){const side=(length-1.5)/2-sign*offset,center=offset+sign*(.75+side/2);add(id+'-jamb',x+(axis==='x'?center:0),floor+1.5,z+(axis==='z'?center:0),axis==='x'?side:.24,3,axis==='z'?side:.24,mat);}
 add(id+'-lintel',x+(axis==='x'?offset:0),floor+2.65,z+(axis==='z'?offset:0),axis==='x'?1.5:.24,.7,axis==='z'?1.5:.24,mat);
}
for(const floor of [0,3]){
 for(const z of [-9,9])for(const x of [-15,-6,6,15])doorway('court-door',x,z,Math.abs(x)===15?6:12,'x',floor,'brick',Math.abs(x)===6?(x<0?-3:3):0);
 for(const x of [-12,12])for(const z of [-6,0,6])doorway('side-door',x,z,6,'z',floor,'brick',x<0&&z===-6?1.9:x>0&&z===6?-1.9:0);
 for(const z of [-12,12])for(const x of [-6,6])doorway('room-door',x,z,6,'z',floor,'stock');
 for(const x of [-15,15])for(const z of [-3,3])add('side-partition',x,floor+1.5,z,6,3,.24,'stock');
}
// Upper perimeter rooms; stair voids intentionally excluded.
for(const z of [-12,12])add('room-floor',0,2.88,z,36,.24,6);
for(const x of [-15,15])for(const z of [-6,0,6])if(!((x<0&&z===-6)||(x>0&&z===6)))add('room-floor',x,2.88,z,6,.24,6);
// Continuous 3m gallery with 18x12m central opening.
for(const z of [-7.5,7.5])add('gallery',0,2.88,z,24,.24,3);
for(const x of [-10.5,10.5])add('gallery',x,2.88,0,3,.24,12);
for(const z of [-6,6])add('rail',0,3.55,z,18,1.1,.08,'rail');
for(const x of [-9,9])add('rail',x,3.55,0,.08,1.1,12,'rail');
// Dogleg stairs, 18 risers at 1/6m, two 1.5m flights, 0.3m going, 1.5m landing.
export const stairRoutes:{x:number;y:number;z:number}[][]=[];
for(const sign of [1,-1]){
 const tx=(u:number)=>sign*(-15+u),tz=(v:number)=>sign*(-6+v);
 const route=[{x:tx(-1),y:0,z:tz(2.4)}];
 for(let i=0;i<9;i++){const h=(i+1)/6;add('stair',tx(-1),h/2,tz(1.9-i*.3),1.5,h,.3);route.push({x:tx(-1),y:h,z:tz(1.9-i*.3)});}
 add('half-landing',tx(0),.75,tz(-1.4),3.5,1.5,1.5);route.push({x:tx(-1),y:1.5,z:tz(-1.4)},{x:tx(1),y:1.5,z:tz(-1.4)});
 for(let i=0;i<9;i++){const h=1.5+(i+1)/6;add('stair',tx(1),h/2,tz(-.5+i*.3),1.5,h,.3);route.push({x:tx(1),y:h,z:tz(-.5+i*.3)});}
 add('top-landing',tx(1.5),2.88,tz(2.25),3,.24,.8);route.push({x:tx(1),y:3,z:tz(2.25)},{x:tx(3),y:3,z:tz(2.25)});stairRoutes.push(route);
 // Central divider protects the open edge between flights.
 add('stair-divider',tx(0),1.8,tz(.7),.12,3.6,2.7,'steel');
}
for(const [x,z,w,d]of [[-5,-4,3,1.5],[5,-5,3,1.5],[-6,4,3,1.5],[6,4,3,1.5]])add('low-cover',x,.5,z,w,1,d);
add('central-screen',0,1.05,0,3,2.1,3,'steel');add('east-screen',10,1.05,0,.6,2.1,2.5,'steel');
// Flat 01 occupies the former north-west plant room. Keep the existing courtyard
// and lobby doors connected by a clear southern hall. Blender owns appearance;
// these simple solids alone own furniture/partition collision and navigation.
doorway('home-bedroom-divider',-12,-13,3.7,'z',0,'plaster',.8);
add('home-bed',-16.2,.36,-13.2,1.6,.72,2.1,'fabric');
add('home-wardrobe',-17.35,1.05,-10.5,.65,2.1,1.6,'wood');
add('home-sofa',-10.7,.45,-13.3,.9,.9,2.2,'fabric');
add('home-kitchen',-8.4,.48,-14.45,3.2,.96,.7,'paint');
add('home-fridge',-6.75,.95,-13.65,.7,1.9,.7,'trim');
add('home-table',-8.0,.38,-12.1,1.1,.76,.65,'wood');
// Bounds measured by Blender from the placed donor model, separate from render triangles.
for(const p of dressing){if(!p.collision)continue;const [w,h,d]=p.size,c=Math.abs(Math.cos(p.ry)),s=Math.abs(Math.sin(p.ry));add('dress-'+p.asset,p.x,p.y+h/2,p.z,w*c+d*s,h,d*c+w*s,'steel')}
export const spawn={x:-9,y:.04,z:12};
export const botSpawns=[{x:15,y:.04,z:-6},{x:12,y:.04,z:-12},{x:6,y:3.04,z:-7.5}];
