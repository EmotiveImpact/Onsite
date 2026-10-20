# Poly Haven scanned details — Heron Reach

Two independently checked CC0 assets are used in the additive
`/models/heron-reach/heron-reach-scanned.glb` dressing model. They add two flush
manhole covers and four individual fluorescent strips. They add no lights,
collision geometry, navigation data or gameplay code.

| Asset | Creator | Original source | Licence |
| --- | --- | --- | --- |
| Water Manhole Cover | Raunox | https://polyhaven.com/a/water_manhole_cover | [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) |
| Mounted Fluorescent Lights | Ulan Cabanilla | https://polyhaven.com/a/mounted_fluorescent_lights | [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) |

Original author metadata was checked at `https://api.polyhaven.com/info/<asset_id>`
on 19 October 2026. [Poly Haven's asset licence](https://polyhaven.com/license)
explicitly covers its models and textures under CC0. Attribution is supplied for
provenance even though CC0 does not require it.

The imported source files are the simplified, embedded-WebP derivatives in
[IRONLINE](https://github.com/cktang88/3d-fps), pinned at
`130ac2a5c856401ec36e7d35afcfefe40c5801f4`, under
`public/assets/models/props/<asset_id>/<asset_id>.glb`. IRONLINE's README credits
these models individually to Poly Haven. The project's package licence is not
being used as asset permission.

The unmodified donor files are preserved outside the delivered web directory:

```text
assets/reference/polyhaven-scanned/water_manhole_cover.glb
SHA-256 04f305364c9e0ffcff0ba453f02c41de91bf1ab1b84bfcb904f695eb465be0f3

assets/reference/polyhaven-scanned/mounted_fluorescent_lights.glb
SHA-256 8852f9cad1005d4a01f29d98e2af4508f93abfec927cc43e09e134d76f4052ad
```

ONSITE modifications: retain metre scale, original UVs, normals and PBR maps;
embed the manhole frame so its highest relief is 18.5 mm above the existing ground;
extract the first complete fluorescent variant from the source's seven-variant
catalogue; duplicate this individual strip at two shop ceiling positions and two
northern upper-gallery soffits; enable
its original emissive mask at strength 1.4; bake the world placements; export
embedded WebP textures and meshopt-compressed geometry. All textures remain with
their original scanned surfaces. No military model, weapon or animation is included.

The two gallery strips are centred at map x52/x61,z38.1, with top y5.81 m,
embedded 10 mm into the verified y5.8 slab underside. Minimum head clearance is
2.77486 m above the y3 gallery floor. The east fixture is moved from the initial
x60 proposal to x61 so it clears the S2 core wall and has full slab support.

The editable Blender 4.3.2 scene is
`assets/blender/heron-reach/scanned-detail.blend`. Its companion
`scanned-detail-manifest.json` records the builder, source and output hashes,
individual source dimensions, selected fixture bounds, exact placements and
compression-tool revision/hash.

```text
Runtime heron-reach-scanned.glb: 499,580 bytes; 2,484 authored triangles
SHA-256 9b59f1d1cc0132d4eceb3fe279db57647a1014dd2a441d6d42fe9d50a1f61029

Editable scanned-detail.blend: 601,775 bytes
SHA-256 155667c668088efd225a49f91a8fc806ea558a0fb518dc2e5ef4d452d6a97943
```
