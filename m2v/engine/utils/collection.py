"""Module for handling Blender collections."""

import bpy  # type: ignore  # pylint: disable=import-error

from ..context import AnimationContext


def delete_collection_recursive(collection: bpy.types.Collection) -> None:
    """Recursively delete a collection and all its child collections/objects.

    Args:
        collection: The collection to delete.
    """
    for child in collection.children:
        delete_collection_recursive(child)

    for obj in collection.objects:
        bpy.data.objects.remove(obj, do_unlink=True)

    bpy.data.collections.remove(collection)


def find_collection(context, item: bpy.types.ID) -> bpy.types.Collection:
    """Search for the collection that contains the given item.

    Args:
        context: The current Blender context.
        item: The Blender data-block to search for.

    Returns:
        The collection containing the item, or the scene collection.
    """
    collections = item.users_collection
    if len(collections) > 0:
        return collections[0]
    return context.scene.collection


def move_to_collection(
    collection: bpy.types.Collection, obj: bpy.types.Object, ctx: AnimationContext
) -> None:
    """Move an object to a new collection.

    Args:
        collection: Target collection
        obj: Object to move
        ctx: Animation context
    """
    collect_to_unlink = find_collection(bpy.context, obj)
    collection.objects.link(obj)
    collect_to_unlink.objects.unlink(obj)

    master_loc_name = f"{collection.name}_MasterLocation"
    mlc = ctx.master_loc_collection
    if mlc and master_loc_name in mlc.objects:
        obj.parent = mlc.objects[master_loc_name]


def create_collection(
    col_name: str,
    col_parent: bpy.types.Collection,
    empty_loc_master: bool = True,
    ctx: AnimationContext | None = None,
) -> bpy.types.Collection:
    """Create a new collection under a specified parent collection.

    Args:
        col_name: Name of the new collection
        col_parent: Parent collection
        empty_loc_master: Whether to create a master location empty
        ctx: Animation context (required if empty_loc_master=True)

    Returns:
        The newly created collection
    """
    if col_name in bpy.data.collections:
        collection = bpy.data.collections[col_name]
        delete_collection_recursive(collection)

    new_collection = bpy.data.collections.new(col_name)
    col_parent.children.link(new_collection)

    if empty_loc_master:
        if ctx is None:
            raise ValueError("ctx is required when empty_loc_master=True")
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
        empty = bpy.context.active_object
        empty.name = f"{col_name}_MasterLocation"

        parent_empty_name = f"{col_parent.name}_MasterLocation"

        if ctx.master_loc_collection and parent_empty_name in ctx.master_loc_collection.objects:
            empty.parent = ctx.master_loc_collection.objects[parent_empty_name]

        move_to_collection(ctx.master_loc_collection, empty, ctx)

    return new_collection


def init_collections(ctx: AnimationContext) -> None:
    """Initialize collections in the Blender scene.

    Args:
        ctx: Animation context to populate with collection references
    """
    col_default = bpy.context.scene.collection.children[0]

    ctx.master_collection = create_collection("M2V", col_default, False)

    master_col = ctx.master_collection

    ctx.master_loc_collection = create_collection(
        "MasterLocation", master_col, False
    )

    ctx.hidden_collection = create_collection("Hidden", master_col, False, ctx)

    ctx.hidden_collection.hide_viewport = True
