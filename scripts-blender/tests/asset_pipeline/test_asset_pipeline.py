import bpy
from bpy.types import Collection, LayerCollection, Object

from ..conftest import load_blend


def test_object_add_remove(context_ap):
    """In this test, we open the Modeling task layer's file, add and remove objects, then pull.
    Whether an object should be preserved or removed depends on its collection assignments,
    and owning task layer.
    """
    load_blend("asset_pipeline/assets/object_add_remove/obj_add_remove-modeling.blend")

    coll_modeling_sub = bpy.data.collections['test_asset-modeling_sub']
    coll_rigging_sub = bpy.data.collections['test_asset-rigging_sub']

    ### Add some objects which should survive pulling.
    # Adding an object without any ownership data, into the (correct) modeling task layer.
    good_cube = add_cube_in_collection(context_ap, coll_modeling_sub, name="New Cube")

    # Same thing, but we explicitly set owner to Modeling.
    # This should happen anyways early on in the Pull process, so doing it explicitly is optional.
    also_good_cube = add_cube_in_collection(context_ap, coll_modeling_sub, name="New Cube 2")
    also_good_cube.asset_id_owner = 'Modeling'

    # Let's also link both to the Rigging collection. They should get unlinked from there on pull.
    coll_rigging_sub.objects.link(good_cube)
    coll_rigging_sub.objects.link(also_good_cube)

    ################################
    ### Add some objects which should disappear on pull.
    # Adding an object owned by us, into the wrong task layer's collection.
    wrong_coll_cube = add_cube_in_collection(context_ap, coll_rigging_sub, name="Cube In Wrong Coll")
    wrong_coll_cube.asset_id_owner = 'Modeling'

    # Adding an object without any ownership data, into the (incorrect) rigging task layer.
    add_cube_in_collection(context_ap, coll_rigging_sub, name="Unowned In Rigging")

    # Adding an object owned by another task layer, in their collection. This would only survive if it also existed in the publish.
    rigging_cube = add_cube_in_collection(context_ap, coll_rigging_sub, name="Rigging Cube")
    rigging_cube.asset_id_owner = 'Rigging'

    # Adding an object which is owned by Rigging, into the modeling task layer.
    # This would only be expected to survive, if the same object is also in the rigging task layer's collection
    # in the publish, which is not the case. So, this object should disappear on pull.
    their_cube_in_our_coll = add_cube_in_collection(context_ap, coll_modeling_sub, name="Not Owned Cube")
    their_cube_in_our_coll.asset_id_owner = 'Rigging'

    ### Unlink an owned object from the owning task layer, and link it to another task layer's collection.
    # This should disappear on pull.
    left_ear = bpy.data.objects["GEO-Ear.L"]
    coll_modeling_sub.objects.unlink(left_ear)
    coll_rigging_sub.objects.link(left_ear)

    ### Delete an object which SHOULD return on pull (because it's not "ours")
    bpy.data.objects.remove(bpy.data.objects["RIG-test_asset"])

    ##################################
    asset_coll = bpy.data.collections['PR-test_asset']

    ### Add a collection in the asset's root, which should survive pull and get assigned our task layer as the owner.
    new_root_coll = bpy.data.collections.new("New Modeling Root Coll")
    asset_coll.children.link(new_root_coll)

    ### Add a collection in our task layer collection, which should survive pull.
    model_coll = bpy.data.collections['test_asset-modeling']
    new_sub_coll = bpy.data.collections.new("New Modeling Sub-coll")
    model_coll.children.link(new_sub_coll)

    new_sub_sub_coll = bpy.data.collections.new("New Modeling Sub-sub-coll")
    coll_modeling_sub.children.link(new_sub_sub_coll)

    ### Add a collection in someone else's task layer collection, which should vanish on pull.
    rigging_coll = bpy.data.collections['test_asset-rigging']
    new_invalid_coll = bpy.data.collections.new("Invalid Rigging Coll")
    rigging_coll.children.link(new_invalid_coll)

    new_invalid_sub_coll = bpy.data.collections.new("Invalid Rigging Sub-Coll")
    coll_rigging_sub.children.link(new_invalid_sub_coll)

    ###### PULL DATA FROM THE PUBLISH.
    bpy.ops.assetpipe.sync_pull()
    bpy.ops.wm.save_mainfile()

    # Assert objects that should still be here.
    for obname in ("GEO-Ear.R", "New Cube", "New Cube 2", "RIG-test_asset"):
        assert bpy.data.objects.get(obname), f"Object should still be here: {obname}"
    # Assert objects that should be deleted.
    for obname in ("Cube In Wrong Coll", "Unowned In Rigging", "Rigging Cube", "GEO-Ear.L", "Not Owned Cube"):
        assert obname not in bpy.data.objects, f"Object should be deleted: {obname}"

    # Assert objects that should still be here, but not linked to the Rigging collection.
    coll_rigging_sub = bpy.data.collections['test_asset-rigging_sub']
    for obname in ("New Cube", "New Cube 2"):
        assert bpy.data.objects.get(obname) not in set(coll_rigging_sub.objects), f"Object shouldn't be in Rigging collection: {obname}"

    # Assert collections that should still be here + their parents.
    surviving_colls = [
        ("New Modeling Sub-coll", "test_asset-modeling"),
        ("New Modeling Sub-sub-coll", "test_asset-modeling_sub"),
    ]
    for child_name, parent_name in surviving_colls:
        child_coll = bpy.data.collections.get(child_name)
        assert child_coll, f"Collection {child_coll} should still exist!"
        parent_coll = bpy.data.collections.get(parent_name)
        assert parent_coll, f"Collection {child_coll} should still exist!"
        assert child_coll in set(parent_coll.children), f"Collection {child_coll.name} should be a child of {parent_coll.name}"
    goner_colls = ["Invalid Rigging Coll", "Invalid Rigging Sub-Coll"]
    for coll_name in goner_colls:
        assert bpy.data.collections.get(coll_name) is None, f"Collection {coll_name} should've been removed by pull!"

def test_data_transfer_simple(context_ap):
    """This test adds some transferable data to objects and then pulls.
    Data transfer only occurs on pull when the data is added to objects owned by
    other task layers. So, in this case, we're adding rigging data to modeling-owned objects.
    """
    load_blend("asset_pipeline/assets/data_transfer_simple/data_transfer_simple-rigging.blend")

    ### Add some data to an object that is not owned by our task layer.
    ### This data should be initialized to be owned by us, and survive pulling.
    our_rig = bpy.data.objects['RIG-test']
    their_sphere = bpy.data.objects['GEO-Sphere']

    def add_driver(owner, data_path):
        drv = owner.driver_add(data_path).driver
        drv.expression = "var"
        var = drv.variables.new()
        var.type = 'TRANSFORMS'
        var.targets[0].id = our_rig
        var.targets[0].bone_target = 'ROOT-Sphere'
        var.targets[0].transform_type = 'SCALE_AVG'
    def check_driver(anim_data, data_path):
        fcurve = anim_data.drivers.find(data_path)
        assert fcurve, f"Driver not found: {data_path}"
        drv = fcurve.driver
        assert drv.expression == "var", f"Unexpected driver expression: {drv.expression}"
        assert len(drv.variables) == 1, f"{len(drv.variables)} variables instead of 1."
        var = drv.variables[0]
        assert var.name == "var", f"Unexpected driver variable name: {var.name}"
        assert var.type == 'TRANSFORMS', f"Unexpected driver variable type: {var.name} -> {var.type}"
        assert var.targets[0].id == our_rig, f"Unexpected driver variable target: {var.targets[0].id}"
        assert var.targets[0].bone_target == 'ROOT-Sphere', f"Unexpected driver variable bone target: {var.targets[0].bone_target}"
        return True

    # Add a vertex group.
    vg = their_sphere.vertex_groups.new(name="ROOT-Sphere")
    verts = [v.index for v in their_sphere.data.vertices]
    vg.add(verts, 1.0, 'REPLACE')

    # Add a modifier with driver.
    arm_mod = their_sphere.modifiers.new(name='Armature', type='ARMATURE')
    arm_mod.object = our_rig
    add_driver(arm_mod, "show_render")

    # Add shape key with driver.
    their_sphere.shape_key_add(name="Basis")
    test_sk = their_sphere.shape_key_add(name="SphereShapeKey")
    test_sk.data[0].co.x += 1.0
    add_driver(test_sk, "value")

    # Add custom property with driver.
    their_sphere['rigging_property'] = 123.45
    add_driver(their_sphere, '["rigging_property"]')

    # Re-parent the sphere, but don't change ownership of the parenting data (so this change will get lost on pull)
    their_sphere.parent = our_rig

    # Add a material, but don't change ownership of the material data (so this change will get lost on pull)
    new_mat = bpy.data.materials.new("SphereMaterial")
    their_sphere.data.materials.append(new_mat)

    ###### PULL DATA FROM THE PUBLISH.
    bpy.ops.assetpipe.sync_pull()
    bpy.ops.wm.save_mainfile()

    our_rig = bpy.data.objects['RIG-test']
    their_sphere = bpy.data.objects['GEO-Sphere']

    vg = their_sphere.vertex_groups.get('ROOT-Sphere')
    assert vg, "Vertex Group transfer failed."
    assert all((vg.weight(i)==1.0) for i in range(len(their_sphere.data.vertices))), "Vertex Group transfer failed."
    assert their_sphere.modifiers['RIG-Armature'].object == our_rig, "Modifier transfer failed."
    assert their_sphere.data.shape_keys.key_blocks['SphereShapeKey'].data[0].co.x == 1.0, "Shape Key transfer failed."
    assert their_sphere['rigging_property'] == 1.0, "Custom Property transfer failed."
    assert check_driver(their_sphere.animation_data, '["rigging_property"]'), "Custom property driver failed to transfer."
    assert check_driver(their_sphere.animation_data, 'modifiers["RIG-Armature"].show_render'), "Modifier driver failed to transfer."
    assert check_driver(their_sphere.data.shape_keys.animation_data, 'key_blocks["SphereShapeKey"].value'), "Shape key driver failed to transfer."

    assert their_sphere.parent is None, "Parenting transfer was supposed to fail but it didn't."
    assert len(their_sphere.data.materials) == 0, "Material transfer was supposed to fail but it didn't."

    # Add a material, this time also change ownership data so this change survives pull.
    new_mat = bpy.data.materials.new("SphereMaterial")
    their_sphere.data.materials.append(new_mat)
    their_sphere.transfer_data_ownership['All Materials'].owner = 'Rigging'
    their_sphere.transfer_data_ownership['All Materials'].surrender = False

    # Re-parent the sphere, but don't change ownership of the parenting data (so this change will get lost on pull)
    their_sphere.parent = our_rig
    their_sphere.transfer_data_ownership['Parent Relationship'].owner = 'Rigging'
    their_sphere.transfer_data_ownership['Parent Relationship'].surrender = False

    ###### PULL DATA FROM THE PUBLISH.
    bpy.ops.assetpipe.sync_pull()
    bpy.ops.wm.save_mainfile()

    our_rig = bpy.data.objects['RIG-test']
    their_sphere = bpy.data.objects['GEO-Sphere']

    assert their_sphere.parent is our_rig, "Parenting transfer was supposed to fail but it didn't."
    assert their_sphere.data.materials[0].name == 'SphereMaterial', "Material transfer was supposed to fail but it didn't."

#############################################


def add_cube_in_collection(context, collection: Collection, name="Cube") -> Object:
    set_active_collection(context, collection)
    bpy.ops.mesh.primitive_cube_add()
    cube = context.active_object
    cube.name = name
    return cube


def recursive_search_layer_collection(
    coll_name: str, layer_coll: LayerCollection
) -> LayerCollection | None:
    # Recursivly transverse layer_collection for a particular name
    # This is the only way to set active collection as of 14-04-2020.
    found = None
    if layer_coll.name == coll_name:
        return layer_coll
    for layer in layer_coll.children:
        found = recursive_search_layer_collection(coll_name, layer)
        if found:
            return found


def set_active_collection(context, collection: Collection):
    layer_coll = context.view_layer.layer_collection

    layer_collection = recursive_search_layer_collection(collection.name, layer_coll)
    assert layer_collection
    context.view_layer.active_layer_collection = layer_collection
