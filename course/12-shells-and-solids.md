# Unit 12 — Shells & Solids

**Goal:** go from a _bag of faces_ to a real **solid** — a closed volume you can
measure and treat as a body, not just a surface. This is the surface→solid step:
sew faces into a watertight **shell**, then turn that shell into a `TopoDS_Solid`.

Difficulty: ⭐⭐⭐

---

## The concept

Everything so far produced **surfaces and faces** — infinitely thin sheets. A
**solid** is the _volume enclosed by_ a closed set of faces. The ladder:

```
Faces            many separate patches (a "bag")
  → Shell        faces stitched together along shared edges
  → (closed)     the shell has no gaps and no free edges — it's WATERTIGHT
  → Solid        the volume bounded by that closed shell
```

Two new ideas make a shell into a solid:

- **Watertight (closed).** No free edges — every edge is shared by at least two
  faces, with no gaps. A box needs all 6 faces; leave one off and the shell is
  open, so there's no "inside" to enclose. For a simple solid each edge is shared
  by _exactly_ two faces (that's also the **manifold** condition).
- **Orientation.** Each face has a front and a back (its normal). For a solid,
  every face must point its normal **outward**, so the kernel knows which side is
  material and which is air.

`BRepBuilderAPI_Sewing` (from Unit 11) handles the stitching; `BRepBuilderAPI_MakeSolid`
wraps the closed shell as a solid; `ShapeFix_Solid` fixes the orientation.

> Because this course builds faces from scratch (with no source orientation data),
> `ShapeFix_Solid` is the right way to get outward normals here. A real importer
> instead reads orientation straight from the model
> ([Appendix A](15-appendix-reading-real-data.md)) rather than repairing after the
> fact; [Appendix B](16-appendix-repair-toolbox.md) covers `ShapeFix_Solid`'s
> limits (it only orients _closed_ solids) and the full repair toolbox.

## The pipeline

A 10×10×10 cube from six planar faces — sewn, solidified, validated, measured.

```python
from OCP.gp import gp_Pnt
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Sewing,
    BRepBuilderAPI_MakeSolid,
)
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.ShapeFix import ShapeFix_Solid
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopoDS import TopoDS

import vis


def p(x, y, z):
    """Corner of a 10x10x10 cube from 0/1 flags."""
    return gp_Pnt(x * 10, y * 10, z * 10)


def quad(a, b, c, d):
    """A planar face from four corner points (a closed polygon wire)."""
    wire = BRepBuilderAPI_MakePolygon(a, b, c, d, True).Wire()
    return BRepBuilderAPI_MakeFace(wire, True).Face()


# Six faces. Adjacent faces reuse the SAME corner points, so their shared
# edges coincide exactly -- that is what lets sewing close the shell.
faces = [
    quad(p(0,0,0), p(1,0,0), p(1,1,0), p(0,1,0)),   # bottom  z=0
    quad(p(0,0,1), p(1,0,1), p(1,1,1), p(0,1,1)),   # top     z=1
    quad(p(0,0,0), p(1,0,0), p(1,0,1), p(0,0,1)),   # front   y=0
    quad(p(0,1,0), p(1,1,0), p(1,1,1), p(0,1,1)),   # back    y=1
    quad(p(0,0,0), p(0,1,0), p(0,1,1), p(0,0,1)),   # left    x=0
    quad(p(1,0,0), p(1,1,0), p(1,1,1), p(1,0,1)),   # right   x=1
]

# 1. SEW the loose faces into a connected shell.
sew = BRepBuilderAPI_Sewing(1e-6)        # tolerance for matching coincident edges
for f in faces:
    sew.Add(f)
sew.Perform()
sewn = sew.SewedShape()

# 2. Pull the SHELL out of the sewing result.
shell = TopoDS.Shell_s(TopExp_Explorer(sewn, TopAbs_SHELL).Current())

# 3. A solid is the volume BOUNDED by a closed shell.
solid = BRepBuilderAPI_MakeSolid(shell).Solid()

# 4. Heal orientation so every face points OUTWARD (defines inside vs. outside).
fix = ShapeFix_Solid(solid)
fix.Perform()
solid = fix.Solid()

# 5. Is it a valid, closed solid? And what volume does it enclose?
print("valid :", BRepCheck_Analyzer(solid).IsValid())     # True
props = GProp_GProps()
BRepGProp.VolumeProperties_s(solid, props)
print("volume:", props.Mass())                            # 1000.0 == 10*10*10

vis.show(solid)
```

Run it: a solid cube. The console prints `valid: True` and `volume: 1000.0` —
proof it's a closed body, not six loose sheets. Delete one face from the list and
re-run: the volume goes wrong / validity fails, because the shell is no longer
closed.

## A solid from _your own_ surfaces

The same recipe closes a cylinder you built in Units 1–2: the lateral wall plus
two disk caps, sewn and solidified.

```python
import math
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Ax3, gp_Circ, gp_Pln
from OCP.Geom import Geom_CylindricalSurface
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_Sewing,
    BRepBuilderAPI_MakeSolid,
)
from OCP.ShapeFix import ShapeFix_Solid
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopoDS import TopoDS

import vis

ax = gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))

# The full lateral wall (Unit 2): radius 5, height 0..20.
lateral = BRepBuilderAPI_MakeFace(
    Geom_CylindricalSurface(ax, 5.0), 0.0, 2 * math.pi, 0.0, 20.0, 1e-6
).Face()


def disk(z):
    """A flat circular cap at height z: a circle wire on a plane (Unit 6)."""
    circ = gp_Circ(gp_Ax2(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1)), 5.0)
    wire = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(circ).Edge()).Wire()
    return BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1)), wire).Face()


sew = BRepBuilderAPI_Sewing(1e-6)
for f in (lateral, disk(0.0), disk(20.0)):
    sew.Add(f)
sew.Perform()

shell = TopoDS.Shell_s(TopExp_Explorer(sew.SewedShape(), TopAbs_SHELL).Current())
solid = BRepBuilderAPI_MakeSolid(shell).Solid()
fix = ShapeFix_Solid(solid)
fix.Perform()
solid = fix.Solid()

props = GProp_GProps()
BRepGProp.VolumeProperties_s(solid, props)
print("cylinder volume:", props.Mass())     # ~1570.8 == pi * 5^2 * 20

vis.show(solid)
```

## What each piece does

- **`BRepBuilderAPI_Sewing(tol)` + `Add` + `Perform`** — stitches faces whose
  edges coincide within `tol` into a connected shell. `SewedShape()` returns the
  result (a shell when everything closes up; a compound if it couldn't).
- **`TopExp_Explorer(sewn, TopAbs_SHELL).Current()` + `TopoDS.Shell_s(...)`** —
  the sewing result is a generic shape, so explore it for the `TopAbs_SHELL` and
  down-cast to a concrete `TopoDS_Shell`.
- **`BRepBuilderAPI_MakeSolid(shell).Solid()`** — wraps a _closed_ shell as the
  solid it bounds. On an open shell you get a solid that won't be valid.
- **`ShapeFix_Solid(solid).Perform()` / `.Solid()`** — reorients faces so normals
  point outward and repairs the shell. Cheap insurance; run it routinely.
- **`BRepCheck_Analyzer(shape).IsValid()`** — the truth test: `True` means a
  well-formed, closed, correctly-oriented solid.
- **`BRepGProp.VolumeProperties_s(solid, props)` + `props.Mass()`** — computes
  geometric properties; `Mass()` is the **enclosed volume** (with unit density).
  A nonzero, correct volume is the strongest signal you really built a solid.

> **`Mass()` means volume here.** `GProp_GProps.Mass()` returns volume for
> `VolumeProperties` (density 1), area for `SurfaceProperties`, and length for
> `LinearProperties`. Same method, different meaning per call.

## Gotchas

- **Open shell → no solid.** If faces don't all share edges (a missing face, or
  a gap larger than the sew tolerance), the shell stays open, `MakeSolid` yields
  an invalid solid, and the volume is meaningless. `IsValid()` catches this.
- **Sewing tolerance vs. gap.** The faces must meet within the sew tolerance.
  Too tight and coincident edges aren't merged (shell stays open); too loose and
  distinct edges get fused. `1e-6` suits clean, exactly-shared corners.
- **Always run `ShapeFix_Solid`.** Hand-built faces are often inconsistently
  oriented; without the fix the "solid" can be inside-out (negative volume) or
  invalid.
- **Down-cast the shell.** `SewedShape()` and explorer results are generic
  `TopoDS_Shape`; use `TopoDS.Shell_s(...)` before `MakeSolid`.
- **Check `.More()` before `.Current()`.** If sewing produced no shell (totally
  disconnected faces), `TopExp_Explorer(...).Current()` on an empty explorer is
  invalid — guard with `.More()` in real code.

## Exercises

1. **Break watertightness.** Delete the `top` face from the cube list, re-run,
   and watch `IsValid()` go `False` and the volume become wrong.
2. **Measure a different box.** Change the cube to 20×10×5 and confirm the printed
   volume is `1000.0`.
3. **Open vs. closed cylinder.** Sew only the lateral wall and _one_ cap, then
   `MakeSolid` — observe it isn't valid. Add the second cap to fix it.
4. **Surface area instead of volume.** Swap `VolumeProperties_s` for
   `SurfaceProperties_s` and read `Mass()` — now it's the total area.

## Checkpoint

You can sew faces into a watertight shell, wrap it as a `TopoDS_Solid`, fix its
orientation, and _prove_ it's a real solid with `BRepCheck_Analyzer.IsValid()`
and a correct enclosed volume from `BRepGProp`. You understand watertightness and
face orientation — the two things that separate a solid from a bag of faces.

**Next:** [Unit 13 — Solid Primitives & Booleans](13-solid-primitives-and-booleans.md)
