// Playable ONSITE levels. Heron Court stays the default and the regression baseline;
// Heron Reach is opened with ?map=heron-reach while it is built block by block.
import * as court from './level'
import * as reach from './heronReach'
import type {Solid} from './level'
type P={x:number;y:number;z:number}
export type Capture={x:number;z:number;radius:number;minY:number;maxY:number;label:string}
export type Level={
 id:'heron-court'|'heron-reach';name:string;solids:Solid[];surfaceIds:string[];
 bounds:{minX:number;minZ:number;maxX:number;maxZ:number};spawn:P&{yaw?:number};botSpawns:P[];botNames:string[];capture:Capture;overview:{from:P;to:P};
 /** Round length in seconds; fences are solids that block movement but not bullets or sight. */
 seconds:number;fenceIds:string[];
}
export const heronCourt:Level={id:'heron-court',name:'HERON COURT',solids:court.solids,surfaceIds:['ground','gallery','room-floor','stair','half-landing','top-landing'],
 bounds:{minX:-18,minZ:-15,maxX:18,maxZ:15},spawn:court.spawn,botSpawns:court.botSpawns,botNames:['EAST','WORKSHOP','GALLERY'],seconds:180,fenceIds:[],capture:{x:0,z:0,radius:4,minY:-1,maxY:1,label:'THE COURT'},
 overview:{from:{x:8.2,y:5.5,z:8.1},to:{x:-1,y:3,z:-6}}};
export const heronReach:Level={id:'heron-reach',name:'HERON REACH',solids:reach.solids,surfaceIds:reach.surfaceIds,bounds:reach.bounds,
 spawn:reach.spawn,botSpawns:reach.botSpawns,botNames:reach.botNames,seconds:300,fenceIds:['fence'],capture:reach.capture,overview:reach.overview};
export const levelFor=(search:string)=>new URLSearchParams(search).get('map')==='heron-reach'?heronReach:heronCourt;
/** Capture volumes are floor-aware: standing on a gallery above the area never counts. */
export const inCapture=(c:Capture,p:P)=>Math.hypot(p.x-c.x,p.z-c.z)<c.radius&&p.y>=c.minY&&p.y<c.maxY;
