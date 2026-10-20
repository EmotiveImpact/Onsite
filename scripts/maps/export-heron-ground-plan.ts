import {writeFileSync,mkdirSync} from 'node:fs'
import {dirname,resolve} from 'node:path'
import {solids,surfaceIds,layout,dressing} from '../../src/onsite/heronReach.ts'
import cells from '../../public/models/heron-reach/grass-cells.json'
import {buildHeronGroundPlan} from '../../src/onsite/heronGroundPlan.ts'
const plan=buildHeronGroundPlan({solids,surfaceIds,layout,grassCells:cells,existingPlacements:dressing.items});
const out=resolve(process.argv[2]??'assets/blender/heron-reach/ground-plan.json');
mkdirSync(dirname(out),{recursive:true});writeFileSync(out,JSON.stringify(plan,null,2)+'\n');console.log(JSON.stringify(plan.stats));console.log(out);
const runtime=resolve(process.argv[3]??'public/models/heron-reach/ground-plan.json');
mkdirSync(dirname(runtime),{recursive:true});writeFileSync(runtime,JSON.stringify(plan)+'\n');console.log(runtime);
