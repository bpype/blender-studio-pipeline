# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from typing import Dict, Set
from .naming import (
    merge_get_target_name,
    task_layer_prefix_basename_get,
)
from .util import get_storage_of_id
from .shared_ids import get_shared_ids
from .. import constants, logging


class AssetTransferMapping:
    """
    The AssetTranfserMapping class represents a mapping between a source and a target.
    It contains an object mapping which connects each source object with a target
    object as well as a collection mapping.
    The mapping process relies heavily on suffixes, which is why we use
    MergeCollections as input that store a suffix.

    Instances of this class will be pased TaskLayer data transfer function so Users
    can easily write their merge instructions.
    """

    def __init__(
        self,
        local_coll: bpy.types.Collection,
        external_coll: bpy.types.Collection,
        local_tls: Set[str],
    ):
        self._local_top_col = local_coll
        self._external_col = external_coll
        self._local_tls = local_tls

        self.external_col_to_remove: Set[bpy.types.Object] = set()
        self.external_col_to_add: Set[bpy.types.Object] = set()
        self.external_obj_to_add: Set[bpy.types.Object] = set()
        self.surrendered_obj_to_remove: Set[bpy.types.Object] = set()
        self._no_match_source_objs: Set[bpy.types.Object] = set()

        self._no_match_source_colls: Set[bpy.types.Object] = set()
        self._no_match_target_colls: Set[bpy.types.Object] = set()

        self.conflict_ids: list[bpy.types.ID] = []
        self.conflict_transfer_data = []  # Item of bpy.types.CollectionProperty
        self.transfer_data_map: Dict[bpy.types.Collection, bpy.types.Collection] = {}

        self.logger = logging.get_logger()

        self.generate_mapping()

    def generate_mapping(self) -> None:
        self.object_map = self._gen_object_map()
        self.collection_map = self._gen_collection_map()
        self.shared_id_map = self._gen_shared_id_map()
        self._gen_transfer_data_map()
        self.index_map = self._gen_active_index_map()

    def _get_external_object(self, local_obj):
        external_obj_name = merge_get_target_name(
            local_obj.name,
        )
        external_obj = self._external_col.all_objects.get(external_obj_name)
        if not external_obj:
            self.logger.debug(f"Failed to find match obj {external_obj_name} for {local_obj.name}")
            self._no_match_source_objs.add(local_obj)
            return
        return external_obj

    def _check_id_conflict(self, external_id, local_id):
        if local_id.asset_id_owner not in self._local_tls:
            # If the local ID was not owned by any task layer of the current file 
            # in the first place, there cannot be a conflict.
            return
        if external_id.asset_id_owner != local_id.asset_id_owner and (
            local_id.asset_id_surrender == external_id.asset_id_surrender
        ):
            self.conflict_ids.append(local_id)

    def _gen_object_map(self) -> Dict[bpy.types.Object, bpy.types.Object]:
        """
        Tries to link all objects in source collection to an object in
        target collection. Uses suffixes to match them up.
        """
        object_map: Dict[bpy.types.Object, bpy.types.Object] = {}
        for local_obj in self._local_top_col.all_objects:
            # Skip items with no owner
            if local_obj.asset_id_owner == "NONE":
                continue
            if local_obj.library:
                continue
            external_obj = self._get_external_object(local_obj)
            if not external_obj:
                self.logger.debug(f"Couldn't find external obj for {local_obj}")
                continue
            self._check_id_conflict(external_obj, local_obj)
            # IF ITEM IS OWNED BY LOCAL TASK LAYERS

            if (
                external_obj.asset_id_surrender
                and not local_obj.asset_id_surrender
                and local_obj.asset_id_owner != external_obj.asset_id_owner
            ):
                self.logger.debug(f"Skipping {external_obj} is surrendered")
                object_map[external_obj] = local_obj
                continue

            if (
                local_obj.asset_id_surrender
                and not external_obj.asset_id_surrender
                and local_obj.asset_id_owner != external_obj.asset_id_owner
            ):
                self.logger.debug(f"Skipping {local_obj} is surrendered")
                object_map[local_obj] = external_obj
                continue

            if local_obj.asset_id_owner in self._local_tls:
                object_map[external_obj] = local_obj
            # IF ITEM IS NOT OWNED BY LOCAL TASK LAYERS
            else:
                object_map[local_obj] = external_obj

        # Find new objects to add to local_col
        for external_obj in self._external_col.all_objects:
            if external_obj.library:
                continue
            local_col_objs = self._local_top_col.all_objects
            obj = local_col_objs.get(merge_get_target_name(external_obj.name))
            if not obj and external_obj.asset_id_owner not in self._local_tls:
                self.external_obj_to_add.add(external_obj)
        return object_map

    def _gen_collection_map(self) -> Dict[bpy.types.Collection, bpy.types.Collection]:
        """
        Tries to link all source collections to a target collection.
        Uses suffixes to match them up.
        """
        coll_map: Dict[bpy.types.Collection, bpy.types.Collection] = {}

        for local_task_layer_col in self._local_top_col.children:
            if local_task_layer_col.asset_id_owner not in self._local_tls:
                # Replace source object suffix with target suffix to get target object.
                external_col_name = merge_get_target_name(local_task_layer_col.name)
                local_col = bpy.data.collections.get(external_col_name)
                if local_col:
                    coll_map[local_task_layer_col] = local_col
                else:
                    self.logger.debug(
                        f"Failed to find match collection {local_task_layer_col.name} for {external_col_name}"
                    )
                    self._no_match_source_colls.add(local_task_layer_col)

        external_top_col_name = merge_get_target_name(self._local_top_col.name)
        external_top_col = bpy.data.collections.get(external_top_col_name)

        # TODO Refactor
        for external_col in external_top_col.children:
            local_col_name = merge_get_target_name(external_col.name)
            local_col = bpy.data.collections.get(local_col_name)
            if not local_col and external_col.asset_id_owner not in self._local_tls:
                self.external_col_to_add.add(external_col)

        for local_col in self._local_top_col.children:
            external_col_name = merge_get_target_name(local_col.name)
            external_col = bpy.data.collections.get(external_col_name)
            if not external_col and local_col.asset_id_owner not in self._local_tls:
                self.external_col_to_remove.add(local_col)

        all_tgt_colls = set(self._external_col.children_recursive)
        all_tgt_colls.add(self._external_col)
        match_target_colls = set([coll for coll in coll_map.values()])
        self._no_match_target_colls = all_tgt_colls - match_target_colls

        return coll_map

    def _get_transfer_data_dict(self, transfer_data_item):
        return {
            'name': transfer_data_item.name,
            "owner": transfer_data_item.owner,
            "surrender": transfer_data_item.surrender,
        }

    def _transfer_data_pair_not_local(self, td_1, td_2):
        # Returns true if neither owners are local to current file
        if td_1.owner not in self._local_tls and td_2.owner not in self._local_tls:
            return True

    def _transfer_data_pair_local(self, td_1, td_2):
        # Returns true both owners are local to current file
        if td_1.owner in self._local_tls and td_2.owner in self._local_tls:
            return True

    def _transfer_data_check_conflict(self, obj, transfer_data_item):
        matching_transfer_data_item = self._transfer_data_get_matching(transfer_data_item)
        if matching_transfer_data_item is None:
            return
        if self._transfer_data_pair_not_local(matching_transfer_data_item, transfer_data_item):
            return
        if matching_transfer_data_item.owner != transfer_data_item.owner and not (
            matching_transfer_data_item.surrender or transfer_data_item.surrender
        ):
            # Skip conflict checker if both owners are local to current file
            if self._transfer_data_pair_local(matching_transfer_data_item, transfer_data_item):
                return
            self.conflict_transfer_data.append(transfer_data_item)
            self.logger.critical(f"Transfer Data Conflict for {transfer_data_item.name}")
            return True

    def _transfer_data_get_matching(self, transfer_data_item):
        obj = transfer_data_item.id_data
        other_obj = bpy.data.objects.get(merge_get_target_name(obj.name))
        # Find Related Transferable Data Item on Target/Source Object
        for other_obj_transfer_data_item in other_obj.transfer_data_ownership:
            if other_obj_transfer_data_item.type == transfer_data_item.type and (
                task_layer_prefix_basename_get(other_obj_transfer_data_item.name)
                == task_layer_prefix_basename_get(transfer_data_item.name)
            ):
                return other_obj_transfer_data_item
        return None

    def _transfer_data_is_surrendered(self, transfer_data_item):
        matching_td = self._transfer_data_get_matching(transfer_data_item)
        if matching_td:
            if (
                transfer_data_item.surrender
                and not matching_td.surrender
                and transfer_data_item.owner != matching_td.owner
            ):
                return True
        return False

    def _transfer_data_map_item_add(self, source_obj, target_obj, transfer_data_item):
        """Adds item to Transfer Data Map"""
        if self._transfer_data_is_surrendered(transfer_data_item):
            return
        td_type_key = transfer_data_item.type
        transfer_data_dict = self._get_transfer_data_dict(transfer_data_item)

        if not source_obj in self.transfer_data_map:
            self.transfer_data_map[source_obj] = {
                "target_obj": target_obj,
                "td_types": {td_type_key: [transfer_data_dict]},
            }
            return

        if not td_type_key in self.transfer_data_map[source_obj]["td_types"]:
            self.transfer_data_map[source_obj]["td_types"][td_type_key] = [transfer_data_dict]
            return
        else:
            self.transfer_data_map[source_obj]["td_types"][td_type_key].append(transfer_data_dict)

    def _transfer_data_map_item(self, source_obj, target_obj, transfer_data_item):
        """Verifies if Transfer Data Item is valid/can be mapped"""

        # If item is locally owned and is part of local file
        if transfer_data_item.owner in self._local_tls and source_obj.name.endswith(
            constants.LOCAL_SUFFIX
        ):
            self._transfer_data_map_item_add(source_obj, target_obj, transfer_data_item)

        # If item is externally owned and is not part of local file
        if (
            transfer_data_item.owner not in self._local_tls
            and transfer_data_item.owner != "NONE"
            and source_obj.name.endswith(constants.EXTERNAL_SUFFIX)
        ):
            self._transfer_data_map_item_add(source_obj, target_obj, transfer_data_item)

    def _gen_transfer_data_map(self):
        # Generate Mapping for Transfer Data Items
        for objs in self.object_map.items():
            _, target_obj = objs
            for obj in objs:
                # Must execute for both objs in map (so we map external and local TD)
                # Must include maps even if obj==target_obj to preserve exisiting local TD entry
                for transfer_data_item in obj.transfer_data_ownership:
                    if self._transfer_data_check_conflict(obj, transfer_data_item):
                        continue
                    self._transfer_data_map_item(obj, target_obj, transfer_data_item)
        return self.transfer_data_map

    def _gen_active_index_map(self):
        # Generate a Map of Indexes that need to be set post merge
        # Stores active_uv & active_color_attribute
        index_map = {}

        for source_obj in self.transfer_data_map:
            target_obj = self.transfer_data_map[source_obj]["target_obj"]
            td_types = self.transfer_data_map[source_obj]["td_types"]
            for td_type_key, _ in td_types.items():
                if td_type_key != constants.MATERIAL_SLOT_KEY:
                    continue
                if source_obj.type != 'MESH':
                    continue

                active_uv_name = (
                    source_obj.data.uv_layers.active.name
                    if source_obj.data.uv_layers.active
                    else ''
                )
                active_color_attribute_name = source_obj.data.color_attributes.active_color_name
                index_map[source_obj] = {
                    'active_uv_name': active_uv_name,
                    'active_color_attribute_name': active_color_attribute_name,
                    'target_obj': target_obj,
                }

        return index_map

    def _gen_shared_id_map(self):
        shared_id_map: Dict[bpy.types.ID, bpy.types.ID] = {}
        for local_id in get_shared_ids(self._local_top_col):
            external_id_name = merge_get_target_name(local_id.name)
            id_storage = get_storage_of_id(local_id)
            external_id = id_storage.get(external_id_name)
            if not external_id:
                continue
            self._check_id_conflict(external_id, local_id)
            if local_id.asset_id_owner in self._local_tls and local_id.asset_id_owner != "NONE":
                if external_id:
                    shared_id_map[external_id] = local_id
            else:
                if external_id:
                    shared_id_map[local_id] = external_id

        return shared_id_map
