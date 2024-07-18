import bpy
from bpy.app.handlers import persistent
from .prefs import get_addon_prefs


@persistent
def start_cleaner(scene, depsgraph):
    bpy.app.handlers.depsgraph_update_pre.append(WeightCleaner.clean_weights)
    bpy.app.handlers.depsgraph_update_post.append(WeightCleaner.reset_flag)


class WeightCleaner:
    """Run bpy.ops.object.vertex_group_clean on every depsgraph update while in weight paint mode (ie. every brush stroke)."""

    # Flag set in post_depsgraph_update, to indicate to pre_depsgraph_update that the depsgraph update has indeed completed.
    can_clean = True
    # Flag set by pre_depsgraph_update to indicate to post_depsgraph_update that the cleanup operator is still running (in a different thread).
    cleaning_in_progress = False

    @classmethod
    def clean_weights(cls, scene, depsgraph):
        context = bpy.context
        prefs = get_addon_prefs(context)
        if context.mode != 'PAINT_WEIGHT':
            return
        if not context or not hasattr(context, 'active_object') or not context.active_object:
            return
        if not prefs.auto_clean_weights:
            return
        if cls.can_clean:
            cls.can_clean = False
            cls.cleaning_in_progress = True
            # This will trigger a depsgraph update, and therefore clean_weights, again.
            try:
                bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.001)
            except Exception:
                # This happens for example if the object has no vertex groups.
                pass
            cls.cleaning_in_progress = False

    @classmethod
    def reset_flag(cls, scene, depsgraph):
        context = bpy.context
        if context.mode != 'PAINT_WEIGHT':
            return
        if not context or not hasattr(context, 'active_object') or not context.active_object:
            return
        if cls.cleaning_in_progress:
            return
        cls.can_clean = True


def register():
    start_cleaner(None, None)
    bpy.app.handlers.load_post.append(start_cleaner)


def unregister():
    bpy.app.handlers.load_post.remove(start_cleaner)
