"""
This example demonstrates how to create a box shape directly
using the OCCT API and then visualize it using VTK.
"""

# pylint: disable=no-name-in-module
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder

# pylint: enable=no-name-in-module
import vis

mk_cylinder = BRepPrimAPI_MakeCylinder(5.0, 20.0)
my_cylinder_shape = mk_cylinder.Shape()

print("Cylinder shape successfully created directly via OCCT API.")
vis.show(my_cylinder_shape)
