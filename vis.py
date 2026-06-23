"""
This module provides a function to visualize a shape using VTK.
"""

import math

# pylint: disable=no-name-in-module
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
from vtkmodules.vtkFiltersCore import vtkFeatureEdges, vtkPolyDataNormals
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

# pylint: enable=no-name-in-module


def triangulate(shape):
    """Triangulate a shape and return the points and cells for VTK."""

    BRepMesh_IncrementalMesh(shape, 0.1, False, 0.1).Perform()

    points = vtkPoints()
    cells = vtkCellArray()
    explorer = TopExp_Explorer(shape, TopAbs_FACE)

    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        location = TopLoc_Location()
        triangulation = BRep_Tool.Triangulation_s(face, location)

        if triangulation is not None:
            offset = points.GetNumberOfPoints()
            apply_trsf = not location.IsIdentity()
            trsf = location.Transformation() if apply_trsf else None

            for i in range(1, triangulation.NbNodes() + 1):
                n = triangulation.Node(i)
                if apply_trsf:
                    n = n.Transformed(trsf)
                points.InsertNextPoint(n.X(), n.Y(), n.Z())

            for i in range(1, triangulation.NbTriangles() + 1):
                n1, n2, n3 = triangulation.Triangle(i).Get()
                cells.InsertNextCell(3)
                cells.InsertCellPoint(offset + n1 - 1)
                cells.InsertCellPoint(offset + n2 - 1)
                cells.InsertCellPoint(offset + n3 - 1)

        explorer.Next()
    return points, cells


def build_actors(points, cells):
    """Build VTK actors for the faces and edges of the shape."""

    polydata = vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(cells)

    normals = vtkPolyDataNormals()
    normals.SetInputData(polydata)
    normals.ComputePointNormalsOn()
    normals.SetFeatureAngle(30)

    face_mapper = vtkPolyDataMapper()
    face_mapper.SetInputConnection(normals.GetOutputPort())

    face_actor = vtkActor()
    face_actor.SetMapper(face_mapper)
    face_actor.GetProperty().SetOpacity(0.8)

    edges = vtkFeatureEdges()
    edges.SetInputData(polydata)

    edge_mapper = vtkPolyDataMapper()
    edge_mapper.SetInputConnection(edges.GetOutputPort())

    edge_actor = vtkActor()
    edge_actor.SetMapper(edge_mapper)
    edge_actor.GetProperty().SetLineWidth(2)
    return face_actor, edge_actor


def show(shape):
    """Visualize a shape using VTK."""

    points, cells = triangulate(shape)

    face_actor, edge_actor = build_actors(points, cells)

    renderer = vtkRenderer()
    renderer.AddActor(face_actor)
    renderer.AddActor(edge_actor)
    renderer.GradientBackgroundOn()
    renderer.SetUseFXAA(True)

    camera = renderer.GetActiveCamera()
    camera.SetPosition(
        [
            math.sin(math.radians(115)),
            math.cos(math.radians(115)),
            math.tan(math.radians(35)),
        ]
    )
    camera.SetFocalPoint(0, 0, 0)
    camera.SetViewUp(0, 0, 1)
    renderer.ResetCamera()

    win = vtkRenderWindow()
    win.SetSize(1280, 960)
    win.AddRenderer(renderer)

    inter = vtkRenderWindowInteractor()
    inter.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
    inter.SetRenderWindow(win)

    axes = vtkAxesActor()
    widget = vtkOrientationMarkerWidget()
    widget.SetOrientationMarker(axes)
    widget.SetInteractor(inter)
    widget.EnabledOn()
    widget.InteractiveOff()

    inter.Initialize()
    win.Render()
    inter.Start()
