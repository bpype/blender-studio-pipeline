from blender_kitsu.shot_builder.asset import Asset


class ProductionAsset(Asset):
    path = "{production.path}/lib/{asset.asset_type}/{asset.code}/{asset.code}.blend"  # Path to most assets
    color_tag = "NONE"


# Categories
class Character(ProductionAsset):
    asset_type = "char"
    collection = "CH-{asset.code}"  # Prefix for characters


class Prop(ProductionAsset):
    asset_type = "props"
    collection = "PR-{asset.code}"  # Prefix for props


# Assets
class MyCharacter(Character):
    name = "My Character"  # Name on Kitsu Server
    code = "mycharacter"  # Name of Collection without prefix (e.g. CH-mycharacter)
    path = "{production.path}/lib/{asset.asset_type}/mycharacter/publish/mycharacter.v001.blend"  # This asset has a custom path
    color_tag = "COLOR_01"


class MyProp(Prop):
    name = "MyProp"
    code = "myprop"
