# Unit 1 — Plane

**Goal:** build and render your first face from scratch, and understand the
**U/V bounds** that turn an infinite surface into a finite patch.

Difficulty: ⭐

---

## The concept

A plane is the simplest surface: a flat, infinite sheet defined by one frame
(`gp_Ax3`). To see it, we cut a rectangle out of it using **U/V parameters**.

Every surface has a 2D parameter space (U, V). For a plane, U and V are just
**distances** along the frame's X and Y axes. So `MakeFace(plane, -10, 10, -10,
10, tol)` means "the patch from X=-10..10, Y=-10..10."

## The pipeline

```python
import math
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3
from OCP.Geom import Geom_Plane
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace

import vis

# 1. Frame: origin at 0, normal pointing up (+Z), X reference along +X.
frame = gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))

# 2. Infinite surface.
plane = Geom_Plane(frame)

# 3. Cut a finite patch: U from -10..10, V from -10..10, build tolerance 1e-6.
face = BRepBuilderAPI_MakeFace(plane, -10.0, 10.0, -10.0, 10.0, 1e-6).Face()

# 4. Render.
vis.show(face)
```

Run it: a flat square floating in the XY plane.

## What each piece does

- `Geom_Plane(frame)` — the infinite surface. Its normal is the frame's main
  direction (`gp_Dir(0,0,1)` here).
- `BRepBuilderAPI_MakeFace(surface, umin, umax, vmin, vmax, tol)` — the workhorse
  you'll use in every analytic unit. The four numbers are the parameter-space
  bounds; `tol` is a tiny build tolerance (`1e-6` is fine).
- `.Face()` — pulls the finished `TopoDS_Face` out of the builder.

> **Pattern alert:** `BRepBuilderAPI_MakeFace(...)` returns a _builder_. You call
> `.Face()` (or `.Shape()`) to get the actual topology. Forgetting `.Face()` is
> a classic first mistake.

## Gotchas

- **Builder vs. result.** `mk = BRepBuilderAPI_MakeFace(...)` then `mk.Face()`.
  You can check `mk.IsDone()` before extracting if you want to be defensive.
- **The normal direction comes from the frame.** Flip `gp_Dir(0,0,1)` to
  `gp_Dir(0,0,-1)` and the face's "front" flips. This matters later for
  lighting/orientation but not for seeing the shape now.

## Exercises

1. Make a **non-square** patch: U from 0..30, V from -5..5.
2. **Tilt** the plane: change the normal to `gp_Dir(0, 1, 1)` (it gets
   normalized automatically). Watch the square tilt.
3. **Move** it: set the origin to `gp_Pnt(50, 0, 0)`.
4. Predict, then verify: what happens if `umin > umax`?

## Checkpoint

You rendered a face, you can change its size/position/orientation, and you know
that `MakeFace`'s four numbers are U/V parameter bounds.

**Next:** [Unit 2 — Cylinder](02-cylinder.md) — where U stops being a distance
and becomes an angle.
