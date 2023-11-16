
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation

import bpy


def better_purge(context, clear_coll_fake_users=True):
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
        do_local_ids=True, do_linked_ids=True, do_recursive=True)


better_purge()
bpy.ops.wm.quit_blender()
