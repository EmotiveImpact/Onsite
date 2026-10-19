"""Shared atlas layouts for the Heron Reach foliage kit.

Both the texture generator (make_heron_foliage_textures.py) and the Blender builder
(make_heron_foliage.py) import this module, so the card UVs always match what was drawn.

Rectangles are in pixels on a 1024 x 1024 image, origin at the top-left corner:
(x, y, w, h). `pivot` is where the twig or petiole enters the card, as a fraction of
the cell (0..1, 0..1) with y measured downwards. Cards are built so that this pivot
sits on the twig in 3D.
"""

SIZE = 1024

# Plane, birch and shrub atlases share one layout: three cluster cells and four singles.
CLUSTER_LAYOUT = {
    "cluster": [
        {"rect": (0, 0, 512, 512), "pivot": (0.5, 0.98)},
        {"rect": (512, 0, 512, 512), "pivot": (0.5, 0.98)},
        {"rect": (0, 512, 512, 512), "pivot": (0.5, 0.98)},
    ],
    "single": [
        {"rect": (512, 512, 256, 256), "pivot": (0.5, 0.97)},
        {"rect": (768, 512, 256, 256), "pivot": (0.5, 0.97)},
        {"rect": (512, 768, 256, 256), "pivot": (0.5, 0.97)},
        {"rect": (768, 768, 256, 256), "pivot": (0.5, 0.97)},
    ],
}

# Hedge atlas: two sprig cells, an opaque inner-foliage tile for the hidden core, four singles.
HEDGE_LAYOUT = {
    "cluster": [
        {"rect": (0, 0, 512, 512), "pivot": (0.5, 0.98)},
        {"rect": (512, 0, 512, 512), "pivot": (0.5, 0.98)},
    ],
    "core": {"rect": (0, 512, 512, 512)},
    "single": [
        {"rect": (512, 512, 256, 256), "pivot": (0.5, 0.97)},
        {"rect": (768, 512, 256, 256), "pivot": (0.5, 0.97)},
        {"rect": (512, 768, 256, 256), "pivot": (0.5, 0.97)},
        {"rect": (768, 768, 256, 256), "pivot": (0.5, 0.97)},
    ],
}

# Grass atlas: twelve full-height blade columns, then two tuft cards on the right.
GRASS_COLUMNS = [{"rect": (i * 64, 0, 64, 1024)} for i in range(12)]
GRASS_TUFTS = [
    {"rect": (768, 0, 256, 512), "pivot": (0.5, 1.0)},
    {"rect": (768, 512, 256, 512), "pivot": (0.5, 1.0)},
]

# Weeds atlas.
WEED_LAYOUT = {
    # four dandelion leaves, base at the bottom of each strip
    "dandelion": [{"rect": (i * 128, 0, 128, 512), "pivot": (0.5, 1.0)} for i in range(4)],
    # four broad plantain-type leaves
    "plantain": [{"rect": (512 + i * 128, 0, 128, 512), "pivot": (0.5, 1.0)} for i in range(4)],
    # side-view grassy crack weed with seed heads
    "crack": {"rect": (0, 512, 512, 512), "pivot": (0.5, 1.0)},
    # side-view herb sprig (groundsel type) with a small yellow flower
    "herb": {"rect": (512, 512, 512, 512), "pivot": (0.5, 1.0)},
}

# Leaf litter atlas: a 4 x 4 grid of fallen leaves, pivot at the cell centre.
LITTER_CELLS = [
    {"rect": (c * 256, r * 256, 256, 256), "pivot": (0.5, 0.5), "kind": ("plane" if (r * 4 + c) < 9 else "birch")}
    for r in range(4)
    for c in range(4)
]


def rect_uv(rect, fx, fy):
    """Return the UV (u, v) for a fractional point (fx, fy) inside a pixel rectangle.

    fx runs left to right, fy runs top to bottom (image convention). Blender UVs have
    v = 0 at the bottom of the image.
    """
    x, y, w, h = rect
    u = (x + fx * w) / SIZE
    v = 1.0 - (y + fy * h) / SIZE
    return (u, v)
