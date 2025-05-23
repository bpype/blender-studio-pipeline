# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.app.handlers import persistent
from .utils import get_addon_prefs

@persistent
def start_cleaner(scene=None, depsgraph=None):
    if WeightCleaner.clean_weights not in bpy.app.handlers.depsgraph_update_pre:
        bpy.app.handlers.depsgraph_update_pre.append(WeightCleaner.clean_weights)
    if WeightCleaner.reset_flag not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(WeightCleaner.reset_flag)

@persistent
def stop_cleaner(scene=None, depsgraph=None):
    if WeightCleaner.clean_weights in bpy.app.handlers.depsgraph_update_pre:
        bpy.app.handlers.depsgraph_update_pre.remove(WeightCleaner.clean_weights)
    if WeightCleaner.reset_flag in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(WeightCleaner.reset_flag)


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
        tool = context.workspace.tools.from_space_view3d_mode("PAINT_WEIGHT", create=False).idname
        if tool == "builtin.gradient":
            # Trying to clean while using gradient causes a crash:
            # https://projects.blender.org/studio/blender-studio-tools/issues/332
            return
        if cls.can_clean:
            cls.can_clean = False
            cls.cleaning_in_progress = True
            # This will trigger a depsgraph update, and therefore clean_weights, again.
            try:
                ensure_mirror_groups(context.active_object)
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

def ensure_mirror_groups(mesh_obj):
    mod_types = [mod.type for mod in mesh_obj.modifiers]
    rigs = [m.object for m in mesh_obj.modifiers if m.type == 'ARMATURE' and m.object]
    if rigs and 'MIRROR' in mod_types:
        for rig in rigs:
            for pb in rig.pose.bones:
                if pb.name in mesh_obj.vertex_groups:
                    flipped_name = bpy.utils.flip_name(pb.name)
                    if flipped_name != pb.name and flipped_name not in mesh_obj.vertex_groups:
                        mesh_obj.vertex_groups.new(name=flipped_name)
        

def register():
    start_cleaner()
    bpy.app.handlers.load_post.append(start_cleaner)


def unregister():
    stop_cleaner()
    bpy.app.handlers.load_post.remove(start_cleaner)
