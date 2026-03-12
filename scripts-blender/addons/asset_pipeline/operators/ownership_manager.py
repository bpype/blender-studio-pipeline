# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Collection, Context, Event, Operator, Panel, UILayout

from .. import constants
from ..merge import task_layer
from ..merge.task_layer import draw_task_layer_selection
from ..props import AssetTransferData
from ..ui import poll_valid_workfile


class ASSETPIPE_PT_ownership_manager(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Pipeline'
    bl_label = "Ownership Manager"

    @classmethod
    def poll(cls, context: Context):
        return poll_valid_workfile(context)

    def draw(self, context: Context) -> None:
        layout = self.layout
        asset_pipe = context.scene.asset_pipeline
        if not asset_pipe.is_asset_pipeline_file:
            layout.label(text="Open valid 'Asset Pipeline' file", icon="ERROR")
            return

        layout.prop(asset_pipe, 'ui_ownership_mode', expand=True)

        if asset_pipe.ui_ownership_mode == 'COLLECTION':
            if not context.collection:
                layout.label(text="Select a Collection in the Outliner.")
                return
            if context.collection not in set(asset_pipe.asset_collection.children_recursive):
                layout.prop(context.collection, 'name', text="", icon='OUTLINER_COLLECTION', emboss=False)
                layout.label(text="Active collection is not a Task Layer Collection.")
                return
            draw_collection_ownership(context, layout, context.collection)

        elif asset_pipe.ui_ownership_mode == 'OBJECT':
            obj = context.active_object
            if not obj:
                layout.label(text="Set an Active Object to Inspect", icon="OBJECT_DATA")
                return

            layout.operator("assetpipe.batch_ownership_change")

            transfer_data = obj.transfer_data_ownership
            col = layout.column()
            main_row = col.row()
            object_row = main_row.row(align=True)
            object_row.prop(obj, 'name', icon="OBJECT_DATA", text="", emboss=False)

            if obj.asset_id_surrender:
                object_row.operator("assetpipe.update_surrendered_object")

            draw_task_layer_selection(context, layout=object_row, id=obj)
            surrender_row = object_row.row()
            surrender_row.enabled = obj.asset_id_owner in asset_pipe.local_task_layers
            surrender_row.prop(obj, "asset_id_surrender", text="", icon="ORPHAN_DATA" if obj.asset_id_surrender else "HEART")

            object_row.operator("assetpipe.clear_ownership_data", text="", icon="TRASH")

            for coll in obj.users_collection:
                if coll in set(asset_pipe.asset_collection.children_recursive):
                    draw_collection_ownership(context, layout, coll)

            draw_all_data_ownership_of_obj(context, col, transfer_data)


class ASSETPIPE_OT_clear_ownership_data(Operator):
    bl_idname = "assetpipe.clear_ownership_data"
    bl_label = "Clear Ownership Data"
    bl_description = """Reset all ownership data on active object.\nAlt: Reset on all selected objects."""
    bl_options = {'REGISTER', 'UNDO'}

    affect_selected: BoolProperty(default=False, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context: Context) -> bool:
        if len(context.selected_objects) == 0:
            cls.poll_message_set("No Objects Selected")
            return False
        return True

    def invoke(self, context: Context, event: Event):
        if event.alt:
            self.affect_selected = True
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: Context):
        self.layout.alert = True
        self.layout.label(text="Clearing ownership data may lead to ownership conflicts.", icon='ERROR')

    def execute(self, context: Context):
        objs = context.selected_objects if self.affect_selected else [context.active_object]
        for obj in objs:
            obj.asset_id_owner = "NONE"
            obj.transfer_data_ownership.clear()
            self.report({'INFO'}, f"'{obj.name}' ownership data cleared ")
        return {'FINISHED'}


class ASSETPIPE_OT_batch_ownership_change(Operator):
    # TODO Update Operator Documentation
    bl_idname = "assetpipe.batch_ownership_change"
    bl_label = "Batch Set Ownership"
    bl_description = """Re-Assign Ownership in a batch operation"""
    bl_options = {'REGISTER', 'UNDO'}

    name_filter: StringProperty(
        name="Filter by Name",
        description="Filter Object or Transferable Data items by name",
        default="",
    )

    data_source: EnumProperty(
        name="Objects",
        items=(
            ('SELECT', "Selected", "Update Selected Objects Only"),
            ('ALL', "All", "Update All Objects"),
        ),
    )

    data_type: EnumProperty(
        name="Ownership Type",
        items=(
            (
                'OBJECT',
                "Object",
                "Update Owner of Objects",
            ),
            (
                'TRANSFER_DATA',
                "Transferable Data",
                "Update Owner of Transferable Data within Objects",
            ),
        ),
    )

    filter_owners: EnumProperty(
        name="Owner Filter",
        items=(
            ('LOCAL', "If Locally Owned", "Only data that is owned locally"),
            ('OWNED', "If Owned By Any",
             "Only data that already have assignment"),
            ('ALL', "No Filter",
             "Set Ownership on any data, even without an owner"),
        ),
    )

    avaliable_owners: EnumProperty(
        name="Avaliable Owners",
        items=(
            ('LOCAL', "Local Task Layers",
             "Only show local task layers as options"),
            (
                'ALL',
                "All Task Layers",
                "Show all task layers as options",
            ),
        ),
    )
    transfer_data_type: EnumProperty(
        name="Type Filter", items=constants.TRANSFER_DATA_TYPES_ENUM_ITEMS)
    owner_selection: StringProperty(name="Set Owner")

    def update_set_surrender(self, context):
        if self.set_surrender:
            self.claim_surrender = False

    set_surrender: BoolProperty(name="Set Surrender",
                                default=False,
                                update=update_set_surrender)

    def update_claim_surrender(self, context: Context):
        if self.claim_surrender:
            self.set_surrender = False

    claim_surrender: BoolProperty(name="Claim Surrender",
                                  default=False,
                                  update=update_claim_surrender)

    def _filter_by_name(self,
                        context: Context,
                        unfiltered_list: list[AssetTransferData] = []):
        if self.name_filter == "":
            return unfiltered_list
        return [
            item for item in unfiltered_list if self.name_filter in item.name
        ]

    def _get_transfer_data_to_update(self, context: Context):
        asset_pipe = context.scene.asset_pipeline
        objs = self._get_objects(context)
        transfer_data_items_to_update = []
        if self.data_type == "TRANSFER_DATA":
            for obj in objs:
                filtered_transfer_data = self._filter_by_name(
                    context, obj.transfer_data_ownership)
                for transfer_data_item in filtered_transfer_data:
                    if self.transfer_data_type != "NONE":
                        if transfer_data_item.type == self.transfer_data_type:
                            transfer_data_items_to_update.append(
                                transfer_data_item)
                    else:
                        transfer_data_items_to_update.append(
                            transfer_data_item)

        if self.claim_surrender:
            return [
                item for item in transfer_data_items_to_update
                if item.surrender
                and item.owner not in asset_pipe.get_local_task_layers()
            ]

        if self.filter_owners == "LOCAL":
            transfer_data_items_to_update = [
                item for item in transfer_data_items_to_update
                if item.owner in asset_pipe.get_local_task_layers()
            ]
        if self.set_surrender:
            return [
                item for item in transfer_data_items_to_update
                if not item.surrender
            ]

        return transfer_data_items_to_update

    def _get_objects(self, context: Context):
        asset_objs = context.scene.asset_pipeline.asset_collection.all_objects
        selected_asset_objs = [
            obj for obj in asset_objs if obj in context.selected_objects
        ]
        return asset_objs if self.data_source == "ALL" else selected_asset_objs

    def _get_filtered_objects(self, context: Context):
        asset_pipe = context.scene.asset_pipeline
        objs = self._get_objects(context)
        filtered_objs = self._filter_by_name(context, objs)
        if self.filter_owners == "LOCAL" and self.data_type == "OBJECT":
            filtered_objs = [
                item for item in filtered_objs
                if item.asset_id_owner in asset_pipe.get_local_task_layers()
            ]
        if self.filter_owners == "OWNED" and self.data_type == "OBJECT":
            filtered_objs = [
                item for item in filtered_objs if item.asset_id_owner != "NONE"
            ]

        if self.claim_surrender:
            claim_objs = self._get_objects(context)
            claim_filtered_objs = self._filter_by_name(context, claim_objs)
            return [
                item for item in claim_filtered_objs
                if item.asset_id_surrender and item.asset_id_owner not in
                asset_pipe.get_local_task_layers()
            ]

        if self.set_surrender:
            return [
                item for item in filtered_objs if not item.asset_id_surrender
                and item.asset_id_owner in asset_pipe.get_local_task_layers()
            ]
        return filtered_objs

    def _get_message(self, context: Context) -> str:
        objs = self._get_filtered_objects(context)
        if self.data_type == "OBJECT":
            data_type_name = "Object(s)"
            length = len(objs) if objs else 0
        else:
            transfer_data_items_to_update = self._get_transfer_data_to_update(
                context)
            data_type_name = "Transferable Data Item(s)"

            length = len(transfer_data_items_to_update
                         ) if transfer_data_items_to_update else 0
        if self.claim_surrender:
            action = "Claim Surrendered on"
        if self.set_surrender:
            action = "Set Surrender on"
        if not (self.claim_surrender or self.set_surrender):
            action = "Change Ownership on"
        return f"{action} {length} {data_type_name}"

    def invoke(self, context: Context, event: Event):
        self.filter_owners = 'LOCAL'
        self.avaliable_owners = 'LOCAL'
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context: Context):
        grey_out = True

        if self.set_surrender:
            grey_out = False
            self.filter_owners = "LOCAL"

        layout = self.layout
        layout.use_property_split = True
        layout.row(align=True).prop(self, "data_source", expand=True)

        layout.prop(self, "data_type", expand=True)
        filter_owner_row = layout.row()
        filter_owner_row.enabled = grey_out
        filter_owner_row.prop(self, "filter_owners")

        if self.data_type == "TRANSFER_DATA":
            layout.prop(self, "transfer_data_type")
        layout.prop(self, "name_filter", text="Name Filter")
        layout.separator()

        owner_row = layout.row(align=True)
        owner_row.enabled = grey_out

        task_layer.draw_task_layer_selection(
            context,
            layout=owner_row,
            id=self,
            data_owner_name='owner_selection',
            current_data_owner=self.owner_selection,
            show_all_task_layers=self.avaliable_owners == 'ALL',
            text="Set To",
        )

        owner_row.prop(self, "avaliable_owners", text="")

        row = layout.row(align=True)
        row.prop(self, 'set_surrender', toggle=True)
        row.prop(self, 'claim_surrender', toggle=True)

        bottom_label = layout.row()
        bottom_label_split = bottom_label.split(factor=0.4)
        bottom_label_split.row()
        bottom_label_split.label(text=self._get_message(context))

    def execute(self, context: Context):
        asset_pipe = context.scene.asset_pipeline
        objs = self._get_filtered_objects(context)
        message = self._get_message(context)

        # Only check for owner selection not surrendering data.
        if not self.set_surrender:
            if self.owner_selection == "":
                self.report(
                    {'ERROR'},
                    "Ownership 'Set To' must be set to a task layer",
                )
                return {'CANCELLED'}

        if self.data_type == "OBJECT":
            for obj in objs:
                if self.claim_surrender:
                    obj.asset_id_surrender = False
                if self.set_surrender:
                    obj.asset_id_surrender = True
                    continue
                obj.asset_id_owner = self.owner_selection
        else:
            transfer_data_items_to_update = self._get_transfer_data_to_update(
                context)

            for transfer_data_item_to_update in transfer_data_items_to_update:
                if self.claim_surrender:
                    transfer_data_item_to_update.surrender = False
                if self.set_surrender:
                    transfer_data_item_to_update.surrender = True
                    continue

                transfer_data_item_to_update.owner = self.owner_selection
                task_layer.get_transfer_data_owner(
                    asset_pipe, transfer_data_item_to_update.type)

        self.report({'INFO'}, message)
        return {'FINISHED'}


def draw_collection_ownership(context: Context, layout: UILayout, collection: Collection):
    asset_pipe = context.scene.asset_pipeline
    layout = layout.box()
    row = layout.row()
    row.label(text="Task Layer Collections:")
    for tl_coll in asset_pipe.asset_collection.children:
        if tl_coll.asset_id_owner == 'NONE':
            continue
        if collection is tl_coll or collection in set(tl_coll.children_recursive):
            split = layout.split()
            split.label(text=f"{tl_coll.name}: ", icon="OUTLINER_COLLECTION")
            draw_task_layer_selection(context, layout=split, id=tl_coll)


def draw_all_data_ownership_of_obj(
    context: Context,
    layout: UILayout,
    transfer_data: list[AssetTransferData],
) -> None:
    """Draw UI List of Transferable Data"""
    vertex_groups = []
    material_slots = []
    modifiers = []
    constraints = []
    custom_props = []
    shape_keys = []
    attributes = []
    parent = []

    for transfer_data_item in transfer_data:
        if transfer_data_item.type == constants.VERTEX_GROUP_KEY:
            vertex_groups.append(transfer_data_item)
        if transfer_data_item.type == constants.MODIFIER_KEY:
            modifiers.append(transfer_data_item)
        if transfer_data_item.type == constants.CONSTRAINT_KEY:
            constraints.append(transfer_data_item)
        if transfer_data_item.type == constants.CUSTOM_PROP_KEY:
            custom_props.append(transfer_data_item)
        if transfer_data_item.type == constants.SHAPE_KEY_KEY:
            shape_keys.append(transfer_data_item)
        if transfer_data_item.type == constants.ATTRIBUTE_KEY:
            attributes.append(transfer_data_item)
        if transfer_data_item.type == constants.PARENT_KEY:
            parent.append(transfer_data_item)
        if transfer_data_item.type == constants.MATERIAL_SLOT_KEY:
            material_slots.append(transfer_data_item)

    draw_ownership_data_single_type(context, layout, vertex_groups)
    draw_ownership_data_single_type(context, layout, modifiers)
    draw_ownership_data_single_type(context, layout, constraints)
    draw_ownership_data_single_type(context, layout, custom_props)
    draw_ownership_data_single_type(context, layout, shape_keys)
    draw_ownership_data_single_type(context, layout, attributes)
    draw_ownership_data_single_type(context, layout, parent)
    draw_ownership_data_single_type(context, layout, material_slots)


def draw_ownership_data_single_type(
    context: Context,
    layout: UILayout,
    transfer_data: list[AssetTransferData],
) -> None:
    """Draw UI Element for items of a Transferable Data type"""
    if transfer_data == []:
        return
    name, icon = constants.TRANSFER_DATA_TYPES[transfer_data[0].type]

    box = layout.box()
    header, panel = box.panel(transfer_data[0].obj_name + name, default_closed=True)
    header.label(text=name, icon=icon)
    if not panel:
        return

    box = panel.box()
    for transfer_data_item in transfer_data:
        draw_ownership_data_single_item(context, box, transfer_data_item)


def draw_ownership_data_single_item(
        context: Context,
        layout: UILayout,
        transfer_data_item: AssetTransferData,
    ):
    main_row = layout.row()
    main_row.label(text=f"{transfer_data_item.name}: ")

    if transfer_data_item.surrender:
        # Disable entire row if the item is surrendered
        main_row.operator("assetpipe.update_surrendered_transfer_data").transfer_data_item_name = (
            transfer_data_item.name
        )

    draw_task_layer_selection(
        context,
        layout=main_row.row(),
        id=transfer_data_item,
    )
    surrender_icon = "ORPHAN_DATA" if transfer_data_item.surrender else "HEART"
    surrender_row = main_row.row()
    asset_pipe = context.scene.asset_pipeline
    surrender_row.enabled = transfer_data_item.owner in asset_pipe.local_task_layers
    surrender_row.prop(transfer_data_item, "surrender", text="", icon=surrender_icon)


registry = [
    ASSETPIPE_PT_ownership_manager,
    ASSETPIPE_OT_clear_ownership_data,
    ASSETPIPE_OT_batch_ownership_change,
]
