"""Shared UV layout for the Heron Reach prop textures.

Rects are (u0, v0, u1, v1) in UV space with v measured upward from the bottom of
the image. The texture generator and the geometry builder both import this file,
so a label drawn into a rect is exactly where the mesh samples it.
"""

PROPS_DIR = "public/materials/heron/props"

# texture name -> (width, height, has_alpha, has_normal)
TEXTURES = {
    "cage_mesh": (1024, 1024, True, False),   # 1 UV = 1 m, 50 mm black weld mesh
    "wire_grid": (1024, 1024, True, False),   # 1 UV = 1 m, 50 mm galvanised wire
    "goal_net": (1024, 1024, True, False),    # 1 UV = 1 m, 100 mm knotted net
    "products": (2048, 2048, False, False),   # packaging atlas
    "shop": (1024, 1024, False, False),       # shop and office details
    "laundry": (1024, 1024, False, False),    # launderette control panels
    "notices": (1024, 1024, False, False),    # estate notice board posters
    "vehicle": (1024, 1024, False, False),    # plates, lamps, grille, wheels
    "litter": (1024, 1024, False, False),     # crisp packet, can, cardboard
    "mattress": (1024, 512, False, False),    # dumped mattress top
    "intercom": (512, 512, False, True),      # entry panel and key legends
    "cctv": (512, 512, False, False),         # worn beige housing paint, 0.25 m tile
    "manhole": (512, 512, False, True),       # cast cover pattern
    "vents": (512, 512, False, True),         # airbrick face
    "pegboard": (512, 512, False, False),     # 0.5 m tile
    "fabric": (512, 512, False, False),       # 0.5 m tile sofa fabric
    "estate_sign": (512, 384, False, False),  # 600 x 450 mm estate sign face, 0-1 UVs
}

# ---------------------------------------------------------------------------
# products atlas: 8 x 8 cells; row 0 is the TOP row of the image.
# ---------------------------------------------------------------------------
CELL = 1.0 / 8.0
PRODUCT_ROWS = {
    "tall": (0, 16, 0.70),    # cereal and carton fronts, aspect w/h
    "wide": (2, 8, 1.60),     # biscuit and tea boxes
    "bag": (3, 8, 0.80),      # crisp bag fronts
    "can": (4, 8, 1.80),      # can wraps (around / height)
    "bottle": (5, 8, None),   # whole bottle wrap: bands bottom to top
    "tin": (6, 8, None),      # whole tin or jar wrap
    "sack": (7, 4, 0.65),     # rice and flour sacks
    "scratch": (7, 2, 1.00),  # scratchcard dispenser fronts, cells 4-5
    "jug": (7, 2, None),      # detergent jugs, cells 6-7
}


def product_cell(category, index):
    row, count, _ = PRODUCT_ROWS[category]
    index %= count
    start = {"scratch": 4, "jug": 6}.get(category, 0)
    col = start + index
    r = row + col // 8
    c = col % 8
    u0 = c * CELL
    v1 = 1.0 - r * CELL
    return (u0, v1 - CELL, u0 + CELL, v1)


def product_rect(category, index):
    """Design region inside a cell, honouring the category aspect."""
    u0, v0, u1, v1 = product_cell(category, index)
    aspect = PRODUCT_ROWS[category][2]
    if aspect is None:
        return (u0, v0, u1, v1)
    w = u1 - u0
    pad = w * 0.04
    if aspect >= 1.0:
        dh = (w - 2 * pad) / aspect
        cv = (v0 + v1) / 2
        return (u0 + pad, cv - dh / 2, u1 - pad, cv + dh / 2)
    dw = (w - 2 * pad) * aspect
    cu = (u0 + u1) / 2
    return (cu - dw / 2, v0 + pad, cu + dw / 2, v1 - pad)


# ---------------------------------------------------------------------------
# other atlases
# ---------------------------------------------------------------------------
SHOP = {
    "price_strip": (0.0, 0.94, 1.0, 1.0),
    "cold_drinks": (0.0, 0.80, 0.6, 0.92),
    "till_screen": (0.62, 0.80, 0.80, 0.92),
    "card_reader": (0.82, 0.80, 0.90, 0.92),
    "counter_front": (0.0, 0.52, 1.0, 0.78),
    "monitor": (0.0, 0.34, 0.30, 0.50),
    "keyboard": (0.32, 0.34, 0.70, 0.50),
    "papers": (0.72, 0.34, 1.0, 0.50),
    "fridge_back": (0.0, 0.0, 0.25, 0.32),
    "phone": (0.27, 0.0, 0.40, 0.12),
    "cash_drawer": (0.42, 0.0, 0.62, 0.12),
}

LAUNDRY = {
    "washer_panel": (0.0, 0.75, 0.5, 1.0),
    "dryer_panel": (0.5, 0.75, 1.0, 1.0),
    "number": [(i * 0.125, 0.60, (i + 1) * 0.125, 0.72) for i in range(8)],
    "notice": (0.0, 0.30, 0.35, 0.58),
}

NOTICES = {
    "board": (0.0, 0.25, 1.0, 1.0),
    "header": (0.0, 0.08, 1.0, 0.22),
}

VEHICLE = {
    "plate_front": (0.0, 0.893, 0.5, 1.0),
    "plate_rear": (0.5, 0.893, 1.0, 1.0),
    "headlight": (0.0, 0.60, 0.40, 0.86),
    "taillight": (0.42, 0.60, 0.82, 0.86),
    "grille": (0.0, 0.36, 0.50, 0.58),
    "alloy": (0.50, 0.0, 1.0, 0.50),
    "steel_wheel": (0.0, 0.0, 0.34, 0.34),
    "van_lamp": (0.84, 0.60, 1.0, 0.86),
}

LITTER = {
    "crisp": (0.0, 0.5, 0.5, 1.0),
    "can": (0.5, 0.75, 1.0, 1.0),
    "can2": (0.5, 0.5, 1.0, 0.75),
    "cardboard": (0.0, 0.0, 0.5, 0.5),
    "cardboard2": (0.5, 0.0, 1.0, 0.5),
}

INTERCOM = {
    "plate": (0.0, 0.0, 0.5, 1.0),
    # 12 key legends, 3 columns x 4 rows, in the right half
    "keys": [
        (0.5 + c * (0.5 / 3), 1.0 - (r + 1) * 0.125, 0.5 + (c + 1) * (0.5 / 3), 1.0 - r * 0.125)
        for r in range(4) for c in range(3)
    ],
    "label": (0.5, 0.30, 1.0, 0.48),
    "metal": (0.5, 0.0, 1.0, 0.28),
}

VENTS = {"airbrick": (0.0, 0.35, 1.0, 1.0), "grime": (0.0, 0.0, 1.0, 0.33)}
MANHOLE = {"cover": (0.0, 0.0, 1.0, 1.0)}
