# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

class ShotInvalidException(Exception):
    """
    Error raised when shot is not valid. For example has no self.id.
    """

    pass
