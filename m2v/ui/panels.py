"""
Main panel for M2V (MIDI to Blender) addon implementation.
This class creates and manages the main panel interface for the MIDI to Blender (M2B) addon
in Blender's 3D View sidebar. It provides a user interface for selecting MIDI and audio files,
configuring animation settings, and generating animations based on MIDI data.
Class Attributes:
    bl_label (str): Display name of the panel in Blender's UI
    bl_idname (str): Unique identifier for the panel
    bl_space_type (str): Blender editor type where the panel appears (3D View)
    bl_region_type (str): Region of the editor where the panel appears (UI sidebar)
    bl_category (str): Tab category name in the sidebar
Properties (accessed via context.scene.m2b):
    midi_file (str): Path to the input MIDI file
    audio_file (str): Path to the accompanying audio file
    animation_type (enum): Type of animation to generate
    track_mask (str): Selection mask for MIDI tracks
    animation_style (enum): Style preset for the generated animation
    draw(context): Creates and arranges UI elements in the panel
Example:
    This panel is automatically registered with Blender's UI system and appears
    in the 3D View sidebar under the 'M2B' tab when the addon is enabled.
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
    m2b = context.scene.m2b
    current_type = m2b.animation_type
    return animation_styles.get(current_type, [])

def update_animation_style(self, context):
    """Callback to update animation style from type"""
    m2b = context.scene.m2b
    current_type = m2b.animation_type
    styles = animation_styles.get(current_type, [])

    # Reset animation style if not in the list of styles
    if m2b.animation_style not in [style[0] for style in styles]:
        m2b.animation_style = styles[0][0] if styles else ""

def update_midi_file(self, context):
    """Callback to update midi file"""
    m2b = context.scene.m2b
    current_midi_file = m2b.midi_file
    name_without_ext = os.path.splitext(current_midi_file)[0]
    current_audio_file = name_without_ext + ".mp3"
    if os.path.exists(current_audio_file):
        m2b.audio_file = current_audio_file
    else:
        m2b.audio_file = ""

class M2B_Properties(bpy.types.PropertyGroup):
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
    bl_idname = "m2b.open_midi_file"
    bl_label = "Open MIDI File"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default="*.mid",
        options={'HIDDEN'}
    )

    def execute(self, context):
        m2b = context.scene.m2b
        m2b.midi_file = self.filepath
        return {'FINISHED'}

class PT_MainPanel(bpy.types.Panel):
    """
    Main panel for M2V (MIDI to Blender) addon.
    This panel provides the main interface for the MIDI to Blender animation generator.
    Located in the 3D View's sidebar under the 'M2B' category.
    """
    bl_label = "M2V - MIDI to Visuals"
    bl_idname = "PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'M2B'

    def draw(self, context):
        """Draw the main M2V panel layout in Blender."""
        layout = self.layout
        m2b = context.scene.m2b

        box = layout.box()
        box.label(text="MIDI File:")
        box.operator("m2b.open_midi_file")
        # box.prop(m2b, "midi_file", text="")
        box.prop(m2b, "audio_file")

        box = layout.box()
        box.prop(m2b, "animation_type")
        box.prop(m2b, "animation_style")
        box.prop(m2b, "track_mask")

        row = layout.row()
        row.scale_y = 2.0
        row.operator("m2b.generate_animation")
