import {createMatch} from '../wwb/game/rules'

/** WWB supplies score/stat bookkeeping; ONSITE owns clear-and-capture victory.
 * Each opponent dies once per encounter, so an unreachable frag limit prevents
 * the last kill freezing the clock and discarding that shot before capture. */
export function createCaptureMatch(botNames:string[],seconds:number){
 return createMatch(botNames,seconds,botNames.length+1)
}
