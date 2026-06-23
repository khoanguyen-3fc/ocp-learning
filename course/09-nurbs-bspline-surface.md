# Unit 9 — NURBS Free-Form Surface

**Goal:** build a `Geom_BSplineSurface` by hand from a grid of control points.
This is how free-form, sculpted surfaces (turbine blades, car bodies, ship hulls)
are represented. It's the hardest _surface_ to build — but self-contained.

Difficulty: ⭐⭐⭐⭐

---

## The concept

A B-spline (NURBS when weighted) surface is a smooth sheet pulled toward a **grid
of control points** (called _poles_). You don't place the surface directly — you
place the poles, and the surface follows, like a rubber sheet attracted to pegs.

It's the 2D cousin of the `Geom_BSplineCurve` you built in
[Unit 5](05-curves-and-edges.md): same idea — poles, knots, multiplicities,
degree — but a grid instead of a row.

To define one you need, in **both** the U and V directions:

| Ingredient         | What it is                                                      |
| ------------------ | --------------------------------------------------------------- |
| **Poles**          | the control-point grid (`nu × nv` points)                       |
| **Degree**         | smoothness/order of the basis (degree 2 = quadratic, 3 = cubic) |
| **Knots**          | the distinct parameter values that segment the surface          |
| **Multiplicities** | how many times each knot repeats                                |
| **Periodic flags** | whether the surface wraps (usually `False`)                     |
| _(Weights)_        | optional, for true NURBS; omit for plain B-splines              |

## The one formula you must satisfy

For each direction, the counts must balance:

```
number_of_poles  +  degree  +  1  ==  sum(multiplicities)
```

Get this wrong and the constructor raises. For a small **3×3 grid, degree 2**, a
"clamped" surface uses knots `[0, 1]` with multiplicities `[3, 3]`:

```
poles(3) + degree(2) + 1 = 6   and   sum(3, 3) = 6   ✓
```

(High multiplicity at the ends "clamps" the surface so it touches the corner
poles — exactly like a Bézier patch here.)

## The pipeline

```python
from OCP.gp import gp_Pnt
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.TColStd import TColStd_Array1OfReal, TColStd_Array1OfInteger
from OCP.Geom import Geom_BSplineSurface
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace

import vis

nu, nv = 3, 3          # 3x3 control grid
udeg, vdeg = 2, 2      # quadratic in both directions

# --- Poles: a flat-ish grid with the center pole lifted into a bump. ---
# NOTE: OCCT arrays are 1-BASED. Indices run 1..nu and 1..nv.
poles = TColgp_Array2OfPnt(1, nu, 1, nv)
for i in range(1, nu + 1):
    for j in range(1, nv + 1):
        x = (i - 1) * 10.0
        y = (j - 1) * 10.0
        z = 8.0 if (i == 2 and j == 2) else 0.0   # lift the middle pole
        poles.SetValue(i, j, gp_Pnt(x, y, z))

# --- Knots + multiplicities (clamped): [0,1] with mults [3,3]. ---
uknots = TColStd_Array1OfReal(1, 2)
uknots.SetValue(1, 0.0)
uknots.SetValue(2, 1.0)
vknots = TColStd_Array1OfReal(1, 2)
vknots.SetValue(1, 0.0)
vknots.SetValue(2, 1.0)

umults = TColStd_Array1OfInteger(1, 2)
umults.SetValue(1, 3)   # poles(3) + deg(2) + 1 = 6 == 3 + 3
umults.SetValue(2, 3)
vmults = TColStd_Array1OfInteger(1, 2)
vmults.SetValue(1, 3)
vmults.SetValue(2, 3)

# --- Build the surface (non-rational: no weights). ---
surf = Geom_BSplineSurface(
    poles, uknots, vknots, umults, vmults, udeg, vdeg, False, False
)

# --- A B-spline already knows its U/V range, so the simple MakeFace works. ---
face = BRepBuilderAPI_MakeFace(surf, 1e-6).Face()

vis.show(face)
```

Run it: a 20×20 patch with a smooth bump pulled up by the center pole. Move that
center pole's `z` and re-run — the surface deforms smoothly. That's the whole
intuition.

## The typed arrays

Unlike Python lists, OCCT wants its own fixed-size, 1-based containers:

- `TColgp_Array2OfPnt(1, nu, 1, nv)` — 2D grid of `gp_Pnt` (the poles).
- `TColStd_Array1OfReal(1, n)` — 1D array of floats (knots).
- `TColStd_Array1OfInteger(1, n)` — 1D array of ints (multiplicities).

Fill them with `.SetValue(index, value)` — and **start at 1, end at n**.

## Gotchas (this is where the time goes)

- **1-based indexing.** `range(1, n + 1)`, and the array is declared `(1, n)`.
  Using 0 will raise an out-of-range error.
- **The balance formula** `poles + degree + 1 == sum(mults)`, _per direction_.
  Mentally check it before every build.
- **Degree must be `< number of poles`.** Degree 2 needs at least 3 poles.
- **Build it tiny first.** A 3×3 degree-2 patch is the smallest meaningful case.
  Only scale up the grid once that renders.
- **Weights (NURBS).** For true rational surfaces there's a constructor overload
  that takes a `TColStd_Array2OfReal` of weights right after the poles. Skip it
  until the non-rational version is solid.

## Exercises

1. Lift a **corner** pole instead of the center; see how the surface peaks there.
2. Make a **4×4, degree-3** patch. Recompute the knots/mults so the formula
   holds: `4 + 3 + 1 = 8`, so clamped knots `[0, 1]` with mults `[4, 4]`.
3. Deliberately break the formula (e.g. mults `[3, 2]`) and read the exception —
   learn to recognize it.
4. Make an **asymmetric** patch: degree 3 in U, degree 2 in V.

## Checkpoint

You can build a `Geom_BSplineSurface` from a pole grid, you can state the
knots/poles/degree balance formula from memory, and you remember arrays are
1-based.

**Next:** [Unit 10 — Blends / Fillets](10-blends.md) (stretch).
