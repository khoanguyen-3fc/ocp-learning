# Unit 4 — Torus

**Goal:** render a toroidal face (a donut), and cement parametric thinking:
**both U and V are angles** here.

Difficulty: ⭐⭐

---

## The concept

A torus is a circle (the _tube_, minor radius) swept around an axis (the _ring_,
major radius). It's defined by:

- a **frame** (`gp_Ax3`) — the axis is the donut's spindle, the origin its center,
- a **major radius** `R` — center of the ring to the center of the tube,
- a **minor radius** `r` — radius of the tube itself.

Parameter space — and this is the lesson — is **two angles**:

- **U = angle around the main axis** (going around the ring, `0 .. 2π`),
- **V = angle around the tube** (going around the cross-section, `0 .. 2π`).

No distances at all. A full donut is `U: 0..2π, V: 0..2π`.

## The pipeline

```python
import math
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3
from OCP.Geom import Geom_ToroidalSurface
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace

import vis

# 1. Frame: main axis is the donut's spindle.
frame = gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))

# 2. Torus: ring radius 10, tube radius 3.
major_radius = 10.0
minor_radius = 3.0
torus = Geom_ToroidalSurface(frame, major_radius, minor_radius)

# 3. Full donut: both U and V sweep a full circle.
face = BRepBuilderAPI_MakeFace(
    torus, 0.0, 2 * math.pi, 0.0, 2 * math.pi, 1e-6
).Face()

# 4. Render.
vis.show(face)
```

Run it: a donut lying flat in the XY plane.

## Playing with the two angles

- `U: 0..π, V: 0..2π` — **half the ring**: a C-shaped half-donut.
- `U: 0..2π, V: 0..π` — the **outer/top half of the tube** all the way around: a
  curved gutter.
- `U: 0..π/2, V: 0..π/2` — a small **patch** — a single quilted panel of the
  donut. This is the clearest way to _see_ that both axes are angular.

Render each and watch which way it cuts. This builds the intuition you'll need
when a real model gives you partial U/V ranges.

## Gotchas

- **Two angles, both radians.** If a result looks like a thin ribbon, you likely
  passed a distance where an angle was expected.
- **`r < R` for a normal donut.** If `minor_radius >= major_radius` you get a
  self-intersecting "spindle/horn" torus — valid geometry, but it looks odd and
  meshes strangely. Keep `r < R` while learning.
- The torus is **closed in both directions**, so it has **two seams** (one in U,
  one in V). Same note as the cylinder — relevant once you trim in Unit 6.

## Exercises

1. Make a **fat** donut (`R=10, r=8`) and a **thin ring** (`R=10, r=1`).
2. Render a quarter-ring with a half-tube: `U: 0..π/2, V: 0..π`.
3. Stand the donut up on its edge by changing the main direction to
   `gp_Dir(0, 1, 0)`.
4. Deliberately set `r > R` and observe the self-intersection.

## Checkpoint

You can render full and partial tori and explain why both U and V are angles.
You've now covered **all four analytic surfaces** — the first major milestone.

**Next:** [Unit 5 — Curves & Edges](05-curves-and-edges.md) — the building blocks
that bound every face.
