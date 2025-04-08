"""
M2B (MIDI to Blender) is a Blender addon that generates 3D animations from MIDI files.
"""
import bpy # type: ignore  # pylint: disable=import-error
from .operators.m2b_ops import M2B_OT_GenerateAnimation
from .ui.panels import M2B_Properties, M2B_PT_MainPanel, M2B_OT_OpenMidiFile

# bl_info = {
#     "name": "M2B - MIDI to Blender",
#     "author": "Patochun (Patrick M)",
#     "version": (10, 0),
#     "blender": (4, 0, 0),
#     "location": "View3D > Sidebar > M2B",
#     "description": "Generate 3D animations from MIDI files",
#     "category": "Animation"
# }

# Register classes
classes = (
    M2B_Properties,
    M2B_OT_OpenMidiFile,
    M2B_OT_GenerateAnimation,
    M2B_PT_MainPanel,
)

def register():
    """
    Register all classes and create a Scene property for M2B addon.

    This function performs the following actions:
    1. Registers all classes defined in the 'classes' list with Blender
    2. Creates a pointer property 'm2b' in the Scene type that points to M2B_Properties

    Note:
        This function should be called when the addon is enabled/registered in Blender.

    Dependencies:
        - bpy: Blender Python API
        - classes: List of classes to be registered
        - M2B_Properties: Property group class for storing addon properties
    """
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.m2b = bpy.props.PointerProperty(type=M2B_Properties)

def unregister():
    """
    Unregisters all classes associated with M2B addon from Blender's API.

    This function performs cleanup when the addon is disabled or removed:
    1. Unregisters all classes in reverse order of registration
    2. Removes the m2b property group from the Scene type

    Raises:
        AttributeError: If bpy.types.Scene.m2b or any class fails to unregister
    """
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.m2b

if __name__ == "__main__":
    register()
