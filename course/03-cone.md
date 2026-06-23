# Unit 3 — Cone

**Goal:** render a conical face, and handle the one thing that bites everyone:
the cone is defined by a **half-angle in radians**.

Difficulty: ⭐⭐

---

## The concept

A conical surface is like a cylinder whose radius grows as you move along the
axis. It's defined by:

- a **frame** (`gp_Ax3`) — the axis is the cone's spine,
- a **half-angle** — the angle between the axis and the cone's slanted side,
- a **reference radius** — the radius at the frame's origin (the V=0 plane).

Parameter space is just like the cylinder:

- **U = angle around the axis** (`0 .. 2π`),
- **V = distance along the cone's _slanted side_** (the generating line), **not**
  the axis — as V grows, the point climbs the slope, so the height _and_ the
  radius increase together. (Axial rise is `V·cos(half_angle)`; the radius grows
  by `V·sin(half_angle)`.)

## The pipeline

```python
import math
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3
from OCP.Geom import Geom_ConicalSurface
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace

import vis

# 1. Frame.
frame = gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))

# 2. Cone: half-angle 30°, radius 5 at the base plane (V=0).
half_angle = math.radians(30)   # MUST be radians, and strictly 0 < a < π/2
ref_radius = 5.0
cone = Geom_ConicalSurface(frame, half_angle, ref_radius)

# 3. Bound it: full sweep, V from 0..15 (radius grows over this range).
face = BRepBuilderAPI_MakeFace(cone, 0.0, 2 * math.pi, 0.0, 15.0, 1e-6).Face()

# 4. Render.
vis.show(face)
```

Run it: a tapering funnel, radius 5 at the bottom, wider as it rises.

## The half-angle gotcha

`Geom_ConicalSurface(frame, ang, radius)` wants `ang` as a **half-angle in
radians**, and it must be strictly between `0` and `π/2`.

- Have **degrees**? `math.radians(deg)`.
- Have a **sin/cos** of the half-angle (common in CAD dumps)? Recover the angle
  with `math.atan2(sin_half, cos_half)`:

  ```python
  half_angle = math.atan2(sin_half_angle, cos_half_angle)
  ```

- A half-angle of 0 is a cylinder (use Unit 2); `π/2` is a plane. Both are
  invalid as a cone and will raise.

## Which way does it taper?

The radius grows in the direction of increasing V (the frame's main direction).
To make a cone that _narrows_ as it goes up, either:

- use a negative V range (`V: -15..0`), or
- flip the frame's main direction to `gp_Dir(0, 0, -1)`.

Experiment until the taper direction is intuitive.

## Gotchas

- **Radians, and `0 < angle < π/2`.** The most common error in this unit.
- **`ref_radius` is the radius at V=0**, not the tip. The tip (apex) is wherever
  the radius would reach 0.
- Set `ref_radius = 0` and `V: 0..15` to start the cone exactly at a sharp apex.

## Exercises

1. Make a **steep** cone (half-angle 60°) and a **shallow** one (10°).
2. Reproduce a cone defined by `sin_half = 0.707107, cos_half = 0.707107` using
   `atan2` (you should get 45°).
3. Render only a **wedge**: `U: 0..π/3`.
4. Build a cone that comes to a point: `ref_radius = 0`.

## Checkpoint

You can render a cone, convert any angle representation into the radians OCCT
wants, and control which direction it tapers.

**Next:** [Unit 4 — Torus](04-torus.md) — where _both_ U and V become angles.
