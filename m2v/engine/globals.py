"""Global constants and state management for M2V engine."""

from enum import Enum
from typing import Any

from .context import get_animation_context


class BlenderObjectTypes(Enum):
    """
    Enumeration of supported Blender object types.

    This enum defines the available primitive and custom object types that can be created
    in Blender through the M2V engine.

    Attributes:
        PLANE: A flat rectangular surface
        ICOSPHERE: A sphere made of triangular faces
        UVSPHERE: A UV-mapped sphere made of quad faces
        CUBE: A six-sided box
        CYLINDER: A circular cylinder
        BEZIER_CIRCLE: A circular curve using Bezier interpolation
        LIGHTSHOW: A custom object type for light animations
        POINT: A single point light in 3D space
        EMPTY: An empty object that can be used as a parent or placeholder
    """

    PLANE = "plane"
    ICOSPHERE = "icosphere"
    UVSPHERE = "uvsphere"
    CUBE = "cube"
    CYLINDER = "cylinder"
    BEZIER_CIRCLE = "bezier_circle"
    LIGHTSHOW = "lightshow"
    POINT = "point"
    EMPTY = "empty"


class _GlobalStateProxy:
    """Proxy to AnimationContext for backward compatibility.

    This allows old code using `glb.attribute` to work with the new context system.
    """

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the current AnimationContext."""
        ctx = get_animation_context()
        return getattr(ctx, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Delegate attribute setting to the current AnimationContext."""
        ctx = get_animation_context()
        setattr(ctx, name, value)


# Backward compatibility: expose as module-level global
glb = _GlobalStateProxy()
