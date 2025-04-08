"""
Root module for animation
"""
from .bar_graph import create_blender_bg_animation
from .strip_notes import create_strip_notes
from .water_fall import create_waterfall
from .fireworks_gn import create_fireworks_v1
from .fireworks_particules import create_fireworks_v2
from .fountain import create_fountain
from .light_show import create_light_show

def animate(animation, track_mask, animation_type):
    """
    Creates an animation based on the specified animation type and parameters.

    Args:
        animation (str): The type of animation to create. Valid options are:
            - "barGraph": Creates a bar graph animation
            - "stripNotes": Creates strip notes animation
            - "waterFall": Creates waterfall animation
            - "fireworksV1": Creates fireworks version 1 animation
            - "fireworksV2": Creates fireworks version 2 animation 
            - "fountain": Creates fountain animation
            - "lightShow": Creates light show animation
        track_mask: The track mask to apply to the animation
        animation_type: The specific type/style of the selected animation

    Raises:
        None: Prints "Invalid animation type" message if animation parameter is not recognized

    Returns:
        None: Creates the specified animation in Blender
    """
    if animation == "barGraph":
        create_blender_bg_animation(track_mask=track_mask, type_anim=animation_type)
    elif animation == "stripNotes":
        create_strip_notes(track_mask=track_mask, type_anim=animation_type)
    elif animation == "waterFall":
        create_waterfall(track_mask=track_mask, type_anim=animation_type)
    elif animation == "fireworksV1":
        create_fireworks_v1(track_mask=track_mask, type_anim=animation_type)
    elif animation == "fireworksV2":
        create_fireworks_v2(track_mask=track_mask, type_anim=animation_type)
    elif animation == "fountain":
        create_fountain(track_mask=track_mask, type_anim=animation_type)
    elif animation == "lightShow":
        create_light_show(track_mask=track_mask, type_anim=animation_type)
    else:
        print("Invalid animation type")
