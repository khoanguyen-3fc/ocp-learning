# OCP: From Surfaces to Solids — Course

A hands-on path from "never used OpenCASCADE" to **building, rendering, and
solidifying a real B-rep part** in OCP — surfaces,
trimmed faces, _and_ watertight solids. Every example uses hard-coded numbers —
no file parsing.

## How this course is built

You only ever learn **one thing**: a 4-step pipeline that turns numbers into a
renderable face. Each unit reuses it with a different surface, curve, or trimming
technique.

```
1. gp frame      gp_Ax3(origin, axis_dir, x_dir)        position + orientation
2. Geom surface  Geom_<Type>Surface(frame, dims...)     the infinite math surface
3. TopoDS face   BRepBuilderAPI_MakeFace(surface, ...)  a bounded, renderable face
4. render        vis.show(face)                         (already written for you)
```

Units 1–4 build surfaces. Units 5–8 build the **boundaries** that trim them
(curves, wires, pcurves, intersections) — this is what a real part needs. Units
9–11 add free-form NURBS, blends, and assembly. Units 12–13 turn faces into
**solids** (sewing, `MakeSolid`, primitives, booleans). Unit 14 ties it all
together.

## Units

| #   | Unit                                                               | You'll be able to...                                                | Est.     |
| --- | ------------------------------------------------------------------ | ------------------------------------------------------------------- | -------- |
| 0   | [Foundations & vocabulary](00-foundations.md)                      | Explain surface vs. face, and the 4 OCCT layers                     | ½ day    |
| 1   | [Plane](01-plane.md)                                               | Render your first face; understand U/V bounds                       | ½ day    |
| 2   | [Cylinder](02-cylinder.md)                                         | Render a cylinder; understand U = angle                             | ½ day    |
| 3   | [Cone](03-cone.md)                                                 | Render a cone; handle the half-angle gotcha                         | ½ day    |
| 4   | [Torus](04-torus.md)                                               | Render a torus; both U & V are angles                               | ½ day    |
| 5   | [Curves & Edges](05-curves-and-edges.md)                           | Build line/arc/ellipse/B-spline/trimmed curves → edges              | 1 day    |
| 6   | [Wires & Trimming](06-wires-and-trimming.md)                       | Cut a planar face to an arbitrary wire                              | 1 day    |
| 7   | [Pcurves & Curved Trimming](07-pcurves-and-curved-trimming.md)     | Trim a _curved_ surface — **the real-part unlock**                  | 1–2 days |
| 8   | [Intersection Edges](08-intersection-edges.md)                     | Compute seam edges with `GeomAPI_IntSS`; skip-and-log               | 1–2 days |
| 9   | [NURBS Free-Form Surface](09-nurbs-bspline-surface.md)             | Build a `Geom_BSplineSurface` by hand                               | 2–4 days |
| 10  | [Blends / Fillets](10-blends.md)                                   | Understand why blends are hard (stretch)                            | optional |
| 11  | [Combine Many Faces](11-combine-and-render.md)                     | Render a whole model as one compound / shell                        | ½ day    |
| 12  | [Shells & Solids](12-shells-and-solids.md)                         | Sew faces into a watertight `TopoDS_Solid`; check validity & volume | 1 day    |
| 13  | [Solid Primitives & Booleans](13-solid-primitives-and-booleans.md) | Build primitive solids; union / cut / intersect                     | ½ day    |
| 14  | [Capstone — a complete model](14-capstone.md)                      | Build + render a full part end-to-end, faces _and_ a solid          | 1 day    |

## Appendices

Reference material for when you move from the course's hard-coded examples to
reading a **real** B-rep model:

- [Appendix A — Reading Real B-rep Data](15-appendix-reading-real-data.md) — the
  _deterministic_ rules an importer uses (face orientation from senses, material
  side from regions, edge direction from loop fins) instead of guess-and-repair.
- [Appendix B — Guess-and-Repair Toolbox](16-appendix-repair-toolbox.md) —
  `Sewing` / `ShapeFix` / `BuildCurves3d_s` / `BRepCheck_Analyzer`: what each
  fixes, when to use it, and its limits.

## Checkpoints

- **After Unit 4** — you can build and render all four _analytic_ surfaces.
- **After Unit 6** — you can cut planar faces to real boundaries.
- **After Unit 8** — you can trim _curved_ faces and compute intersection edges:
  the two techniques a real trimmed part actually requires.
- **After Unit 9** — you can build free-form (blade-like) NURBS surfaces.
- **After Unit 13** — you can turn faces into watertight **solids** (and build
  them top-down from primitives + booleans), measuring volume to prove it.
- **After Unit 14** — you can assemble every surface, trimmed face, and a solid
  into one rendered, complete model, skipping and logging any failure.

## How to work through a unit

Each unit is self-contained:

1. Read the unit.
2. Copy its `python` block into a scratch file at the repo root (e.g. `scratch.py`).
3. Run it, see the shape, then **change the numbers and re-run** — that's where
   the learning happens.

## Conventions used in every unit

- Code runs from the **repo root** so that `import vis` resolves
  (`PYTHONPATH=. .venv/bin/python your_file.py`).
- OCCT uses **1-based** indexing for its arrays. This bites everyone once.
- Angles passed to `Geom` constructors are in **radians**.
- `vis.show()` opens a **blocking** VTK window — close it (`q`) before the script
  continues. To check geometry without a window, use `vis.triangulate(shape)` and
  assert it returns more than zero points.
- `vis` renders **faces** only. A bare edge or wire produces no mesh — cap or
  trim it into a face to see it.

Start at **[Unit 0 — Foundations](00-foundations.md)**.
