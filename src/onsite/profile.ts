// Original ONSITE local preferences and encounter records. No account or remote storage.
export type MapId = 'heron-court' | 'heron-reach'
export type QualityProfile = 'auto' | 'balanced' | 'detail'
export type OperatorKit = {hood: 'up' | 'down'; trainers: 'court' | 'runner' | 'high'}
export type PlayerSettings = {
  sensitivity: number; sound: boolean; volume: number; reducedMotion: boolean; quality: QualityProfile
}
export type RoundRecord = {
  outcome: 'won' | 'lost'; seconds: number; shots: number; hits: number; kills: number; completedAt: number
}
export type MapRecord = {played: number; secured: number; last: RoundRecord | null; best: RoundRecord | null}
export type PlayerProfile = {
  version: 1; settings: PlayerSettings; kit: OperatorKit; records: Record<MapId, MapRecord>
}
export type ProfileStorage = Pick<Storage, 'getItem' | 'setItem'>
export const PROFILE_KEY = 'onsite.player.v1'
const object = (value: unknown): Record<string, unknown> => value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
const finite = (value: unknown, fallback: number, min: number, max: number) => typeof value === 'number' && Number.isFinite(value) ? Math.min(max, Math.max(min, value)) : fallback
const count = (value: unknown, max = 1_000_000) => Math.floor(finite(value, 0, 0, max))
const bool = (value: unknown, fallback: boolean) => typeof value === 'boolean' ? value : fallback
export function defaultProfile(reducedMotion = false): PlayerProfile {
  return {version: 1, settings: {sensitivity: 1, sound: true, volume: .6, reducedMotion, quality: 'auto'}, kit: {hood: 'up', trainers: 'court'}, records: {'heron-court': {played: 0, secured: 0, last: null, best: null}, 'heron-reach': {played: 0, secured: 0, last: null, best: null}}}
}
function normaliseRound(value: unknown): RoundRecord | null {
  const r = object(value)
  if (r.outcome !== 'won' && r.outcome !== 'lost') return null
  const shots = count(r.shots)
  return {outcome: r.outcome, seconds: finite(r.seconds, 0, 0, 86400), shots, hits: Math.min(shots, count(r.hits)), kills: count(r.kills, 6), completedAt: count(r.completedAt, 8.64e15)}
}
export function normaliseProfile(value: unknown, reducedMotion = false): PlayerProfile {
  const p = object(value), result = defaultProfile(reducedMotion)
  // Unknown future formats are left untouched in storage until the user changes a preference.
  if (p.version !== 1) return result
  const s = object(p.settings), k = object(p.kit), records = object(p.records)
  result.settings = {sensitivity: finite(s.sensitivity, 1, .5, 2), sound: bool(s.sound, true), volume: finite(s.volume, .6, 0, 1), reducedMotion: bool(s.reducedMotion, reducedMotion), quality: s.quality === 'balanced' || s.quality === 'detail' ? s.quality : 'auto'}
  result.kit = {hood: k.hood === 'down' ? 'down' : 'up', trainers: k.trainers === 'runner' || k.trainers === 'high' ? k.trainers : 'court'}
  for (const id of ['heron-court', 'heron-reach'] as const) {
    const record = object(records[id]), played = count(record.played), best = normaliseRound(record.best)
    result.records[id] = {played, secured: Math.min(played, count(record.secured)), last: normaliseRound(record.last), best: best?.outcome === 'won' ? best : null}
  }
  return result
}
export function loadProfile(storage?: ProfileStorage, reducedMotion = false): PlayerProfile {
  try {
    const source = storage ?? (typeof window === 'undefined' ? undefined : window.localStorage)
    const saved = source?.getItem(PROFILE_KEY)
    return saved ? normaliseProfile(JSON.parse(saved), reducedMotion) : defaultProfile(reducedMotion)
  } catch { return defaultProfile(reducedMotion) }
}
/** A blocked/private/quota-full store must never prevent play. */
export function saveProfile(profile: PlayerProfile, storage?: ProfileStorage): boolean {
  try {
    const target = storage ?? (typeof window === 'undefined' ? undefined : window.localStorage)
    if (!target) return false
    target.setItem(PROFILE_KEY, JSON.stringify(normaliseProfile(profile)))
    return true
  } catch { return false }
}
export const accuracy = (round: Pick<RoundRecord, 'shots' | 'hits'>) => round.shots ? Math.round(round.hits / round.shots * 100) : 0
/** Best means fastest completed capture, with accuracy breaking exact time ties. */
export function recordRound(profile: PlayerProfile, map: MapId, round: RoundRecord): PlayerProfile {
  const next = normaliseProfile(profile), valid = normaliseRound(round)
  if (!valid) return next
  const previous = next.records[map]
  const best = valid.outcome === 'won' && (!previous.best || valid.seconds < previous.best.seconds || (valid.seconds === previous.best.seconds && accuracy(valid) > accuracy(previous.best))) ? valid : previous.best
  next.records[map] = {played: previous.played + 1, secured: previous.secured + Number(valid.outcome === 'won'), last: valid, best}
  return next
}
