"""Class shared by all"""

from enum import Enum
class BlenderObjectTypes(Enum):
    """
    Enumeration of supported Blender object types.

    This enum defines the available primitive and custom object types that can be created
    in Blender through the M2V engine.

    Attributes:
        PLANE: A flat rectangular surface
        ICOSPHERE: A sphere made of triangular faces
        UVSPHERE: A UV-mapped sphere made of quad faces
        CUBE: A six-sided box
        CYLINDER: A circular cylinder
        BEZIER_CIRCLE: A circular curve using Bezier interpolation
        LIGHTSHOW: A custom object type for light animations
        POINT: A single point light in 3D space
        EMPTY: An empty object that can be used as a parent or placeholder
    """
    PLANE = "plane"
    ICOSPHERE = "icosphere"
    UVSPHERE = "uvsphere"
    CUBE = "cube"
    CYLINDER = "cylinder"
    BEZIER_CIRCLE = "bezier_circle"
    LIGHTSHOW = "lightshow"
    POINT = "point"
    EMPTY = "empty"
    
   

class GlobalState:
    """Some datas with global scope"""
    def __init__(self):
        self.fps = 0
        self.tracks = []
        self.last_note_time_off = 0.0
        self.mat_global_custom: None
        self.master_collection: None
        self.master_loc_collection: None
        self.hidden_collection: None
        self.f_log: None

glb = GlobalState()
