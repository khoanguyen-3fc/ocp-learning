# Appendix B — The Guess-and-Repair Toolbox

The course repeatedly reaches for a small set of _heal-it-and-check_ tools:
sewing, `ShapeFix`, `BuildCurves3d_s`, and `BRepCheck_Analyzer`. They are
"guess-and-repair": they infer or fix something that wasn't given explicitly. This
appendix catalogs them — what each does, when it is the right call, and its limits.

> **Repair vs. read.** These tools are the right choice when you build geometry
> **from scratch / synthetically** (as the course does) or when the source data is
> **missing** a piece. When you _have_ the source data — face/surface senses,
> regions, loop fins — prefer the **deterministic rules** in
> [Appendix A](15-appendix-reading-real-data.md); they give the exact answer
> without a repair pass.

---

## B.1 Sewing — `BRepBuilderAPI_Sewing`

Stitches a bag of loose faces into a connected shell by **matching coincident
edges within a tolerance**. Used in [Units 11](11-combine-and-render.md) and
[12](12-shells-and-solids.md).

- **Use when:** faces were built independently and you need them connected (a
  prerequisite for `MakeSolid`).
- **Limit:** the tolerance must be **larger than the gap** between faces but
  **smaller than the distance between distinct edges** — too tight leaves the
  shell open, too loose fuses edges that shouldn't merge.

## B.2 `ShapeFix` — Face / Shape / Solid

Healers that repair wire order/orientation, tolerance mismatches, and (for solids)
face orientation. Used in [Units 6](06-wires-and-trimming.md),
[7](07-pcurves-and-curved-trimming.md), [12](12-shells-and-solids.md).

- `ShapeFix_Face` — fixes a face's wires (ordering, orientation, missing pcurves).
- `ShapeFix_Shape` — generic healer; walks a whole shape.
- `ShapeFix_Solid` — fixes shell/solid orientation so normals point outward.
- **Limit:** `ShapeFix_Solid` can only orient a **closed solid** — it has nothing
  to reason about on an open sheet, a lone face, or a non-manifold body. If you
  have the data, the sense rule in [Appendix A](15-appendix-reading-real-data.md#a1-face-orientation--from-facesense-vs-surfsense)
  is exact and works in all those cases.

## B.3 `BRepLib.BuildCurves3d_s` — synthesize missing 3D curves

Given a face whose edges carry only **pcurves** (2D curves in the surface's
parameter space), this maps each pcurve through the surface to build the missing
**3D curve**, so the face can be meshed. The key step in
[Unit 7](07-pcurves-and-curved-trimming.md).

- **Use when:** an edge has a pcurve but no 3D curve (a "pcurve-only" edge).
- **Limit:** it can only synthesize a 3D curve when a **pcurve exists** to map; it
  cannot invent geometry from nothing.

## B.4 `BRepCheck_Analyzer` — the validity truth-test

`BRepCheck_Analyzer(shape).IsValid()` returns `True` for a well-formed,
closed, correctly-oriented shape. The final gate in [Unit 12](12-shells-and-solids.md).

```python
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeFix import ShapeFix_Shape

solid = BRepPrimAPI_MakeBox(10., 10., 10.).Solid()
print("valid before:", BRepCheck_Analyzer(solid).IsValid())

fix = ShapeFix_Shape(solid)        # generic healer
fix.Perform()
healed = fix.Shape()
print("valid after :", BRepCheck_Analyzer(healed).IsValid())
```

- **Use when:** you want a yes/no gate after building or repairing a shape.
- **Tip:** pair it with `BRepGProp` volume ([Unit 12](12-shells-and-solids.md)) —
  a valid solid with a correct, positive volume is the strongest "it's really a
  solid" signal.

## B.5 Deterministic vs. repair — which to reach for

| Situation                                      | Reach for                                                      |
| ---------------------------------------------- | -------------------------------------------------------------- |
| You have the source senses / regions / fins    | **Read them** ([Appendix A](15-appendix-reading-real-data.md)) |
| Building from scratch / synthetic geometry     | Repair tools (this appendix)                                   |
| Edge has a pcurve but no 3D curve              | `BuildCurves3d_s` (B.3)                                        |
| Independently-built faces, small gaps to close | `Sewing` with tolerance (B.1)                                  |
| Wire/orientation/tolerance glitches            | `ShapeFix_*` (B.2)                                             |
| Final correctness gate                         | `BRepCheck_Analyzer` (B.4)                                     |

The rule of thumb: **repair is a fallback, not the plan.** A reader that has the
model data should use [Appendix A](15-appendix-reading-real-data.md) for
orientation, material side, and edge direction, and keep these repair tools for
the gaps and for sanity-checking the result.

---

See also: [Appendix A — Reading Real B-rep Data](15-appendix-reading-real-data.md) ·
[Unit 12 — Shells & Solids](12-shells-and-solids.md) · back to the
[course index](README.md).
