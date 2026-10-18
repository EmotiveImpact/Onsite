/** Fixed accumulator adapted from WWB engine/loop.ts, 4cf34e8.
 * MIT © 2026 Jeevesh Singale; public/licenses/WWB-MIT.txt.
 * ONSITE: callback can stop a completed round; six-step catch-up budget.
 */
export class FixedStepper {
  constructor(stepSeconds=1/60){this.stepSeconds=stepSeconds;this.accumulator=0;}
  resetAccumulator(){this.accumulator=0;}
  advance(frameSeconds,step){
    this.accumulator+=Math.min(frameSeconds,.1);let count=0;
    while(this.accumulator>=this.stepSeconds&&count++<6){
      this.accumulator-=this.stepSeconds;if(step(this.stepSeconds)===false){this.accumulator=0;break;}
    }
    return this.accumulator/this.stepSeconds;
  }
}
