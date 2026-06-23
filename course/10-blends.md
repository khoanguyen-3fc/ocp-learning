# Unit 10 — Blends / Fillets (Stretch)

**Goal:** understand what blend/fillet surfaces are, why they're the hardest to
reconstruct by hand, and what your practical options are.

Difficulty: ⭐⭐⭐⭐⭐ — optional. Skip on a first pass.

---

## The concept

A **blend** (or **fillet**) is the smooth, rounded transition surface where two
other faces meet — the rounded edge of a phone, the smooth root where a blade
joins a hub. The classic case is a **rolling-ball blend**: imagine a ball of
fixed radius rolling along the crease between two surfaces; the surface it
sweeps out is the fillet.

The key difference from the surfaces in Units 1–9: a blend is a **derived**
surface. It isn't defined by its own simple frame + radius — it's defined
_relative to its two neighbor surfaces and the edge between them_. Its true
boundary curves are often **surface–surface intersection curves** (Unit 8), which
have no tidy closed form.

## Why it's hard to build from hard-coded values

For the analytic surfaces you typed in a frame and a couple of numbers. A blend
has no such compact description you can just paste:

- its shape depends on the two adjacent surfaces and the edge geometry,
- its edges are intersection curves (computed, not given — see Unit 8),
- exporters often store it as an already-converted **NURBS surface** plus
  trimming data, rather than as "a blend" you can reconstruct.

This is exactly why blend faces are the ones that fail to rebuild when you only
have a surface-type summary — the summary doesn't carry enough to regenerate the
geometry.

## Your practical options

In order of preference for a "render the surfaces" goal:

1. **Skip them.** If the blends are small fillets, dropping them leaves the model
   readable — you'll see sharp edges where the rounds were. Perfectly fine while
   learning. Just note in your output which faces were skipped. (The robust
   skip-and-log loop is in Units 8 and 11.)

2. **Represent the blend as a NURBS surface** ([Unit 9](09-nurbs-bspline-surface.md)).
   If you have (or can sample) a control-point grid for the fillet, build it as a
   `Geom_BSplineSurface` like any other free-form patch. The renderer doesn't
   care that it "is" a blend.

3. **Generate the fillet with OCCT** (advanced, and a different workflow): build
   the two neighbor solids/faces and let OCCT compute the fillet for you with
   `BRepFilletAPI_MakeFillet`. This _creates_ a blend rather than reconstructing
   one from data, so it only helps if you're modeling from scratch.

## What to actually do

For this course: **recognize a blend, and skip it (option 1)** unless a specific
model makes the missing fillets unacceptable — in which case reach for option 2.
Don't sink days into reconstructing fillets by hand; that's a rabbit hole well
outside "cover the surfaces."

## Exercises (optional)

1. Take two boxes that share an edge and use `BRepFilletAPI_MakeFillet` to round
   it — see a blend _generated_ so you know what one looks like.
2. Approximate a quarter-round fillet as a NURBS patch (Unit 9) and convince
   yourself the renderer treats it identically to any other surface.

## Checkpoint

You can explain what a blend is, why it resists hard-coded reconstruction, and
you have a default plan (skip, or model as NURBS).

**Next:** [Unit 11 — Combine Many Faces](11-combine-and-render.md) — assemble
everything into one rendered model.
