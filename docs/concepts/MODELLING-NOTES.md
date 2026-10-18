# ONSITE modelling handoff

These images are modelling references, not meshes, UV maps, rigged characters or ready-to-use texture maps. Front/side/back views reduce guesswork, but generated views still need reconciliation in 3D.

## Visual source of truth

- Jay and Alex are Black British adults. Use the new individual character sheets for their faces, hair and proportions. Keep their identities consistent in selection, kit, gameplay and cinematics.
- Keep ONSITE's condensed white type, amber selection colour, dark translucent panels and established menu positions. Implement UI as reusable components rather than baking screenshot text into the game.
- Clothes default to black. Masks and hood state are kit choices; character selection should show recognisable faces.
- Use the individual runner sheet for footwear: black athletic trainers, black soles, no logos or coloured accents. Use the individual plain jogger sheet for trousers; it takes precedence over cargo pockets in older concepts.
- Use the hoodie and balaclava sheets for garment construction. Match attachments to both character bodies; check hair/hood/mask clipping.

## Initial modelling targets

| Asset | Proposed scale | Construction approach |
| --- | --- | --- |
| Jay | 1.80 m | Separate body/head, hair and interchangeable kit; shared humanoid skeleton |
| Alex | 1.70 m | Preserve distinct face and hair; compatible animation naming and kit slots |
| Runner | Fit each foot | Separate left/right shoe meshes; model silhouette, bake small tread and mesh detail |
| Hoodie / joggers | Fit each body | Skinned clothing, clean elbow/knee topology; normal maps for small folds |
| Balaclava | Fit each head | Separate wearable mesh with eye aperture and hair visibility rules |
| Facade bay | 3 x 3 x 0.25 m | Grid-snapping wall module, recessed window, shared brick/concrete materials |
| Court fence | 2.5 x 3 m | Simple frame geometry; test alpha-masked mesh against geometric mesh at gameplay distance |

Dimensions are initial design targets, not measurements reconstructed from the images.

## From reference to Three.js

1. Block out the estate in metres and test player scale, collision, stairs and sightlines.
2. Model facade and fence modules first; reuse them with instancing where appropriate.
3. Model and UV the characters and independent clothing pieces. Reconcile seams and shapes across reference views before detailed work.
4. Rig and skin characters and kit. Check idle, walk, run, crouch and aim animations for clipping; create first-person hands separately.
5. Export GLB assets with sensible pivots, named materials and animation clips. Keep editable modelling source files alongside exports when created.
6. Test actual browser load time, memory, draw calls and frame time. Set final mesh/texture budgets from measured performance, then add LODs and texture compression as needed.

No 3D meshes or playable game have been produced by this reference-generation batch.
