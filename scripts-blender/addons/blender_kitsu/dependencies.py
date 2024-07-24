
# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

def preload_modules() -> None:
    """Pre-load the datetime module from a wheel so that the API can find it."""
    import sys

    if "gazu" in sys.modules:
        return

    from . import wheels

    wheels.load_wheel_global("bidict", "bidict")
    wheels.load_wheel_global("engineio", "python_engineio")
    wheels.load_wheel_global("socketio", "python_socketio")
    wheels.load_wheel_global("gazu", "gazu")
