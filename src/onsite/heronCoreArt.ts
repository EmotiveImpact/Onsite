import spec from '../../docs/maps/heron-reach-32/blueprints/build-spec.json'
import type {LightAnchor} from './heronReachArt'

/** Fluorescent fittings over existing core landings. Art-only; no physical geometry ownership. */
export const coreLightAnchors:LightAnchor[]=spec.cores.flatMap(c=>c.levels.map(y=>({
 x:c.rect[0]+1.75-72,y:y+2.65,z:c.rect[1]+(c.mirrorZ?1:5)-60,kind:'core'
})));
