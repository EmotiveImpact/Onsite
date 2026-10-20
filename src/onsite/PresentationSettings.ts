import type {PlayerSettings} from './profile'

/** Settings affect rendering only; simulation cadence and weapon accuracy stay unchanged. */
export function presentationProfile(settings: Pick<PlayerSettings, 'quality' | 'reducedMotion'>, software: boolean, deviceRatio: number, inspectionRatio?: number) {
  const ratio = Number.isFinite(deviceRatio) ? Math.max(.5, deviceRatio) : 1
  return {
    pixelRatio: software ? Math.max(.5, Math.min(1, inspectionRatio ?? .5)) : Math.min(ratio, settings.quality === 'balanced' ? 1 : 1.5),
    bloom: !software && settings.quality !== 'balanced',
    reducedMotion: settings.reducedMotion,
  }
}

/** Only the visual kick is reduced; the player's simulated aim and weapon state are read-only. */
export function cameraPresentation(pitch: number, yaw: number, punch: {pitch:number;yaw:number;roll:number}, reducedMotion: boolean) {
  const scale = reducedMotion ? .25 : 1
  return {pitch:pitch+punch.pitch*scale,yaw:yaw+punch.yaw*scale,roll:punch.roll*scale}
}
