# Unit 14 — Capstone — Render a Complete Model

**Goal:** tie _everything_ together. Build one hand-coded, synthetic model that
exercises every technique a real part needs — analytic faces, a
trimmed curved face, a NURBS patch, a surface–surface intersection edge, **and a
watertight solid** — driven by a **robust per-face loop** that logs and skips
failures, then sew, solidify, and render the result.

Difficulty: ⭐⭐⭐⭐⭐

---

## The concept

A real CAD part is a **bag of faces** (plus edges), and where the faces close up
they bound a **solid** — the same recipes you have practiced for thirteen units:

```
Face   =  Geom surface  (+ optional trimming Wire of pcurves)
Edge   =  a 3D curve, sometimes recovered from an intersection
Shell  =  faces sewn along shared edges
Solid  =  the volume bounded by a closed shell
Part   =  many faces/solids dropped into a compound
```

Every technique in the course maps onto one piece:

| Piece                                  | Technique                                                          | Unit  |
| -------------------------------------- | ------------------------------------------------------------------ | ----- |
| analytic faces (cylinder, cone, plane) | `Geom_CylindricalSurface` / `Geom_ConicalSurface` / `Geom_Plane`   | 1–4   |
| a trimmed **curved** face              | a wire of **pcurves** laid on a surface                            | 7     |
| a free-form patch                      | `Geom_BSplineSurface` (NURBS)                                      | 9     |
| a surface–surface edge                 | `GeomAPI_IntSS`                                                    | 8     |
| a watertight **solid**                 | sew faces → shell → `BRepBuilderAPI_MakeSolid` (+ validity/volume) | 12    |
| build it without crashing              | `try/except` per face, log + skip                                  | 8, 11 |
| stitch + show                          | `BRepBuilderAPI_Sewing` → `TopoDS_Compound` → `vis.show`           | 11    |

This capstone builds all of them from **invented numbers** — no file is read.
The only thing a real importer adds on top is a data reader; the geometry
construction is exactly what you see below.

## The pipeline

```python
"""
Capstone — Render a Complete Model
============================================
This unit ties together every technique the course has covered into ONE
hand-coded, synthetic model (no file parsing, all numbers invented):

  * analytic faces        -> Geom_CylindricalSurface / Geom_ConicalSurface / Geom_Plane   (Units 1-4)
  * a trimmed CURVED face -> a wire of pcurves laid on a surface                            (Unit 7)
  * a NURBS patch         -> Geom_BSplineSurface                                            (Unit 9)
  * a surface-surface edge-> GeomAPI_IntSS                                                  (Unit 8)
  * a watertight SOLID    -> sew faces -> shell -> BRepBuilderAPI_MakeSolid                 (Unit 12)

We drive the build with a ROBUST per-face loop: each face is a (name, builder)
spec built inside try/except. A failing face is logged and skipped, never
fatal -- exactly how a real dump of a messy CAD part marks bad faces. Good
faces are sewn (BRepBuilderAPI_Sewing) into a shell, dropped into a
TopoDS_Compound alongside the intersection edge and the solid, and shown.

Copy this block into capstone.py at the repo root, then run:
    PYTHONPATH=. .venv/bin/python capstone.py
"""
import math

import vis

from OCP.gp import (
    gp_Pnt, gp_Dir, gp_Ax2, gp_Ax3, gp_Pln, gp_Circ, gp_Pnt2d, gp_Dir2d,
)
from OCP.Geom import (
    Geom_CylindricalSurface,
    Geom_ConicalSurface,
    Geom_Plane,
    Geom_BSplineSurface,
)
from OCP.Geom2d import Geom2d_Line
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.TColStd import TColStd_Array1OfReal, TColStd_Array1OfInteger
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_Sewing,
    BRepBuilderAPI_MakeSolid,
)
from OCP.BRepLib import BRepLib
from OCP.BRep import BRep_Builder
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.ShapeFix import ShapeFix_Solid
from OCP.TopoDS import TopoDS, TopoDS_Compound
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopExp import TopExp_Explorer
from OCP.GeomAPI import GeomAPI_IntSS


# --------------------------------------------------------------------------
# FACE BUILDERS  -- each returns a TopoDS_Face
# Remember: angles passed to Geom constructors are in RADIANS, and every
# OCCT array (poles, knots, mults) is 1-BASED.
# --------------------------------------------------------------------------

def build_cylinder():
    """Unit 1-4: an analytic cylindrical face, half a tube, 10 tall."""
    ax = gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))
    surf = Geom_CylindricalSurface(ax, 5.0)               # radius 5
    # u (angle, RADIANS) in [0, pi]; v (height) in [0, 10]
    return BRepBuilderAPI_MakeFace(surf, 0.0, math.pi, 0.0, 10.0, 1e-6).Face()


def build_cone():
    """Unit 1-4: an analytic conical face. Half-angle is in RADIANS."""
    ax = gp_Ax3(gp_Pnt(0, 0, 12), gp_Dir(0, 0, 1))
    surf = Geom_ConicalSurface(ax, math.radians(20.0), 5.0)  # 20deg, ref radius 5
    return BRepBuilderAPI_MakeFace(surf, 0.0, math.pi, 0.0, 6.0, 1e-6).Face()


def build_plane():
    """Unit 1-4: a flat analytic face from a gp_Pln."""
    pln = gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0))
    return BRepBuilderAPI_MakeFace(pln, -5.0, 5.0, -5.0, 5.0).Face()


def build_trimmed_pcurve_face():
    """Unit 7: a CURVED face trimmed by a wire defined in (u,v) parameter
    space. Each edge carries a 2D pcurve (Geom2d_Line) that lives ON the
    surface; BRepLib.BuildCurves3d_s then materialises the matching 3D
    curves so the face can be meshed."""
    ax = gp_Ax3(gp_Pnt(20, 0, 0), gp_Dir(0, 0, 1))
    surf = Geom_CylindricalSurface(ax, 4.0)

    # Closed loop of corners in (u,v): a curved "window" on the cylinder.
    corners = [(0.2, 0.0), (2.0, 0.0), (2.0, 5.0), (0.2, 5.0)]
    mk_wire = BRepBuilderAPI_MakeWire()
    n = len(corners)
    for i in range(n):
        u0, v0 = corners[i]
        u1, v1 = corners[(i + 1) % n]
        # pcurve = a 2D line in parameter space from corner i to corner i+1
        direction = gp_Dir2d(u1 - u0, v1 - v0)
        pcurve = Geom2d_Line(gp_Pnt2d(u0, v0), direction)
        length = math.hypot(u1 - u0, v1 - v0)
        # edge built FROM a pcurve + its host surface (note the surf arg)
        edge = BRepBuilderAPI_MakeEdge(pcurve, surf, 0.0, length).Edge()
        mk_wire.Add(edge)
    wire = mk_wire.Wire()

    face = BRepBuilderAPI_MakeFace(surf, wire, True).Face()
    BRepLib.BuildCurves3d_s(face)   # pcurve -> 3D curve, required before meshing
    return face


def build_nurbs_patch():
    """Unit 9: a free-form NURBS patch (bicubic, 4x4 control net) as a
    Geom_BSplineSurface. Clamped knots [0,1] with multiplicity 4 give a
    single bicubic Bezier-like span."""
    nu, nv = 4, 4
    poles = TColgp_Array2OfPnt(1, nu, 1, nv)         # 1-BASED 2D array
    for i in range(1, nu + 1):
        for j in range(1, nv + 1):
            x = 30.0 + (i - 1) * 2.0
            y = (j - 1) * 2.0
            z = math.sin(i) * math.cos(j) * 1.5      # some gentle waviness
            poles.SetValue(i, j, gp_Pnt(x, y, z))

    uknots = TColStd_Array1OfReal(1, 2)
    uknots.SetValue(1, 0.0); uknots.SetValue(2, 1.0)
    vknots = TColStd_Array1OfReal(1, 2)
    vknots.SetValue(1, 0.0); vknots.SetValue(2, 1.0)
    umults = TColStd_Array1OfInteger(1, 2)
    umults.SetValue(1, 4); umults.SetValue(2, 4)     # clamped: mult = degree+1
    vmults = TColStd_Array1OfInteger(1, 2)
    vmults.SetValue(1, 4); vmults.SetValue(2, 4)

    surf = Geom_BSplineSurface(poles, uknots, vknots, umults, vmults, 3, 3)
    return BRepBuilderAPI_MakeFace(surf, 1e-6).Face()


def build_intersection_edge():
    """Unit 8: an edge produced by intersecting two surfaces. The plane/plane
    intersection yields a single 3D line we trim and turn into an edge."""
    s1 = Geom_Plane(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))
    s2 = Geom_Plane(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0))
    inter = GeomAPI_IntSS(s1, s2, 1e-7)
    assert inter.IsDone() and inter.NbLines() >= 1, "surfaces do not intersect"
    line3d = inter.Line(1)                            # a Geom_Curve (here Geom_Line)
    return BRepBuilderAPI_MakeEdge(line3d, -5.0, 5.0).Edge()


def build_closed_cylinder_solid():
    """Unit 12: a genuine watertight SOLID -- a closed cylinder (lateral wall
    plus two disk caps) sewn into a shell and wrapped as a TopoDS_Solid.
    Returns the solid; the caller checks validity and volume."""
    ax = gp_Ax3(gp_Pnt(40, 0, 0), gp_Dir(0, 0, 1))
    wall = BRepBuilderAPI_MakeFace(
        Geom_CylindricalSurface(ax, 3.0), 0.0, 2 * math.pi, 0.0, 8.0, 1e-6
    ).Face()

    def disk(z):
        circ = gp_Circ(gp_Ax2(gp_Pnt(40, 0, z), gp_Dir(0, 0, 1)), 3.0)
        wire = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(circ).Edge()).Wire()
        return BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(40, 0, z), gp_Dir(0, 0, 1)), wire).Face()

    sew = BRepBuilderAPI_Sewing(1e-6)
    for f in (wall, disk(0.0), disk(8.0)):
        sew.Add(f)
    sew.Perform()
    shell = TopoDS.Shell_s(TopExp_Explorer(sew.SewedShape(), TopAbs_SHELL).Current())
    solid = BRepBuilderAPI_MakeSolid(shell).Solid()
    fix = ShapeFix_Solid(solid)
    fix.Perform()
    return fix.Solid()


# --------------------------------------------------------------------------
# ROBUST BUILD LOOP  (build, log, skip failures, sew, solidify, render)
# --------------------------------------------------------------------------

def main():
    face_specs = [
        ("cylinder",       build_cylinder),
        ("cone",           build_cone),
        ("plane",          build_plane),
        ("trimmed_pcurve", build_trimmed_pcurve_face),
        ("nurbs_patch",    build_nurbs_patch),
    ]

    good_faces = []
    print("=== BUILD REPORT ===")
    for name, builder in face_specs:
        try:
            face = builder()
            good_faces.append(face)
            print(f"  [OK    ] {name}")
        except Exception as exc:                      # one bad face never kills the run
            print(f"  [FAILED] {name}: {exc}")

    # The intersection edge is built the same defensive way.
    try:
        inter_edge = build_intersection_edge()
        print("  [OK    ] intersection_edge")
    except Exception as exc:
        inter_edge = None
        print(f"  [FAILED] intersection_edge: {exc}")

    # A real watertight SOLID (Unit 12): build it, then prove it with validity
    # and an enclosed volume.
    try:
        solid = build_closed_cylinder_solid()
        valid = BRepCheck_Analyzer(solid).IsValid()
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(solid, props)
        print(f"  [OK    ] closed_cylinder_solid (valid={valid}, volume={props.Mass():.1f})")
    except Exception as exc:
        solid = None
        print(f"  [FAILED] closed_cylinder_solid: {exc}")

    # Sew the good faces into a shell (gaps up to 1e-3 are stitched).
    sew = BRepBuilderAPI_Sewing(1e-3)
    for face in good_faces:
        sew.Add(face)
    sew.Perform()
    sewn = sew.SewedShape()

    has_shell = TopExp_Explorer(sewn, TopAbs_SHELL).More()
    print(f"\nSewing produced a shell: {has_shell}")

    # Collect everything into one TopoDS_Compound for display.
    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)
    builder.Add(compound, sewn)
    if inter_edge is not None:
        builder.Add(compound, inter_edge)
    if solid is not None:
        builder.Add(compound, solid)

    # Open the interactive VTK window on the finished model.
    vis.show(compound)


# --------------------------------------------------------------------------
# Applying this to your real part
# --------------------------------------------------------------------------
# You now own every building block. To turn a real part into
# rendered geometry, walk it CONCEPTUALLY the same way -- no new API needed:
#
#   For each FACE in the part:
#     1. Read its surface TYPE and parameters, and rebuild the matching Geom
#        surface: plane/cylinder/cone -> Geom_Plane / Geom_CylindricalSurface /
#        Geom_ConicalSurface (Units 1-4); a free-form patch -> Geom_BSplineSurface
#        from its pole/knot/mult arrays (Unit 9). (Angles RADIANS, arrays 1-BASED.)
#     2. Read its LOOPS and EDGES and build the 3D curves (Unit 5).
#     3. For a trimmed face, lay each edge's 2D PCURVE on the surface and make
#        the bounding wire, then BRepLib.BuildCurves3d_s to recover 3D curves (Unit 7).
#     4. For an INTERSECTION edge, reconstruct it with GeomAPI_IntSS on the two
#        host surfaces instead of trusting stored points (Unit 8).
#     5. Wrap each face build in try/except: log "[FAILED] <id>" and SKIP, so one
#        broken face cannot sink the whole import.
#   Then SEW the good faces with BRepBuilderAPI_Sewing. If the body is a closed
#   solid (most mechanical parts are), wrap the shell with BRepBuilderAPI_MakeSolid
#   and verify it with BRepCheck_Analyzer + BRepGProp (Unit 12). Drop the shell or
#   solid into a TopoDS_Compound and vis.show it (Unit 11).
#
# That is the entire pipeline. The only thing this capstone leaves out on
# purpose is the data reader -- the geometry construction is identical.

if __name__ == "__main__":
    main()
```

Run it and you get a `=== BUILD REPORT ===` listing every face as `[OK]`, the
solid as `[OK ... valid=True, volume=...]`, a `Sewing produced a shell: True`
line, then the VTK window opens on the assembled compound: a half-cylinder, a
cone, a flat plane, a curved "window" patch, a wavy NURBS patch, the intersection
line through the origin, and a closed cylindrical **solid** off to the side.

## What each piece does

- **The face builders** are the analytic and free-form recipes from earlier
  units, each wrapped in a function returning one `TopoDS_Face`:
  `build_cylinder`/`build_cone`/`build_plane` are Units 1–4,
  `build_trimmed_pcurve_face` is Unit 7, `build_nurbs_patch` is Unit 9.
- **The pcurve face** (Unit 7) is the only subtle face. Its wire is built in
  **parameter space**: each edge is a `Geom2d_Line` (a 2D line in `(u, v)`)
  attached to the host surface via `BRepBuilderAPI_MakeEdge(pcurve, surf, 0, len)`.
  After `MakeFace(surf, wire, True)` the edges still have _no 3D curves_, so
  `BRepLib.BuildCurves3d_s(face)` materialises them.
- **The intersection edge** (Unit 8) is produced by `GeomAPI_IntSS`, not stored
  coordinates. We guard with `IsDone()` and `NbLines() >= 1`, then take `Line(1)`.
- **The closed solid** (Unit 12) is the real surface→solid step: a lateral
  cylinder wall plus two disk caps are sewn into a shell, wrapped with
  `BRepBuilderAPI_MakeSolid`, healed with `ShapeFix_Solid`, then _proven_ with
  `BRepCheck_Analyzer.IsValid()` and an enclosed volume from `BRepGProp`.
- **The robust loop** is the spine. Each builder runs inside `try/except` so a
  single bad face is logged `[FAILED]` and skipped rather than crashing the run.
  This mirrors how a real importer marks bad faces in a messy part and keeps going.
- **Sewing + compound** (Unit 11) stitches the good faces, then everything —
  shell, intersection edge, and solid — goes into one `TopoDS_Compound` for
  `vis.show`.

> **Note on watertightness.** The five loose synthetic faces don't share edges,
> so sewing them yields a shell of disconnected faces, **not** a closed solid —
> that's why the _separate_ `build_closed_cylinder_solid` exists to demonstrate a
> genuine solid. A real part whose faces share edges sews into a proper closed
> shell you can solidify directly.

## Verifying headlessly

`vis.show(compound)` opens a **blocking** GUI window, which you cannot run in a
test. To prove the model is renderable without a window, swap in
`vis.triangulate`, which meshes the faces and returns points/cells with no
window:

```python
pts, cells = vis.triangulate(compound)
assert pts.GetNumberOfPoints() > 0     # this model meshes to ~1100 points
print("points:", pts.GetNumberOfPoints())
```

Because `vis.show` and `vis.triangulate` take the _same_ compound, a positive
point count proves the geometry is sound right up to the windowing call.

## Gotchas

- **OCCT arrays are 1-BASED.** `TColgp_Array2OfPnt(1, nu, 1, nv)`,
  `TColStd_Array1OfReal(1, 2)`, and every `SetValue`/`GetValue` index start at
  **1**, never 0.
- **Angles are RADIANS.** The `Geom_ConicalSurface` half-angle and the
  cylinder/cone `u` range use `math.radians(...)` / `math.pi` — never raw degrees.
- **Trimmed pcurve faces need `BRepLib.BuildCurves3d_s(face)`** (note the `_s`
  static suffix). Skip it and the boundary meshes to 0 nodes.
- **A solid needs a _closed_ shell.** `build_closed_cylinder_solid` works because
  the wall and both caps share their circular edges; drop a cap and
  `BRepCheck_Analyzer` reports invalid. Always run `ShapeFix_Solid` and check
  validity (Unit 12).
- **`GeomAPI_IntSS` is 1-based and may be empty.** Index with `Line(1)` and guard
  with `IsDone()` and `NbLines() >= 1`.
- **A bare edge contributes 0 points.** `vis.triangulate` only walks
  `TopAbs_FACE`, so the intersection edge meshes to nothing — it rides in the
  compound purely for display. Verify renderability from the faces/solid.
- **Use `gp_Ax3`, not `gp_Ax2`,** for the Geom analytic-surface constructors.
- **Clamped B-spline knots must match the poles.** Degree 3 with 4 poles needs
  knots `[0, 1]` with multiplicity 4 (= degree + 1) at each end.

## Exercises

1. **Inject a failure.** Add a sixth face spec whose builder does
   `raise ValueError("bad face")`; confirm the report prints `[FAILED]` for it
   while every other face and the solid still build.
2. **Break the solid.** In `build_closed_cylinder_solid`, sew only the wall and
   one cap; watch `valid=False` in the report. Restore the second cap.
3. **Measure it.** Print the solid's volume and check it against `π·3²·8`.
4. **Add a boolean.** Cut a small `BRepPrimAPI_MakeBox` out of the closed solid
   (Unit 13) and add the result to the compound.
5. **Headless gate.** Wrap the `vis.triangulate` check into an
   `assert pts.GetNumberOfPoints() > 0` at the end of `main`, so the build fails
   loudly if a change makes the model un-meshable.

## Applying this to your real part

You now own every building block. Turning a real part into rendered
geometry — surfaces **and** solids — is the **same loop**, only a data reader
bolted on the front (which this course deliberately leaves to you):

For each **face** in the part:

1. **Rebuild the surface.** Read its surface _type_ and parameters and construct
   the matching Geom surface: plane/cylinder/cone →
   `Geom_Plane` / `Geom_CylindricalSurface` / `Geom_ConicalSurface` (Units 1–4);
   a free-form patch → `Geom_BSplineSurface` from its pole/knot/mult arrays
   (Unit 9). Angles in **radians**, arrays **1-based**.
2. **Rebuild the curves.** Read its loops and edges and build the 3D curves
   (Unit 5).
3. **Trim curved faces.** Lay each edge's 2D **pcurve** on the surface, make the
   bounding wire, then `BRepLib.BuildCurves3d_s` to recover the 3D curves (Unit 7).
4. **Reconstruct intersection edges.** Where two faces meet, rebuild the edge
   with `GeomAPI_IntSS` on the two host surfaces (Unit 8).
5. **Skip and log failures.** Wrap each face build in `try/except`: log
   `[FAILED] <id>` and **skip**, so one broken face never sinks the whole import.

Then **sew** the good faces with `BRepBuilderAPI_Sewing`. If the body is a closed
solid, wrap the shell with `BRepBuilderAPI_MakeSolid` and confirm it with
`BRepCheck_Analyzer` + `BRepGProp` (Unit 12). Drop the shell or solid into a
`TopoDS_Compound`, and `vis.show` it (Unit 11). That is the entire pipeline — the
geometry construction is identical to what you ran above.

> **Two appendices go deeper on this bridge.** A real model stores face/surface
> **senses**, **regions** (solid vs. void), and loop **fins** — read those and you
> recover orientation, the material side, and each edge's direction
> _deterministically_, instead of leaning on `ShapeFix`. See
> [Appendix A — Reading Real B-rep Data](15-appendix-reading-real-data.md). The
> healing tools used above (`Sewing`, `ShapeFix`, `BuildCurves3d_s`,
> `BRepCheck_Analyzer`) are catalogued in
> [Appendix B — Guess-and-Repair Toolbox](16-appendix-repair-toolbox.md).

## Checkpoint — course complete

You can build analytic faces, trim a curved face with pcurves, lay down a NURBS
patch, recover an edge from a surface–surface intersection, **sew faces into a
watertight solid and verify it by volume**, and drive all of it through a
defensive per-face loop that logs failures, sews the survivors, and renders the
result — verifying headlessly with `vis.triangulate` before ever opening a
window. That is the full B-rep construction toolkit a real part
demands, surfaces _and_ solids. The only thing left to add is a reader for your
own data, and every constructor it needs to call is one you have now used by hand.

Back to the [course index](README.md).
