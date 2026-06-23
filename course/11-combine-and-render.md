# Unit 11 — Combine Many Faces

**Goal:** put many faces into a single shape and render them together — the step
that turns isolated surface demos into "a model."

Difficulty: ⭐⭐

---

## The concept

`vis.show()` walks every face in whatever shape you hand it (its
`TopExp_Explorer` loops over `TopAbs_FACE`). So to render a whole model, you just
need **one shape that contains all your faces**. The simplest such container is a
**`TopoDS_Compound`** — a loose bag of shapes with no connectivity requirements.
Perfect for "I built a pile of faces, draw them all."

## The pipeline

```python
import math
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3
from OCP.Geom import (
    Geom_Plane,
    Geom_CylindricalSurface,
    Geom_ConicalSurface,
    Geom_ToroidalSurface,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder

import vis


def make_faces():
    """Return a list of TopoDS_Face — one of each surface type, spread out."""
    faces = []

    # Plane at the origin.
    fr = gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))
    faces.append(BRepBuilderAPI_MakeFace(Geom_Plane(fr), -8, 8, -8, 8, 1e-6).Face())

    # Cylinder, shifted +X.
    fr = gp_Ax3(gp_Pnt(30, 0, 0), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))
    cyl = Geom_CylindricalSurface(fr, 5.0)
    faces.append(BRepBuilderAPI_MakeFace(cyl, 0, 2 * math.pi, 0, 20, 1e-6).Face())

    # Cone, shifted further +X.
    fr = gp_Ax3(gp_Pnt(60, 0, 0), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))
    cone = Geom_ConicalSurface(fr, math.radians(30), 5.0)
    faces.append(BRepBuilderAPI_MakeFace(cone, 0, 2 * math.pi, 0, 15, 1e-6).Face())

    # Torus, shifted further still.
    fr = gp_Ax3(gp_Pnt(95, 0, 0), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))
    tor = Geom_ToroidalSurface(fr, 10.0, 3.0)
    faces.append(BRepBuilderAPI_MakeFace(tor, 0, 2 * math.pi, 0, 2 * math.pi, 1e-6).Face())

    return faces


def to_compound(faces):
    """Pack a list of faces into a single TopoDS_Compound."""
    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)        # initialize the empty compound
    for face in faces:
        builder.Add(compound, face)       # drop each face in
    return compound


compound = to_compound(make_faces())
vis.show(compound)
```

Run it: all four surfaces in one window, laid out along X. `vis.show()` needed no
changes — it meshed and drew every face in the compound.

## The two-line idiom to remember

Building a compound always looks like this:

```python
builder = BRep_Builder()
compound = TopoDS_Compound()
builder.MakeCompound(compound)   # <-- easy to forget; without it, Add fails
builder.Add(compound, shape)     # repeat per shape
```

`MakeCompound` initializes the empty container; `Add` puts shapes in. You can
`Add` faces, wires, even other compounds.

## Optional: stitch into a shell

A compound is just a bag — the faces aren't "connected." If you want a proper
connected **shell** (e.g. for cleaner shared-edge rendering or downstream solid
operations), sew the faces:

```python
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing

sew = BRepBuilderAPI_Sewing(1e-6)     # tolerance for matching coincident edges
for face in make_faces():
    sew.Add(face)
sew.Perform()
sewn = sew.SewedShape()               # a shell/compound of connected faces
vis.show(sewn)
```

For "just render the surfaces," the plain compound is enough — reach for sewing
only when you need connectivity. The capstone (Unit 14) sews and solidifies a
whole model. (Sewing's tolerance trade-off and the rest of the repair toolbox are
in [Appendix B](16-appendix-repair-toolbox.md).)

## Gotchas

- **Forgetting `MakeCompound`.** `Add` on an uninitialized compound fails. The
  three setup lines always go together.
- **Sewing tolerance.** If faces don't visibly join after sewing, your tolerance
  is smaller than the gap between their edges — increase it.

## Exercises

1. Extend `make_faces()` with a NURBS patch from [Unit 9](09-nurbs-bspline-surface.md).
2. Write a helper `show_faces(faces)` that compounds-then-shows, so future demos
   are one call.
3. Build 20 cylinders of random-ish radii in a row and render them all at once.

## Checkpoint

You can pack any number of faces into a `TopoDS_Compound`, render them in one
window, and optionally sew them into a connected shell. Next you'll turn a closed
shell into an actual **solid** — a volume you can measure.

**Next:** [Unit 12 — Shells & Solids](12-shells-and-solids.md)
