"""
Module to create a waterfall visualization of MIDI notes with animated camera movement.
"""
from math import tan
import bpy # type: ignore  # pylint: disable=import-error
from ..globals import glb
from .strip_notes import create_strip_notes
from ..utils.stuff import w_log, parse_range_from_tracks

def create_waterfall(track_mask, type_anim):
    """
    Creates a waterfall visualization of MIDI notes with animated camera movement.

    This function creates a waterfall view where:
    - Uses strip notes visualization as base
    - Adds orthographic camera that follows notes
    - Smooth vertical scrolling through timeline
    - Notes appear as they are played

    Parameters:
        master_collection (bpy.types.Collection): Parent collection for organization
        track_mask (str): Track selection pattern (e.g. "0-5,7,9-12")
        type_anim (str): Animation style to apply

    Structure:
        - StripNotes (base visualization)
        - Camera
            - Orthographic setup
            - Linear vertical movement
            - Follows note timing

    Returns:
        None
    """

    w_log("Create a waterfall Notes Animation type")

    create_strip_notes(track_mask, type_anim)

    (
        list_of_selected_track,
        _,
        _,
        _,
        _,
        _
    ) = parse_range_from_tracks(track_mask)

    tracks = glb.tracks
    fps = glb.fps

    # Initialize a list to store all notes from the selected tracks along with their track index
    selected_notes = []

    # Iterate through all tracks and collect notes from the selected tracks
    for track_index, track in enumerate(tracks):
        if track_index in list_of_selected_track:  # Check if the current track is selected
            # Add each note as a tuple (track_index, note) to the list
            selected_notes.extend((track_index, note) for note in track.notes)

    # Find the tuple with the note that has the largest time_off value
    note_max_time_off = max(selected_notes, key=lambda x: x[1].time_off)

    # Create a new camera
    camera_data = bpy.data.cameras.new(name="Camera")
    camera_obj = bpy.data.objects.new("Camera", camera_data)
    glb.master_collection.objects.link(camera_obj)

    # orthographic mode
    camera_data.type = 'ORTHO'

    # Get the sizeX of the background plane
    # Sum sizeX of all object in collection StripNotes/BG
    size_x = 0
    collect_stripe_bg = bpy.data.collections["StripNotes"].children["BG"]
    for obj in collect_stripe_bg.objects:
        size_y = obj.scale.y
        location_y = obj.location.y
        size_x += obj.scale.x

    # othographic scale (Field of View)
    camera_data.ortho_scale = size_x

    offset_y_camera = size_x*(9/16)/2
    ortho_fov = 38.6

    camera_location_z = (size_x/2) / (tan(ortho_fov/2))

    # Set the initial position of the camera
    camera_obj.location = (0, offset_y_camera, camera_location_z)  # X, Y, Z
    camera_obj.rotation_euler = (0, 0, 0)  # Orientation
    camera_obj.data.shift_y = -0.01

    # Add a keyframe for the starting Y position
    camera_obj.location.y = offset_y_camera + location_y - (size_y/2)
    camera_obj.keyframe_insert(data_path="location",
                               index=1,
                               frame=0)

    # Add a keyframe for the ending Y position
    camera_obj.location.y = offset_y_camera + location_y + (size_y/2)
    camera_obj.keyframe_insert(data_path="location",
                               index=1,
                               frame=note_max_time_off[1].time_off*fps)

    # Set the active camera for the scene
    bpy.context.scene.camera = camera_obj

    # Make animation linear
    action = camera_obj.animation_data.action  # Get animation action
    fcurve = action.fcurves.find(data_path="location", index=1)  # F-Curve for Y axis

    if fcurve:
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = 'LINEAR'  # Set interpolation to 'LINEAR'
