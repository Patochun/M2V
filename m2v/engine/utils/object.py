"""
Module about blender objects
"""
from math import atan2
import bpy # type: ignore  # pylint: disable=import-error
import bmesh # type: ignore  # pylint: disable=import-error
from ..globals import glb, BlenderObjectTypes
# from ..config.config import BlenderObjectTypes
from ..utils.collection import move_to_collection

def create_custom_attributes(obj):
    """
    Creates custom attributes for Blender objects to control material properties.

    This function adds custom properties to Blender objects that control various
    material aspects through the GlobalCustomMaterial shader.

    Parameters:
        obj (bpy.types.Object): Object to add custom properties to

    Custom Properties Added:
        base_color (float): 0.0-1.0
            Controls base color selection in material color ramp
            
        emission_color (float): 0.0-1.0
            Controls emission color selection in material color ramp
            
        emission_strength (float): 0.0-50.0
            Controls emission intensity with soft limits
            
        alpha (float): 0.0-1.0
            Controls object transparency

    Returns:
        None

    Usage:
        create_custom_attributes(blender_object)
    """
    # Add custom attributes
    obj["base_color"] = 0.0  # Base color as a float
    obj.id_properties_ui("base_color").update(
        min=0.0,  # Minimum value
        max=1.0,  # Maximum value
        step=0.01,  # Step size for the slider
        description="Color factor for base Color (0 to 1)"
    )
    obj["base_saturation"] = 1.0  # Base saturation as a float
    obj.id_properties_ui("base_saturation").update(
        min=0.0,  # Minimum value
        max=1.0,  # Maximum value
        step=0.01,  # Step size for the slider
        description="Saturation factor for base Color (0 to 1)"
    )
    obj["emission_color"] = 0.0  # Emission color as a float
    obj.id_properties_ui("emission_color").update(
        min=0.0,  # Minimum value
        max=1.0,  # Maximum value
        step=0.01,  # Step size for the slider
        description="Color factor for the emission (0 to 1)"
    )
    obj["emission_strength"] = 0.0  # Emission strength as a float
    obj.id_properties_ui("emission_strength").update(
        min=0.0,  # Minimum value
        soft_min=0.0,  # Soft minimum for UI
        soft_max=50.0,  # Soft maximum for UI
        description="Strength of the emission"
    )
    obj["alpha"] = 1.0  # Emission strength as a float
    obj.id_properties_ui("alpha").update(
        min=0.0, # Minimum value
        max=1.0, # Maximum value
        soft_min=0.0,  # Soft minimum for UI
        soft_max=50.0,  # Soft maximum for UI
        description="Alpha transparency"
    )
    obj["note_status"] = 0.0  # Status of note as a float
    obj.id_properties_ui("note_status").update(
        min=0.0,  # Minimum value
        max=1.0,  # Maximum value
        step=0.01,  # Step size for the slider
        description="Mean if note Off = 0.0 else = velocity"
    )

def create_blender_object(
    object_type: BlenderObjectTypes,
    collection,
    name: str,
    material=None,
    location: tuple=(0,0,0),
    scale: tuple=(1,1,1),
    radius: float=1.0,
    height: float=1.0,
    width: float=1.0,
    bevel: bool=False,
    resolution: int=12,
    segments: int=24,
    rings: int=24,
    type_light: str='POINT'
) -> bpy.types.Object:
    """Creates a Blender object with specified parameters"""

    match object_type:
        case BlenderObjectTypes.PLANE:
            bpy.ops.mesh.primitive_plane_add(size=1, location=location)
            obj = bpy.context.active_object
            obj.scale = (width, height, 1)

        case BlenderObjectTypes.ICOSPHERE:
            bpy.ops.mesh.primitive_ico_sphere_add(radius=radius, location=location)
            obj = bpy.context.active_object

        case BlenderObjectTypes.UVSPHERE:
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=radius,
                location=location,
                segments=segments,
                ring_count=rings
            )
            temp_obj = bpy.context.active_object
            temp_obj.name = "UVSphereTemp"
            temp_mesh = temp_obj.data

            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(temp_mesh)

            original_vertices = list(bm.verts)

            pole_north = max(original_vertices, key=lambda v: v.co.z)
            sorted_verts = [pole_north]

            unique_z_values = sorted(set(v.co.z for v in original_vertices), reverse=True)[1:-1]

            for z in unique_z_values:
                ring_verts = [v for v in original_vertices if v.co.z == z]
                ring_verts.sort(key=lambda v: atan2(v.co.y, v.co.x))
                sorted_verts.extend(ring_verts)

            pole_south = min(original_vertices, key=lambda v: v.co.z)
            sorted_verts.append(pole_south)

            new_mesh = bpy.data.meshes.new("UVSphereReordered")
            obj = bpy.data.objects.new("UVSphereReordered", new_mesh)
            bpy.context.collection.objects.link(obj)

            new_vertices = [v.co for v in sorted_verts]

            old_faces = [[original_vertices.index(v) for v in f.verts] for f in bm.faces]
            new_faces = [[sorted_verts.index(original_vertices[idx]) for idx in face] for face in old_faces]

            new_mesh.from_pydata(new_vertices, [], new_faces)
            new_mesh.update()

            bpy.data.objects.remove(temp_obj)

            bpy.context.view_layer.objects.active = obj
            obj = bpy.context.active_object

        case BlenderObjectTypes.CUBE:
            bpy.ops.mesh.primitive_cube_add(size=1, location=location)
            obj = bpy.context.active_object
            obj.scale = scale
            if bevel:
                bpy.ops.object.modifier_add(type="BEVEL")
                bpy.ops.object.modifier_apply(modifier="BEVEL")

        case BlenderObjectTypes.CYLINDER:
            bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=location)
            obj = bpy.context.active_object
            obj.scale = (radius, radius, height)

        case BlenderObjectTypes.BEZIER_CIRCLE:
            bpy.ops.curve.primitive_bezier_circle_add(location=location, radius=radius)
            obj = bpy.context.active_object
            obj.data.resolution_u = resolution

        case BlenderObjectTypes.POINT:
            bpy.ops.object.light_add(type=type_light, location=location)
            obj = bpy.context.active_object

            obj_data = obj.data
            obj_data.energy = 20000
            obj_data.shadow_soft_size = radius
            obj_data.color = (1.0,1.0,1.0)

        case BlenderObjectTypes.LIGHTSHOW:
            bpy.ops.object.light_add(type=type_light, location=location)
            obj = bpy.context.active_object

            obj_data = obj.data
            obj_data.energy = 1
            obj_data.shadow_soft_size = radius
            obj_data.color = (1.0,1.0,1.0)
            obj_data.use_nodes = True

            node_tree = obj_data.node_tree
            nodes = node_tree.nodes
            links = node_tree.links

            for node in nodes:
                nodes.remove(node)

            color_ramp_emission = nodes.new(type="ShaderNodeValToRGB")
            color_ramp_emission.location = (-400, 0)
            color_ramp_emission.color_ramp.color_mode = 'HSV'
            color_ramp_emission.color_ramp.interpolation = 'CARDINAL'
            color_ramp_emission.color_ramp.elements.new(0.01)
            color_ramp_emission.color_ramp.elements.new(0.02)
            color_ramp_emission.color_ramp.elements.new(0.40)
            color_ramp_emission.color_ramp.elements.new(0.60)
            color_ramp_emission.color_ramp.elements.new(0.80)
            color_ramp_emission.color_ramp.elements[0].color = (0, 0, 0, 1)
            color_ramp_emission.color_ramp.elements[1].color = (1, 1, 1, 1)
            color_ramp_emission.color_ramp.elements[2].color = (0, 0, 1, 1)
            color_ramp_emission.color_ramp.elements[3].color = (1, 0, 0, 1)
            color_ramp_emission.color_ramp.elements[4].color = (1, 1, 0, 1)
            color_ramp_emission.color_ramp.elements[5].color = (0, 1, 0, 1)
            color_ramp_emission.color_ramp.elements[6].color = (0, 1, 1, 1)

            tex_coord = nodes.new(type='ShaderNodeTexCoord')
            tex_coord.location = (-800, -200)

            voronoi_texture = nodes.new(type='ShaderNodeTexVoronoi')
            voronoi_texture.location = (-600, -200)
            voronoi_texture.inputs['Scale'].default_value = 10
            voronoi_texture.inputs['Roughness'].default_value = 0
            voronoi_texture.inputs['Randomness'].default_value = 0

            color_ramp_texture = nodes.new(type="ShaderNodeValToRGB")
            color_ramp_texture.location = (-400, -200)
            color_ramp_texture.color_ramp.color_mode = 'RGB'
            color_ramp_texture.color_ramp.interpolation = 'LINEAR'
            color_ramp_texture.color_ramp.elements[0].position = 0.4
            color_ramp_texture.color_ramp.elements[0].color = (0, 0, 0, 1)
            color_ramp_texture.color_ramp.elements[1].position = 0.5
            color_ramp_texture.color_ramp.elements[1].color = (1, 1, 1, 1)

            mix_color = nodes.new(type='ShaderNodeMixRGB')
            mix_color.location = (-100, -100)
            mix_color.blend_type = 'DIVIDE'
            mix_color.inputs[0].default_value = 0.5

            emission_node = nodes.new(type="ShaderNodeEmission")
            emission_node.location = (100, 0)

            output_node = nodes.new(type="ShaderNodeOutputLight")
            output_node.location = (300, 0)

            links.new(color_ramp_emission.outputs[0], mix_color.inputs[1])
            links.new(tex_coord.outputs["Normal"], voronoi_texture.inputs["Vector"])
            links.new(voronoi_texture.outputs[0], color_ramp_texture.inputs[0])
            links.new(color_ramp_texture.outputs[0], mix_color.inputs[2])
            links.new(mix_color.outputs[0], emission_node.inputs["Color"])
            links.new(emission_node.outputs["Emission"], output_node.inputs["Surface"])

            driver = emission_node.inputs["Strength"].driver_add("default_value").driver
            driver.type = 'SCRIPTED'

            var = driver.variables.new()
            var.name = "emission_strength"
            var.type = 'SINGLE_PROP'
            var.targets[0].id = obj
            var.targets[0].data_path = '["emission_strength"]'

            driver.expression = "emission_strength"

            driver = color_ramp_emission.inputs[0].driver_add('default_value').driver
            driver.type = 'SCRIPTED'

            var = driver.variables.new()
            var.name = "emission_color"
            var.type = 'SINGLE_PROP'
            var.targets[0].id = obj
            var.targets[0].data_path = '["emission_color"]'

            driver.expression = "emission_color"

        case BlenderObjectTypes.EMPTY:
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
            obj = bpy.context.active_object
            obj.name = name
            obj.empty_display_size = 2.0
            obj.empty_display_type = 'PLAIN_AXES'

    obj.name = name
    if material:
        obj.data.materials.append(material)
    create_custom_attributes(obj)
    move_to_collection(collection, obj)

    return obj

def create_duplicate_linked_object(collection, original_object, name, independant=False):
    """Creates a linked duplicate of an object"""
    if independant:
        linked_object = original_object.copy()
        linked_object.data = original_object.data.copy()
        linked_object.animation_data_clear()
        linked_object.name = name
    else:
        linked_object = original_object.copy()
        linked_object.name = name

    collection.objects.link(linked_object)
    if glb.master_loc_collection and collection.name+"_MasterLocation" in glb.master_loc_collection.objects:
        parent_empty = glb.master_loc_collection.objects[collection.name+"_MasterLocation"]
        linked_object.parent = parent_empty
    return linked_object

def get_object_by_name(name):
    """Get an object by name"""
    return bpy.data.objects[name]

def create_mat_global_custom():
    """
    Creates a global custom material with color ramps and emission control

    This function creates or updates a shared material used across multiple objects.
    It sets up a node network for dynamic color and emission control through object properties.

    Node Setup:
        - Principled BSDF: Main shader
        - Color Ramps (HSV mode):
        - Base color: Black -> White -> Blue -> Red -> Yellow -> Green -> Cyan
        - Emission: Same color progression
        - Attribute nodes for:
        - base_color: Controls base color selection (0.0-1.0)
        - emission_color: Controls emission color selection (0.0-1.0)
        - emission_strength: Controls emission intensity
        - alpha: Controls transparency

    Custom Properties Used:
        - base_color: Object property for base color selection
        - base_saturation: Object property for color saturation
        - emission_color: Object property for emission color
        - emission_strength: Object property for emission intensity
        - alpha: Object property for transparency

    Returns:
        bpy.types.Material: The created or updated material

    Usage:
        material = create_mat_global_custom()
        object.data.materials.append(material)
    """
    material_name = "GlobalCustomMaterial"
    if material_name not in bpy.data.materials:
        mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True
    else:
        mat = bpy.data.materials[material_name]

    # Configure the material nodes
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Add necessary nodes
    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (600, 0)

    principled_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled_bsdf.location = (300, 0)

    attribute_base_color = nodes.new(type="ShaderNodeAttribute")
    attribute_base_color.location = (-400, 100)
    attribute_base_color.attribute_name = "base_color"
    attribute_base_color.attribute_type = 'OBJECT'

    attribute_base_sat = nodes.new(type="ShaderNodeAttribute")
    attribute_base_sat.location = (-400, 300)
    attribute_base_sat.attribute_name = "base_saturation"
    attribute_base_sat.attribute_type = 'OBJECT'

    color_ramp_base = nodes.new(type="ShaderNodeValToRGB")
    color_ramp_base.location = (-200, 100)
    color_ramp_base.color_ramp.color_mode = 'HSV'
    color_ramp_base.color_ramp.interpolation = 'CARDINAL'  # Ensure linear interpolation
    color_ramp_base.color_ramp.elements.new(0.01)  # Add a stop at 0.01
    color_ramp_base.color_ramp.elements.new(0.02)  # Add a stop at 0.02
    color_ramp_base.color_ramp.elements.new(0.40)  # Add a stop at 0.40
    color_ramp_base.color_ramp.elements.new(0.60)  # Add a stop at 0.60
    color_ramp_base.color_ramp.elements.new(0.80)  # Add a stop at 0.80
    color_ramp_base.color_ramp.elements[0].color = (0, 0, 0, 1)  # Black 0.0
    color_ramp_base.color_ramp.elements[1].color = (1, 1, 1, 1)  # White 0.01
    color_ramp_base.color_ramp.elements[2].color = (0, 0, 1, 1)  # Blue 0.02
    color_ramp_base.color_ramp.elements[3].color = (1, 0, 0, 1)  # Red 0.4
    color_ramp_base.color_ramp.elements[4].color = (1, 1, 0, 1)  # Yellow 0.6
    color_ramp_base.color_ramp.elements[5].color = (0, 1, 0, 1)  # Green 0.8
    color_ramp_base.color_ramp.elements[6].color = (0, 1, 1, 1)  # Cyan 1.0

    mix_color_base = nodes.new(type='ShaderNodeMixRGB')
    mix_color_base.location = (100, 200)
    mix_color_base.blend_type = 'MIX'
    mix_color_base.inputs[2].default_value = (0.0, 0.0, 0.0, 1)

    attribute_emission_strength = nodes.new(type="ShaderNodeAttribute")
    attribute_emission_strength.location = (-400, -300)
    attribute_emission_strength.attribute_name = "emission_strength"
    attribute_emission_strength.attribute_type = 'OBJECT'

    attribute_emission_color = nodes.new(type="ShaderNodeAttribute")
    attribute_emission_color.location = (-400, -100)
    attribute_emission_color.attribute_name = "emission_color"
    attribute_emission_color.attribute_type = 'OBJECT'

    color_ramp_emission = nodes.new(type="ShaderNodeValToRGB")
    color_ramp_emission.location = (-200, -100)
    color_ramp_emission.color_ramp.color_mode = 'HSV'
    color_ramp_emission.color_ramp.interpolation = 'CARDINAL'  # Ensure linear interpolation
    color_ramp_emission.color_ramp.elements.new(0.01)  # Add a stop at 0.01
    color_ramp_emission.color_ramp.elements.new(0.02)  # Add a stop at 0.02
    color_ramp_emission.color_ramp.elements.new(0.40)  # Add a stop at 0.40
    color_ramp_emission.color_ramp.elements.new(0.60)  # Add a stop at 0.60
    color_ramp_emission.color_ramp.elements.new(0.80)  # Add a stop at 0.80
    color_ramp_emission.color_ramp.elements[0].color = (0, 0, 0, 1)  # Black 0.0
    color_ramp_emission.color_ramp.elements[1].color = (1, 1, 1, 1)  # White 0.01
    color_ramp_emission.color_ramp.elements[2].color = (0, 0, 1, 1)  # Blue 0.02
    color_ramp_emission.color_ramp.elements[3].color = (1, 0, 0, 1)  # Red 0.4
    color_ramp_emission.color_ramp.elements[4].color = (1, 1, 0, 1)  # Yellow 0.6
    color_ramp_emission.color_ramp.elements[5].color = (0, 1, 0, 1)  # Green 0.8
    color_ramp_emission.color_ramp.elements[6].color = (0, 1, 1, 1)  # Cyan 1.0

    attribute_alpha = nodes.new(type="ShaderNodeAttribute")
    attribute_alpha.location = (-400, -500)
    attribute_alpha.attribute_name = "alpha"
    attribute_alpha.attribute_type = 'OBJECT'

    # Connect the nodes
    links.new(attribute_base_color.outputs["Fac"], color_ramp_base.inputs["Fac"])  # Emission color
    links.new(attribute_emission_strength.outputs["Fac"], principled_bsdf.inputs["Emission Strength"])  # Emission strength
    links.new(attribute_alpha.outputs["Fac"], principled_bsdf.inputs["Alpha"])  # Emission strength
    links.new(attribute_emission_color.outputs["Fac"], color_ramp_emission.inputs["Fac"])  # Emission color
    links.new(color_ramp_base.outputs["Color"], mix_color_base.inputs[2])   # Original color
    links.new(attribute_base_sat.outputs["Fac"], mix_color_base.inputs[0])  # Factor from base_saturation
    links.new(mix_color_base.outputs["Color"], principled_bsdf.inputs["Base Color"])  # Output to shader
    links.new(color_ramp_emission.outputs["Color"], principled_bsdf.inputs["Emission Color"])  # Emission color
    links.new(principled_bsdf.outputs["BSDF"], output.inputs["Surface"])  # Output surface

    return mat

def init_materials():
    """Initialize global materials"""
    glb.mat_global_custom = create_mat_global_custom()
