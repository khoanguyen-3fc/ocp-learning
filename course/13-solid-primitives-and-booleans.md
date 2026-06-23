# Unit 13 — Solid Primitives & Booleans

**Goal:** the other half of solid modeling. Instead of sewing faces by hand
(Unit 12), make ready-built **primitive solids** in one call, then combine them
with **boolean operations** — union, difference, intersection.

Difficulty: ⭐⭐⭐

---

## The concept

Unit 12 built a solid the _hard_ way — face by face. Most solid modeling instead
starts from **primitives** (box, cylinder, sphere, cone) and combines them with
**booleans**:

| Operation    | OCP class            | Meaning                      |
| ------------ | -------------------- | ---------------------------- |
| Union        | `BRepAlgoAPI_Fuse`   | everything in A **or** B     |
| Difference   | `BRepAlgoAPI_Cut`    | A **minus** B (drill a hole) |
| Intersection | `BRepAlgoAPI_Common` | only what's in A **and** B   |

This is how real parts get their shape: start with stock, cut pockets and holes,
fuse on bosses. (`hello.py` already used one primitive — `BRepPrimAPI_MakeCylinder`.)

## The pipeline

```python
from OCP.gp import gp_Pnt
from OCP.BRepPrimAPI import (
    BRepPrimAPI_MakeBox,
    BRepPrimAPI_MakeCylinder,
    BRepPrimAPI_MakeSphere,
)
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

import vis


def volume(shape):
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return props.Mass()


# --- Primitives are valid solids straight away ------------------------------
box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Solid()       # corner at origin
cyl = BRepPrimAPI_MakeCylinder(5.0, 20.0).Solid()         # radius 5, height 20
sph = BRepPrimAPI_MakeSphere(5.0).Solid()                 # radius 5
print("box volume   :", volume(box))                      # 1000.0
print("cyl volume   :", volume(cyl))                      # ~1570.8

# --- Booleans combine two solids --------------------------------------------
# Two 10-cubes, the second offset by (5,5,5) so they overlap in a 5-cube.
a = BRepPrimAPI_MakeBox(gp_Pnt(0, 0, 0), 10.0, 10.0, 10.0).Shape()
b = BRepPrimAPI_MakeBox(gp_Pnt(5, 5, 5), 10.0, 10.0, 10.0).Shape()

fused  = BRepAlgoAPI_Fuse(a, b).Shape()      # union
cut    = BRepAlgoAPI_Cut(a, b).Shape()       # a minus b
common = BRepAlgoAPI_Common(a, b).Shape()    # intersection (a 5-cube => 125)

for name, solid in (("fuse", fused), ("cut", cut), ("common", common)):
    print(f"{name:7s} valid={BRepCheck_Analyzer(solid).IsValid()}  volume={volume(solid):.1f}")

# Show the cut result: box a with a corner bitten out by box b.
vis.show(cut)
```

Run it: the printed volumes are `fuse 1875.0`, `cut 875.0`, `common 125.0`
(the overlap is a 5×5×5 = 125 cube), and the window shows box `a` with a corner
removed. Each boolean result is itself a valid solid you can feed into the next
operation.

## What each piece does

- **`BRepPrimAPI_MakeBox / MakeCylinder / MakeSphere`** — parametric primitive
  builders. `.Solid()` returns a ready, valid `TopoDS_Solid`; `.Shape()` returns
  it as a generic shape (what the boolean APIs accept). `MakeBox(dx, dy, dz)`
  sits at the origin; `MakeBox(gp_Pnt, dx, dy, dz)` places a corner.
- **`BRepAlgoAPI_Fuse / Cut / Common(a, b)`** — the boolean engine. `.Shape()`
  gives the resulting solid. Order matters for `Cut`: `Cut(a, b)` is "a with b
  removed," not the reverse.
- **`BRepCheck_Analyzer(...).IsValid()` and `BRepGProp` volume** — the same
  validity and volume checks from Unit 12. Booleans can occasionally produce
  invalid results on degenerate input, so verifying still pays off.

## Gotchas

- **Booleans want solids, not faces.** Feed `BRepAlgoAPI_*` closed solids
  (primitives, or your sewn solids from Unit 12). Open shells give garbage.
- **`Cut(a, b)` is ordered.** It's `a − b`. Swap the arguments and you get a
  different (often empty) result.
- **Disjoint inputs.** `Common` of two solids that don't overlap is _empty_; its
  volume is 0 and there may be nothing to show. `Fuse` of disjoint solids is a
  valid compound-like solid of two lumps.
- **`.Shape()` vs `.Solid()`.** Primitive builders offer both; boolean builders
  offer `.Shape()`. Mixing them up is a common `TypeError`.
- **Re-validate after booleans.** Chaining many booleans can accumulate tiny
  invalidities; run `BRepCheck_Analyzer` (and `ShapeFix` if needed) on the result.

## Exercises

1. **Drill a hole.** `Cut` a `MakeCylinder(2, 10)` out of `MakeBox(10,10,10)` and
   confirm the volume drops by `π·2²·10`.
2. **Chain booleans.** Fuse box+cylinder, then cut a sphere from the result.
   Check `IsValid()` at each step.
3. **Disjoint `Common`.** Move box `b` far away so the boxes don't touch; print
   the `common` volume (expect 0).
4. **Compare paths.** Build a 10-cube two ways — `MakeBox` (this unit) and the
   six-face sew (Unit 12) — and confirm both report volume `1000.0`.

## Checkpoint

You can create primitive solids in one call and combine them with union,
difference, and intersection — the everyday solid-modeling workflow — and you
keep validating with `BRepCheck_Analyzer` and `BRepGProp`. Together with Unit 12
you can build solids both _bottom-up_ (sew faces) and _top-down_ (primitives +
booleans).

**Next:** [Unit 14 — Capstone — Render a Complete Model](14-capstone.md)
