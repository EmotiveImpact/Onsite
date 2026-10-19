import test from 'node:test'
import assert from 'node:assert/strict'
import {createCaptureMatch} from '../src/onsite/CaptureRound'
import {createMatch,registerKill,recordShot,tick} from '../src/wwb/game/rules'
import {Encounter,type Command} from '../src/onsite/Encounter'
import {heronCourt} from '../src/onsite/levels'
import {Vector3} from 'three'

for(const count of [3,6])test(`${count}-opponent capture round keeps its final shot and deadline after every opponent is cleared`,()=>{
 let match=createCaptureMatch(Array.from({length:count},(_,i)=>String(i+1)),10)
 for(let id=1;id<=count;id++){
  // The real Arsenal damages/kills first, then Encounter records that step's shot.
  match=registerKill(match,{killer:0,victim:id,weapon:'rifle'}).state
  match=recordShot(match,1,1,100)
 }
 assert.equal(match.phase,'playing');assert.equal(match.stats.shots,count)
 assert.equal(match.stats.hits,count);assert.equal(match.stats.damageDealt,count*100)
 const elapsed=tick(match,2.5)
 assert.equal(elapsed.timeLeft,7.5);assert.equal(elapsed.elapsed,2.5)
 assert.equal(elapsed.phase,'playing','Only the ONSITE capture volume can decide capture victory')
 assert.equal(tick(elapsed,7.5).timeLeft,0,'Failure to reach capture still exhausts the deadline')
})
test('the donor score-race rule remains unchanged for an actual frag-limited match',()=>{
 let match=createMatch(['BOT'],30,1)
 match=registerKill(match,{killer:0,victim:1}).state
 assert.equal(match.phase,'won');assert.equal(match.endReason,'frags')
})

test('the actual encounter step gives death and deadline precedence over simultaneous capture',()=>{
 // Isolate the final simulation tick: movement, Arsenal and physics are inert;
 // the production Encounter.step, donor clock and capture-volume check run.
 const finalTick=(alive:boolean,seconds:number)=>{
  const encounter=Object.assign(Object.create(Encounter.prototype),{
   state:'active',time:0,steps:0,hit:0,hurt:0,capture:2.49,
   match:createCaptureMatch(heronCourt.botNames,seconds),level:heronCourt,bots:[],
   player:{alive,position:new Vector3(),velocity:new Vector3(),step:()=>{},eye:()=>new Vector3()},
   arsenal:{step:()=>{},shotsThisStep:0,hitsThisStep:0,damageThisStep:0},physics:{step:()=>{}},
  }) as Encounter
  encounter.step(1/60,{x:0,y:0,jump:false,sprint:false,ads:false,fire:false,firePressed:false,reload:false,yaw:0,pitch:0} satisfies Command)
  return encounter.state
 }
 assert.equal(finalTick(true,.01),'lost','The deadline cannot be overwritten by capture')
 assert.equal(finalTick(false,1),'lost','A dead player cannot complete capture')
 assert.equal(finalTick(true,1),'won','A surviving player still completes capture before the deadline')
})
