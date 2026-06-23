# Unit 5 — Curves & Edges

**Goal:** build _every_ boundary-curve type these parts use — lines, arcs,
ellipses, B-splines, trimmed curves — and turn each one into a `TopoDS_Edge`.

Difficulty: ⭐⭐⭐

---

## The concept

A face is bounded by a _wire_ — a closed loop of edges — which you'll assemble in
the next unit. First you need the vocabulary: what exactly _is_ an edge? Here is
the answer, and it is the through-line for this whole unit:

```
edge  =  a curve (the geometry/shape)  +  a parameter range (where it starts & stops)
```

A curve is infinite or full-length on its own. An **edge** pins it down to a
piece. OpenCASCADE gives you two layers of curve:

- `gp_*` — lightweight **analytic primitives**: `gp_Lin`, `gp_Circ`, `gp_Elips`.
  Cheap, math-only, no endpoints.
- `Geom_*` — full **curve objects**: `Geom_Line`, `Geom_Circle`,
  `Geom_Ellipse`, `Geom_BSplineCurve`, `Geom_TrimmedCurve`. These are what edges
  actually reference.

The one tool that turns any of these into an edge is
`BRepBuilderAPI_MakeEdge`. It is heavily overloaded; the four forms worth
memorizing are:

```
MakeEdge(p1, p2)           two points       -> straight edge (the shortcut)
MakeEdge(curve)            a whole curve    -> edge over the curve's full range
MakeEdge(curve, u1, u2)    curve + params   -> edge trimmed by PARAMETER (radians for arcs!)
MakeEdge(curve, p1, p2)    curve + points   -> edge trimmed by POINTS on the curve
```

## The pipeline

```python
"""
Curves & Edges
===============
An EDGE is the marriage of two things:

        edge  =  a curve (the geometry/shape)  +  a parameter range (where it starts & stops)

OpenCASCADE gives you two layers:
  * gp_*    -> lightweight analytic primitives (gp_Lin, gp_Circ, gp_Elips)
  * Geom_*  -> full curve objects (Geom_Line, Geom_Circle, Geom_Ellipse,
               Geom_BSplineCurve, Geom_TrimmedCurve)

BRepBuilderAPI_MakeEdge is the universal "turn this into a topological edge" tool.
It is heavily overloaded; the four forms worth memorizing are:

    MakeEdge(p1, p2)            two points        -> straight edge (the shortcut)
    MakeEdge(curve)             a whole curve     -> edge over the curve's full range
    MakeEdge(curve, u1, u2)    curve + params    -> edge trimmed by PARAMETER  (radians for arcs!)
    MakeEdge(curve, p1, p2)    curve + points    -> edge trimmed by POINTS on the curve

Run from the repo root:
    PYTHONPATH=. .venv/bin/python this_file.py
"""
import math

# pylint: disable=no-name-in-module
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Lin, gp_Circ, gp_Elips
from OCP.Geom import (
    Geom_Line, Geom_Circle, Geom_Ellipse, Geom_BSplineCurve, Geom_TrimmedCurve,
)
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.TColStd import TColStd_Array1OfReal, TColStd_Array1OfInteger
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace,
)
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
# pylint: enable=no-name-in-module

import vis


# ---------------------------------------------------------------------------
# 1. STRAIGHT LINE
# ---------------------------------------------------------------------------
p1 = gp_Pnt(0, 0, 0)
p2 = gp_Pnt(10, 0, 0)

# The shortcut: two points is all you need for a straight edge.
line_from_points = BRepBuilderAPI_MakeEdge(p1, p2).Edge()

# The explicit way: gp_Lin is an INFINITE line (a point + a direction).
# It has no endpoints, so we MUST hand MakeEdge a parameter range to bound it.
# For a line the parameter equals arc length from the base point.
lin = gp_Lin(p1, gp_Dir(1, 0, 0))
line_from_gp = BRepBuilderAPI_MakeEdge(lin, 0.0, 10.0).Edge()

# Geom_Line is the same idea as a full Geom_ curve object.
geom_line = Geom_Line(p1, gp_Dir(1, 0, 0))
line_from_geom = BRepBuilderAPI_MakeEdge(geom_line, 0.0, 10.0).Edge()


# ---------------------------------------------------------------------------
# 2. CIRCLE and circular ARC
# ---------------------------------------------------------------------------
# gp_Ax2 = a local coordinate system: an origin (the circle CENTER) plus the
# axis normal to the circle's plane. Build the analytic circle, then wrap it
# in a Geom_Circle so it can drive edges in every form.
axis = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))     # center at origin, lies in XY plane
circ = gp_Circ(axis, 5.0)                            # radius 5
geom_circle = Geom_Circle(circ)

# Full circle: just the curve, no range -> uses the curve's natural 0..2pi.
full_circle = BRepBuilderAPI_MakeEdge(geom_circle).Edge()

# Arc by PARAMETER. For a circle the parameter is the angle in RADIANS.
# 0 -> pi/2 is a quarter arc.
arc_by_params = BRepBuilderAPI_MakeEdge(geom_circle, 0.0, math.pi / 2).Edge()

# Arc by POINTS that lie on the circle. OCCT finds the parameters for you.
pa = gp_Pnt(5, 0, 0)   # at angle 0
pb = gp_Pnt(0, 5, 0)   # at angle pi/2
arc_by_points = BRepBuilderAPI_MakeEdge(geom_circle, pa, pb).Edge()


# ---------------------------------------------------------------------------
# 3. ELLIPSE  (real parts often have ellipse edges)
# ---------------------------------------------------------------------------
# Same gp_Ax2 placement, but now a major and a minor radius.
elips = gp_Elips(axis, 8.0, 4.0)                     # major 8, minor 4
geom_ellipse = Geom_Ellipse(elips)

full_ellipse = BRepBuilderAPI_MakeEdge(geom_ellipse).Edge()
half_ellipse = BRepBuilderAPI_MakeEdge(geom_ellipse, 0.0, math.pi).Edge()  # params in radians


# ---------------------------------------------------------------------------
# 4. NURBS / B-spline curve  (Geom_BSplineCurve)  -- B_SPLINE_CURVE in STEP
# ---------------------------------------------------------------------------
# A B-spline curve is the 1D analog of a NURBS surface. It needs:
#   * poles (control points), a 1D TColgp_Array1OfPnt
#   * knots + their multiplicities (how the parameter is partitioned)
#   * a degree
#
# THE BALANCE FORMULA that must hold:
#       n_poles + degree + 1 == sum(multiplicities)
#
# A "clamped" curve passes through its first and last poles; you get that by
# giving the two END knots a multiplicity of (degree + 1).
#
# REMEMBER: OCCT arrays are 1-BASED -- indices run 1..N, not 0..N-1.
degree = 3

poles = TColgp_Array1OfPnt(1, 5)                     # five control points, indices 1..5
poles.SetValue(1, gp_Pnt(0, 0, 0))
poles.SetValue(2, gp_Pnt(2, 4, 0))
poles.SetValue(3, gp_Pnt(5, 5, 0))
poles.SetValue(4, gp_Pnt(8, 4, 0))
poles.SetValue(5, gp_Pnt(10, 0, 0))

knots = TColStd_Array1OfReal(1, 3)                   # three distinct knot values
knots.SetValue(1, 0.0)
knots.SetValue(2, 0.5)
knots.SetValue(3, 1.0)

mults = TColStd_Array1OfInteger(1, 3)
mults.SetValue(1, degree + 1)                        # 4 -> clamp the start
mults.SetValue(2, 1)                                 # 1 -> interior knot
mults.SetValue(3, degree + 1)                        # 4 -> clamp the end

# Check the balance:  5 + 3 + 1 == 4 + 1 + 4 == 9  ✓
assert poles.Length() + degree + 1 == sum(
    mults.Value(i) for i in range(1, mults.Length() + 1)
)

bspline = Geom_BSplineCurve(poles, knots, mults, degree)
bspline_edge = BRepBuilderAPI_MakeEdge(bspline).Edge()


# ---------------------------------------------------------------------------
# 5. TRIMMED CURVE  (Geom_TrimmedCurve)  -- TRIMMED_CURVE in STEP
# ---------------------------------------------------------------------------
# Geom_TrimmedCurve wraps a basis curve and a [u1, u2] range, producing a new
# curve that only exists over that range. Angles are in RADIANS.
trimmed = Geom_TrimmedCurve(geom_circle, 0.0, math.pi / 2)
edge_from_trimmed_curve = BRepBuilderAPI_MakeEdge(trimmed).Edge()

# The edge-level equivalent: instead of trimming the CURVE first, you can trim
# at the EDGE with MakeEdge(curve, u1, u2). Same resulting quarter-arc edge.
edge_trimmed_at_edge = BRepBuilderAPI_MakeEdge(geom_circle, 0.0, math.pi / 2).Edge()


# ---------------------------------------------------------------------------
# Visualize. vis only renders FACES, so to actually SEE a curve we close the
# full circle edge into a wire and cap it with a planar face. The bare edges
# are added to the compound too (they carry the real curve geometry we built).
# ---------------------------------------------------------------------------
circle_wire = BRepBuilderAPI_MakeWire(full_circle).Wire()
circle_face = BRepBuilderAPI_MakeFace(circle_wire, True).Face()

builder = BRep_Builder()
compound = TopoDS_Compound()
builder.MakeCompound(compound)
for edge in (line_from_points, full_ellipse, bspline_edge,
             arc_by_params, edge_from_trimmed_curve):
    builder.Add(compound, edge)
builder.Add(compound, circle_face)   # the face is what you'll actually see shaded

vis.show(compound)
```

Run it from the repo root with `PYTHONPATH=. .venv/bin/python this_file.py`.
You'll see the capped circle shaded, with the other edges drawn as wireframe.

## What each piece does

Walk it section by section — each is one curve family, each ends in a
`TopoDS_Edge`.

- **Straight line (§1).** Three ways to the same edge. `MakeEdge(p1, p2)` is the
  shortcut. `gp_Lin(point, dir)` is an _infinite_ line, so you must supply a
  parameter range `(0.0, 10.0)`; for a line the parameter is just arc length
  from the base point. `Geom_Line` is the heavyweight version of the same idea.
- **Circle & arc (§2).** `gp_Ax2(center, normal)` places the circle: the origin
  is the **center**, the direction is the **normal** to the circle's plane.
  `gp_Circ(axis, 5.0)` adds the radius; `Geom_Circle` wraps it so it can drive
  edges. `MakeEdge(geom_circle)` with no range gives the full 0..2π circle.
  `MakeEdge(curve, 0.0, math.pi/2)` trims by **parameter** (radians) to a
  quarter arc. `MakeEdge(curve, pa, pb)` trims by **points** that lie on the
  circle — OCCT finds the parameters for you.
- **Ellipse (§3).** Identical placement, but `gp_Elips(axis, 8.0, 4.0)` takes a
  major and a minor radius. `Geom_Ellipse` wraps it; `0..math.pi` (radians) is
  the half-ellipse.
- **B-spline / NURBS curve (§4).** The 1D analog of a NURBS surface. It needs
  **poles** (a 1D `TColgp_Array1OfPnt`), **knots** (`TColStd_Array1OfReal`),
  **multiplicities** (`TColStd_Array1OfInteger`), and a **degree**. The balance
  formula `n_poles + degree + 1 == sum(mults)` must hold or the constructor
  raises. Multiplicity `degree + 1` on the two end knots **clamps** the curve so
  it passes through its first and last poles. All arrays are **1-based**.
- **Trimmed curve (§5).** `Geom_TrimmedCurve(basis, u1, u2)` makes a _new curve_
  that only exists over `[u1, u2]`. `MakeEdge(trimmed)` and
  `MakeEdge(geom_circle, u1, u2)` produce the same quarter-arc edge — one trims
  the curve, the other trims at the edge.

> **Pattern alert:** `BRepBuilderAPI_MakeEdge(...)` returns a _builder_, not an
> edge. Call `.Edge()` to get the `TopoDS_Edge` (and `.IsDone()` first if you
> want to be defensive). Same shape as `MakeFace(...).Face()` from Unit 1.

## Gotchas

- **OCCT arrays are 1-based.** `TColgp_Array1OfPnt(1, 5)` has indices `1..5`;
  read and write them with `SetValue(i, ...)` / `Value(i)`. Passing `0` raises
  an out-of-range error.
- **Arc/ellipse trim parameters are radians, not degrees.** `MakeEdge(curve,
u1, u2)` and `Geom_TrimmedCurve(curve, u1, u2)` take **angles in radians** for
  circles and ellipses. `0..math.pi/2` is a quarter circle; `0..90` would sweep
  the curve dozens of times around.
- **`gp_Lin` / `gp_Circ` / `gp_Elips` are infinite or full curves.** They have
  no endpoints. `MakeEdge(gp_Lin)` alone is unbounded — you must supply
  `(u1, u2)` or two points to get a finite edge.
- **The B-spline balance is strict.** `n_poles + degree + 1 == sum(mults)`. For
  a clamped curve the two **end** knots get multiplicity `degree + 1`. Get it
  wrong and `Geom_BSplineCurve(...)` raises on construction.
- **`MakeEdge` is a builder, not a function.** Construct it, then call `.Edge()`
  (optionally `.IsDone()` first). It does not return an edge directly.
- **`vis` only renders FACES.** `vis.show` / `vis.triangulate` walk
  `TopAbs_FACE` triangulation. A bare edge or wire produces **zero** mesh points
  and renders nothing. To _see_ a curve, close it into a wire and cap it with a
  face (`BRepBuilderAPI_MakeFace`) — that's why the example builds a
  `circle_face`. The line, ellipse, and B-spline edges show up only as the
  compound's wireframe.
- **`gp_Ax2(origin, dir)` places a curve by center + normal.** The origin is the
  circle/ellipse **center**, the direction is the **normal** to its plane — not
  a point on the curve.
- **Compounds need `BRep_Builder`.** Call `builder.MakeCompound(comp)` _first_,
  then `builder.Add(comp, shape)` once per member.

## Exercises

1. Change the quarter arc `arc_by_params` to a **three-quarter** arc
   (`0.0` to `3 * math.pi / 2`). Predict the angle, then confirm it's not the
   small arc.
2. Move the circle's center off the origin (e.g. `gp_Pnt(20, 0, 0)`) by editing
   the `gp_Ax2`, and watch every circle/arc/trimmed edge follow.
3. Add a **sixth pole** to the B-spline. Recompute the knots/multiplicities so
   the balance formula still holds (hint: bump an interior knot's multiplicity,
   or add another knot), then rebuild.
4. Break the balance on purpose — set one end knot to multiplicity `degree`
   instead of `degree + 1` — and read the error.
5. Cap the **half-ellipse** into a face (close it with a straight edge across its
   ends, build a wire, then `MakeFace`) so `vis.show` shades it.

## Checkpoint

You can build every boundary-curve type these parts use — line, circle, arc,
ellipse, B-spline, trimmed curve — and turn each into a `TopoDS_Edge` through the
four `MakeEdge` forms. You internalized **edge = curve + parameter range**, you
know arc parameters are radians, you know the B-spline balance formula, and you
know why a bare edge renders nothing.

**Next:** [Unit 6 — Wires & Trimming](06-wires-and-trimming.md)
