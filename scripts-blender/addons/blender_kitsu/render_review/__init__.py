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
# (c) 2021, Blender Foundation - Paul Golter

import bpy

from . import (
    util,
    props,
    opsdata,
    checksqe,
    ops,
    ui,
    draw,
)


_need_reload = "ops" in locals()


if _need_reload:
    import importlib

    util = importlib.reload(util)
    props = importlib.reload(props)
    opsdata = importlib.reload(opsdata)
    checksqe = importlib.reload(checksqe)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)
    draw = importlib.reload(draw)


def register():
    props.register()
    ops.register()
    ui.register()
    draw.register()


def unregister():
    draw.unregister()
    ui.unregister()
    ops.unregister()
    props.unregister()
