"""
Module for fountain animation
"""
from math import radians, cos, sin, tan, degrees
import bpy # type: ignore  # pylint: disable=import-error
from ..globals import glb, BlenderObjectTypes
from ..utils.collection import create_collection
from ..utils.object import create_blender_object, create_duplicate_linked_object, get_object_by_name
from ..utils.stuff import (w_log, parse_range_from_tracks, extract_octave_and_note,
                           color_from_note_number)
from ..utils.animation import note_animate, distribute_objects_with_clamp_to, anim_circle_curve

def create_fountain(track_mask, type_anim):
    """
    Creates a fountain-style MIDI visualization with particle trajectories.

    This function creates a circular fountain display where:
    - Notes are arranged in concentric rings by octave
    - Emitters move along circular path
    - Particles shoot from emitters to note targets
    - Physics-based particle trajectories

    Parameters:
        master_collection (bpy.types.Collection): Parent collection for organization
        track_mask (str): Track selection pattern (e.g. "0-5,7,9-12")
        type_anim (str): Animation style to apply ("fountain")

    Structure:
        - Fountain (main collection)
            - FountainTargets (note target planes)
            - FountainEmitters (moving particle emitters)
                - Trajectory curve
                - Track-based emitters
                - Particle systems

    Physics Setup:
        - Particle trajectories calculated with gravity
        - Collision detection on targets
        - Linear emitter movement on curve
        - Particle lifetime based on travel time

    Returns:
        None
    """

    w_log(f"Create a Fountain Notes Animation type = {type_anim}")

    (
        list_of_selected_track,
        _,
        _,
        _,
        _,
        tracks_color
    ) = parse_range_from_tracks(track_mask)

    tracks = glb.tracks
    fps = glb.fps

    # Create Collection
    fountain_collection = create_collection("Fountain", glb.master_collection)

    # Create model objects
    fountain_model_plane = create_blender_object(
        BlenderObjectTypes.PLANE,
        collection=glb.hidden_collection,
        name="fountain_model_plane",
        material=glb.mat_global_custom,
        location=(0, 0, -10),
        height=1,
        width=1
    )

    fountain_model_particle = create_blender_object(
        BlenderObjectTypes.CUBE,
        collection=glb.hidden_collection,
        name="fountain_model_particle",
        material=glb.mat_global_custom,
        location=(2,0,-10),
        scale=(1,1,1),
        bevel=False
    )

    fountain_model_emitter = create_blender_object(
        BlenderObjectTypes.CYLINDER,
        collection=glb.hidden_collection,
        name="fountain_model_emitter",
        material=glb.mat_global_custom,
        location=(4,0,-10),
        radius=1,
        height=1
    )

    # Create Target Collection
    fountain_target_collection = create_collection("FountainTargets", fountain_collection)

    # Construction of the fountain Targets
    theta = radians(360)  # 2 Pi, just one circle
    alpha = theta / 12  # 12 is the Number of notes per octave
    for note in range(132):
        octave, num_note = extract_octave_and_note(note)
        target_name = f"Target-{num_note}-{octave}"
        target_obj = create_duplicate_linked_object(fountain_target_collection,
                                                    fountain_model_plane,
                                                    target_name,
                                                    independant=False)
        space_y = 0.1
        space_x = 0.1
        angle = (12 - note) * alpha
        distance = (octave * (1 + space_x)) + 4
        px = distance * cos(angle)
        py = distance * sin(angle)
        rot = radians(degrees(angle))
        target_obj.location = (px, py, 0)
        target_obj.rotation_euler = (0, 0, rot)
        sx = 1 # mean size of note in direction from center to border (octave)
        # sy => mean size of note in rotate direction (num_note)
        sy = (2 * distance * tan(radians(15))) - space_y
        target_obj.scale = (sx, sy, 1)
        target_obj["base_color"] = color_from_note_number(num_note)
        # Add Taper modifier
        simple_deform_modifier = target_obj.modifiers.new(name="SimpleDeform", type='SIMPLE_DEFORM')
        simple_deform_modifier.deform_method = 'TAPER'
        big_side = (2 * (distance+sx/2) * tan(radians(15))) - space_y
        taper_factor = 2*(big_side/sy-1)
        simple_deform_modifier.factor = taper_factor

        # Add collision Physics
        target_obj.modifiers.new(name="Collision", type='COLLISION')

    w_log("Fountain - create 132 targets")

    # Create Target Collection
    fountain_emitter_collection = create_collection("FountainEmitters", fountain_collection)

    # g = -bpy.context.scene.gravity[2]  # z gravity from blender (m/s^2)

    delay_impact = 3.0  # Time in second from emitter to target
    frame_delay_impact = delay_impact * fps

    # Create empty object for storing somes constants for drivers
    fountain_constants_obj = bpy.data.objects.new("fountain_constants_values", None)
    fountain_constants_obj.location=(6,0,-10)
    glb.hidden_collection.objects.link(fountain_constants_obj)
    fountain_constants_obj["delay"] = delay_impact

    emitters_list = []
    for track_count, track_index in enumerate(list_of_selected_track):
        track = tracks[track_index]

        # Particle
        particle_name = f"Particle-{track_index}-{track.name}"
        particle_obj = create_duplicate_linked_object(glb.hidden_collection,
                                                      fountain_model_particle,
                                                      particle_name,independant=False)
        particle_obj.name = particle_name
        particle_obj.location = (track_index * 2, 0, -12)
        particle_obj.scale = (0.3,0.3,0.3)
        particle_obj["base_color"] = tracks_color[track_count]
        particle_obj["emission_color"] = tracks_color[track_count]
        particle_obj["emission_strength"] = 8.0

        # Emitter around the targets
        emitter_name = f"Emitter-{track_index}-{track.name}"
        emitter_obj = create_duplicate_linked_object(fountain_emitter_collection,
                                                     fountain_model_emitter,
                                                     emitter_name,independant=False)
        emitters_list.append(emitter_obj)

        emitter_obj.location = (0, 0, 0)
        emitter_obj.scale = (1, 1, 0.2)
        emitter_obj["base_color"] = tracks_color[track_count]
        emitter_obj["emission_color"] = tracks_color[track_count]

        # One particle per note
        for note_index, note in enumerate(track.notes):

            frame_time_on = int(note.time_on * fps)
            octave, num_note = extract_octave_and_note(note.note_number)

            # Add a particle system to the object
            p_system_name = f"ParticleSystem-{octave}-{note_index}"
            particle_system = emitter_obj.modifiers.new(name=p_system_name, type='PARTICLE_SYSTEM')
            p_setting_name = f"ParticleSettings-{octave}-{note_index}"
            particle_settings = bpy.data.particles.new(name=p_setting_name)
            particle_system.particle_system.settings = particle_settings

            # Configure particle system settings - Emission
            particle_settings.count = 1
            particle_settings.lifetime = fps * 4
            # Be sure to initialize frame_end before frame_start because
            # frame_start can't be greather than frame_end at any time
            # particle_settings.frame_end = frame_time_off - frame_delay_impact
            particle_settings.frame_end = frame_time_on - frame_delay_impact + 1
            particle_settings.frame_start = frame_time_on - frame_delay_impact

            # Configure particle system settings - Emission - Source
            particle_settings.emit_from = 'FACE'
            particle_settings.distribution = 'GRID'
            particle_settings.grid_resolution = 1
            particle_settings.grid_random = 0

            # Configure particle system settings - Velocity - Using drivers
            # Retrieve Target Object
            target_name = f"Target-{num_note}-{octave}"
            target = get_object_by_name(target_name)

            # Add drivers for object_align_factors
            for i, axis in enumerate(['X', 'Y', 'Z']):
                driver = particle_settings.driver_add('object_align_factor', i).driver
                driver.type = 'SCRIPTED'

                # Add variables for emitter position
                var_e = driver.variables.new()
                var_e.name = f"e{axis}"
                var_e.type = 'TRANSFORMS'
                var_e.targets[0].id = emitter_obj
                var_e.targets[0].transform_type = f'LOC_{axis}'
                var_e.targets[0].transform_space = 'WORLD_SPACE'

                # Add variables for target position
                var_t = driver.variables.new()
                var_t.name = f"t{axis}"
                var_t.type = 'TRANSFORMS'
                var_t.targets[0].id = target
                var_t.targets[0].transform_type = f'LOC_{axis}'
                var_t.targets[0].transform_space = 'WORLD_SPACE'

                # Add delay variable (from emitter object)
                var_delay = driver.variables.new()
                var_delay.name = "delay"
                var_delay.type = 'SINGLE_PROP'
                var_delay.targets[0].id = fountain_constants_obj
                var_delay.targets[0].data_path = '["delay"]'

                if axis == 'Z':
                    # Optimized expression to avoid "Slow Python Expression"
                    driver.expression = f"(t{axis} - e{axis} + 4.905 * delay*delay) / delay"
                else:
                    driver.expression = f"(t{axis} - e{axis}) / delay"

            # Configure particle system settings - Render
            particle_settings.render_type = 'OBJECT'
            particle_settings.instance_object = particle_obj
            particle_settings.particle_size = note.velocity * 1.4  # Base size of the particle

            # Configure particle system settings - Fields Weights
            particle_settings.effector_weights.gravity = 1

        w_log(f"Fountain - create {len(track.notes)} particles for track {track_index}")

        # Animate target
        for note_index, note in enumerate(track.notes):
            octave, num_note = extract_octave_and_note(note.note_number)
            target_name = f"Target-{num_note}-{octave}"
            note_obj = bpy.data.objects[target_name]
            note_animate(note_obj, "MULTILIGHT", track, note_index, tracks_color[track_count])

        w_log(f"Fountain - animate targets with {note_index} notes")

    # Create circle curve for trajectory of emitters
    radius_curve = 20
    fountain_emitter_trajectory = create_blender_object(
        BlenderObjectTypes.BEZIER_CIRCLE,
        collection=fountain_emitter_collection,
        name="fountain_emitter_trajectory",
        location=(0, 0, 3),
        radius=radius_curve
    )

    # emitters along the curve
    distribute_objects_with_clamp_to(emitters_list, fountain_emitter_trajectory)
    anim_circle_curve(fountain_emitter_trajectory, 0.05)
