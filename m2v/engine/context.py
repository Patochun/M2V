"""Context manager for M2V animation state.

This module provides a context manager to handle animation state
instead of using global variables.
"""

from contextlib import contextmanager
from typing import Any


class AnimationContext:
    """Container for animation state passed between functions."""

    def __init__(self):
        self.fps = 0
        self.tracks = []
        self.last_note_time_off = 0.0
        self.mat_global_custom: Any = None
        self.master_collection: Any = None
        self.master_loc_collection: Any = None
        self.hidden_collection: Any = None
        self.f_log: Any = None


# Thread-local storage for context (for Blender's execution model)
_current_context: AnimationContext | None = None


def get_animation_context() -> AnimationContext:
    """Get the current animation context.

    Raises:
        RuntimeError: If context not initialized with with_animation_context()
    """
    if _current_context is None:
        raise RuntimeError(
            "Animation context not initialized. Use with_animation_context() first."
        )
    return _current_context


def set_animation_context(ctx: AnimationContext) -> None:
    """Set the current animation context.

    Args:
        ctx: AnimationContext instance to use
    """
    global _current_context
    _current_context = ctx


@contextmanager
def with_animation_context():
    """Context manager for animation state.

    Usage:
        with with_animation_context() as ctx:
            ctx.fps = scene.render.fps
            # ... use ctx throughout

    Yields:
        AnimationContext: The current animation context
    """
    global _current_context
    old_context = _current_context
    _current_context = AnimationContext()
    try:
        yield _current_context
    finally:
        _current_context = old_context

