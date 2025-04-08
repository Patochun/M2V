"""
Module for light show animation
"""
from colorsys import hsv_to_rgb
import bpy # type: ignore  # pylint: disable=import-error
from ..globals import glb, BlenderObjectTypes
from ..utils.collection import create_collection
from ..utils.object import create_blender_object, create_duplicate_linked_object
from ..utils.stuff import w_log, parse_range_from_tracks, extract_octave_and_note
from ..utils.animation import distribute_objects_with_clamp_to, anim_circle_curve

# Return a list of color r,g,b,a dispatched
def generate_hsv_colors(n_series):
    """
    Generate a list of RGB colors evenly distributed in HSV color space.

    This function creates a list of RGB color tuples by converting from HSV color space,
    using uniform hue distribution while keeping constant saturation and value.

    Args:
        n_series (int): Number of colors to generate.

    Returns:
        list: A list of RGB color tuples, where each tuple contains 3 float values
              between 0 and 1 representing (red, green, blue) components.

    Example:
        >>> generate_hsv_colors(3)
        [(0.9, 0.18, 0.18), (0.18, 0.9, 0.18), (0.18, 0.18, 0.9)]
    """
    colors = []
    for i in range(n_series):
        hue = i / n_series  # uniform space
        saturation = 0.8    # Saturation high for vibrant color
        value = 0.9         # High luminosity
        r,g,b = hsv_to_rgb(hue, saturation, value)
        colors.append((r,g,b))
    return colors

def create_light_show(track_mask, type_anim):
    """Creates a light show animation in Blender using spheres and lights.
    This function generates a visual light show animation where spheres
    with lights represent musical tracks. 
    Each sphere has sections that light up based on musical notes,
    creating a synchronized light show effect.
    Args:
        track_mask (list): List of track indices to include in the animation.
        type_anim (str): Animation type, either "Cycle" or standard. Affects light creation style.
    Returns:
        None
    """

    w_log(f"Create a Light Show Notes Animation type = {type_anim}")

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

    # generate a track count list of dispatched colors
    random_hsv_colors = generate_hsv_colors(len(tracks))

    # Create master LightShow collection
    light_show_collection = create_collection("LightShow", glb.master_collection)

    ring_count = 64  # Number of rings to create
    # Create model objects
    light_show_model_uv_sphere = create_blender_object(
        BlenderObjectTypes.UVSPHERE,
        collection=glb.hidden_collection,
        name="light_show_model_uv_sphere",
        location=(0, 0, -5),
        radius=1,
        segments=48,
        rings=ring_count
    )

    # Create the two materials
    mat_opaque = bpy.data.materials.new(name="mat_opaque")
    mat_opaque.use_nodes = True
    mat_opaque.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 1.0

    mat_trans = bpy.data.materials.new(name="mat_trans")
    mat_trans.use_nodes = True
    mat_trans.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.0

    # Assign both materials to sphere
    light_show_model_uv_sphere.data.materials.append(mat_opaque)  # Material index 0
    light_show_model_uv_sphere.data.materials.append(mat_trans)   # Material index 1

    vertices_per_ring = 48
    vertices_per_octave = vertices_per_ring * 3

    mesh = light_show_model_uv_sphere.data

    # Create dictionary to store face indices per note
    note_faces = {}

    offset = 10  # Offset to center the rings
    # Create vertex groups and store face indices
    for octave in range(11):
        for note in range(12):
            vg = light_show_model_uv_sphere.vertex_groups.new(name=f"note_{octave}-{note}")

            base_index = 1 + ((octave+offset) * vertices_per_octave)
            v1 = base_index + (note * 4)
            v2 = v1 + 1
            v3 = v1 + vertices_per_ring
            v4 = v2 + vertices_per_ring

            if all(v < len(mesh.vertices) for v in [v1, v2, v3, v4]):
                vg.add([v1, v2, v3, v4], 1.0, 'ADD')

                for face in mesh.polygons:
                    if all(v in face.vertices for v in [v1, v2, v3, v4]):
                        note_faces[f"note_{octave}-{note}"] = face.index
                        break

    sphere_lights = []
    # Create one sphere per track
    for track_count, track_index in enumerate(list_of_selected_track):
        track = tracks[track_index]

        # Create collection for track
        track_name = f"Track-{track_index}-{track.name}"
        track_collection = create_collection(track_name, light_show_collection)

        # Create sphere object
        sphere_name = f"Sphere-{track_index}-{track.name}"
        sphere = create_duplicate_linked_object(track_collection, light_show_model_uv_sphere,
                                                sphere_name, independant=True)
        sphere.location = (0, 0, 0)
        sphere_lights.append(sphere)

        if type_anim == "CYCLE":
            # Create Light Point into sphere
            light_point = create_blender_object(
                BlenderObjectTypes.LIGHTSHOW,
                collection=track_collection,
                name=f"Light-{track_index}-{track.name}",
                location=sphere.location,
                type_light='POINT',
                radius=0.2
            )
            light_point["emission_color"] = tracks_color[track_count]
            light_point["emission_strength"] = 20000
        else:
            light_point = create_blender_object(
                BlenderObjectTypes.POINT,
                collection=track_collection,
                name=f"Light-{track_index}-{track.name}",
                location=sphere.location,
                type_light='POINT',
                radius=0.8
            )
            light_point.data.color = random_hsv_colors[track_index]
            light_point.data.energy = 2000000

        # parent light to sphere
        light_point.parent = sphere

        # Initialize all faces to opaque at frame 0
        mesh = sphere.data
        for face in mesh.polygons:
            face.material_index = 0
            face.keyframe_insert('material_index', frame=0)

        # Animate the sphere
        for note in track.notes:

            octave, note_number = extract_octave_and_note(note.note_number)
            note_name = f"note_{octave}-{note_number}"
            note_frame_on = int(note.time_on * fps)
            note_frame_off = int(note.time_off * fps)

            if note_name in note_faces:
                face = mesh.polygons[note_faces[note_name]]
                face.material_index = 0
                face.keyframe_insert('material_index', frame=note_frame_on - 1)
                face.material_index = 1
                face.keyframe_insert('material_index', frame=note_frame_on)
                face.material_index = 1
                face.keyframe_insert('material_index', frame=note_frame_off - 1)
                face.material_index = 0
                face.keyframe_insert('material_index', frame=note_frame_off)

        w_log(f"Light Show - Animate track {track_index} with {len(track.notes)} notes")

    # Create circle curve for trajectory of spheres
    radius_curve = 10
    light_show_trajectory = create_blender_object(
        BlenderObjectTypes.BEZIER_CIRCLE,
        collection=light_show_collection,
        name="light_show_trajectory",
        location=(0, 0, 3),
        radius=radius_curve
    )

    # spheres along the curve
    distribute_objects_with_clamp_to(sphere_lights, light_show_trajectory)
    anim_circle_curve(light_show_trajectory, 0.03)
