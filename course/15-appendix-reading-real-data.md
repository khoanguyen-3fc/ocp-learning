# Appendix A — Reading Real B-rep Data (the Deterministic Rules)

The course builds every shape from hard-coded numbers. A real **importer** instead
reads the shape from a B-rep model (e.g. a STEP file). The good news: that data
_already encodes_ the answers the course otherwise recovers by healing —
orientation, which side is material, and which way each edge runs. **Read them;
don't guess.** (The healing tools the course leans on are catalogued in
[Appendix B](16-appendix-repair-toolbox.md).)

This appendix is generic — it applies to any B-rep source that carries face/surface
senses, regions, and loop fins.

---

## The big idea: deterministic, not repaired

Units 12 and 14 obtain outward normals and closed solids by **sewing then
repairing** (`ShapeFix_Solid`). That works for clean synthetic input, but it is a
_guess-and-fix_. A real model stores the facts directly, so a reader can be
**deterministic**: compute the result from the data instead of repairing after the
fact. Three rules carry most of the weight.

## A.1 Face orientation — from `face.sense` vs `surf.sense`

Each face stores a sense, and so does its surface. The face's realized (outward)
normal points along the surface's natural normal **exactly when the two senses
agree**:

```
flip = (face_sense != surf_sense)
```

Set the `TopoDS_Face` `REVERSED` when `flip` is true, `FORWARD` otherwise:

```python
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3
from OCP.Geom import Geom_Plane
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.TopAbs import TopAbs_REVERSED

frame = gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))
face = BRepBuilderAPI_MakeFace(Geom_Plane(frame), -10., 10., -10., 10., 1e-6).Face()

# These two senses come straight from the model (each +1/-1 or '+'/'-').
face_sense, surf_sense = +1, -1
flip = (face_sense != surf_sense)               # -> True here

oriented = face.Reversed() if flip else face    # data-driven orientation
print("reversed:", oriented.Orientation() == TopAbs_REVERSED)
```

**Why this beats repair:** `ShapeFix_Solid` can only fix orientation when it has a
_closed solid_ to reason about. For an open sheet, a lone face, or a non-manifold
body it has nothing to close, so the orientation stays whatever you built. The
sense data answers it face-by-face regardless.

## A.2 Material side — from regions

A body's faces partition space into **regions**, each tagged **solid** (material)
or **void** (empty). The "head" region — the one with no predecessor — is the
**infinite region** surrounding the part, and is always void.

- Build solids only from the **solid** regions; **exclude the infinite void**.
- A body may have **several** solid regions and **internal void cavities**.

**Why this beats repair:** the course's "sew → `MakeSolid`" assumes _one closed
shell = one solid_. That cannot represent an internal cavity, cannot handle a body
with multiple solid lumps, and cannot tell which side of a shell is material — the
region tag states it outright.

## A.3 Edge order & direction — from loop fins

A face's boundary loop is an **ordered ring of fins** (a fin = a directed use of an
edge by a loop, i.e. a half-edge). Each fin has a sense: `+` means it runs the same
direction as the edge's curve, `-` means reversed. The **same edge appears in two
adjacent loops with opposite fin sense**.

Build the wire by walking the fins in order, orienting each edge from its sense:

```python
from OCP.gp import gp_Pnt
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

# Each loop fin gives an edge + a sense (+1 along the curve, -1 reversed).
fins = [
    (BRepBuilderAPI_MakeEdge(gp_Pnt(0, 0, 0), gp_Pnt(10, 0, 0)).Edge(),  +1),
    (BRepBuilderAPI_MakeEdge(gp_Pnt(10, 0, 0), gp_Pnt(10, 10, 0)).Edge(), +1),
    (BRepBuilderAPI_MakeEdge(gp_Pnt(10, 10, 0), gp_Pnt(0, 0, 0)).Edge(),  +1),
]
mk = BRepBuilderAPI_MakeWire()
for edge, sense in fins:
    mk.Add(edge if sense > 0 else edge.Reversed())   # orientation from fin sense
wire = mk.Wire()
print("wire built:", not wire.IsNull(), "closed:", wire.Closed())
```

**Why this beats repair:** [Unit 6](06-wires-and-trimming.md) connects edges by
geometric end-to-end matching, which is fragile (tolerance-dependent) and needs
`ShapeFix` to reorder. The fins give the order _and_ direction exactly.

## A.4 Other data you must respect

- **Bounded/trimmed curves:** the stored start/end parameters can be _descending_
  (`u2 < u1`) to signal a reversed basis curve. Order them ascending for
  `MakeEdge`, and carry the reversal into the edge's orientation rather than
  assuming `u1 < u2`.
- **NURBS source:** read poles, distinct knots, and multiplicities from the
  _structured_ records — not a human-readable summary, which may not populate the
  pole count. Map knots/mults 1:1 to OCCT (no flattening) and re-check
  `n_poles + degree + 1 == sum(mults)` per direction ([Unit 9](09-nurbs-bspline-surface.md)).
- **Rational NURBS:** poles are often stored _weighted_ as `(x·w, y·w, z·w, w)`.
  Divide each pole's xyz by its weight `w` before handing poles + weights to OCCT.
- **Frame field names:** the principal direction may be labelled `normal`
  (plane/circle/ellipse) or `axis` (cylinder/cone/torus) — both feed the
  `gp_Ax3` main direction; the Y axis is implied right-handed (`axis × x_axis`).
- **Cone parameterization:** only the _geometry_ (frame + half-angle + reference
  radius) transfers. OCCT re-parameterizes V along the slant (see
  [Unit 3](03-cone.md)); a stored axial V does **not** map 1:1.
- **Transforms (instances / assemblies):** a placement is a rotation + translation,
  with any uniform **scale applied last** (`x' = (R·x + t)·scale`). Map to
  `gp_Trsf` (`SetValues` + `SetScaleFactor`); a **reflection** or general affine
  needs `gp_GTrsf`, not `gp_Trsf`. Apply it as a `TopLoc_Location` — the same
  location machinery [`vis.py`](../vis.py) already honours when meshing.

## A reader's order of operations

1. Read node payloads from the **structured** records (full data + canonical
   field order); treat any human-readable dump as a projection only.
2. Walk the topology: Assembly/Instance → Body → Region → Shell → Face → Loop →
   Fin → (Edge, Vertex). Apply each Instance's transform (A.4).
3. **Regions:** build solids only from solid regions; exclude the infinite void
   (A.2).
4. **Per face:** build the `Geom` surface from its frame + dims
   ([Units 1–4](01-plane.md), [9](09-nurbs-bspline-surface.md)).
5. **Orientation:** set the face `REVERSED`/`FORWARD` from
   `flip = (face_sense != surf_sense)` (A.1).
6. **NURBS:** poles/knots/mults from structured records; rational-weight division;
   balance check (A.4).
7. **Per loop:** build the wire from ordered fins, each edge oriented by its sense
   (A.3).
8. **Per edge:** build the curve ([Unit 5](05-curves-and-edges.md)); honour
   trimmed-curve param order (A.4); recover intersection / pcurve-only edges with
   the stored pcurve or `BuildCurves3d_s` ([Units 7](07-pcurves-and-curved-trimming.md),
   [8](08-intersection-edges.md)).
9. **Blends:** derived — skip or fit a NURBS, and handle nested references
   ([Unit 10](10-blends.md)).
10. **Vertices → `gp_Pnt`;** resolve shared geometry references.
11. **Assemble:** sew and solidify ([Unit 12](12-shells-and-solids.md)); validate
    with the tools in [Appendix B](16-appendix-repair-toolbox.md).

---

See also: [Appendix B — Guess-and-Repair Toolbox](16-appendix-repair-toolbox.md) ·
[Unit 14 — Capstone](14-capstone.md) · back to the [course index](README.md).
