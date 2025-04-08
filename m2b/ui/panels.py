"""
Main panel for M2V (MIDI To Visuals) addon implementation.
This class creates and manages the main panel interface for the MIDI To Visuals (M2V) addon
in Blender's 3D View sidebar. It provides a user interface for selecting MIDI and audio files,
configuring animation settings, and generating animations based on MIDI data.
Class Attributes:
    bl_label (str): Display name of the panel in Blender's UI
    bl_idname (str): Unique identifier for the panel
    bl_space_type (str): Blender editor type where the panel appears (3D View)
    bl_region_type (str): Region of the editor where the panel appears (UI sidebar)
    bl_category (str): Tab category name in the sidebar
Properties (accessed via context.scene.M2V):
    midi_file (str): Path to the input MIDI file
    audio_file (str): Path to the accompanying audio file
    animation_type (enum): Type of animation to generate
    track_mask (str): Selection mask for MIDI tracks
    animation_style (enum): Style preset for the generated animation
    draw(context): Creates and arranges UI elements in the panel
Example:
    This panel is automatically registered with Blender's UI system and appears
    in the 3D View sidebar under the 'M2V' tab when the addon is enabled.
"""
import os
import bpy  # type: ignore  # pylint: disable=import-error
from bpy_extras.io_utils import ImportHelper

# Define animation style from animation type
animation_styles = {
    'barGraph': [
        ('ZSCALE', "Z-Scale", "Scale on Z axis"),
        ('B2R_LIGHT', "Blue to Red Light", "Color gradient from blue to red"),
        ('MULTILIGHT', "Multi light", "Light colors are same as base colors"),
    ],
    'stripNotes': [
        ('ZSCALE', "Z-Scale", "Scale on Z axis"),
        ('B2R_LIGHT', "Blue to Red Light", "Color gradient from blue to red"),
        ('MULTILIGHT', "Multi light", "Light colors are same as base colors"),
    ],
    'waterFall': [
        ('ZSCALE', "Z-Scale", "Scale on Z axis"),
        ('B2R_LIGHT', "Blue to Red Light", "Color gradient from blue to red"),
        ('MULTILIGHT', "Multi light", "Light colors are same as base colors"),
    ],
    'lightShow': [
        ('EEVEE', "EEVEE rendering", "For EEVEE rendering"),
        ('CYCLE', "Cycle rendering", "For CYCLES rendering"),
    ],
    'fountain': [
        ('FOUNTAIN', "fountain mode", "fountain mode"),
    ],
    'fireworksV1': [
        ('SPREAD', "spread mode", "spread mode"),
    ],
    'fireworksV2': [
        ('SPREAD', "spread mode", "spread mode"),
    ],
    # Add other animation types and their styles here
}

def get_animation_styles(self, context):
    """Return the list of styles based on the current animation type."""
    M2V = context.scene.M2V
    current_type = M2V.animation_type
    return animation_styles.get(current_type, [])

def update_animation_style(self, context):
    """Callback to update animation style from type"""
    M2V = context.scene.M2V
    current_type = M2V.animation_type
    styles = animation_styles.get(current_type, [])

    # Reset animation style if not in the list of styles
    if M2V.animation_style not in [style[0] for style in styles]:
        M2V.animation_style = styles[0][0] if styles else ""

def update_midi_file(self, context):
    """Callback to update midi file"""
    M2V = context.scene.M2V
    current_midi_file = M2V.midi_file
    name_without_ext = os.path.splitext(current_midi_file)[0]
    current_audio_file = name_without_ext + ".mp3"
    if os.path.exists(current_audio_file):
        M2V.audio_file = current_audio_file
    else:
        M2V.audio_file = ""

class Properties(bpy.types.PropertyGroup):
    """Properties for M2V add-on"""

    midi_file: bpy.props.StringProperty(
        name="MIDI File",
        description="Path to MIDI file",
        default="",
        subtype='FILE_PATH',
        update=update_midi_file
    )

    audio_file: bpy.props.StringProperty(
        name="Audio File",
        description="Path to audio file for synchronization",
        default="",
        subtype='FILE_PATH'
    )

    animation_type: bpy.props.EnumProperty(
        name="Type",
        description="Type of animation to generate",
        items=[
            ('barGraph', "Bar Graph", "Bar graph visualization"),
            ('stripNotes', "Strip Notes", "Strip notes visualization"),
            ('waterFall', "Waterfall", "Waterfall visualization"),
            ('fireworksV1', "Fireworks V1", "Fireworks version 1"),
            ('fireworksV2', "Fireworks V2", "Fireworks version 2"),
            ('fountain', "Fountain", "Fountain visualization"),
            ('lightShow', "Light Show", "Light show visualization")
        ],
        default='barGraph',
        update=update_animation_style
    )

    animation_style: bpy.props.EnumProperty(
        items=get_animation_styles,  # Use the function to get items
        name="Style",
        description="Style/preset for the generated animation"
    )

    track_mask: bpy.props.StringProperty(
        name="Track Selection",
        description="Track selection pattern (e.g. '0-5,7,9-12' or '*' for all)",
        default="*"
    )

class OT_OpenMidiFile(bpy.types.Operator, ImportHelper):
    """Open MIDI File"""
    bl_idname = "M2V.open_midi_file"
    bl_label = "Open MIDI File"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default="*.mid",
        options={'HIDDEN'}
    )

    def execute(self, context):
        M2V = context.scene.M2V
        M2V.midi_file = self.filepath
        return {'FINISHED'}

class PT_MainPanel(bpy.types.Panel):
    """
    Main panel for M2V (MIDI To Visuals) addon.
    This panel provides the main interface for the MIDI To Visuals animation generator.
    Located in the 3D View's sidebar under the 'M2V' category.
    """
    bl_label = "M2V - MIDI To Visuals"
    bl_idname = "PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'M2V'

    def draw(self, context):
        """Draw the main M2V panel layout in Blender."""
        layout = self.layout
        M2V = context.scene.M2V

        box = layout.box()
        box.label(text="MIDI File:")
        box.operator("M2V.open_midi_file")
        # box.prop(M2V, "midi_file", text="")
        box.prop(M2V, "audio_file")

        box = layout.box()
        box.prop(M2V, "animation_type")
        box.prop(M2V, "animation_style")
        box.prop(M2V, "track_mask")

        row = layout.row()
        row.scale_y = 2.0
        row.operator("M2V.generate_animation")
