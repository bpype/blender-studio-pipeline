# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .background_process import BackgroundProcess, Processes
from ..util import redraw_viewport


class BGP_SVN_Redraw_Viewport(BackgroundProcess):
    name = "Redraw Viewport"
    repeat_delay = 1
    debug = False
    tick_delay = 1
    needs_authentication = False

    def tick(self, context, prefs):
        redraw_viewport()

    def acquire_output(self, context, prefs):
        return ""

    def process_output(self, context, prefs):
        return ""


def register():
    Processes.start("Redraw Viewport")
