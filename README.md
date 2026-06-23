# OCP: From Surfaces to Solids

Learning [OpenCASCADE](https://www.opencascade.com/) (OCCT) through its Python
bindings [**OCP**](https://github.com/CadQuery/OCP), with one concrete goal:

> **Build B-rep surfaces and solids in code and render them** — from a single
> plane to a full trimmed, watertight solid.

The rendering side is already solved by [`vis.py`](vis.py), which meshes any
OCCT shape and draws it with VTK. The thing this repo teaches is the **missing
middle**: turning surface and boundary definitions (frames, curves, knots) into
trimmed `TopoDS_Face`s — and sewing those into watertight `TopoDS_Solid`s — that
`vis.show()` can display, up to a full, real mechanical part.

All examples use **hard-coded values** — no model files are parsed, so you can
learn the API in isolation.

## Motivation

I wanted to learn OpenCASCADE but didn't know where to begin — so I asked Claude
to plan a course for me, and I'm working through it here. This repo is both that
course and my progress through it.

## Why OCP?

[OCP](https://github.com/CadQuery/OCP) is a straightforward Python binding to
OpenCASCADE: `pip install cadquery-ocp` and you're done — **no conda environment
required**. That keeps the whole setup a plain `venv` + `pip`, so the focus stays
on the geometry instead of on toolchain wrangling.

## Repo layout

| Path                                   | What it is                                                            |
| -------------------------------------- | --------------------------------------------------------------------- |
| [`course/`](course/)                   | The learning course — start at [`course/README.md`](course/README.md) |
| [`vis.py`](vis.py)                     | `vis.show(shape)` — meshes a shape and renders it in a VTK window     |
| [`hello.py`](hello.py)                 | Smallest possible example: make a cylinder primitive, show it         |
| [`requirements.txt`](requirements.txt) | `cadquery-ocp`, stubs, and `vtk`                                      |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify everything works — this opens an interactive 3D window with a cylinder:

```bash
python hello.py
```

Rotate with the mouse (trackball controls), scroll to zoom, `q` to quit.

## The course

A 15-unit course (plus two appendices) takes you from your first face to a full
trimmed **solid** — surfaces, curves, trimming, pcurves, intersections, NURBS,
then sewing, solids, and booleans. It all lives in [`course/`](course/) and uses
only hard-coded values.

**→ Start at [`course/README.md`](course/README.md)** — it has the full unit
list, the 4-step pipeline every unit follows, the appendices, and the
run-it-yourself conventions.

## Acknowledgements

- [**CadQuery OCP**](https://github.com/CadQuery/OCP) — the OpenCASCADE Python
  bindings this course is built on, and the reason OCCT is a single `pip install`
  away. Thank you.
- [OpenCASCADE (OCCT)](https://www.opencascade.com/) — the underlying B-rep kernel.
- [VTK](https://vtk.org/) — the renderer behind [`vis.py`](vis.py).
- [Claude](https://claude.ai) — planned and wrote this course with me, and verified
  every example against the real OCP.

## License

Released under the MIT License — see [`LICENSE`](LICENSE).
