import test from 'node:test'
import assert from 'node:assert/strict'
import {PROFILE_KEY, accuracy, defaultProfile, loadProfile, normaliseProfile, recordRound, saveProfile, type ProfileStorage, type RoundRecord} from '../src/onsite/profile.ts'

test('Player preferences survive a reload without sharing map records', () => {
  const data = new Map<string, string>(), storage: ProfileStorage = {getItem: key => data.get(key) ?? null, setItem: (key, value) => {data.set(key, value)}}
  const profile = defaultProfile(); profile.settings = {sensitivity: 1.7, sound: false, volume: .35, quality: 'balanced', reducedMotion: true}; profile.kit = {hood: 'down', trainers: 'high'}
  assert(saveProfile(profile, storage)); assert.deepEqual(loadProfile(storage), profile)
  assert.equal(profile.records['heron-reach'].played, 0); assert.equal(data.size, 1); assert(data.has(PROFILE_KEY))
})

test('Corrupt, absent, future-version and inaccessible local data cannot prevent play', () => {
  for (const value of ['{broken', 'null', '[]', '{"version":999}', '{"version":1,"settings":null,"records":null}']) {
    const profile = loadProfile({getItem: () => value, setItem: () => {}}, true)
    assert.equal(profile.settings.sensitivity, 1); assert.equal(profile.settings.reducedMotion, true)
  }
  const denied: ProfileStorage = {getItem: () => {throw Error('denied')}, setItem: () => {throw Error('quota')}}
  assert.deepEqual(loadProfile(denied), defaultProfile()); assert.equal(saveProfile(defaultProfile(), denied), false)
})

test('Invalid saved values are bounded and unsupported kit/quality values do not reach runtime', () => {
  const p = normaliseProfile({version: 1, settings: {sensitivity: 999, sound: 'false', volume: -1, reducedMotion: 7, quality: 'ultra'}, kit: {hood: 'missing', trainers: 'flight'}, records: {'heron-reach': {played: 2, secured: 88, best: {outcome: 'lost', seconds: -3}, last: {outcome: 'won', shots: 5, hits: 400, kills: 999, seconds: Infinity}}}})
  assert.equal(p.settings.sensitivity, 2); assert.equal(p.settings.volume, 0); assert.equal(p.settings.sound, true); assert.equal(p.settings.quality, 'auto')
  assert.deepEqual(p.kit, {hood: 'up', trainers: 'court'}); assert.equal(p.records['heron-reach'].secured, 2); assert.equal(p.records['heron-reach'].best, null)
  assert.equal(p.records['heron-reach'].last?.hits, 5); assert.equal(p.records['heron-reach'].last?.kills, 6); assert.equal(p.records['heron-reach'].last?.seconds, 0)
})

test('Only captured rounds become a map best; losses and slower wins retain the record', () => {
  const round = (outcome: 'won' | 'lost', seconds: number, hits = 15): RoundRecord => ({outcome, seconds, hits, shots: 30, kills: 3, completedAt: 100})
  const original = defaultProfile(), first = recordRound(original, 'heron-court', round('won', 90))
  assert.equal(original.records['heron-court'].played, 0)
  let current = recordRound(first, 'heron-court', round('lost', 20))
  current = recordRound(current, 'heron-court', round('won', 100))
  assert.equal(current.records['heron-court'].best?.seconds, 90); assert.equal(current.records['heron-court'].played, 3); assert.equal(current.records['heron-court'].secured, 2)
  current = recordRound(current, 'heron-court', round('won', 90, 20))
  assert.equal(current.records['heron-court'].best?.hits, 20)
  current = recordRound(current, 'heron-reach', round('won', 80))
  assert.equal(current.records['heron-reach'].played, 1); assert.equal(current.records['heron-court'].played, 4)
  assert.equal(accuracy({shots: 0, hits: 0}), 0)
})
