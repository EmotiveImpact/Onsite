// As-built plan for Heron Reach step 1, drawn from the runtime collision boxes and the layered
// navigation graph (not from the B01 drawings). Writes an SVG (not committed: ~2 MB of nav dots); render it to PNG in a browser.
import {writeFileSync,mkdirSync} from 'node:fs'
import {heronReach as level} from '../../src/onsite/levels'
import {LayeredNav} from '../../src/onsite/navigation'
import {PAD,OX,OZ,deviations} from '../../src/onsite/heronReach'
const out=process.argv[2]||'docs/maps/heron-reach-32/as-built';mkdirSync(out,{recursive:true});
const nav=new LayeredNav(level),S=10,W=PAD[2]*S,H=PAD[3]*S,gap=40,top=90;
const px=(x:number)=>(x+OX-PAD[0])*S,pz=(z:number)=>(z+OZ-PAD[1])*S;
const panels=[['G / FFL +0.00',0],['L1 / FFL +3.00',3],['L2 / FFL +6.00',6],['R / FFL +9.00',9]] as const;
let svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${2*W+3*gap}" height="${top+2*H+3*gap+40+deviations.length*18}" font-family="Helvetica,Arial,sans-serif"><rect width="100%" height="100%" fill="#f4f6f7"/>`;
svg+=`<text x="${gap}" y="40" font-size="22" font-weight="700" fill="#16324a">ONSITE / HERON REACH / ROWAN HOUSE AS-BUILT (STEP 1)</text><text x="${gap}" y="64" font-size="13" fill="#4b6275">Drawn from runtime collision boxes and the layered navigation graph · 1 square = 1 m · north up · ${level.solids.length} solids · ${nav.nodes.length} nav nodes</text>`;
panels.forEach(([title,y],i)=>{
 const ox=gap+(i%2)*(W+gap),oy=top+Math.floor(i/2)*(H+gap);svg+=`<g transform="translate(${ox},${oy})"><rect width="${W}" height="${H}" fill="#fff" stroke="#9fb2c1"/>`;
 for(let m=0;m<=PAD[2];m+=6)svg+=`<line x1="${m*S}" y1="0" x2="${m*S}" y2="${H}" stroke="#eef2f5"/>`;for(let m=0;m<=PAD[3];m+=6)svg+=`<line x1="0" y1="${m*S}" x2="${W}" y2="${m*S}" stroke="#eef2f5"/>`;
 const r=(s:typeof level.solids[0],fill:string,op=1)=>`<rect x="${px(s.x-s.w/2).toFixed(1)}" y="${pz(s.z-s.d/2).toFixed(1)}" width="${(s.w*S).toFixed(1)}" height="${(s.d*S).toFixed(1)}" fill="${fill}" fill-opacity="${op}"/>`;
 for(const s of level.solids){const t=s.y+s.h/2,b=s.y-s.h/2;if(s.id==='ground'&&y===0)continue;if(level.surfaceIds.includes(s.id)&&Math.abs(t-y)<.01)svg+=r(s,'#cfe0ee')}
 for(const s of level.solids){const t=s.y+s.h/2;if((s.id==='stair')&&t>y&&t<y+3)svg+=r(s,'#7aa7c7',.35+.6*(t-y)/3)}
 for(const n of nav.nodes)if(Math.abs(n.y-y)<.01)svg+=`<circle cx="${px(n.x).toFixed(1)}" cy="${pz(n.z).toFixed(1)}" r="1.4" fill="#2e8b57" fill-opacity=".55"/>`;
 for(const s of level.solids){const t=s.y+s.h/2,b=s.y-s.h/2;if(level.surfaceIds.includes(s.id)||s.id.endsWith('-cap'))continue;if(b<=y+1.05&&t>=y+1.05)svg+=r(s,s.mat==='steel'?'#d2691e':s.mat==='glass'||s.mat==='lit'?'#5fa8d3':['wood','fabric','trim','paint'].includes(s.mat)&&s.id.startsWith('home')?'#b9a27a':'#1d2b36')}
 svg+=`<text x="10" y="22" font-size="15" font-weight="700" fill="#16324a">${title}</text></g>`;
});
const ly=top+2*H+2*gap+10;svg+=`<g font-size="12" fill="#1d2b36"><rect x="${gap}" y="${ly}" width="12" height="12" fill="#1d2b36"/><text x="${gap+18}" y="${ly+10}">wall / solid cut at FFL+1.05</text><rect x="${gap+200}" y="${ly}" width="12" height="12" fill="#d2691e"/><text x="${gap+218}" y="${ly+10}">1.2 m guard</text><rect x="${gap+320}" y="${ly}" width="12" height="12" fill="#5fa8d3"/><text x="${gap+338}" y="${ly+10}">closed glazing</text><rect x="${gap+450}" y="${ly}" width="12" height="12" fill="#cfe0ee"/><text x="${gap+468}" y="${ly+10}">floor at this FFL</text><rect x="${gap+590}" y="${ly}" width="12" height="12" fill="#7aa7c7"/><text x="${gap+608}" y="${ly+10}">stair treads rising to next FFL</text><circle cx="${gap+826}" cy="${ly+6}" r="3" fill="#2e8b57"/><text x="${gap+836}" y="${ly+10}">walkable nav node</text></g>`;
deviations.forEach((d,i)=>svg+=`<text x="${gap}" y="${ly+40+i*18}" font-size="12" fill="#4b6275">Deviation ${i+1}: ${d}</text>`);
svg+='</svg>';writeFileSync(`${out}/rowan-step1-as-built.svg`,svg);console.log('wrote',`${out}/rowan-step1-as-built.svg`,svg.length);
