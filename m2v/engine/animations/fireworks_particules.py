"""
Module for firework version 2 animation with particle system
"""
import bpy # type: ignore  # pylint: disable=import-error
from ..globals import glb, BlenderObjectTypes
from ..utils.collection import create_collection
from ..utils.object import create_blender_object, create_duplicate_linked_object, get_object_by_name
from ..utils.stuff import w_log, parse_range_from_tracks

def create_fireworks_v2(track_mask, type_anim):
    """
    Creates a particle-based fireworks visualization using Blender's particle system.

    This function creates an advanced fireworks display where:
    - Notes are arranged in a 3D grid (X: notes, Y: octaves, Z: tracks)
    - Each note has an emitter and sparkle objects
    - Emitters shoot particles based on note timing
    - Particles inherit track colors and note velocities

    Parameters:
        master_collection (bpy.types.Collection): Parent collection for organization
        track_mask (str): Track selection pattern (e.g. "0-5,7,9-12")
        type_anim (str): Animation style to apply

    Structure:
        - FireworksV2 (main collection)
            - FW-TrackN (per track collections)
                - Emitter spheres
                - Sparkle particles
                - Particle systems

    Grid Layout:
        - X axis: Notes within octave (0-11)
        - Y axis: Octaves
        - Z axis: Track layers

    Particle System:
        - Count: 100 particles per note
        - Lifetime: 50 frames
        - Velocity: Based on note velocity
        - Gravity: Reduced to 10%
        - Size variation: 20%

    Returns:
        None
    """

    w_log(f"Create a Fireworks V2 Notes Animation type = {type_anim}")

    (
        list_of_selected_track,
        note_min,
        note_max,
        _,
        _,
        tracks_color
    ) = parse_range_from_tracks(track_mask)

    tracks = glb.tracks
    fps = glb.fps

    # Create master BG collection
    fw_collect = create_collection("FireworksV2", glb.master_collection)

    # Create model objects
    fw_model_emitter = create_blender_object(
        BlenderObjectTypes.ICOSPHERE,
        collection=glb.hidden_collection,
        name="FWV2Emitter",
        material=glb.mat_global_custom,
        location=(0,0,-5),
        radius=1
    )

    fw_model_sparkle = create_blender_object(
        BlenderObjectTypes.ICOSPHERE,
        collection=glb.hidden_collection,
        name="FWV2Sparkles",
        material=glb.mat_global_custom,
        location=(0,0,-5),
        radius=0.1
    )

    space_x = 5
    space_y = 5
    space_z = 5
    offset_x = 5.5 * space_x # center of the octave, mean between fifth and sixt note
    octave_min = note_min // 12
    octave_max = note_max // 12
    octave_center = ((octave_max - octave_min) / 2) + octave_min
    track_center = (len(tracks)-1) / 2

    # Construction
    note_count = 0
    for track_count, track_index in enumerate(list_of_selected_track):
        track = tracks[track_index]

        # create collection
        fw_track_name = f"FW-{track_index}-{track.name}"
        fw_track_collect = create_collection(fw_track_name, fw_collect)

        # one sphere per note used
        for note in track.notes_used:
            # create sphere
            px = (note % 12) * space_x - offset_x
            py = ((note // 12) - octave_center) * space_y
            pz = (track_index - track_center) * space_z
            emitter_name = f"noteEmitter-{track_index}-{note}"
            sphere_linked = create_duplicate_linked_object(fw_track_collect, fw_model_emitter,
                                                           emitter_name, independant=False)
            sphere_linked.location = (px, py, pz)
            sphere_linked.scale = (1,1,1)
            sphere_linked["alpha"] = 0.0
            sparkle_name = f"noteSparkles-{track_index}-{note}"
            sphere_linked = create_duplicate_linked_object(glb.hidden_collection,
                                                           fw_model_sparkle,
                                                           sparkle_name, independant=False)
            sphere_linked.location = (px, py, pz)
            sphere_linked.scale = (1,1,1)
            sphere_linked["base_color"] = tracks_color[track_count]
            sphere_linked["emission_color"] = tracks_color[track_count]

        w_log(f"FW V2: {len(track.notes_used)} clouds for track {track_index}")

        # create animation
        note_count = 0
        for note in track.notes:
            note_count += 1

            frame_time_on = int(note.time_on * fps)
            frame_time_off = int(note.time_off * fps)

            emitter_name = f"noteEmitter-{track_index}-{note.note_number}"
            emitter_obj = get_object_by_name(emitter_name)

            # Add a particle system to the object
            ps_name = f"PS-{note_count}"
            particle_system = emitter_obj.modifiers.new(name=ps_name, type='PARTICLE_SYSTEM')
            particle_settings = bpy.data.particles.new(name="ParticleSettings")

            # Assign the particle settings to the particle system
            particle_system.particle_system.settings = particle_settings

            # Configure particle system settings
            particle_settings.count = 100  # Number of particles
            particle_settings.lifetime = 50  # Lifetime of each particle
            particle_settings.frame_start = frame_time_on  # Start frame for particle emission
            particle_settings.frame_end = frame_time_off  # End frame for particle emission
            particle_settings.normal_factor = note.velocity  # Speed of particles along normals
            particle_settings.effector_weights.gravity = 0.1  # Reduce gravity influence to 20%

            # Set the particle system to render the sparkle object
            brightness = 4 + (note.velocity * 10)
            particle_settings.render_type = 'OBJECT'
            sparkle_name = f"noteSparkles-{track_index}-{note.note_number}"
            sparkle_obj = bpy.data.objects[sparkle_name]
            sparkle_obj["emission_strength"] = brightness

            particle_settings.instance_object = sparkle_obj
            particle_settings.particle_size = 1.0  # Size of particles
            particle_settings.size_random = 0.2    # 20 % of variability

        w_log(f"Fireworks V2 - animate {note_count} sparkles cloud for track {track_index}")
