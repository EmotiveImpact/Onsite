import {writeFileSync,mkdirSync} from 'node:fs';import {solids,spawn,botSpawns,stairRoutes} from '../src/onsite/level';
mkdirSync('docs/development/evidence',{recursive:true});
writeFileSync('docs/development/evidence/layout.json',JSON.stringify({units:'metres',north:'-Z',bounds:{width:36,depth:30},galleryHeight:3,centralVoid:{width:18,depth:12},spawn,botSpawns,stairRoutes,solids},null,2));
const esc=(s:string)=>s.replaceAll('&','&amp;').replaceAll('<','&lt;');
let svg=`<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="830" viewBox="0 0 1440 830"><rect width="1440" height="830" fill="#10181d"/><style>text{font-family:Arial,sans-serif;fill:#eee9db}.label{font-size:13px;fill:#c5cbcb}.small{font-size:12px;fill:#97a5aa}</style><text x="40" y="55" font-size="34" font-weight="bold">ONSITE / AS-BUILT</text><text x="40" y="82" class="label">Generated from src/onsite/level.ts • collision geometry • metres • north ↑ • 18 October 2026</text>`;
for(const [floor,ox,title]of [[0,60,'GROUND / +0.00 m'],[3,780,'GALLERY / +3.00 m']] as const){const scale=16,oy=160;const X=(x:number)=>ox+(x+18)*scale,Z=(z:number)=>oy+(z+15)*scale;
svg+=`<text x="${ox}" y="128" font-size="20" font-weight="bold">${title}</text><rect x="${ox}" y="${oy}" width="576" height="480" fill="#26333a"/>`;
if(floor)svg+=`<rect x="${X(-9)}" y="${Z(-6)}" width="288" height="192" fill="#10181d"/><text x="${X(0)}" y="${Z(0)}" text-anchor="middle" class="label">OPEN TO COURT</text>`;
for(const s of solids){if(['ground','room-floor','gallery'].includes(s.id))continue;const low=s.y-s.h/2,high=s.y+s.h/2;if(s.id==='stair'||s.id==='half-landing'||s.id==='top-landing'){}else if(!(low<floor+1.6&&high>floor+.1))continue;
const color=s.id==='stair'?'#6aa5ac':s.id.includes('screen')?'#bc8940':s.mat==='rail'?'#7b9c9e':'#9aa6a8';svg+=`<rect x="${X(s.x-s.w/2)}" y="${Z(s.z-s.d/2)}" width="${s.w*scale}" height="${s.d*scale}" fill="${color}" stroke="#121b22" stroke-width=".6"><title>${esc(s.id)}: ${s.w} × ${s.h} × ${s.d}m</title></rect>`}
for(const [label,x,z]of [['FLAT 01',-12,-12],['NORTH LOBBY',0,-12],['WORKSHOP',12,-12],['ENTRY',-12,12],['CYCLE STORE',0,12],['SOUTH LOBBY',12,12],['STAIR A',-15,-6],['STAIR B',15,6]] as const)svg+=`<text x="${X(x)}" y="${Z(z)}" class="small" text-anchor="middle">${label==='FLAT 01'&&floor?'NORTH WEST ROOM':label}</text>`;
for(const [label,p]of [['P',spawn],...botSpawns.map((p,i)=>['B'+(i+1),p])] as [string,{x:number;y:number;z:number}][]){if(Math.abs(p.y-floor)>.2)continue;svg+=`<circle cx="${X(p.x)}" cy="${Z(p.z)}" r="10" fill="#10181d" stroke="#e5b15c" stroke-width="2"/><text x="${X(p.x)}" y="${Z(p.z)+4}" font-size="11" text-anchor="middle">${label}</text>`}
svg+=`<text x="${ox+288}" y="${oy+505}" text-anchor="middle" class="label">36 m × 30 m</text>`;
}
svg+=`<text x="60" y="715" class="label">Two 1.5 m stair flights per core • 18 × 0.167 m risers • 0.30 m going • 1.5 m mid-landing</text><text x="60" y="745" class="label">Gallery width 3 m • door clear width 1.5 m • low cover 1 m • tall screens 2.1 m • P player / B1–B3 bots</text><text x="60" y="780" class="small">Stair doors offset towards landing ends. Small render-only details and upper facade storeys omitted. Ground and upper routes tested with WWB actors.</text></svg>`;
writeFileSync('docs/development/evidence/as-built.svg',svg);

// Detail of the accessible flat, derived from the same authoritative collision list.
const hx=(x:number)=>60+(x+18)*52,hz=(z:number)=>110+(z+15)*52;
let home=`<svg xmlns="http://www.w3.org/2000/svg" width="744" height="510" viewBox="0 0 744 510"><rect width="744" height="510" fill="#10181d"/><style>text{font-family:Arial,sans-serif;fill:#eee9db}</style><defs><clipPath id="flat"><rect x="60" y="110" width="624" height="312"/></clipPath></defs><text x="60" y="45" font-size="27" font-weight="bold">ONSITE / FLAT 01 — AS-BUILT</text><text x="60" y="78" font-size="14">North-west ground floor · 12 × 6 m gross · north ↑</text><rect x="60" y="110" width="624" height="312" fill="#34454c"/><g clip-path="url(#flat)">`;
for(const s of solids){if(['ground','gallery','room-floor'].includes(s.id)||s.y-s.h/2>1.7||s.y+s.h/2<.1)continue;home+=`<rect x="${hx(s.x-s.w/2)}" y="${hz(s.z-s.d/2)}" width="${s.w*52}" height="${s.d*52}" fill="${s.id.startsWith('home-')?'#a58a62':'#bac2bc'}" stroke="#10181d"><title>${esc(s.id)}</title></rect>`}
home+='</g>';
for(const [label,x,z]of [['BEDROOM',-14.6,-13.9],['KITCHEN',-8.4,-13.8],['LIVING',-8.5,-10.8],['HALL',-13.4,-10.25],['COURT ENTRY',-9,-9.05]]as const)home+=`<text x="${hx(x)}" y="${hz(z)}" font-size="12" text-anchor="middle">${label}</text>`;
home+=`<text x="60" y="458" font-size="13">Furniture and partition collision shown. Closed rear windows stay solid.</text><text x="60" y="483" font-size="13">Existing court and lobby doors retained. Bathroom not yet modelled.</text></svg>`;
writeFileSync('docs/development/evidence/home-plan.svg',home);
