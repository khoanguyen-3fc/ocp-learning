# Unit 7 — Pcurves & Curved Trimming

**Goal:** the real-part unlock. A **plane** can be trimmed by a 3D wire
directly — but a **cylinder/cone/torus/NURBS** can't. A curved surface needs a
**pcurve**: the boundary expressed in the surface's own (U, V) parameter space,
attached to each edge. Build a trimmed cylindrical face, prove it triangulates.

Difficulty: ⭐⭐⭐⭐

---

## The concept

In Unit 6 you cut a _plane_ with a wire of 3D edges, and it just worked. The
reason: OCCT can always project a 3D curve straight down onto a plane —
unambiguously and stably. There's exactly one answer.

On a **curved** surface there isn't. Projecting a 3D curve onto a cylinder is
ambiguous (which way did the curve wrap?) and numerically fragile. So OCCT
refuses to guess. Instead, each boundary edge must carry a **pcurve** — a 2D
`Geom2d` curve living directly in the surface's (U, V) parameter space:

```
3D world (x,y,z)          parameter space (u,v)
  the real curve   <--->   the pcurve (Geom2d)
                  surface
```

For a `Geom_CylindricalSurface` the parameter space is **not** two lengths:

- **U is an ANGLE in RADIANS** around the axis,
- **V is a height/length** along the axis.

So a "rectangle" in (U, V) is really an _angular band_ crossed with a _height
band_ — a curved window cut out of the cylinder wall.

The plan: define a closed trimming loop **directly in (U, V)** with 2D segments,
build each edge so it _carries_ its pcurve, make the face, then synthesize the
missing 3D curves and repair.

## The pipeline

```python
"""
Unit: Pcurves & Curved Trimming  ("the real-part unlock")

A PLANE can be trimmed by a 3D wire alone -- OCCT can always project a 3D
curve onto a plane unambiguously. A CURVED surface (cylinder, cone, torus,
NURBS) cannot: projecting a 3D curve onto it is ambiguous and unstable.
The fix is a PCURVE -- the boundary expressed directly in the surface's own
(u,v) parameter space, attached to each edge. On a cylinder, u is the angle
around the axis (radians) and v is the height along the axis.

This script builds a trimmed cylindrical face three ways and shows it.

Run from the repo root:
    PYTHONPATH=. .venv/bin/python this_file.py
"""

import vis

from OCP.gp import gp_Ax3, gp_Pnt, gp_Dir, gp_Pnt2d
from OCP.Geom import Geom_CylindricalSurface
from OCP.GCE2d import GCE2d_MakeSegment
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
)
from OCP.BRepLib import BRepLib
from OCP.ShapeFix import ShapeFix_Face, ShapeFix_Shape
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
from OCP.TopoDS import TopoDS_Compound

# ---------------------------------------------------------------------------
# The underlying surface: an infinite cylinder of radius 10 about the Z axis.
# Its parameter space is (u, v) = (angle in RADIANS, height along axis).
# ---------------------------------------------------------------------------
RADIUS = 10.0
cylinder = Geom_CylindricalSurface(gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), RADIUS)


def segment2d(p1, p2):
    """A straight Geom2d curve segment in (u,v) space, from p1 to p2."""
    # GCE2d_MakeSegment.Value() returns a Geom2d_TrimmedCurve already trimmed
    # to [first, last]; we read those params back when we build the edge.
    return GCE2d_MakeSegment(p1, p2).Value()


def face_from_uv_loop(corners):
    """
    Build a trimmed cylindrical FACE from a closed loop of (u,v) corners.

    For each side of the loop we:
      1. make a 2D segment in parameter space (the PCURVE),
      2. build an edge with MakeEdge(pcurve, surface, u1, u2) so the edge
         CARRIES that pcurve -- this is the curved-surface trimming workhorse,
      3. add the edges to a wire.
    Then we make the face from (surface, wire), generate the missing 3D
    curves from the pcurves, and run the standard repair passes.
    """
    wire_maker = BRepBuilderAPI_MakeWire()
    for i in range(len(corners)):
        pcurve = segment2d(corners[i], corners[(i + 1) % len(corners)])
        # MakeEdge(curve2d, surface, u1, u2): the edge lives in (u,v) on the
        # surface. u1/u2 are the pcurve's own parameter range.
        edge = BRepBuilderAPI_MakeEdge(
            pcurve, cylinder, pcurve.FirstParameter(), pcurve.LastParameter()
        ).Edge()
        wire_maker.Add(edge)
    wire = wire_maker.Wire()

    # Make the face: the wire (given in uv) trims the cylinder.
    # The third arg True asks OCC to take the wire as the outer bound.
    face = BRepBuilderAPI_MakeFace(cylinder, wire, True).Face()

    # Each edge so far has ONLY a pcurve (a "NO_CURVE"-style edge -- no 3D
    # geometry yet). BuildCurves3d_s synthesizes the 3D curve of every edge by
    # mapping its pcurve through the surface. After this the edges carry BOTH
    # representations (the "SP_CURVE" idea: surface-pcurve plus 3D curve).
    BRepLib.BuildCurves3d_s(face)

    # Repair: fix wire order/orientation on the face, then heal the whole shape.
    fix_face = ShapeFix_Face(face)
    fix_face.Perform()
    face = fix_face.Face()
    fix_shape = ShapeFix_Shape(face)
    fix_shape.Perform()
    return fix_shape.Shape()


# --- Case 1: an axis-aligned rectangular "window" in (u,v) ------------------
# u from 0.5 to 2.0 rad (a ~86 degree arc), v from 2 to 12 (height band).
rect_face = face_from_uv_loop(
    [
        gp_Pnt2d(0.5, 2.0),
        gp_Pnt2d(2.0, 2.0),
        gp_Pnt2d(2.0, 12.0),
        gp_Pnt2d(0.5, 12.0),
    ]
)

# --- Case 2: a slanted (parallelogram) loop in (u,v) ------------------------
# The loop need not be axis-aligned -- any closed Geom2d loop trims the surface.
slanted_face = face_from_uv_loop(
    [
        gp_Pnt2d(0.6, 3.0),
        gp_Pnt2d(2.2, 5.0),
        gp_Pnt2d(2.0, 13.0),
        gp_Pnt2d(0.4, 11.0),
    ]
)

# --- Bonus: attach a pcurve to an EXISTING edge with BRep_Builder -----------
# Sometimes you already have a face/edge and just need to (re)attach the
# parameter-space curve. BRep_Builder.UpdateEdge(edge, curve2d, face, tol)
# stores a pcurve onto an edge for a given face directly.
builder = BRep_Builder()
explorer = TopExp_Explorer(rect_face, TopAbs_EDGE)
first_edge = TopoDS.Edge_s(explorer.Current())
# A fresh pcurve matching this edge's uv span, re-attached for the face.
extra_pcurve = segment2d(gp_Pnt2d(0.5, 2.0), gp_Pnt2d(2.0, 2.0))
builder.UpdateEdge(first_edge, extra_pcurve, TopoDS.Face_s(rect_face), 1e-7)
# Read it back to confirm the pcurve is now stored on the edge for this face.
recovered = BRep_Tool.CurveOnSurface_s(first_edge, TopoDS.Face_s(rect_face), 0.0, 0.0)
assert recovered is not None  # the pcurve round-tripped

# ---------------------------------------------------------------------------
# Show both trimmed CURVED faces side by side in one compound.
# ---------------------------------------------------------------------------
compound = TopoDS_Compound()
builder.MakeCompound(compound)
builder.Add(compound, rect_face)
builder.Add(compound, slanted_face)

vis.show(compound)
```

Run it: two curved patches cut out of the same cylinder wall — one a clean
angular-by-height window, one a slanted parallelogram. Both are genuinely
trimmed _curved_ faces, not flat polygons.

## What each piece does

- **`Geom_CylindricalSurface(gp_Ax3(...), RADIUS)`** — the infinite cylinder.
  Remember: its (U, V) is (angle in radians, height). Everything 2D below lives
  in _that_ space, not in millimeters-by-millimeters.
- **`GCE2d_MakeSegment(p1, p2).Value()`** — a straight 2D segment in (U, V),
  i.e. one pcurve. `.Value()` hands you a `Geom2d_TrimmedCurve` already trimmed
  to its own `[FirstParameter, LastParameter]`.
- **`BRepBuilderAPI_MakeEdge(curve2d, surface, u1, u2)`** — the curved-trimming
  workhorse. This builds an edge that lives **in parameter space on the
  surface**. Pass the pcurve's own `FirstParameter()`/`LastParameter()` as
  `u1, u2`. At this moment the edge has a pcurve but **no 3D curve yet**.
- **`BRepBuilderAPI_MakeFace(surface, wire, True)`** — trims the cylinder by the
  (U, V) wire. The `True` takes the wire as the outer bound.
- **`BRepLib.BuildCurves3d_s(face)`** — the key step. It walks the face and
  synthesizes the missing **3D curve** of every edge by mapping its pcurve
  through the surface. Without this the edges are pcurve-only and the face won't
  triangulate.
- **`ShapeFix_Face` / `ShapeFix_Shape`** — the usual healing passes: fix wire
  order/orientation, then clean up the whole shape. `ShapeFix_Shape.Shape()`
  returns a generic `TopoDS_Shape`, so down-cast with `TopoDS.Face_s(...)` /
  `TopoDS.Edge_s(...)` before any API that demands a concrete subtype. (These and
  `BuildCurves3d_s` are catalogued in [Appendix B](16-appendix-repair-toolbox.md).)

### Two pcurve / 3D-curve states

This is the mental model that unlocks curved trimming in real models. (The labels
**SP_CURVE** and **NO_CURVE** below name the two edge states — they are _not_
OpenCASCADE API names. CAD exchange formats like STEP carry the same distinction
— a 2D curve-on-surface vs. a 3D curve on an edge; in OCCT an edge simply carries
a pcurve, a 3D curve, or both, queried with `BRep_Tool.CurveOnSurface_s` and
`BRep_Tool.Curve_s`.)

- **Before `BuildCurves3d_s`** the edge holds _only_ a pcurve — there is no 3D
  geometry attached. Think of this as a **pcurve-only / NO_CURVE** edge: it
  exists purely in the surface's parameter space.
- **After `BuildCurves3d_s`** the same edge holds **both** a pcurve _and_ the
  synthesized 3D curve. The pcurve and 3D curve coexist — the **SP_CURVE**
  ("surface-pcurve") situation: an edge with a curve-on-surface plus its 3D
  representation.

Curved B-rep faces in production models lean on exactly this: every boundary
edge of a trimmed cylinder/cone/torus carries a pcurve, and most also carry the
3D curve. When one is missing, `BuildCurves3d_s` (3D from pcurve) or
`ShapeFix` is how you restore it.

### Attaching a pcurve to an existing edge

The bonus block shows the other direction: you already have an edge and a face,
and you want to _store_ a pcurve onto it. That's
`BRep_Builder.UpdateEdge(edge, curve2d, face, tol)`. Read it back with
`BRep_Tool.CurveOnSurface_s(edge, face, First, Last)` to confirm the round-trip.

## Gotchas

- **It's `BuildCurves3d_s` — trailing `_s`, plural "Curves."** That static
  helper does the whole face. Don't confuse it with the singular
  `BuildCurve3d_s` (one edge) or `BuildPCurveForEdgeOnPlane_s` (a different job
  entirely).
- **Cylinder (U, V) are not both lengths.** U is an **angle in RADIANS** around
  the axis; V is a height along the axis. A (U, V) "rectangle" is an angular band
  crossed with a height band, _not_ a flat square.
- **Use the pcurve's own parameter range, not `0..1`.**
  `GCE2d_MakeSegment(p1, p2).Value()` returns a `Geom2d_TrimmedCurve` already
  trimmed to `[FirstParameter, LastParameter]`. Pass exactly those into
  `MakeEdge(curve2d, surface, u1, u2)`. Hard-coding `0.0, 1.0` is wrong.
- **No `.IsNull()` on the recovered pcurve.** OCP auto-unwraps OCCT handles, so
  `BRep_Tool.CurveOnSurface_s(...)` returns a `Geom2d_TrimmedCurve` _directly_.
  It has no `.IsNull()` method — check `is not None` instead.
- **`CurveOnSurface_s` needs the First/Last args.** It's overloaded; the form
  that returns the pcurve is `CurveOnSurface_s(edge, face, First, Last)`. Omit
  the two trailing floats (e.g. `0.0, 0.0`) and you get a `TypeError` about
  incompatible arguments.
- **`UpdateEdge` has 9 overloads.** The pcurve-on-face one is
  `UpdateEdge(edge, Geom2d_Curve, TopoDS_Face, tol)`. Pass a real `TopoDS_Face`
  (use `TopoDS.Face_s(shape)` after `ShapeFix` hands you a generic
  `TopoDS_Shape`), or you'll match the wrong overload.
- **Down-cast after `ShapeFix`.** `ShapeFix_Face.Face()` and
  `ShapeFix_Shape.Shape()` return healed shapes; the latter is a generic
  `TopoDS_Shape`. Use `TopoDS.Face_s` / `TopoDS.Edge_s` before subtype-specific
  APIs.
- **Small triangle counts are fine.** On a small trimmed patch
  `vis.triangulate` meshes at deflection 0.1 and yields only tens of points
  (≈62 / ≈68 here). The success signal is **points > 0**, not a big number.

## Exercises

1. **Verify it triangulates.** Replace the final `vis.show(compound)` with a
   headless check and confirm both faces mesh to more than zero points:
   ```python
   for name, f in [("rect", rect_face), ("slanted", slanted_face)]:
       pts, cells = vis.triangulate(f)
       print(name, pts.GetNumberOfPoints())
       assert pts.GetNumberOfPoints() > 0
   ```
2. **Widen the angular band.** In Case 1 push U from `0.5..2.0` to `0.0..3.14`
   (about half the cylinder). Watch the patch wrap further around.
3. **Make it taller.** Change V from `2..12` to `-20..20` and see the height band
   grow.
4. **Break it on purpose.** Comment out the `BRepLib.BuildCurves3d_s(face)` line
   and re-run Exercise 1. Watch the triangulation collapse — this is what a
   pcurve-only (NO_CURVE) face does without its 3D curves.
5. **Re-attach by hand.** Pull a second edge with the `TopExp_Explorer`, build a
   matching pcurve for it, `UpdateEdge` it onto `rect_face`, and read it back
   with `CurveOnSurface_s`.

## Checkpoint

You can trim a _curved_ surface: define a closed loop in the surface's (U, V)
space, build edges that carry their pcurves with
`MakeEdge(curve2d, surface, u1, u2)`, make the face, synthesize the 3D curves
with `BRepLib.BuildCurves3d_s`, and heal with `ShapeFix`. You can attach a
pcurve to an existing edge with `BRep_Builder.UpdateEdge` and read it back, and
you understand the pcurve-only (NO_CURVE) vs. pcurve+3D (SP_CURVE) edge states.

**Next:** [Unit 8 — Intersection Edges](08-intersection-edges.md)
