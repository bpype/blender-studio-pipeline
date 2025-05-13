# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging


class LoggerFactory:

    """
    Utility class to streamline logger creation
    """

    @staticmethod
    def getLogger(name=__name__):
        logger = logging.getLogger(name)
        return logger
