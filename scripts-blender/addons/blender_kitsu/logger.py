# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from typing import List, Tuple


class LoggerFactory:

    """
    Utility class to streamline logger creation
    """

    @staticmethod
    def getLogger(name="blender-kitsu"):
        name = name
        logger = logging.getLogger(name)
        return logger


logger = LoggerFactory.getLogger(__name__)


class LoggerLevelManager:
    logger_levels: List[Tuple[logging.Logger, int]] = []

    @classmethod
    def configure_levels(cls):
        cls.logger_levels = []
        for key in logging.Logger.manager.loggerDict:
            if key.startswith("urllib3"):
                # Save logger and value.
                log = logging.getLogger(key)
                cls.logger_levels.append((log, logger.level))

                log.setLevel(logging.CRITICAL)

        # Set root logger level.
        logging.getLogger().setLevel(logging.INFO)
        logger.info("Configured logging Levels")

    @classmethod
    def restore_levels(cls):
        for logger, level in cls.logger_levels:
            logger.setLevel(level)
        logger.info("Restored logging Levels")
