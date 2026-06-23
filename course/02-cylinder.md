# Unit 2 — Cylinder

**Goal:** render a cylindrical face, and internalize the single most important
idea about curved surfaces: **U is an angle, not a distance.**

Difficulty: ⭐⭐

---

## The concept

A cylindrical surface is "a circle of radius `r`, extruded along the frame's Z
axis, forever." Its parameter space:

- **U = angle around the axis**, in radians, `0 .. 2π` for a full loop.
- **V = height** along the axis (a distance).

So a full pipe of height 20 is the patch `U: 0..2π, V: 0..20`. A _half_ pipe is
`U: 0..π`. This is the first surface where the U/V bounds aren't both distances —
get this and cones/tori are easy.

## The pipeline

```python
import math
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3
from OCP.Geom import Geom_CylindricalSurface
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace

import vis

# 1. Frame: the Z axis is the cylinder's spine.
frame = gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))

# 2. Infinite cylinder, radius 5.
radius = 5.0
cyl = Geom_CylindricalSurface(frame, radius)

# 3. Bound it: U = full circle (0..2π), V = height 0..20.
face = BRepBuilderAPI_MakeFace(cyl, 0.0, 2 * math.pi, 0.0, 20.0, 1e-6).Face()

# 4. Render.
vis.show(face)
```

Run it: an open tube standing on the origin, 20 tall.

## Why "U = angle" matters

Try `U: 0..math.pi` instead of `0..2*math.pi`. You get a **half** pipe — a
trough. The U bound is sweeping the circle, not measuring length. If you ever see
a curved face come out as a thin sliver or the whole thing, it's almost always
because you mixed up radians vs. degrees, or a full vs. partial sweep.

## The seam (preview of Unit 6)

A full cylinder (`U: 0..2π`) is a **closed** surface — U wraps around and meets
itself. The line where it closes is called the **seam**. OCCT handles it for
analytic surfaces automatically here, but seams become important when you trim
with explicit boundary loops in [Unit 6](06-wires-and-trimming.md). Just file the word away
for now.

## Gotchas

- **Radians, always.** `2 * math.pi`, not `360`.
- **Frame axis = spine.** Tilt the cylinder by changing the frame's main
  direction to e.g. `gp_Dir(0, 1, 0)` — now it lies along Y.
- **V is signed.** `V: -10..10` centers the tube on the origin instead of having
  it grow upward from it.

## Exercises

1. Render a **quarter** pipe (`U: 0..π/2`).
2. Make a **fat short** cylinder: radius 20, height 3.
3. Lay the cylinder on its side (spine along X): set the main direction to
   `gp_Dir(1, 0, 0)` and pick a sensible X reference like `gp_Dir(0, 0, 1)`.
4. Predict the shape of `U: 0..2π, V: 0..0.001`, then check.

## Checkpoint

You can render full and partial cylinders, and you can explain why changing the
U upper bound changes how far around the tube goes.

**Next:** [Unit 3 — Cone](03-cone.md) — same idea, plus the half-angle gotcha.
