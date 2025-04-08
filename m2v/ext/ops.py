
"""
Blender operator for generating MIDI-to-Blender animations.
This operator takes MIDI and audio files as input and creates animated visualizations in Blender.
It handles initialization of collections, materials, and nodes, processes MIDI data, and generates
the final animation based on user-selected parameters.
"""
from time import time
from math import ceil
import bpy # type: ignore  # pylint: disable=import-error
from ..engine.globals import glb
from ..engine.utils.stuff import init_log, w_log, end_log, create_compositor_nodes, determine_global_ranges, load_audio
from ..engine.utils.midi import read_midi_file
from ..engine.utils.collection import init_collections
from ..engine.utils.object import init_materials
from ..engine.animations.animate import animate

class OT_GenerateAnimation(bpy.types.Operator):
    """
    Blender operator to generate music visualization animation from MIDI and audio files.
    This operator processes MIDI and audio files to create synchronized animations in Blender.
    It handles the complete workflow from initialization to final compositor setup.
    """
    # bl_idname = "m2v.generate_animation"
    bl_idname = "scene.m2v_generate_animation"
    bl_label = "Generate Animation"

    @classmethod
    def poll(cls, context):
        """
        Poll function to check if the operator can be executed.
        """
        # Check if we're in Object mode and in a 3D Viewport area
        return (
            context.mode == 'OBJECT'
            and context.area is not None
            and context.area.type == 'VIEW_3D'
        )

    def execute(self, context):
        """
        Executes the main MIDI to Blender (m2v) animation generation process.
        The function performs the following key steps:
        1. Initializes logging and collections
        2. Sets up required materials
        3. Loads audio file
        4. Reads and processes MIDI file
        5. Determines global ranges for notes
        6. Generates animation based on specified parameters
        7. Sets up compositor nodes
        """

        scene = context.scene
        m2b = scene.m2b

        # Initialize
        paths = {
            "midi": m2b.midi_file,
            "audio": m2b.audio_file,
            "log": m2b.midi_file + ".log"
        }

        try:
            time_start = time()

            # Core M2V logic
            init_log(paths["log"])
            init_collections()
            init_materials()
            glb.fps = scene.render.fps

            load_audio(paths["audio"])

            midi_file, _, glb.tracks = read_midi_file(paths["midi"])

            w_log(f"Midi type = {midi_file.midi_format}")
            w_log(f"animation type = {m2b.animation_type}")
            w_log(f"track mask = {m2b.track_mask}")
            w_log(f"animation style = {m2b.animation_style}")

            (_, _, _, glb.last_note_time_off,
            note_mid_range_all_tracks) = determine_global_ranges()

            w_log(f"Note mid range for all tracks: {note_mid_range_all_tracks}")

            animate(m2b.animation_type, m2b.track_mask, m2b.animation_style)

            bpy.context.scene.frame_end = ceil(glb.last_note_time_off + 5) * glb.fps
            create_compositor_nodes()

            w_log(f"Script Finished: {time() - time_start:.2f} sec")
            end_log()

            self.report({'INFO'}, "Animation generated successfully")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}
