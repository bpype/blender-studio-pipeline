# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

import bpy

from . import (
    propsdata,
    props,
    cache
)
from .ops import (
    CM_OT_cache_export,
    CM_OT_cacheconfig_export,
    CM_OT_import_cache,
    CM_OT_import_colls_from_config,
    CM_OT_update_cache_colls_list,
    CM_OT_cache_list_actions,
    CM_OT_assign_cachefile,
    CM_OT_cache_show,
    CM_OT_cache_hide,
    CM_OT_cache_remove,
    CM_OT_set_cache_version,
    CM_OT_add_cache_version_increment,
)


class CM_PT_vi3d_cache(bpy.types.Panel):
    bl_category = "CacheManager"
    bl_label = "Cache"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        split_factor = 0.225
        split_factor_small = 0.95
        # Category to choose between export / import.
        row = layout.row(align=True)
        row.prop(context.scene.cm, "category", expand=True)

        # Add some space.
        row = layout.row(align=True)
        row.separator()

        # Box for cache version and cacheconfig.
        box = layout.box()

        # Version.
        version_text = self._get_version_text(context)

        split = box.split(factor=split_factor, align=True)

        # Version label.
        split.label(text="Version:")

        if context.scene.cm.category == "EXPORT":
            sub_split = split.split(factor=split_factor_small, align=True)
            sub_split.operator(
                CM_OT_set_cache_version.bl_idname,
                icon="DOWNARROW_HLT",
                text=version_text,
            )
            sub_split.operator(
                CM_OT_add_cache_version_increment.bl_idname,
                icon="ADD",
                text="",
            )

        else:
            split.operator(
                CM_OT_set_cache_version.bl_idname,
                icon="DOWNARROW_HLT",
                text=version_text,
            )

        # Cachedir.
        split = box.split(factor=split_factor, align=True)

        # Cachedir label.
        split.label(text="Cache Directory:")

        if not context.scene.cm.is_cachedir_valid:
            split.label(text=f"Invalid. Check Addon Preferences.")

        else:
            if context.scene.cm.category == "EXPORT":
                if context.scene.cm.cachedir_path.exists():
                    sub_split = split.split(factor=1 - split_factor_small)
                    sub_split.label(icon="ERROR")
                    sub_split.prop(context.scene.cm, "cachedir", text="")

                else:
                    split.prop(context.scene.cm, "cachedir", text="")

            else:
                if not context.scene.cm.cachedir_path.exists():
                    split.label(text=f"Not found")
                else:
                    split.prop(context.scene.cm, "cachedir", text="")

        # Cacheconfig.
        split = box.split(factor=split_factor, align=True)
        # Cachedir label.
        split.label(text="Cacheconfig:")

        if not context.scene.cm.is_cacheconfig_valid:
            if (
                context.scene.cm.use_cacheconfig_custom
                and context.scene.cm.category == "IMPORT"
            ):
                sub_split = split.split(factor=0.95, align=True)
                sub_split.prop(context.scene.cm, "cacheconfig_custom", text="")
                sub_split.operator(
                    CM_OT_import_colls_from_config.bl_idname, icon="PLAY", text=""
                )
            else:
                split.label(text=f"Invalid. Check Addon Preferences.")

            row = box.row(align=True)
            row.prop(context.scene.cm, "use_cacheconfig_custom")

        else:
            if context.scene.cm.category == "EXPORT":

                if context.scene.cm.cacheconfig_path.exists():
                    sub_split = split.split(factor=1 - split_factor_small)
                    sub_split.label(icon="ERROR")
                    sub_split.prop(context.scene.cm, "cacheconfig", text="")

                else:
                    split.prop(context.scene.cm, "cacheconfig", text="")
            else:
                if context.scene.cm.use_cacheconfig_custom:
                    sub_split = split.split(factor=0.95, align=True)
                    sub_split.prop(context.scene.cm, "cacheconfig_custom", text="")
                    sub_split.operator(
                        CM_OT_import_colls_from_config.bl_idname, icon="PLAY", text=""
                    )

                else:
                    if not context.scene.cm.cacheconfig_path.exists():
                        split.label(text=f"Not found")

                    else:
                        sub_split = split.split(factor=0.95, align=True)
                        sub_split.prop(context.scene.cm, "cacheconfig", text="")
                        sub_split.operator(
                            CM_OT_import_colls_from_config.bl_idname,
                            icon="PLAY",
                            text="",
                        )
                row = box.row(align=True)
                row.prop(context.scene.cm, "use_cacheconfig_custom")

        # Add some space.
        row = layout.row(align=True)
        row.separator()

        # Collection operations.
        box = layout.box()
        box.label(text="Cache Collections", icon="OUTLINER_COLLECTION")
        if context.scene.cm.category == "EXPORT":

            # Get collections.
            collections = list(props.get_cache_collections_export(context))

            # Ui-list.
            row = box.row()
            row.template_list(
                "CM_UL_collection_cache_list_export",
                "collection_cache_list_export",
                context.scene.cm,
                "colls_export",
                context.scene.cm,
                "colls_export_index",
                rows=5,
                type="DEFAULT",
            )
            col = row.column(align=True)
            col.operator(
                CM_OT_update_cache_colls_list.bl_idname, icon="FILE_REFRESH", text=""
            )
            col.operator(
                CM_OT_cache_list_actions.bl_idname, icon="ADD", text=""
            ).action = "ADD"
            col.operator(
                CM_OT_cache_list_actions.bl_idname, icon="REMOVE", text=""
            ).action = "REMOVE"

            row = box.row(align=True)
            row.operator(
                CM_OT_cache_export.bl_idname,
                text=f"Cache {len(collections)} Collections",
                icon="EXPORT",
            ).do_all = True

            row.operator(
                CM_OT_cacheconfig_export.bl_idname,
                text="",
                icon="ALIGN_LEFT",
            ).do_all = True

        else:
            # Get collections.
            collections = list(props.get_cache_collections_import(context))

            # Ui-list.
            row = box.row()
            row.template_list(
                "CM_UL_collection_cache_list_import",
                "collection_cache_list_import",
                context.scene.cm,
                "colls_import",
                context.scene.cm,
                "colls_import_index",
                rows=5,
                type="DEFAULT",
            )
            col = row.column(align=True)
            col.operator(
                CM_OT_update_cache_colls_list.bl_idname, icon="FILE_REFRESH", text=""
            )
            col.operator(
                CM_OT_cache_list_actions.bl_idname, icon="ADD", text=""
            ).action = "ADD"
            col.operator(
                CM_OT_cache_list_actions.bl_idname, icon="REMOVE", text=""
            ).action = "REMOVE"

            row = box.row(align=True)
            row.operator(
                CM_OT_import_cache.bl_idname,
                text="Load",
                icon="IMPORT",
            ).do_all = True
            row.operator(
                CM_OT_cache_show.bl_idname, text="Show", icon="HIDE_OFF"
            ).do_all = True

            row.operator(
                CM_OT_cache_hide.bl_idname, text="Hide", icon="HIDE_ON"
            ).do_all = True

            row.operator(
                CM_OT_cache_remove.bl_idname, text="Remove", icon="REMOVE"
            ).do_all = True

    def _get_version_text(self, context: bpy.types.Context) -> str:
        version_text = "Select Version"

        if context.scene.cm.cache_version:
            version_text = context.scene.cm.cache_version

        return version_text


class CM_PT_vi3d_advanced(bpy.types.Panel):
    bl_parent_id = "CM_PT_vi3d_cache"
    bl_category = "CacheManager"
    bl_label = "Advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        # Alembic export settings.
        box = layout.box()
        box.label(text="Alembic Export Settings", icon="MODIFIER")

        # Frame range.
        col = box.column(align=True)
        col.prop(context.scene.cm, "frame_handles_left")
        col.prop(context.scene.cm, "frame_handles_right")

        # Shutter.
        col = box.column(align=True)
        col.prop(context.scene.cm, "sh_open")
        col.prop(context.scene.cm, "sh_close")

        # Samples.
        col = box.column(align=True)
        col.prop(context.scene.cm, "xsamples")
        col.prop(context.scene.cm, "gsamples")


class CM_UL_collection_cache_list_export(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        coll = item.coll_ptr

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            # Item got deleted.
            if not coll:
                layout.label(text=f"{item.name} was deleted")
                return

            split = layout.split(factor=0.5, align=True)
            split.prop(
                coll,
                "name",
                text="",
                emboss=False,
                icon="OUTLINER_COLLECTION",
            )
            split = split.split(factor=0.75, align=True)
            split.label(text=f"/{propsdata.gen_cache_coll_filename(coll)}")
            split.operator(
                CM_OT_cache_export.bl_idname,
                text="",
                icon="EXPORT",
            ).index = index
            # Disable row if coll not valid.
            if not cache.is_valid_cache_coll(coll):
                split.enabled = False

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=layout.icon(coll))


class CM_UL_collection_cache_list_import(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        coll = item.coll_ptr

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            # Item got deleted.
            if not coll:
                layout.label(text=f"{item.name} was deleted")
                return

            split = layout.split(factor=0.4, align=True)
            split.prop(
                coll,
                "name",
                text="",
                emboss=False,
                icon="OUTLINER_COLLECTION",
            )
            split = split.split(factor=0.7, align=True)

            cachefile = coll.cm.cachefile
            op_text = "Select Cachefile"
            if cachefile:
                op_text = Path(cachefile).name

            split.operator(
                CM_OT_assign_cachefile.bl_idname, text=op_text, icon="DOWNARROW_HLT"
            ).index = index

            if not coll.cm.is_cache_loaded:
                split.operator(
                    CM_OT_import_cache.bl_idname,
                    text="",
                    icon="IMPORT",
                ).index = index
            else:
                split.operator(
                    CM_OT_cache_remove.bl_idname, text="", icon="REMOVE"
                ).index = index

            if coll.cm.is_cache_hidden:
                split.operator(
                    CM_OT_cache_show.bl_idname, text="", icon="HIDE_ON"
                ).index = index
            else:
                split.operator(
                    CM_OT_cache_hide.bl_idname, text="", icon="HIDE_OFF"
                ).index = index

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=layout.icon(item.coll_ptr))


# ---------REGISTER ----------.

classes = [
    CM_UL_collection_cache_list_export,
    CM_UL_collection_cache_list_import,
    CM_PT_vi3d_cache,
    CM_PT_vi3d_advanced,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
