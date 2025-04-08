"""
Module for bar graph animation
"""
from ..globals import glb, BlenderObjectTypes
from ..utils.collection import create_collection
from ..utils.object import create_blender_object, create_duplicate_linked_object, get_object_by_name
from ..utils.animation import note_animate
from ..utils.stuff import w_log, parse_range_from_tracks, color_from_note_number

def create_blender_bg_animation(track_mask, type_anim):
    """
    Creates a bar graph visualization for MIDI tracks in Blender.
    ...
    """
    w_log(f"Create a BarGraph Animation type = {type_anim}")

    (
        list_of_selected_track,
        note_min,
        note_max,
        _,
        number_of_rendered_tracks,
        tracks_color
    ) = parse_range_from_tracks(track_mask)

    # Create master BG collection
    bg_collect = create_collection("BarGraph", glb.master_collection)

    # Create models Object
    bg_model_cube = create_blender_object(
        BlenderObjectTypes.CUBE,
        collection=glb.hidden_collection,
        name="bg_model_cube",
        material=glb.mat_global_custom,
        location=(0,0,-5),
        scale=(1,1,1),
        bevel=False
    )

    bg_model_plane = create_blender_object(
        BlenderObjectTypes.PLANE,
        collection=glb.hidden_collection,
        name="bg_model_plane",
        material=glb.mat_global_custom,
        location=(0,0,-5),
        height=1,
        width=1
    )

    # Create cubes from track
    # Parse track to create BG
    track_center = number_of_rendered_tracks / 2
    note_mid_range = (note_min + note_max) / 2
    cube_space = bg_model_cube.scale.x * 1.2 # mean x size of cube + 20 %

    # Parse track to create BG
    for track_count, track_index in enumerate(list_of_selected_track):
        track = glb.tracks[track_index]

        # create collection
        bg_track_name = f"BG-{track_index}-{track.name}"
        bg_track_collect = create_collection(bg_track_name, bg_collect)

        # one cube per note used
        for note in track.notes_used:
            # create cube
            cube_name = f"Cube-{track_index}-{note}"
            offset_x = (note - note_mid_range) * cube_space
            offset_y = (track_count - track_center) * cube_space + cube_space / 2
            cube_linked = create_duplicate_linked_object(bg_track_collect, bg_model_cube,
                                                         cube_name, independant=False)
            cube_linked.location = (offset_x, offset_y, 0)
            cube_linked["base_color"] = color_from_note_number(note % 12)

        msg = f"BarGraph - {len(track.notes_used)} cubes | track {track_index} | "
        msg += f"{track.min_note}-{track.max_note}"
        w_log(msg)

    # Create a plane by octave to have a visualisation for them
    min_octave = note_min // 12
    max_octave = note_max // 12

    bg_plane_collect = create_collection("BG-Plane", bg_collect)

    plan_pos_x_offset = (((note_mid_range % 12) - 5) * cube_space) - (cube_space / 2)
    for octave in range(min_octave, max_octave + 1):
        plan_size_x = 12 * cube_space
        plan_size_y = len(list_of_selected_track) * cube_space
        plan_pos_x = (octave - (note_mid_range // 12)) * 12 * cube_space
        plan_pos_x -= plan_pos_x_offset
        plane_name = f"Plane-{octave}"
        obj = create_duplicate_linked_object(bg_plane_collect, bg_model_plane,
                                             plane_name, independant=False)
        obj.scale = (plan_size_x, plan_size_y, 1)
        obj.location = (plan_pos_x, 0, (-bg_model_cube.scale.z / 2)*1.005)
        obj["base_saturation"] = 0.3
        if octave % 2 == 0:
            obj["base_color"] = 0.6 # Yellow
        else:
            obj["base_color"] = 1.0 # Cyan

    # Animate cubes accordingly to notes event
    for track_count, track_index in enumerate(list_of_selected_track):
        track = glb.tracks[track_index]

        for note_index, note in enumerate(track.notes):
            # Construct the cube name and animate
            cube_name = f"Cube-{track_index}-{note.note_number}"
            note_obj = get_object_by_name(cube_name)
            note_animate(note_obj, type_anim, track, note_index, tracks_color[track_count])

        w_log(f"BarGraph - Animate cubes for track {track_index} (notesCount) ({len(track.notes)})")
