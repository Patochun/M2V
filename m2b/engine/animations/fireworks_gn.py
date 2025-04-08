"""
Module for firework version 1 animation with geomtry nodes
"""
import bpy # type: ignore  # pylint: disable=import-error
from ..globals import glb, BlenderObjectTypes
from ..utils.collection import create_collection
from ..utils.object import create_blender_object, create_duplicate_linked_object, get_object_by_name
from ..utils.animation import note_animate
from ..utils.stuff import w_log, parse_range_from_tracks

def create_sp_cloud_gn(name_gn, obj, sparkles_material):
    """
    Creates a Geometry Nodes setup for generating sparkles cloud effect

    This function creates a geometry nodes modifier that generates a cloud of sparkles
    around a mesh. It uses point distribution on an icosphere to create the cloud effect.

    Parameters:
        name_gn (str): Name for the geometry nodes group and modifier
        obj (bpy.types.Object): Blender object to add the modifier to
        sparkles_material (bpy.types.Material): Material to apply to sparkles

    Node Setup:
        - Input icosphere for cloud volume
        - Point distribution for sparkle positions
        - Instance smaller icospheres as sparkles
        - Material assignment for sparkles

    Inputs exposed:
        - radius_sparkles_cloud: Overall cloud size (0.0-1.0)
        - radius_sparkles: Individual sparkle size (0.0-0.05)
        - density_cloud: Sparkle density (0-10)
        - density_seed: Random seed for distribution (0-100000)
        - sparkle_material: Material for sparkles

    Returns:
        None
    """

    # Add a modifier Geometry Nodes
    mod = obj.modifiers.new(name=name_gn, type='NODES')

    # Create a new node group
    ng = bpy.data.node_groups.new(name=name_gn, type="GeometryNodeTree")

    # Associate group with modifier
    mod.node_group = ng

    # Define inputs and outputs
    ng.interface.new_socket(socket_type="NodeSocketGeometry",
                            name="Geometry", in_out="INPUT")
    radius_sparkles_cloud = ng.interface.new_socket(socket_type="NodeSocketFloat",
                                                    name="radiusSparklesCloud",
                                                    in_out="INPUT",
                                                    description="Radius of the sparkles cloud")
    radius_sparkles = ng.interface.new_socket(socket_type="NodeSocketFloat",
                                              name="radiusSparkles",
                                              in_out="INPUT",
                                              description="Radius of the sparkles")
    socket_density_cloud = ng.interface.new_socket(socket_type="NodeSocketFloat",
                                                   name="density_cloud",
                                                   in_out="INPUT",
                                                   description="Density of the sparkles cloud")
    socket_density_seed = ng.interface.new_socket(socket_type="NodeSocketInt",
                                                  name="density_seed",
                                                  in_out="INPUT",
                                                  description="Seed of the sparkles cloud")
    ng.interface.new_socket(socket_type="NodeSocketMaterial",
                            name="sparkleMaterial",
                            in_out="INPUT")
    ng.interface.new_socket(socket_type="NodeSocketGeometry",
                            name="Geometry",
                            in_out="OUTPUT")

    radius_sparkles_cloud.default_value = 1.0
    radius_sparkles_cloud.min_value = 0.0
    radius_sparkles_cloud.max_value = 1.0

    radius_sparkles.default_value = 0.02
    radius_sparkles.min_value = 0.0
    radius_sparkles.max_value = 0.05

    socket_density_cloud.default_value = 10
    socket_density_cloud.min_value = 0
    socket_density_cloud.max_value = 10

    socket_density_seed.default_value = 0
    socket_density_seed.min_value = 0
    socket_density_seed.max_value = 100000

    # Add necessary nodes
    node_input = ng.nodes.new("NodeGroupInput")
    node_input.location = (-500, 0)

    node_output = ng.nodes.new("NodeGroupOutput")
    node_output.location = (800, 0)

    icosphere_cloud = ng.nodes.new("GeometryNodeMeshIcoSphere")
    icosphere_cloud.location = (-300, 200)
    icosphere_cloud.inputs["Subdivisions"].default_value = 3

    multiply_node = ng.nodes.new("ShaderNodeMath")
    multiply_node.location = (-300, -100)
    multiply_node.operation = 'MULTIPLY'
    multiply_node.inputs[1].default_value = 10.0

    distribute_points = ng.nodes.new("GeometryNodeDistributePointsOnFaces")
    distribute_points.location = (0, 200)

    icosphere_sparkles = ng.nodes.new("GeometryNodeMeshIcoSphere")
    icosphere_sparkles.location = (0, -200)
    icosphere_sparkles.inputs["Subdivisions"].default_value = 1

    instance_on_points = ng.nodes.new("GeometryNodeInstanceOnPoints")
    instance_on_points.location = (300, 200)

    set_material = ng.nodes.new("GeometryNodeSetMaterial")
    set_material.location = (600, 200)

    # Connect nodes
    links = ng.links
    links.new(icosphere_cloud.outputs["Mesh"], distribute_points.inputs["Mesh"])
    links.new(distribute_points.outputs["Points"], instance_on_points.inputs["Points"])
    links.new(multiply_node.outputs["Value"], distribute_points.inputs["Density"])
    links.new(instance_on_points.outputs["Instances"], set_material.inputs["Geometry"])
    links.new(icosphere_sparkles.outputs["Mesh"], instance_on_points.inputs["Instance"])
    links.new(node_input.outputs["radiusSparklesCloud"], icosphere_cloud.inputs["Radius"])
    links.new(node_input.outputs["radiusSparkles"], icosphere_sparkles.inputs["Radius"])
    links.new(node_input.outputs["density_cloud"], multiply_node.inputs[0])
    links.new(node_input.outputs["density_seed"], distribute_points.inputs["Seed"])
    links.new(node_input.outputs["sparkleMaterial"], set_material.inputs["Material"])
    links.new(set_material.outputs["Geometry"], node_output.inputs["Geometry"])

    w_log(f"Geometry Nodes '{name_gn}' created successfully!")

def create_fireworks_v1(track_mask, type_anim):
    """
    Creates a fireworks visualization where notes are represented as exploding sparkle clouds.

    This function creates a fireworks display where:
    - Notes are arranged in a grid pattern
    - Each note is represented by a sphere with sparkle particles
    - Spheres explode with particles when notes are played
    - Colors are assigned by track

    Parameters:
        track_mask (str): Track selection pattern (e.g. "0-5,7,9-12")
        type_anim (str): Animation style to apply ("Spread", "MultiLight", etc)

    Structure:
        - FireworksV1 (main collection)
            - FW-TrackN (per track collections)
                - Sphere objects with sparkle clouds
                - Each sphere positioned by note/octave

    Grid Layout:
        - X axis: Notes within octave (0-11)
        - Y axis: Octaves
        - Z axis: Animation space for explosions

    Returns:
        None
    """

    w_log(f"Create a Fireworks V1 Notes Animation type = {type_anim}")

    (list_of_selected_track,
    _,
    _,
    octave_count,
    _,
    tracks_color
    ) = parse_range_from_tracks(track_mask)

    tracks = glb.tracks

    # Create master BG collection
    fw_collect = create_collection("FireworksV1", glb.master_collection)

    # Create model Sphere
    fw_sphere = create_blender_object(
        BlenderObjectTypes.ICOSPHERE,
        collection=glb.hidden_collection,
        name="FWModelSphere",
        material=glb.mat_global_custom,
        location=(0,0,-5),
        radius=1
    )

    # create sparkles_cloud_gn and set parameters
    # Create sparkles cloud geometry nodes
    create_sp_cloud_gn("SparklesCloud", fw_sphere, glb.mat_global_custom)

    # Get modifier interface identifiers
    mod = fw_sphere.modifiers["SparklesCloud"]
    items = mod.node_group.interface.items_tree

    # Set modifier parameters
    radius_cloud_id = items["radiusSparklesCloud"].identifier
    mod[radius_cloud_id] = 1.0

    radius_spark_id = items["radiusSparkles"].identifier
    mod[radius_spark_id] = 0.02

    density_id = items["density_cloud"].identifier
    mod[density_id] = 0.1

    material_id = items["sparkleMaterial"].identifier
    mod[material_id] = glb.mat_global_custom

    space_x = 5
    space_y = 5
    offset_x = 5.5 * space_x # center of the octave, mean between fifth and sixt note
    offset_y = (octave_count * space_y) - (space_y / 2)

    # Construction
    note_count = 0
    for track_count, track_index in enumerate(list_of_selected_track):
        track = tracks[track_index]

        # create collection
        fw_track_name = f"FW-{track_index}-{track.name}"
        fw_track_collect = create_collection(fw_track_name, fw_collect)

        # one sphere per note used
        for note in track.notes_used:
            note_count += 1
            s = create_duplicate_linked_object(fw_track_collect, fw_sphere,
                                               f"Sphere-{track_index}-{note}")
            s.location = ((note % 12) * space_x - offset_x, (note // 12) * space_y - offset_y, 0)
            s.scale = (0,0,0)
            s["base_color"] = tracks_color[track_count]
            s["emission_color"] = tracks_color[track_count]
            s.modifiers["SparklesCloud"][items["density_seed"].identifier] = note_count

        w_log(f"FW - {note_count} sparkles "
              f"for track {track_index} ({track.min_note}-{track.max_note})")

    # Animation
    for track_count, track_index in enumerate(list_of_selected_track):
        track = tracks[track_index]

        for note_index, note in enumerate(track.notes):
            # Construct the sphere name and animate
            obj_name = f"Sphere-{track_index}-{note.note_number}"
            note_obj = get_object_by_name(obj_name)
            note_animate(note_obj, type_anim, track, note_index, tracks_color[track_count-1])

        w_log(f"Fireworks - Animate sparkles cloud for track {track_index} "
              f"(notesCount) ({len(track.notes)})")
