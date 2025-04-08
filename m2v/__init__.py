"""
M2V (MIDI To Visuals) is a Blender addon that generates 3D animations from MIDI files.
"""
import bpy # type: ignore  # pylint: disable=import-error
from .operators.ops import OT_GenerateAnimation
from .ui.panels import Properties, PT_MainPanel, OT_OpenMidiFile

# Register classes
classes = (
    Properties,
    OT_OpenMidiFile,
    OT_GenerateAnimation,
    PT_MainPanel,
)

def register():
    """
    Register all classes and create a Scene property for M2V addon.

    This function performs the following actions:
    1. Registers all classes defined in the 'classes' list with Blender
    2. Creates a pointer property 'M2V' in the Scene type that points to Properties

    Note:
        This function should be called when the addon is enabled/registered in Blender.

    Dependencies:
        - bpy: Blender Python API
        - classes: List of classes to be registered
        - Properties: Property group class for storing addon properties
    """
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.M2V = bpy.props.PointerProperty(type=Properties)

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
