import bpy
from bpy.types import Collection
from .transfer_data.transfer_functions.shape_keys import shape_key_set_active

class Perserve:
    def __init__(self, local_col: Collection) -> None:
        self._local_col = local_col
        self._action_dict: dict = {}
        self.generate_preserve_maps()

    def generate_preserve_maps(self) -> None:
        self._action_dict = self._get_action_map()
        self._active_index_dict = self._get_active_index_map()

    def _get_action_map(self):
        action_dict = {}
        for obj in self._local_col.all_objects:
            # Set action map for armatures only
            if obj.type != "ARMATURE":
                continue
            # Only set action map if obj has action assignment
            if not obj.animation_data or not obj.animation_data.action:
                continue

            # Store obj name as obj may removed during merge
            action = obj.animation_data.action
            action_dict[obj.name] = {'action': action, 'fake_user': action.use_fake_user}
            action.use_fake_user = True
        return action_dict

    def set_action_map(self):
        for obj_name, action_info in self._action_dict.items():
            obj = bpy.data.objects.get(obj_name)
            if not obj:
                continue
            action = action_info.get('action')
            if not obj.animation_data:
                obj.animation_data_create()
            obj.animation_data.action = action
            action.use_fake_user = action_info.get('fake_user')

    def _get_active_index_map(self):
        active_index = {}
        for obj in self._local_col.all_objects:
            indexes = {}

            if getattr(obj.data, "uv_layers", None) and getattr(obj.data.uv_layers, "active", None):
                indexes['uv_layer'] = obj.data.uv_layers.active.name

            if getattr(obj.vertex_groups, "active", None):
                indexes['vertex_group'] = obj.vertex_groups.active.name

            if getattr(obj.data, "color_attributes", None) and getattr(
                obj.data.color_attributes, "active", None
            ):
                indexes['color_attribute'] = obj.data.color_attributes.active_color_name

            if getattr(obj.data, "attributes", None) and getattr(
                obj.data.attributes, "active", None
            ):
                indexes['attribute'] = obj.data.attributes.active.name

            if getattr(obj.data, "shape_keys", None) and getattr(obj, "active_shape_key", None):
                indexes['shape_key'] = obj.active_shape_key.name

            active_index[obj.name] = indexes
        return active_index

    def set_active_index_map(self):
        for obj_name, indexes in self._active_index_dict.items():
            obj = bpy.data.objects.get(obj_name)
            if not obj:
                continue

            if indexes.get('uv_layer'):
                uv_layer = obj.data.uv_layers[indexes.get('uv_layer')]
                if uv_layer:
                    obj.data.uv_layers.active = uv_layer

            if indexes.get('vertex_group'):
                vertex_group = obj.vertex_groups.get(indexes.get('vertex_group'))
                if vertex_group:
                    obj.vertex_groups.active = vertex_group

            # Setting color_attribute active also sets attribute active, so attribute must always follow color_attribute
            if indexes.get('color_attribute'):
                color_attribute = obj.data.color_attributes.get(indexes.get('color_attribute'))
                for index, color_attribute in enumerate(obj.data.color_attributes):
                    if color_attribute.name == indexes.get('color_attribute'):
                        obj.data.color_attributes.active_color_index = index

            if indexes.get('attribute'):
                attribute = obj.data.attributes.get(indexes.get('attribute'))
                if attribute:
                    obj.data.attributes.active = attribute

            if indexes.get('shape_key'):
                shape_key = obj.data.shape_keys.key_blocks.get(indexes.get('shape_key'))
                if shape_key:
                    shape_key_set_active(obj, indexes.get('shape_key'))
