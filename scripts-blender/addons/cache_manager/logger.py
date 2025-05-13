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
        name = name
        logger = logging.getLogger(name)
        return logger


logger = LoggerFactory.getLogger(__name__)

def gen_processing_string(item: str) -> str:
    return f"---Processing {item}".ljust(50, "-")


def log_new_lines(multiplier: int) -> None:
    print("\n" * multiplier)
