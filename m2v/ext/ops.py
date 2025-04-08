
"""
Blender operator for generating MIDI-to-Blender animations.
This operator takes MIDI and audio files as input and creates animated visualizations in Blender.
It handles initialization of collections, materials, and nodes, processes MIDI data, and generates
the final animation based on user-selected parameters.
Attributes:
    bl_idname (str): Unique identifier for the operator ('generate_animation')
    bl_label (str): Display name for the operator in Blender UI ('Generate Animation')
Returns:
    Set[str]: Blender operator return set
        {'FINISHED'} - On successful execution
        {'CANCELLED'} - If an error occurs during execution
Raises:
    Exception: Any error during the animation generation process will be caught and reported
Note:
    This operator requires the following scene properties to be set:
    - m2b.midi_file: Path to input MIDI file
    - m2b.audio_file: Path to input audio file
    - m2b.animation_type: Type of animation to generate
    - m2b.track_mask: Track selection mask
    - m2b.animation_style: Style of animation
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
    Attributes:
        bl_idname (str): Internal name of the operator, "m2v.generate_animation"
        bl_label (str): Display name of the operator, "Generate Animation"
    Returns:
        dict: Status set containing 'FINISHED' on success or 'CANCELLED' on error
    Raises:
        Exception: Any error during the animation generation process will be caught and reported
    The operator performs the following key steps:
    1. Initializes logging, collections and materials
    2. Loads audio file
    3. Processes MIDI file and tracks
    4. Determines global ranges for notes
    5. Generates animation based on selected type, track mask and style
    6. Sets up compositor nodes
    """
    bl_idname = "m2v.generate_animation"
    bl_label = "Generate Animation"

    def execute(self, context):
        """
        Executes the main MIDI to Blender (m2v) animation generation process.
        This method processes MIDI and audio files to create animations in Blender.
        It handles the full workflow from initialization to final compositor setup.
        Args:
            context: Blender context containing scene and other relevant data
        Returns:
            dict: Status dictionary
                - {'FINISHED'} if animation generation was successful
                - {'CANCELLED'} if an error occurred during execution
        Raises:
            Various exceptions may be raised during MIDI processing, audio loading,
            or animation generation
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
