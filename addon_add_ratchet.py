# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Ratchet Gear",
    "author": "Francis Joseph Serina",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > Gears > Ratchet",
    "description": "Adds a new Ratchet Gear",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import bpy
from bpy.types import Operator
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    EnumProperty
)
from bpy_extras.object_utils import AddObjectHelper, object_data_add
import math

def polar_coords(radius, angleRad, z = 0):
    vert = (radius * math.cos(angleRad), radius * math.sin(angleRad), z)
    return vert

def flip_face(face):
    newFace = face[::-1]
    return newFace

def flip_faces(faces):
    newFaces = []
    for f in faces:
        newFaces.append(flip_face(f))
    return newFaces

def bridge_upper_lower_teeth(numVerts, startIdxUpper, startIdxLower):
    faces = []
    for i in range(numVerts - 1):
        face = (i + startIdxUpper + 1, i + startIdxUpper, i + startIdxLower, i + startIdxLower + 1)
        faces.append(face)
    face = (startIdxUpper, startIdxUpper + numVerts - 1, startIdxLower + numVerts - 1, startIdxLower)
    faces.append(face)
    return faces

def bridge_teeth_base_external(vertPerTooth, baseStartIdx, baseEndIdx, teethStartIdx, teethEndIdx):
    faces = []
    j = teethStartIdx
    for i in range(baseStartIdx, baseEndIdx):
        if (j % ( vertPerTooth ) == 0):
            j += 1
        if ((j + 1) % ( vertPerTooth ) == 0):
            face = (i + 1, i, j, j + 1, j + 2)
        else:
            face = (i + 1, i, j, j + 1)
        j += 1
        faces.append(face)
    face = (baseStartIdx, baseEndIdx, teethEndIdx, teethStartIdx, teethStartIdx + 1)
    faces.append(face)
    return faces

def bridge_teeth_base_internal(vertPerTooth, baseStartIdx, baseEndIdx, teethStartIdx, teethEndIdx):
    faces = []
    j = teethStartIdx
    for i in range(baseStartIdx, baseEndIdx):
        if (j % vertPerTooth == 0):
            face = (i + 1, i, j, j + 1, j + 2)
            j += 1
        else:
            face = (i + 1, i, j, j + 1)
        j += 1
        faces.append(face)
    face = (baseStartIdx, baseEndIdx, teethEndIdx, teethStartIdx)
    faces.append(face)
    return faces

def add_faces_external(numVertsTeeth, vertPerTooth,
        startIdxUpperTeeth, endIdxUpperTeeth,
        startIdxLowerTeeth, endIdxLowerTeeth,
        startIdxUpperBase, endIdxUpperBase,
        startIdxLowerBase, endIdxLowerBase):
    faces = []

    faces.extend(
        bridge_upper_lower_teeth( numVertsTeeth,
            startIdxUpperTeeth, startIdxLowerTeeth
        )
    )

    faces.extend(
        bridge_teeth_base_external( vertPerTooth,
            startIdxUpperBase, endIdxUpperBase,
            startIdxUpperTeeth, endIdxUpperTeeth
        )
    )

    faces.extend( flip_faces(
        bridge_teeth_base_external( vertPerTooth,
            startIdxLowerBase, endIdxLowerBase,
            startIdxLowerTeeth, endIdxLowerTeeth
        )
    ))
    return faces

def add_faces_internal(numVertsTeeth, vertPerTooth,
        startIdxUpperTeeth, endIdxUpperTeeth,
        startIdxLowerTeeth, endIdxLowerTeeth,
        startIdxUpperBase, endIdxUpperBase,
        startIdxLowerBase, endIdxLowerBase):
    faces = []

    faces.extend( flip_faces(
        bridge_upper_lower_teeth( numVertsTeeth,
            startIdxUpperTeeth, startIdxLowerTeeth
        )
    ))

    faces.extend( flip_faces(
        bridge_teeth_base_internal( vertPerTooth,
            startIdxUpperBase, endIdxUpperBase,
            startIdxUpperTeeth, endIdxUpperTeeth
        )
    ))

    faces.extend(
        bridge_teeth_base_internal( vertPerTooth,
            startIdxLowerBase, endIdxLowerBase,
            startIdxLowerTeeth, endIdxLowerTeeth
        )
    )
    return faces

def create_teeth(vertPerTooth, numSegments, radius, addendum, z):
    verts = []
    for i in range(numSegments):
        angleRad = math.radians(i * 360.0 / numSegments)
        if (i % vertPerTooth == 0):
            vert = polar_coords(radius + addendum, angleRad, z)
            verts.append(vert)
        radiusAdd = ( (i % vertPerTooth ) / (vertPerTooth) ) * addendum
        vert = polar_coords(radius + radiusAdd, angleRad, z)
        verts.append(vert)
    return verts

def create_base(radius, numSegments, z):
    angleRad = math.radians( 360.0 / numSegments)
    verts = [polar_coords(radius, angleRad * i, z) for i in range(numSegments) ]
    return verts

def add_object(self, context):
    verts = []
    faces = []
    
    numSegments = (self.vertPerTooth - 1) * self.numTeeth
    
    vertsUpperTeeth = create_teeth(self.vertPerTooth - 1, numSegments, self.radius, self.addendum, self.width / 2.0)
    vertsLowerTeeth = create_teeth(self.vertPerTooth - 1, numSegments, self.radius, self.addendum, -self.width / 2.0)
    vertsUpperTeethStartIdx = len(verts)
    verts.extend(vertsUpperTeeth)
    vertsLowerTeethStartIdx = len(verts)
    verts.extend(vertsLowerTeeth)

    if self.internality == 'EXTERNAL':
        vertsUpperBase = create_base(self.radius - self.base, numSegments, self.width / 2.0)
        vertsLowerBase = create_base(self.radius - self.base, numSegments, -self.width / 2.0)
    elif self.internality == 'INTERNAL':
        vertsUpperBase = create_base(self.radius + self.base + self.addendum, numSegments, self.width / 2.0)
        vertsLowerBase = create_base(self.radius + self.base + self.addendum, numSegments, -self.width / 2.0)
    vertsUpperBaseStartIdx = len(verts)
    verts.extend(vertsUpperBase)
    vertsLowerBaseStartIdx = len(verts)
    verts.extend(vertsLowerBase)
    
    if self.internality == 'EXTERNAL':
        faces = add_faces_external(vertsLowerTeethStartIdx, self.vertPerTooth,
            vertsUpperTeethStartIdx, vertsLowerTeethStartIdx - 1,
            vertsLowerTeethStartIdx, vertsUpperBaseStartIdx - 1,
            vertsUpperBaseStartIdx, vertsLowerBaseStartIdx - 1,
            vertsLowerBaseStartIdx, len(verts) -1)
    elif self.internality == 'INTERNAL':
        faces = add_faces_internal(vertsLowerTeethStartIdx, self.vertPerTooth,
            vertsUpperTeethStartIdx, vertsLowerTeethStartIdx - 1,
            vertsLowerTeethStartIdx, vertsUpperBaseStartIdx - 1,
            vertsUpperBaseStartIdx, vertsLowerBaseStartIdx - 1,
            vertsLowerBaseStartIdx, len(verts) -1)
    
    mesh = bpy.data.meshes.new(name="Ratchet")
    mesh.from_pydata(verts, [], faces)

    # useful for development when the mesh may be invalid.
    mesh.validate(verbose=True)
    object_data_add(context, mesh, operator=self)


class AddRatchetGear(Operator, AddObjectHelper):
    """Create a new Ratchet Gear"""
    bl_idname = "mesh.primitive_ratchet"
    bl_label = "Add Ratchet"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    RatchetGear: BoolProperty(name = "Ratchet",
        default = True,
        description = "Ratchet")
        
    #### change properties
    name: StringProperty(name = "Name",
        description = "Name")

    change: BoolProperty(name = "Change",
        default = False,
        description = "change Gear")
        
    numTeeth: IntProperty(
        name="Number of Teeth",
        description="Number of teeth on the gear",
        default=10,
        min=3,
        soft_max=1000,
    )
    
    vertPerTooth: IntProperty(
        name="Vertices per Tooth",
        description="Number of Vertices per tooth, more for smoother",
        default=4,
        min=2,
        soft_max=100
    )
    
    internality: EnumProperty(
        name="Internality",
        default='EXTERNAL',
        description="Internality state of the gear",
        items=[('INTERNAL', 'Internal', 'Teeth point inwards'),
            ('EXTERNAL', 'External', 'Teeth point outwards')]
    )

    radius: FloatProperty(name="Radius",
        description="Radius of the gear, negative for crown gear",
        min=0.0,
        soft_max=1000.0,
        unit='LENGTH',
        default=1.0
    )
    
    addendum: FloatProperty(name="Addendum",
        description="Addendum, extent of tooth above radius",
        min=0.0,
        soft_max=1000.0,
        unit='LENGTH',
        default=0.5
    )
    
    base: FloatProperty(name="Base",
        description="Base, extent of gear below radius",
        min=0.0,
        soft_max=1000.0,
        unit='LENGTH',
        default=0.2
    )
    
    width: FloatProperty(name="Width",
        description="Width, thickness of gear",
        min=0.0,
        soft_max=1000.0,
        unit='LENGTH',
        default=0.2
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self, 'numTeeth')
        box.prop(self, 'vertPerTooth')

        box = layout.box()
        box.prop(self, 'radius')
        box.prop(self, 'base')
        box.prop(self, 'width')
        box.prop(self, 'addendum')

        box = layout.box()
        box.prop(self, 'internality')

        if self.change == False:
            # generic transform props
            box = layout.box()
            box.prop(self, 'align', expand=True)
            box.prop(self, 'location', expand=True)
            box.prop(self, 'rotation', expand=True)
            
    def execute(self, context):

        add_object(self, context)

        return {'FINISHED'}


# Registration

def add_object_button(self, context):
    self.layout.operator(
        AddRatchetGear.bl_idname,
        icon='PREFERENCES',
        text="Ratchet")


# This allows you to right click on a button and link to documentation
def add_object_manual_map():
    url_manual_prefix = "https://docs.blender.org/manual/en/latest/"
    url_manual_mapping = (
        ("bpy.ops.mesh.add_object", "scene_layout/object/types.html"),
    )
    return url_manual_prefix, url_manual_mapping


def register():
    bpy.utils.register_class(AddRatchetGear)
    bpy.utils.register_manual_map(add_object_manual_map)
    bpy.types.VIEW3D_MT_mesh_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(AddRatchetGear)
    bpy.utils.unregister_manual_map(add_object_manual_map)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_object_button)


if __name__ == "__main__":
    register()
