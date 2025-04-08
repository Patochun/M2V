"""
Module to create a strip-based visualization of MIDI notes with animations.
"""
from ..globals import glb, BlenderObjectTypes
from ..utils.collection import create_collection
from ..utils.object import create_blender_object, create_duplicate_linked_object
from ..utils.animation import note_animate
from ..utils.stuff import (
    w_log,
    parse_range_from_tracks,
    color_from_note_number,
    extract_octave_and_note
)

def create_strip_notes(track_mask, type_anim):
    """
    Creates a strip-based visualization of MIDI notes with animations.

    This function creates a vertical strip visualization where:
    - Each note is represented by a rectangle
    - X axis: Note pitch and track offset
    - Y axis: Time (note start/duration)
    - Background plane shows total time range
    - Notes are colored by track

    Parameters:
        track_mask (str): Track selection pattern (e.g. "0-5,7,9-12")
        type_anim (str): Animation style to apply ("ZScale", "B2R-Light", etc)

    Structure:
        - StripNotes (main collection)
            - Notes-TrackN (per track collections)
                - Note rectangles
            - NotesStripPlane (background)

    Returns:
        bpy.types.Object: The created background plane object
    """

    w_log(f"Create a Strip Notes Animation type = {type_anim}")

    (
        list_of_selected_track,
        note_min,
        note_max,
        _,
        number_of_rendered_tracks,
        tracks_color
    ) = parse_range_from_tracks(track_mask)

    tracks = glb.tracks

    # Create models Object
    strip_model_cube = create_blender_object(
        BlenderObjectTypes.CUBE,
        collection=glb.hidden_collection,
        name="StripNotesModelCube",
        material=glb.mat_global_custom,
        location=(0,0,-5),
        scale=(1,1,1),
        bevel=False
    )

    strip_model_plane = create_blender_object(
        BlenderObjectTypes.PLANE,
        collection=glb.hidden_collection,
        name="StripBGModelPlane",
        material=glb.mat_global_custom,
        location=(0, 0, -10),
        width=1,
        height=1
    )

    strip_collect = create_collection("StripNotes", glb.master_collection)

    note_count = (note_max - note_min) + 1

    margin_ext_y = 0 # in sec
    cell_size_x = 1 # size X for each note in centimeters
    cell_size_y = 4 # size for each second in centimeters
    interval_x = cell_size_x / 10
    track_width = (cell_size_x + interval_x) * (number_of_rendered_tracks)
    plane_offset = -((note_count * track_width) / 2)

    # Parse tracks
    length = 0
    for track_count, track_index in enumerate(list_of_selected_track):
        track = tracks[track_index]

        length = max(length, track.notes[-1].time_off)
        offset_track = (track_count) * (cell_size_x + interval_x)
        interval_y = 0 # have something else to 0 create artefact in Y depending on how many note

        # Create collections
        notes_collection = create_collection(f"Notes-Track-{track_count}", strip_collect)

        size_x = cell_size_x

        for note_index, note in enumerate(track.notes):

            # plane_offset + (note_num - note_min) * track_width + track_width / 2,
            pos_x = plane_offset + (note.note_number - note_min) * track_width
            pos_x += offset_track + cell_size_x / 2

            # pos_x = ((note.note_number - note_middle) * (track_width)) + offset_track
            size_y = round(((note.time_off - note.time_on) * cell_size_y), 2)
            pos_y = ((margin_ext_y + note.time_on) * (cell_size_y + interval_y)) + (size_y / 2)
            name_of_note_played = f"Note-{track_count}-{note.note_number}-{note_index}"

            # Duplicate the existing note
            note_obj = create_duplicate_linked_object(notes_collection, strip_model_cube,
                       name_of_note_played, independant=False)
            note_obj.location = (pos_x, pos_y, 0) # Set instance position
            note_obj.scale = (size_x, size_y, 1) # Set instance scale
            note_obj["base_color"] = tracks_color[track_count]

            # Animate note
            # Be aware to animate duplicate only, never the model one
            # Pass the current note, previous note, and next note to the function
            note_animate(note_obj, type_anim, track, note_index, tracks_color[track_count])

        w_log(f"Notes Strip track {track_count} - create & animate {len(track.notes) + 1}")

    # Create background plane
    # plan_size_x = (margin_ext_x * 2) + (note_count * cell_size_x) + (note_count * track_width)
    plan_size_y = (length + (margin_ext_y * 2)) * cell_size_y
    bg_collection = create_collection("BG", strip_collect)
    for note_num in range(note_min, note_max + 1):
        plane_name = f"{note_num}-BG"
        plane_obj = create_duplicate_linked_object(bg_collection, strip_model_plane,
                    plane_name, independant=False)
        plane_obj.scale = (track_width, plan_size_y, 1)
        plane_obj.location = (
            plane_offset + (note_num - note_min) * track_width + track_width / 2,
            plan_size_y / 2,
            (-strip_model_cube.scale.z / 2)
            )
        octave, note = extract_octave_and_note(note_num)
        color = 0.400 + color_from_note_number(note_num % 12) * 4
        if octave % 2 == 0:
            color += 0.1
        plane_obj["base_color"] = color
        plane_obj["base_saturation"] = 0.4
