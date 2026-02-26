import bpy

from ..conftest import load_blend


def test_asset_pipeline(context_ap):
    load_blend("asset_pipeline/assets/test_simple/test_asset-modeling.blend")
    bpy.ops.assetpipe.sync_pull()
    assert bpy.data.objects.get('GEO-Ear.L')
