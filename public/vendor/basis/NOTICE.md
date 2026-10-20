# Basis Universal transcoder

Unmodified `basis_transcoder.js` and `basis_transcoder.wasm`, copied from the installed
`three@0.186.1` package's `examples/jsm/libs/basis/` directory. Its README identifies the
transcoder as **Apache-2.0**: <https://github.com/BinomialLLC/basis_universal>.
The complete licence is included alongside these files. Retrieved licence Git blob:
`94ea880430871f065fc4d9aef92fb5854003bd01` (BinomialLLC/basis_universal/LICENSE).

SHA-256:

- JS: `8478b5b6d6b74e7d3082b89f6417321d8d1dc0307f2b30d4484bb11b441696a1`
- WASM: `6cf17dc889352c42e9acf8897107978d127005fe3386c36a0e3845e27967630a`
- Licence: `065fcf48d6af21c0b75e23be5ed5753aee75c892e1c2cf178fa6736305614a5c`

The Three.js KTX2Loader is used from the existing MIT-licensed Three.js dependency. It selects
the renderer's supported block-compressed format. ONSITE retains WebP for software rendering,
unsupported compression formats and individual KTX2 decode/load failures.
