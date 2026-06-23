# Unit 8 — Intersection Edges

**Goal:** handle edges that have **no closed form** — the seam where a turbine
blade meets a hub, the boundary of a fillet — by asking the kernel to compute
the curve where two surfaces cross.

Difficulty: ⭐⭐⭐⭐⭐

---

## The concept

Up to now every edge came from a curve you could type in: a `Geom_Line`, a
`Geom_Circle`. But many real edges are **intersection edges**. They are wherever
two surfaces meet, and that curve usually has no name and no formula you can
write by hand.

The classic examples are mechanical seams: where a blade fairs into a hub, or
where a rounded blend runs out onto a flat. You can't construct those edges —
you have to **compute** them from the two surfaces that produce them.

The tool is `GeomAPI_IntSS` — *Int*ersection of *S*urface and *S*urface. You
hand it two `Geom` surfaces and a tolerance; it hands you back one or more
`Geom_Curve`s, which you then turn into real edges.

## The pipeline

```python
"""
Unit: Intersection Edges
========================
Some edges in a B-rep have NO closed form. The seam where a turbine blade meets
the hub, or the boundary of a fillet/blend, is the curve where two surfaces
cross. There is no "circle" or "line" you can type in -- you have to ASK the
kernel to compute the intersection.

The tool for that is GeomAPI_IntSS  (Int-Surface-Surface).

Run from the repo root:
    PYTHONPATH=. .venv/bin/python intersection_edges.py
"""

from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3
from OCP.Geom import Geom_CylindricalSurface, Geom_Plane
from OCP.GeomAPI import GeomAPI_IntSS
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder

import vis

# ---------------------------------------------------------------------------
# 1. Two surfaces that genuinely cross.
#    A cylinder (axis = Z, radius 5) and a horizontal plane at height z = 2.
#    Their intersection is a circle -- but we never had to know that. The
#    kernel will discover it for us.
# ---------------------------------------------------------------------------
cylinder = Geom_CylindricalSurface(gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), 5.0)
plane = Geom_Plane(gp_Pnt(0, 0, 2), gp_Dir(0, 0, 1))

# ---------------------------------------------------------------------------
# 2. Compute the intersection. The third argument is a tolerance (model units).
#    1e-7 is a good default for a clean, analytic intersection.
# ---------------------------------------------------------------------------
intersector = GeomAPI_IntSS(cylinder, plane, 1.0e-7)

# ALWAYS check IsDone() before trusting the result.
assert intersector.IsDone(), "intersection failed"

# NbLines() = how many separate intersection curves were found.
# (Two cylinders crossing at right angles, for example, yields several.)
print(f"Found {intersector.NbLines()} intersection curve(s)")

# ---------------------------------------------------------------------------
# 3. Pull each intersection curve out as a Geom_Curve and turn it into a real
#    topological edge with BRepBuilderAPI_MakeEdge.
#    NOTE: OCCT line indices are 1-BASED, so we count from 1.
# ---------------------------------------------------------------------------
builder = BRep_Builder()
compound = TopoDS_Compound()
builder.MakeCompound(compound)

# A bounded patch of the plane so there is a surface to look at in the viewer.
host_face = BRepBuilderAPI_MakeFace(plane.Pln(), -8, 8, -8, 8).Face()
builder.Add(compound, host_face)

for i in range(1, intersector.NbLines() + 1):
    curve = intersector.Line(i)              # a Geom_Curve (here a trimmed circle)
    edge = BRepBuilderAPI_MakeEdge(curve).Edge()
    builder.Add(compound, edge)
    print(f"  built edge for intersection line {i}")

# ===========================================================================
# PRACTICAL GUIDANCE
# ===========================================================================
# * In a REAL exported model you almost never call GeomAPI_IntSS yourself.
#   The file already stores a PCURVE for each edge (see Unit 7) -- the edge's
#   parametric track on its face -- so you trim with that stored pcurve
#   instead of recomputing the intersection from scratch. Recomputation is the
#   fallback for when geometry is missing, not the normal path.
#
# * NO_CURVE edges: an edge can have ONLY a pcurve (a 2D track on a surface)
#   and NO 3D curve. BRep_Tool.Curve_s returns nothing for it, and naive code
#   crashes. The fix is exactly Unit 7's BRepLib.BuildCurves3d_s(shape), which
#   rebuilds the missing 3D curves from the pcurves.
#
# * Robust rendering: never let one bad face kill the whole model. Wrap each
#   face's build/triangulate in try/except, SKIP failures, and keep going.
#   The loop below prints a per-face OK/FAILED report.

faces = {"plane_patch": host_face, "deliberately_broken": None}
for name, face in faces.items():
    try:
        if face is None:
            raise ValueError("missing/unbuildable geometry")
        points, _ = vis.triangulate(face)
        assert points.GetNumberOfPoints() > 0
        print(f"[OK]     {name}")
    except Exception as exc:  # keep rendering the rest of the model
        print(f"[FAILED] {name}: {exc}")

# ---------------------------------------------------------------------------
# 4. Show the host face plus the computed intersection edge(s).
# ---------------------------------------------------------------------------
vis.show(compound)
```

Run it: a flat square patch with a **circle** drawn on it where the cylinder
pierces the plane — a curve you never typed in.

## What each piece does

- `Geom_CylindricalSurface(gp_Ax3(...), 5.0)` and `Geom_Plane(point, normal)` —
  two ordinary `Geom` surfaces, exactly the kind you built in Units 1–4. These
  are the _handles_ `GeomAPI_IntSS` wants, not faces.
- `GeomAPI_IntSS(surf1, surf2, tol)` — the intersector. The third argument is a
  numeric tolerance in model units; `1e-7` is right for clean analytic surfaces.
- `intersector.IsDone()` — **check this first.** A failed intersection that you
  query anyway returns garbage.
- `intersector.NbLines()` — how many separate curves were found. Cylinder +
  plane gives one. Two cylinders crossing gives **several** (seven, in one
  probe).
- `intersector.Line(i)` — the _i_-th curve as a `Geom_Curve` (here concretely a
  trimmed circle). **Indices are 1-based**, so iterate `range(1, NbLines()+1)`.
- `BRepBuilderAPI_MakeEdge(curve).Edge()` — turns a computed `Geom_Curve` into a
  real `TopoDS_Edge`, same builder you met in Unit 5.
- `plane.Pln()` then `BRepBuilderAPI_MakeFace(pln, -8, 8, -8, 8)` — a bounded
  patch of the plane so there's an actual surface to look at; a bare edge has
  nothing to mesh.
- `BRep_Builder` + `TopoDS_Compound` — `MakeCompound(comp)` once, then
  `Add(comp, shape)` per face/edge to bundle everything into one shape to show.

## Why you usually _don't_ call this yourself

This is the important part. In a real exported model (STEP, etc.), the
intersection edges have **already been computed** by the CAD system and stored.
Each edge carries a **pcurve** — its track in the face's (U, V) parameter space,
the thing you met in Unit 7. The normal workflow is to trim using that stored
pcurve, not to recompute the intersection from the two surfaces.

`GeomAPI_IntSS` is the **fallback** for when that geometry is missing or you're
constructing something from scratch — not the everyday path.

### NO_CURVE edges

A related trap: an edge can have **only a pcurve and no 3D curve**. Then
`BRep_Tool.Curve_s` returns nothing, and naive code that assumes a 3D curve
crashes. The fix is exactly Unit 7's `BRepLib.BuildCurves3d_s(shape)`, which
rebuilds the missing 3D curves from the pcurves the file _does_ have.

### Render robustly: skip, don't crash

When you process many faces, one unbuildable face should not kill the render.
Wrap each face in `try/except`, skip the failures, keep going, and print a
per-face report. The pipeline's `faces` loop does exactly this: it triangulates
the good patch and reports `[OK]`, while the deliberately broken entry reports
`[FAILED]` instead of taking the whole program down.

Note that you must triangulate a **face**, not a bare edge: `vis.triangulate`
only meshes `TopAbs_FACE`, so an edge alone yields 0 points.

## Gotchas

- **`IsDone()` before everything.** Call it before `NbLines()` or `Line(i)`. A
  failed intersection queried anyway gives you junk, not an error.
- **1-based indices.** `NbLines()` / `Line(i)` count from 1. Looping from 0
  silently skips the first curve or errors. Use `range(1, NbLines()+1)`.
- **Surfaces, not faces.** `GeomAPI_IntSS` takes `Geom` surface handles
  (`Geom_CylindricalSurface`, `Geom_Plane`, …), not `TopoDS_Face`s.
- **Tolerance is in model units.** `1e-7` suits clean analytic surfaces. Messy
  or real-world intersections may need a looser value.
- **`Line(i)` is a `Geom_Curve`** (concretely a `Geom_TrimmedCurve` here), which
  `BRepBuilderAPI_MakeEdge(curve).Edge()` accepts directly — no conversion.
- **One clean curve vs. many.** Cylinder + plane → a single curve (the easy
  teaching case). Two cylinders crossing → many curves; your loop must handle
  `NbLines() > 1`.
- **A bare edge won't render.** `vis.triangulate(edge)` gives 0 points; the
  renderer only meshes faces. Put a host face in the compound to see anything.
- **`Geom_Plane.Pln()`** returns the `gp_Pln` that
  `BRepBuilderAPI_MakeFace(pln, umin, umax, vmin, vmax)` needs for a bounded,
  viewable patch.
- **Compounds need `BRep_Builder`.** `MakeCompound(comp)` first, then
  `Add(comp, shape)` for each member.
- **`IntSS` vs `IntCS`.** `GeomAPI_IntSS` is surface/surface. `GeomAPI_IntCS`
  intersects a curve with a surface — different tool, same family.

## Exercises

1. Raise the plane to `z = 6`. Because the `Geom` cylinder is **infinite** along
   its axis, any horizontal plane still cuts it — confirm `NbLines()` is unchanged
   and the intersection circle still has radius 5.
2. Replace the plane with a **second cylinder** whose axis is along X, radius 4,
   passing through the origin. Print `NbLines()` — expect more than one curve —
   and build an edge for each.
3. Tilt the plane's normal to `gp_Dir(0, 1, 1)`. The intersection is now an
   **ellipse**. Confirm `IsDone()` is still true and one curve comes back.
4. Add a third entry to the `faces` dict that builds correctly, and a second
   broken one, then read the `[OK]` / `[FAILED]` report.
5. Try a plane that **misses** the cylinder entirely (e.g. move it far off-axis
   so it never crosses the radius-5 wall). What does `NbLines()` return?

## Checkpoint

You can compute an edge that has no closed form: feed two surfaces to
`GeomAPI_IntSS`, check `IsDone()`, walk `Line(i)` from 1 to `NbLines()`, and
`MakeEdge` each curve. You know the everyday path is the **stored pcurve**
(Unit 7), that missing 3D curves are repaired with `BRepLib.BuildCurves3d_s`,
and that a robust renderer skips bad faces and reports per-face status.

**Next:** [Unit 9 — NURBS Free-Form Surface](09-nurbs-bspline-surface.md)
