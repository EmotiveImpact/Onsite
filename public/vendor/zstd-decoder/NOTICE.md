# Zstandard decoder used by Three.js KTX2Loader

The unmodified `three@0.186.1/examples/jsm/libs/zstddec.module.js` dependency is bundled by Vite
when KTX2Loader is used. SHA-256:
`5cbf818e842628a4464e748594a6deae18ceddda3c2f541e7b3a0ff5fc7611e2`.

- JavaScript/WASM wrapper: [Don McCurdy / zstddec-wasm](https://github.com/donmccurdy/zstddec-wasm),
  MIT, copyright 2020 Don McCurdy. Complete licence in `WRAPPER-MIT.txt`; upstream licence blob
  `20f1e36127e99795e341229358d1d43d5bd8ec1d`.
- Embedded Zstandard decoder: [Meta Platforms / Zstandard](https://github.com/facebook/zstd),
  BSD licence. Complete notice in `ZSTD-BSD.txt`; upstream licence blob
  `75800288cc243f164b9d130f125e2ffae28f8e39`.

ONSITE does not modify either decoder. These notices supplement the existing Three.js and
Basis Universal notices rather than assigning Three.js's licence to every bundled component.
