"""
Module for handling Blender collections.
"""
import bpy # type: ignore  # pylint: disable=import-error
from ..globals import glb
from ..utils.stuff import w_log

def delete_collection_recursive(collection):
    """
    Recursively delete a collection and all its child collections and objects.

    Args:
    collection (bpy.types.Collection): The collection to delete.
    """
    for child in collection.children:
        delete_collection_recursive(child)

    for obj in collection.objects:
        bpy.data.objects.remove(obj, do_unlink=True)

    bpy.data.collections.remove(collection)

def find_collection(context, item):
    """
    This function searches for the collection that contains the given item.

    Parameters:
    context (bpy.types.Context): The current Blender context.
    item (bpy.types.ID): The Blender data-block to search for.
    """
    collections = item.users_collection
    if len(collections) > 0:
        return collections[0]
    return context.scene.collection

def move_to_collection(collection, obj):
    """
    This function moves an object to a new collection.
    """
    collect_to_unlink = find_collection(bpy.context, obj)
    collection.objects.link(obj)
    collect_to_unlink.objects.unlink(obj)

    master_loc_name = f"{collection.name}_MasterLocation"
    mlc = glb.master_loc_collection  # master location collection
    if mlc and master_loc_name in mlc.objects:
        obj.parent = mlc.objects[master_loc_name]

def create_collection(col_name, col_parent, empty_loc_master=True):
    """
    This function creates a new collection under a specified parent collection.
    """
    if col_name in bpy.data.collections:
        collection = bpy.data.collections[col_name]
        delete_collection_recursive(collection)

    new_collection = bpy.data.collections.new(col_name)
    col_parent.children.link(new_collection)

    if empty_loc_master:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        empty = bpy.context.active_object
        empty.name = f"{col_name}_MasterLocation"

        parent_empty_name = f"{col_parent.name}_MasterLocation"

        if parent_empty_name in glb.master_loc_collection.objects:
            empty.parent = glb.master_loc_collection.objects[parent_empty_name]

        move_to_collection(glb.master_loc_collection, empty)

    return new_collection

def purge_unused_datas():
    """
    Purge all orphaned (unused) data in the current Blender file.
    """
    purged_items = 0
    data_categories = [
        bpy.data.objects, bpy.data.curves, bpy.data.meshes, bpy.data.materials,
        bpy.data.textures, bpy.data.images, bpy.data.particles, bpy.data.node_groups,
        bpy.data.actions, bpy.data.collections, bpy.data.sounds
    ]

    for data_block in data_categories:
        for item in list(data_block):
            if not item.users:
                data_block.remove(item)
                purged_items += 1

    w_log(f"Purging complete. {purged_items} orphaned data cleaned up.")

def init_collections():
    """
    Initialize global variables that require Blender context
    """
    col_default = bpy.context.scene.collection.children[0]

    glb.master_collection = create_collection("M2B", col_default, False)
    purge_unused_datas()

    master_col = glb.master_collection

    glb.master_loc_collection = create_collection(
        "MasterLocation", 
        master_col,
        False
    )

    glb.hidden_collection = create_collection(
        "Hidden", 
        master_col,
        False
    )

    glb.hidden_collection.hide_viewport = True
