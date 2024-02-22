# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
import contextlib


def main():
    if len(bpy.data.libraries) == 0:
        return

    for lib in bpy.data.libraries:
        lib.reload()

    with override_save_version():
        bpy.ops.wm.save_mainfile()
        print(f"Reloaded & Saved file: '{bpy.data.filepath}'")
        bpy.ops.wm.quit_blender()


@contextlib.contextmanager
def override_save_version():
    """Overrides the save version settings"""
    save_version = bpy.context.preferences.filepaths.save_version

    try:
        bpy.context.preferences.filepaths.save_version = 0
        yield

    finally:
        bpy.context.preferences.filepaths.save_version = save_version


if __name__ == "__main__":
    main()
