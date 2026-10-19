// As-built plan for Heron Reach, drawn from the runtime collision boxes and the layered navigation
// graph (not from the B01 drawings). Writes a compact JSON dump; draw_heron_as_built.py renders the PNG.
import {writeFileSync,mkdirSync} from 'node:fs'
import {heronReach as level} from '../../src/onsite/levels'
import {LayeredNav} from '../../src/onsite/navigation'
import {OX,OZ,SITE,deviations,levelY} from '../../src/onsite/heronReach'
const out=process.argv[2]||'test-results/heron-reach';mkdirSync(out,{recursive:true});
const nav=new LayeredNav(level),r=(v:number)=>Math.round(v*1000)/1000;
const data={site:SITE,levels:levelY,cell:nav.cell,surfaceIds:level.surfaceIds,deviations,
 solids:level.solids.map(s=>[s.id,s.mat,r(s.x+OX-s.w/2),r(s.z+OZ-s.d/2),r(s.w),r(s.d),r(s.y-s.h/2),r(s.y+s.h/2)]),
 nodes:nav.nodes.map(n=>[r(n.x+OX),r(n.z+OZ),r(n.y)])};
writeFileSync(`${out}/as-built.json`,JSON.stringify(data));console.log('wrote',`${out}/as-built.json`,level.solids.length,'solids',nav.nodes.length,'nodes');
