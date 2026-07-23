import bpy

from ..conftest import load_blend


def test_force_apply_mirror(context_ew):
    load_blend("easy_weight/test_force_apply_mirror.blend")

    suzanne = bpy.data.objects['Suzanne']
    suzanne.select_set(True)
    context_ew.view_layer.objects.active = suzanne

    assert suzanne.modifiers[0].type == 'MIRROR'

    assert bpy.ops.object.force_apply_mirror_modifier() == {'FINISHED'}

    assert suzanne.modifiers[0].type != 'MIRROR'
    mirrored_shape_key = suzanne.data.shape_keys.key_blocks.get('Ear.R')
    assert mirrored_shape_key

    context_ew.scene.frame_current = 10
    assert abs(mirrored_shape_key.value - 1.0) < 0.001

    assert mirrored_shape_key.vertex_group == 'Side.R'
    assert suzanne.vertex_groups.get('Side.R')
