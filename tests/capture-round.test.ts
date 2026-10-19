import test from 'node:test'
import assert from 'node:assert/strict'
import {createCaptureMatch} from '../src/onsite/CaptureRound'
import {createMatch,registerKill,recordShot,tick} from '../src/wwb/game/rules'

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
