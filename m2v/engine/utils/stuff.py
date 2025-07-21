"""
Module for miscellaneous utility functions.
"""
from os import path
import re
import bpy # type: ignore  # pylint: disable=import-error
from ..globals import glb

def init_log(log_file):
    """Open log file for append"""
    glb.f_log = open(log_file, "w+", encoding="utf-8")

def w_log(to_log):
    """Write to screen and log"""
    print(to_log)
    glb.f_log.write(to_log + "\n")

def end_log():
    """Close logFile"""
    glb.f_log.close()

def parse_range_from_tracks(range_str):
    """
    Parses a range string and returns a list of numbers.
    Example input: "1-5,7,10-12"
    Example output: [1, 2, 3, 4, 5, 7, 10, 11, 12]
    """
    def max_gap_values(n, start=0.02, end=1):
        """
        Returns a list of n values between start and end,
        arranged so that the gap between consecutive values is maximized.
        """
        if n < 1:
            raise ValueError("n must be a positive integer")
        if n == 1:
            return [(start + end) / 2]

        step = (end - start) / (n - 1)
        sorted_values = [start + i * step for i in range(n)]

        result = []
        mid_index = len(sorted_values) // 2
        result.append(sorted_values.pop(mid_index))

        toggle = True
        while sorted_values:
            if toggle:
                result.append(sorted_values.pop(0))
            else:
                result.append(sorted_values.pop(-1))
            toggle = not toggle

        return result

    tracks = glb.tracks
    w_log(f"Track filter used = {range_str}")

    numbers = []
    if range_str == "*":
        numbers = range(len(tracks))
    else:
        segments = range_str.split(',')

        for segment in segments:
            match = re.match(r'^(\d+)-(\d+)$', segment)
            if match:
                start, end = map(int, match.groups())
                numbers.extend(range(start, end + 1))
            elif re.match(r'^\d+$', segment):
                numbers.append(int(segment))
            else:
                raise ValueError(f"Invalid format : {segment}")

    note_min = 1000
    note_max = 0
    effective_track_count = 0
    tracks_selected = ""
    list_of_selected_tracks = []
    for track_index, track in enumerate(tracks):
        if track_index not in numbers:
            continue

        effective_track_count += 1
        tracks_selected += (f"{track_index},")
        list_of_selected_tracks.append(track_index)
        note_min = min(note_min, track.min_note)
        note_max = max(note_max, track.max_note)

    tracks_selected = tracks_selected[:-1]
    w_log(f"Track selected are = {tracks_selected}")

    octave_count = (note_max // 12) - (note_min // 12) + 1

    tracks_color = max_gap_values(effective_track_count, start=0.02, end=1)

    return (
        list_of_selected_tracks,
        note_min,
        note_max,
        octave_count,
        effective_track_count,
        tracks_color
    )

def color_from_note_number(note_number):
    """Define color from note number when sharp (black) or flat (white)"""
    if note_number in [1, 3, 6, 8, 10]:
        return 0.001  # Black note (almost)
    return 0.01  # White note

def extract_octave_and_note(note_number):
    """Retrieve octave and note_number from note number (0-127)"""
    octave = note_number // 12
    note_number = note_number % 12
    return octave, note_number

def create_compositor_nodes():
    """Creates a Compositor node setup for post-processing effects"""
    # Enable the compositor
    bpy.context.scene.use_nodes = True
    node_tree = bpy.context.scene.node_tree

    # Remove existing nodes
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)

    # Add necessary nodes
    render_layers_node = node_tree.nodes.new(type='CompositorNodeRLayers')
    render_layers_node.location = (0, 0)

    glare_node = node_tree.nodes.new(type='CompositorNodeGlare')
    glare_node.location = (300, 0)

    # Configure the Glare node
    glare_node.glare_type = 'BLOOM'
    glare_node.quality = 'MEDIUM'
    glare_node.mix = 0.0
    glare_node.threshold = 5
    glare_node.size = 4

    composite_node = node_tree.nodes.new(type='CompositorNodeComposite')
    composite_node.location = (600, 0)

    # Connect the nodes
    links = node_tree.links
    links.new(render_layers_node.outputs['Image'], glare_node.inputs['Image'])
    links.new(glare_node.outputs['Image'], composite_node.inputs['Image'])


def set_blender_units(unit_scale=0.01, length_unit="CENTIMETERS"):
    """Define blender unit system"""
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.system_rotation = 'DEGREES'
    bpy.context.scene.unit_settings.length_unit = length_unit
    bpy.context.scene.unit_settings.scale_length = unit_scale

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.overlay.grid_scale = 0.01
                    space.clip_end = 10000.0
                    break

def determine_global_ranges():
    """Calculate global note and time ranges across all tracks"""
    stats = {
        'note_min': 1000,
        'note_max': 0,
        'time_min': 1000,
        'time_max': 0,
        'note_mid_range': 0
    }

    for track in glb.tracks:
        stats.update({
            'note_min': min(stats['note_min'], track.min_note),
            'note_max': max(stats['note_max'], track.max_note),
            'time_min': min(stats['time_min'], track.notes[0].time_on),
            'time_max': max(stats['time_max'], track.notes[-1].time_off)
        })

    stats['note_mid_range'] = stats['note_min'] + (stats['note_max'] - stats['note_min']) / 2

    log_messages = (
        f"Note range: {stats['note_min']} to {stats['note_max']} "
        f"(mid: {stats['note_mid_range']})\n"
        f"Time range: {stats['time_min']:.2f}s to {stats['time_max']:.2f}s"
    )
    w_log(log_messages)

    return (
        stats['note_min'],
        stats['note_max'],
        stats['time_min'],
        stats['time_max'],
        stats['note_mid_range']
    )

def load_audio(audio_path_str):
    """
    Load the provided audio file into the VSE at the given offset_time (in seconds),
    without relying on the UI or context overrides.
    """
    scene = bpy.context.scene

    # Create the sequence editor if it doesn't exist
    if scene.sequence_editor is None:
        scene.sequence_editor_create()

    # Force refresh
    seq_editor = scene.sequence_editor
    if seq_editor is None:
        w_log("Error: sequence_editor could not be created.")
        return

    # Clear previous strips (optional, depending on your logic)
    seq_editor_clear = getattr(seq_editor, "clear", None)
    if callable(seq_editor_clear):
        seq_editor.clear()

    # Add the sound strip directly
    seq_editor.sequences.new_sound(
        name="Audio",
        filepath=audio_path_str,
        channel=1,
        frame_start=0
    )

    w_log(f"Audio file loaded into VSE: {audio_path_str}")

def load_audio2(audio_path):
    """Load audio file mp3 with the same name of midi file if exists"""
    if path.exists(audio_path):
        if not bpy.context.scene.sequence_editor:
            bpy.context.scene.sequence_editor_create()

        bpy.context.scene.sequence_editor_clear()
        my_contextmem = bpy.context.area.type
        my_context = 'SEQUENCE_EDITOR'
        bpy.context.area.type = my_context
        my_context = bpy.context.area.type
        bpy.ops.sequencer.sound_strip_add(
            filepath=audio_path,
            relative_path=True,
            frame_start=1,
            channel=1
        )
        bpy.context.area.type = my_contextmem
        my_context = bpy.context.area.type
        w_log("Audio file mp3 is loaded into VSE")
    else:
        w_log("Audio file mp3 not exist")
