# Unit 6 — Wires & Trimming

**Goal:** cut a face to an _arbitrary_ loop instead of a rectangular U/V range.
This is the heart of B-rep — real faces are bounded by wires of edges.

Difficulty: ⭐⭐⭐

---

## The concept

So far you bounded faces with four numbers (`umin, umax, vmin, vmax`) — always a
rectangle in parameter space. Real models bound a face with a **wire**: a closed
loop of **edges**, each edge a bounded piece of a **curve**.

The topology you're now building:

```
Face  =  surface  +  Wire
Wire  =  ordered, closed list of Edges
Edge  =  a curve (Geom_Line, Geom_Circle, ...) bounded between two points
```

You built each curve type and turned it into an edge in
[Unit 5](05-curves-and-edges.md); here you assemble those edges into closed wires
and use them to cut faces.

## Easiest first: a planar face from a polygon

When the boundary is straight segments on a plane, OCCT can build everything —
including figuring out the plane — from just the corner points.

```python
from OCP.gp import gp_Pnt
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace

import vis

# Four corners of an L-ish quad in the XY plane.
p1 = gp_Pnt(0, 0, 0)
p2 = gp_Pnt(20, 0, 0)
p3 = gp_Pnt(20, 10, 0)
p4 = gp_Pnt(5, 15, 0)

# Build a closed wire from the points (True = close it back to p1).
wire = BRepBuilderAPI_MakePolygon(p1, p2, p3, p4, True).Wire()

# Make a planar face bounded by that wire (True = only accept a planar wire).
face = BRepBuilderAPI_MakeFace(wire, True).Face()

vis.show(face)
```

Run it: a flat quadrilateral with the exact corners you gave. **You just trimmed
a plane to an arbitrary shape.**

## Building a wire edge-by-edge

`MakePolygon` is a shortcut. The general tool is to make edges (the curve types
from Unit 5) and assemble a wire — here, two lines and a circular arc:

```python
import math
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Circ
from OCP.Geom import Geom_Circle
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
)

import vis

# Two straight edges...
p1 = gp_Pnt(0, 0, 0)
p2 = gp_Pnt(20, 0, 0)
e1 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()

p3 = gp_Pnt(20, 20, 0)
e2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()

# ...and a circular arc edge closing back toward the start.
# A circle in the XY plane, centered at (0,20), radius 20.
circ = gp_Circ(gp_Ax2(gp_Pnt(0, 20, 0), gp_Dir(0, 0, 1)), 20.0)
e3 = BRepBuilderAPI_MakeEdge(circ, p3, p1).Edge()   # arc from p3 to p1

# Assemble the wire in order; it must form a closed loop.
mk_wire = BRepBuilderAPI_MakeWire()
mk_wire.Add(e1)
mk_wire.Add(e2)
mk_wire.Add(e3)
wire = mk_wire.Wire()

face = BRepBuilderAPI_MakeFace(wire, True).Face()
vis.show(face)
```

Key APIs:

- `BRepBuilderAPI_MakeEdge(p1, p2)` — a straight edge between two points.
- `BRepBuilderAPI_MakeEdge(curve, p1, p2)` — an edge along a curve, trimmed
  between two points (here a circular arc). (All the `MakeEdge` forms are in
  [Unit 5](05-curves-and-edges.md).)
- `BRepBuilderAPI_MakeWire().Add(edge)` — chain edges; call `.Add()` per edge.

## Edge order and orientation

A wire must be **closed** (last edge ends where the first begins) and edges must
connect end-to-end. If `MakeWire` complains or the face comes out empty:

- check each edge's endpoints actually meet the next,
- check you closed the loop,
- when things are _almost_ right but fail on tolerance, run a repair pass:

  ```python
  from OCP.ShapeFix import ShapeFix_Face
  fixer = ShapeFix_Face(face)
  fixer.Perform()
  face = fixer.Face()
  ```

  `ShapeFix_Face` / `ShapeFix_Shape` clean up small ordering, orientation, and
  tolerance problems. Keep them in your toolbox — you'll use them again in Unit 7,
  and [Appendix B](16-appendix-repair-toolbox.md) catalogs the full repair set,
  when to reach for it, and its limits.

## Trimming a _curved_ surface — coming next

Trimming a **plane** with a wire is easy because the wire lies in the plane.
Trimming a **cylinder / cone / torus / NURBS** is harder: OCCT needs a **pcurve**
— each boundary edge expressed in the surface's own (U, V) parameter space. That
is exactly what [Unit 7](07-pcurves-and-curved-trimming.md) covers, and it's the
key that unlocks a real trimmed part. For now, just hold these two cases
in mind:

- **planar faces** → trim with a 3D wire (this unit), and
- **curved faces** → either bound with U/V ranges (Units 2–4) or trim with
  pcurves (Unit 7).

## Gotchas

- `MakeFace(wire, True)` — the `True` means "the wire must be planar." For a
  non-planar wire it fails; that's the signal you need the pcurve route (Unit 7).
- 1-based, closed loops, end-to-end connectivity — most failures are one of these.

## Exercises

1. Trim a plane into a **triangle**, then a **5-point star**-ish polygon.
2. Build the line+line+arc wire above, then change the arc radius and watch the
   face change.
3. Break the loop on purpose (don't close it) and read the error.
4. Take a slightly-off wire and fix it with `ShapeFix_Face`.

## Checkpoint

You can build edges, assemble a closed wire, and cut a planar face to it — and
you know that curved faces need pcurves, which is the next unit.

**Next:** [Unit 7 — Pcurves & Curved Trimming](07-pcurves-and-curved-trimming.md)
