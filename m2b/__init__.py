"""
M2V (MIDI To Visuals) is a Blender addon that generates 3D animations from MIDI files.
"""
import bpy # type: ignore  # pylint: disable=import-error
from .operators.M2V_ops import M2V_OT_GenerateAnimation
from .ui.panels import M2V_Properties, M2V_PT_MainPanel, M2V_OT_OpenMidiFile

# bl_info = {
#     "name": "M2V - MIDI To Visuals",
#     "author": "Patochun (Patrick M)",
#     "version": (10, 0),
#     "blender": (4, 0, 0),
#     "location": "View3D > Sidebar > M2V",
#     "description": "Generate 3D animations from MIDI files",
#     "category": "Animation"
# }

# Register classes
classes = (
    M2V_Properties,
    M2V_OT_OpenMidiFile,
    M2V_OT_GenerateAnimation,
    M2V_PT_MainPanel,
)

def register():
    """
    Register all classes and create a Scene property for M2V addon.

    This function performs the following actions:
    1. Registers all classes defined in the 'classes' list with Blender
    2. Creates a pointer property 'M2V' in the Scene type that points to M2V_Properties

    Note:
        This function should be called when the addon is enabled/registered in Blender.

    Dependencies:
        - bpy: Blender Python API
        - classes: List of classes to be registered
        - M2V_Properties: Property group class for storing addon properties
    """
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.M2V = bpy.props.PointerProperty(type=M2V_Properties)

def unregister():
    """
    Unregisters all classes associated with M2V addon from Blender's API.

    This function performs cleanup when the addon is disabled or removed:
    1. Unregisters all classes in reverse order of registration
    2. Removes the M2V property group from the Scene type

    Raises:
        AttributeError: If bpy.types.Scene.M2V or any class fails to unregister
    """
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.M2V

if __name__ == "__main__":
    register()
