# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy


def better_purge(clear_coll_fake_users=True):
    """Call Blender's purge function, but first Python-override all library IDs'
    use_fake_user to False.
    Otherwise, linked IDs essentially do not get purged properly.

    Also set all Collections' use_fake_user to False, so unused collections
    aren't kept in the file.
    """

    if clear_coll_fake_users:
        for coll in bpy.data.collections:
            coll.use_fake_user = False

    id_list = list(bpy.data.user_map().keys())
    for id in id_list:
        if id.library:
            id.use_fake_user = False

    bpy.ops.outliner.orphans_purge(
        do_local_ids=True, do_linked_ids=True, do_recursive=True
    )


better_purge()
bpy.ops.wm.quit_blender()
