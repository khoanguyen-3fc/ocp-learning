# Unit 0 — Foundations & Vocabulary

**Goal:** before writing geometry code, build the mental model. By the end you
can explain _surface vs. face_ and name the four OCCT layers and what each does.

Difficulty: — (no code)

No new code to write here — but read [`hello.py`](../hello.py) and
[`vis.py`](../vis.py), because you'll build on both.

---

## 1. The one distinction that matters: surface vs. face

This trips up everyone new to B-rep (Boundary representation):

- A **surface** is an _infinite_ mathematical sheet. A plane extends forever. A
  cylindrical surface is an endless pipe. It has no edges.
- A **face** is a _bounded patch_ cut out of a surface by one or more boundary
  loops. The side wall of a can is a face; the surface it lives on is an
  infinite cylinder.

> You never render a raw surface. You render **faces**. A face = a surface +
> the boundaries that trim it.

The whole course is: define a surface, then bound it into a face.

## 2. The B-rep vocabulary

A solid model, from biggest to smallest:

```
Solid   → a closed volume
  Shell → a connected set of faces
  Face  → a bounded patch of one surface          ← what we render
    Wire  → a closed loop of edges (the boundary)
      Edge  → a bounded piece of one curve
        Vertex → a point
```

You start by caring about **Face** and the **Wire / Edge** that bound it; once
faces close up, the **Shell** and **Solid** are how you get a measurable volume
(Units 12–13).

## 3. The four OCCT layers (and the OCP modules they live in)

Everything you do moves data up this stack:

| Layer                | Purpose                               | Example classes                         | OCP module           |
| -------------------- | ------------------------------------- | --------------------------------------- | -------------------- |
| **`gp`**             | Pure math: points, directions, frames | `gp_Pnt`, `gp_Dir`, `gp_Ax3`            | `OCP.gp`             |
| **`Geom`**           | Infinite geometry: surfaces & curves  | `Geom_Plane`, `Geom_CylindricalSurface` | `OCP.Geom`           |
| **`TopoDS`**         | Topology: faces, wires, shells        | `TopoDS_Face`, `TopoDS_Wire`            | `OCP.TopoDS`         |
| **`BRepBuilderAPI`** | The glue that turns `Geom` → `TopoDS` | `BRepBuilderAPI_MakeFace`               | `OCP.BRepBuilderAPI` |

The recurring pipeline is literally "walk these four rows top to bottom."

## 4. The key object: `gp_Ax3` (a coordinate frame)

Almost every surface is defined as **"this frame, plus a size."** A `gp_Ax3` is:

- an **origin** point (`gp_Pnt`),
- a **main direction** — the surface's local Z axis (`gp_Dir`),
- a **reference X direction** — fixes the rotation about Z (`gp_Dir`).

```python
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3

origin = gp_Pnt(0, 0, 0)
axis   = gp_Dir(0, 0, 1)   # local Z — e.g. a cylinder's spine
x_ref  = gp_Dir(1, 0, 0)   # local X — where angle 0 points

frame = gp_Ax3(origin, axis, x_ref)
```

A cylinder built on this frame stands up the Z axis, centered at the origin.
Change `axis` and the whole surface tilts. **Get comfortable with this — it is
the input to every surface in units 1–4.**

## 5. What `vis.show()` already does for you

Open [`vis.py`](../vis.py) and read `triangulate()`. It:

1. Calls `BRepMesh_IncrementalMesh(shape, 0.1, ...)` — this _meshes_ the shape,
   approximating every face with triangles.
2. Walks every face with a `TopExp_Explorer(shape, TopAbs_FACE)`.
3. Reads each face's triangulation and feeds the points/triangles to VTK.

The important consequence: **`vis.show()` accepts any shape that contains faces**
— a single `TopoDS_Face`, or a `TopoDS_Compound` of hundreds of them. You build
faces; it draws them.

[`hello.py`](../hello.py) is the smallest consumer: it makes a cylinder
_primitive_ (`BRepPrimAPI_MakeCylinder`) and shows it. You're about to do the
same, but building surfaces explicitly so you control the exact geometry.

---

## Exercises

1. In your own words, write one sentence each for: surface, face, wire, edge.
2. Point to the line in `vis.py` where meshing happens, and the line where faces
   are iterated.
3. Run `python hello.py`. Rotate the cylinder. You're looking at ~3 faces (side
   - two caps) meshed into triangles.

## Checkpoint

You can explain why we never render a "surface" directly, and you can build a
`gp_Ax3` from an origin and two directions.

**Next:** [Unit 1 — Plane](01-plane.md) — your first hand-built face.
