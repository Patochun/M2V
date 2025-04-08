"""
Module for handling animation of Blender objects based on MIDI events.
"""
from math import ceil, sin, pi
from random import randint
import bpy # type: ignore  # pylint: disable=import-error
from ..globals import glb
from ..utils.stuff import w_log

def calculate_event_len_move(fps, note):
    """
    Calculate the length of a note movement event in frames.

    Parameters:
        fps (int): Frames per second of the animation
        note (Note): Note object containing time_on and time_off properties

    Returns:
        int: Number of frames for the movement event, minimum 1 frame, maximum of:
            - 10% of fps (rounded up)
            - Half the note's duration in frames

    The function ensures reasonable animation length by capping at either 10% of fps
    or half the note duration, whichever is smaller, while never going below 1 frame.
    """
    return max(1, min(ceil(fps * 0.1), (note.time_off - note.time_on) * fps // 2))

def calculate_brightness(note):
    """
    Calculates the brightness value for a note based on its velocity.

    This function uses a sine wave transformation to create a non-linear mapping
    of note velocity to brightness values. The result ranges from approximately
    3 to 7 units of brightness.

    Args:
        note: A note object containing a velocity attribute.

    Returns:
        float: A brightness value between approximately 3 and 7.
    """
    return 5 + (sin(note.velocity * pi / 2) * 2)

def process_zscale(note, frames):
    """Process scale and location animation frames for Z-axis note animation.

    Args:
        note: The note object containing velocity information
        frames (dict): A dictionary containing frame timing points with keys 't1', 't2', 't3', 't4'

    Returns:
        list: A list of tuples containing animation keyframes
    """
    velocity = 6 * note.velocity
    return [
        (frames['t1'], "scale", (None, None, 1)),
        (frames['t1'], "location", (None, None, 0)),
        (frames['t2'], "scale", (None, None, velocity)),
        (frames['t2'], "location", (None, None, (velocity - 1) / 2)),
        (frames['t3'], "scale", (None, None, velocity)),
        (frames['t3'], "location", (None, None, (velocity - 1) / 2)),
        (frames['t4'], "scale", (None, None, 1)),
        (frames['t4'], "location", (None, None, 0)),
    ]

def process_b2r_light(obj, note, track, frames, brightness):
    """Process blue to red light animation keyframes for a given object."""
    velocity_blue_to_red = (0.02 + 0.38 *
                           (((note.velocity * 127) - track.min_velo) /
                            (track.max_velo - track.min_velo + 1)))
    mem_base_color = obj["base_color"]
    return [
        (frames['t1'], "base_color", mem_base_color),
        (frames['t1'], "emission_color", velocity_blue_to_red),
        (frames['t1'], "emission_strength", 0.0),
        (frames['t2'], "base_color", velocity_blue_to_red),
        (frames['t2'], "emission_color", velocity_blue_to_red),
        (frames['t2'], "emission_strength", brightness),
        (frames['t3'], "emission_color", velocity_blue_to_red),
        (frames['t3'], "emission_strength", brightness),
        (frames['t4'], "base_color", mem_base_color),
        (frames['t4'], "emission_color", velocity_blue_to_red),
        (frames['t4'], "emission_strength", 0.0),
    ]

def process_multilight(obj, color_track, frames, brightness):
    """Process multilight animation frames for an object."""
    if obj["emission_color"] > 0.01:
        color_track = (obj["emission_color"] + color_track) / 2
    return [
        (frames['t1'], "emission_color", color_track),
        (frames['t1'], "emission_strength", 0.0),
        (frames['t2'], "emission_color", color_track),
        (frames['t2'], "emission_strength", brightness),
        (frames['t3'], "emission_color", color_track),
        (frames['t3'], "emission_strength", brightness),
        (frames['t4'], "emission_color", color_track),
        (frames['t4'], "emission_color", obj["base_color"]),
        (frames['t4'], "emission_strength", 0.0),
    ]

def process_spread(obj, note, frames):
    """Process animation keyframes for a spreading sparkle effect."""
    pos_z = note.velocity * 30
    radius = min((frames['t4'] - frames['t1']) // 2, 5)
    density_cloud = (obj.modifiers["SparklesCloud"]
                    .node_group.interface.items_tree["density_cloud"].identifier)
    density_seed = (obj.modifiers["SparklesCloud"]
                   .node_group.interface.items_tree["density_seed"].identifier)
    return [
        (frames['t1'], "location", (None, None, pos_z)),
        (frames['t1'], "scale", (0, 0, 0)),
        (frames['t1'], "emission_strength", 0),
        (frames['t1'], f'modifiers.SparklesCloud.{density_cloud}', note.velocity / 3),
        (frames['t1'], f'modifiers.SparklesCloud.{density_seed}', randint(0, 1000)),
        (frames['t2'], "scale", (radius, radius, radius)),
        (frames['t2'], "emission_strength", 20),
        (frames['t4'], "scale", (0, 0, 0)),
        (frames['t4'], "emission_strength", 0),
        (frames['t4'], f'modifiers.SparklesCloud.{density_seed}', randint(0, 1000)),
    ]

def add_note_status_keyframes(frames, note):
    """Creates a list of keyframes for note status animation."""
    return [
        (frames['t1'], "note_status", 0.0),
        (frames['t2'], "note_status", note.velocity),
        (frames['t3'], "note_status", note.velocity),
        (frames['t4'], "note_status", 0.0),
    ]

def process_animation_type(animation_type, obj, note, track, frames, color_track):
    """Process different types of animation based on the provided animation type."""
    brightness = calculate_brightness(note)
    keyframes = []
    match animation_type.strip():
        case "ZSCALE":
            keyframes.extend(process_zscale(note, frames))
        case "B2R_LIGHT":
            keyframes.extend(process_b2r_light(obj, note, track, frames, brightness))
        case "MULTILIGHT":
            keyframes.extend(process_multilight(obj, color_track, frames, brightness))
        case "SPREAD":
            keyframes.extend(process_spread(obj, note, frames))
        case _:
            w_log(f"Unknown animation type: {animation_type}")
    return keyframes

def apply_keyframes(obj, keyframes):
    """
    Applies keyframe animations to a Blender object's properties.

    This function handles different types of properties including vectors (tuple values),
    custom properties, and modifier properties.

    Args:
        obj (bpy.types.Object): The Blender object to animate
        keyframes (list): List of tuples containing (frame, data_path, value)
            - frame (int): The frame number for the keyframe
            - data_path (str): Property path to animate
            - value (Union[tuple, float, int, str]): Value to set at the keyframe.
              For vector properties, can be tuple with None values to skip components

    Special data_path handling:
        - Vector properties: Use tuple values with optional None to skip components
        - Custom properties: "note_status", "emission_color", "emission_strength", "base_color" 
        - Modifier properties: Use "modifiers.{modifier_name}.{property_name}" format

    Example:
        keyframes = [
            (1, "location", (1, None, 0)),  # Only animate x and z
            (10, "rotation_euler", (0, 0, 3.14)),
            (20, "modifiers.Array.count", 5)
        ]
        apply_keyframes(my_object, keyframes)
    """
    for frame, data_path, value in keyframes:
        if isinstance(value, tuple):
            for i, v in enumerate(value):
                if v is not None:
                    val = getattr(obj, data_path)
                    val[i] = v
                    setattr(obj, data_path, val)
                    obj.keyframe_insert(data_path=f"{data_path}", index=i, frame=frame)
        else:
            if data_path in ["note_status", "emission_color", "emission_strength", "base_color"]:
                obj[data_path] = value
                obj.keyframe_insert(data_path=f'["{data_path}"]', frame=frame)
            elif data_path.startswith('modifiers'):
                mod_data_path = data_path.split('.')[1]
                mod_data_index = data_path.split('.')[2]
                obj.modifiers[mod_data_path][mod_data_index] = value
                data_path = f'modifiers["{mod_data_path}"]["{mod_data_index}"]'
                obj.keyframe_insert(data_path=data_path, frame=frame)
            else:
                obj[data_path] = value
                obj.keyframe_insert(data_path=data_path, frame=frame)

def calculate_keyframe_times_dict(frame_time_on, frame_time_off, event_len_move):
    """
    Calculate keyframe times and return them as a dictionary.

    Args:
        frame_time_on (int): Start frame of the note
        frame_time_off (int): End frame of the note
        event_len_move (int): Duration of the event movement

    Returns:
        dict: A dictionary containing frame timing points with keys 't1', 't2', 't3', 't4'
    """
    return {
        't1': frame_time_on,
        't2': frame_time_on + event_len_move,
        't3': frame_time_off - event_len_move,
        't4': frame_time_off
    }

def find_adjacent_notes(track, note_index, note):
    """
    Find the adjacent notes (previous and next) with the same note number in a track.

    Args:
        track: A track object containing a list of notes
        note_index: The index of the current note in the track
        note: The current note object to find adjacents for

    Returns:
        dict: A dictionary containing:
            - 'previous': The previous note with same note_number (None if not found)
            - 'next': The next note with same note_number (None if not found)
    """
    previous_note = None
    for prev_index in range(note_index - 1, -1, -1):
        if track.notes[prev_index].note_number == note.note_number:
            previous_note = track.notes[prev_index]
            break

    next_note = None
    for next_index in range(note_index + 1, len(track.notes)):
        if track.notes[next_index].note_number == note.note_number:
            next_note = track.notes[next_index]
            break

    return {'previous': previous_note, 'next': next_note}

def calculate_adjacent_frame_times(adjacent_notes, fps, frame_time_on, frame_time_off):
    """Calculate frame times for adjacent notes in an animation sequence.

    Args:
        adjacent_notes (dict): Dictionary containing 'previous' and 'next' notes
        fps (int): Frames per second of the animation
        frame_time_on (int): Frame number when current note starts
        frame_time_off (int): Frame number when current note ends

    Returns:
        tuple: A pair of integers (frame_time_off_previous, frame_time_on_next) where:
            - frame_time_off_previous: Frame number when previous note ends
            - frame_time_on_next: Frame number when next note starts
    """
    prev_note = adjacent_notes['previous']
    next_note = adjacent_notes['next']
    frame_time_off_prev = int(prev_note.time_off * fps) if prev_note else frame_time_on
    frame_time_on_next = int(next_note.time_on * fps) if next_note else frame_time_off
    return frame_time_off_prev, frame_time_on_next

def calculate_frame_times_dict(note, fps):
    """
    Calculate frame timing for a note and return as a dictionary.

    Args:
        note: A Note object containing time_on and time_off attributes in seconds
        fps (float): Frames per second rate

    Returns:
        dict: A dictionary containing frame timing points with keys 'on' and 'off'
    """
    frame_time_on = int(note.time_on * fps)
    frame_time_off = max(frame_time_on + 2, int(note.time_off * fps))
    return {'on': frame_time_on, 'off': frame_time_off}

def note_animate(obj, type_anim, track, note_index, color_track):
    """
    Animate a Blender object based on MIDI note events and animation type.

    Parameters:
        obj (bpy.types.Object): Blender object to animate
        type_anim (str): Animation style(s), comma-separated
        track (Track): Track containing MIDI notes
        note_index (int): Index of the current note
        color_track (float): Color value for track (0.0-1.0)
    """
    note = track.notes[note_index]
    adjacent_notes = find_adjacent_notes(track, note_index, note)
    event_len_move = calculate_event_len_move(glb.fps, note)

    frame_times = calculate_frame_times_dict(note, glb.fps)

    frames = calculate_keyframe_times_dict(frame_times['on'], frame_times['off'], event_len_move)

    frame_time_off_previous, frame_time_on_next = calculate_adjacent_frame_times(
        adjacent_notes, glb.fps, frame_times['on'], frame_times['off'])

    if frame_times['on'] < frame_time_off_previous or frame_times['off'] > frame_time_on_next:
        return

    keyframes = []
    for animation_type in type_anim.split(','):
        keyframes.extend(process_animation_type(
            animation_type, obj, note, track,
            frames, color_track))

    keyframes.extend(add_note_status_keyframes(frames, note))
    keyframes.sort(key=lambda x: (x[0], x[1]))
    apply_keyframes(obj, keyframes)

def distribute_objects_with_clamp_to(list_obj: list, curve: bpy.types.Object):
    """
    Distributes objects evenly along a Bezier curve using Clamp To constraints.

    Args:
        list_obj (list): List of objects to distribute along the curve
        curve (bpy.types.Object): Target Bezier curve object
        
    The function:
    - Calculates even spacing between objects
    - Adds Clamp To constraint to each object
    - Sets initial positions proportionally along curve
    - Maintains dynamic curve following with influence=1

    Note:
        Objects will be clamped to curve while maintaining even distribution
        Positioning uses curve dimensions for initial placement
        Constraint influence is set to 1 to maintain curve following
    """
    num_objects = len(list_obj)

    # Adjust factor based on number of objects
    base_factor = curve.dimensions.x + 2
    factor = base_factor / num_objects

    for i, obj in enumerate(list_obj):

        # Compute initial position before applying Clamp To
        obj.location.x = factor * (i+1)

        # Apply the Clamp To modifier
        clamp_mod = obj.constraints.new(type='CLAMP_TO')
        clamp_mod.target = curve
        clamp_mod.use_cyclic = True
        clamp_mod.main_axis = 'CLAMPTO_X'
        clamp_mod.influence = 1.0

def anim_circle_curve(curve, rotation_speed):
    """
    Animate rotation of a curve based on rotation speed and note duration.

    Args:
        curve (bpy.types.Object): Curve object to animate
        rotation_speed (float): Rotations per second

    Note:
        Uses global lastNotetime_off and fps variables
        Creates linear animation from start to end
    """
    # Animate circle curve with rotation_speed = Rotations per second
    start_frame = 1
    end_frame = int(glb.last_note_time_off * glb.fps)  # Use global lastNotetime_off
    total_rotations = rotation_speed * glb.last_note_time_off

    # Set keyframes for Z rotation
    curve.rotation_euler.z = 0
    curve.keyframe_insert(data_path="rotation_euler", index=2, frame=start_frame)

    curve.rotation_euler.z = total_rotations * 2 * pi  # Convert to radians
    curve.keyframe_insert(data_path="rotation_euler", index=2, frame=end_frame)

    # Make animation linear
    for fcurve in curve.animation_data.action.fcurves:
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = 'LINEAR'
