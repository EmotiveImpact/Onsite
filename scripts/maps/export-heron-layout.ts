// Writes the Heron Reach generator output for the Blender art build: the semantic layout plus every
// collision box in map coordinates (x east, z south, y up). Blender builds around these; it never edits them.
import {writeFileSync} from 'node:fs'
import {solids,layout,OX,OZ,surfaceIds} from '../../src/onsite/heronReach'
const r=(v:number)=>Math.round(v*1e4)/1e4;
const boxes=solids.map(s=>({id:s.id,mat:s.mat,x0:r(s.x+OX-s.w/2),x1:r(s.x+OX+s.w/2),y0:r(s.y-s.h/2),y1:r(s.y+s.h/2),z0:r(s.z+OZ-s.d/2),z1:r(s.z+OZ+s.d/2)}));
const out=process.argv[2]||'assets/blender/heron-reach/layout.json';
writeFileSync(out,JSON.stringify({generated:'src/onsite/heronReach.ts',coordinates:'map: x east, z south, y up; Blender (x-72, 60-z, y)',surfaceIds,...layout,boxes}));
console.log('wrote',out,boxes.length,'boxes');
