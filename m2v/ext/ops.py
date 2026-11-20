
"""Blender operator for generating MIDI-to-Blender animations.

This operator takes MIDI and audio files as input and creates animated visualizations
in Blender. It handles initialization of collections, materials, and nodes, processes
MIDI data, and generates the final animation based on user-selected parameters.
"""

from math import ceil
from time import time

import bpy  # type: ignore  # pylint: disable=import-error

from ..engine.animations.animate import animate
from ..engine.context import set_animation_context, with_animation_context
from ..engine.utils.collection import init_collections
from ..engine.utils.midi import read_midi_file
from ..engine.utils.object import init_materials
from ..engine.utils.stuff import (
    create_compositor_nodes,
    determine_global_ranges,
    end_log,
    init_log,
    load_audio,
    w_log,
)


class OT_GenerateAnimation(bpy.types.Operator):
    """Generate music visualization animation from MIDI and audio files.

    This operator processes MIDI and audio files to create synchronized
    animations in Blender. It handles the complete workflow from
    initialization to final compositor setup.
    """

    bl_idname = "scene.m2v_generate_animation"
    bl_label = "Generate Animation"

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed."""
        return (
            context.mode == "OBJECT"
            and context.area is not None
            and context.area.type == "VIEW_3D"
        )

    def execute(self, context):
        """Execute MIDI to Blender (m2v) animation generation process.

        Steps:
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

        paths = {
            "midi": m2b.midi_file,
            "audio": m2b.audio_file,
            "log": m2b.midi_file + ".log",
        }

        try:
            with with_animation_context() as ctx:
                # Set global compatibility mode
                set_animation_context(ctx)

                time_start = time()

                # Core M2V logic
                init_log(paths["log"], ctx)
                init_collections(ctx)
                init_materials()
                ctx.fps = scene.render.fps

                load_audio(paths["audio"])

                midi_file, _, ctx.tracks = read_midi_file(paths["midi"])

                w_log(f"Midi type = {midi_file.midi_format}", ctx)
                w_log(f"animation type = {m2b.animation_type}", ctx)
                w_log(f"track mask = {m2b.track_mask}", ctx)
                w_log(f"animation style = {m2b.animation_style}", ctx)

                (
                    _,
                    _,
                    _,
                    ctx.last_note_time_off,
                    note_mid_range_all_tracks,
                ) = determine_global_ranges(ctx)

                w_log(
                    f"Note mid range for all tracks: {note_mid_range_all_tracks}",
                    ctx,
                )

                animate(m2b.animation_type, m2b.track_mask, m2b.animation_style)

                bpy.context.scene.frame_end = (
                    ceil(ctx.last_note_time_off + 5) * ctx.fps
                )
                create_compositor_nodes()

                elapsed = time() - time_start
                w_log(f"Script Finished: {elapsed:.2f} sec", ctx)
                end_log(ctx)

            self.report({"INFO"}, "Animation generated successfully")
            return {"FINISHED"}
        except RuntimeError as e:
            self.report({"ERROR"}, f"Error: {e!s}")
            return {"CANCELLED"}
