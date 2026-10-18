// Adapted from WWB 4cf34e8072ce0985eeae6d41c60c6a15cc4c1dd1. MIT © 2026 Jeevesh Singale.
// Full notice: public/licenses/WWB-MIT.txt. See docs/development/DONOR-MAP.md for changes.
import * as THREE from 'three'
export function noiseTexture(size = 256, seed = 1, scale = 8, contrast = 1): THREE.CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = size
  const ctx = canvas.getContext('2d')!
  const img = ctx.createImageData(size, size)
  let s = seed * 9301 + 49297
  const rand = () => ((s = (s * 16807) % 2147483647) / 2147483647)
  const layers = [scale, scale * 2, scale * 4, scale * 8]
  const grids = layers.map(n => Array.from({ length: n * n }, rand))
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      let v = 0
      let amp = 0.5
      for (let l = 0; l < layers.length; l += 1) {
        const n = layers[l]
        const fx = (x / size) * n
        const fy = (y / size) * n
        const x0 = Math.floor(fx)
        const y0 = Math.floor(fy)
        const tx = fx - x0
        const ty = fy - y0
        const g = grids[l]
        const at = (a: number, b: number) => g[((b % n) * n + (a % n))]
        const sx = tx * tx * (3 - 2 * tx)
        const sy = ty * ty * (3 - 2 * ty)
        const top = at(x0, y0) * (1 - sx) + at(x0 + 1, y0) * sx
        const bot = at(x0, y0 + 1) * (1 - sx) + at(x0 + 1, y0 + 1) * sx
        v += (top * (1 - sy) + bot * sy) * amp
        amp *= 0.5
      }
      const c = Math.max(0, Math.min(255, (0.5 + (v / 0.9375 - 0.5) * contrast) * 255))
      const i = (y * size + x) * 4
      img.data[i] = img.data[i + 1] = img.data[i + 2] = c
      img.data[i + 3] = 255
    }
  }
  ctx.putImageData(img, 0, 0)
  const tex = new THREE.CanvasTexture(canvas)
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping
  return tex
}
