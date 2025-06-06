# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

class NoImageStripAvailableException(Exception):
    """
    Error raised when trying to gather image sequence in folder but no files are existent
    """
