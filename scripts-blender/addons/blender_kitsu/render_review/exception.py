# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later


class NoImageSequenceAvailableException(Exception):
    """
    Error raised when trying to gather image sequence in folder but no files are existent
    """
