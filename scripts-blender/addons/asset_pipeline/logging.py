# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from . import constants
from .utils import get_addon_prefs


def get_logger(name="asset_pipeline"):
    logger = logging.getLogger(name)
    addon_prefs = get_addon_prefs()
    logging_level = int(addon_prefs.logger_level)
    # Return logger if it has already been setup
    if len(logger.handlers) > 0:
        return logger

    # create console handler and set level to debug
    logger.setLevel(logging_level)
    ch = logging.StreamHandler()
    ch.setLevel(logging_level)

    # create formatter
    formatter = logging.Formatter('%(levelname)s-%(name)s: %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    return logger


PROFILE_KEYS = {
    "IMPORT": "To import Collection & add suffixes",
    "MAPPING": "To create Asset Mapping",
    "TRANSFER_DATA": "To apply all Transferable Data",
    "OBJECTS": "To remap all Obejcts",
    "INDEXES": "To restore Active Indexes on all Objects",
    "COLLECTIONS": "To remap all Collections",
    "SHARED_IDS": "To remap all Shared IDs",
    "MERGE": "To complete entire merge process",
    "TOTAL": "Total time to sync this direction",
}

TD_KEYS = [type for type in constants.TRANSFER_DATA_TYPES]

INFO_KEYS = ["TOTAL"]  # Profile Keys to print in the logger's info mode

_profiler_instance = None


def get_profiler():
    global _profiler_instance
    if not _profiler_instance:
        _profiler_instance = Profiler()
    return _profiler_instance


class Profiler:

    def __init__(self) -> None:
        self.pull_profiles = {}
        self.push_profiles = {}
        self._logger = get_logger()

    def add(self, elapsed_time: int, key: str):
        if self._is_push:
            profiles = self.push_profiles
        else:  # is pull
            profiles = self.pull_profiles

        if key not in profiles:
            profiles[key] = elapsed_time
        else:
            profiles[key] += elapsed_time

    def log_all(self):
        self.log_profiles("PULL", self.pull_profiles)
        self.log_profiles("PUSH", self.push_profiles)

    def log_profiles(self, direction: str, profiles: dict):
        if profiles == {}:
            return
        for key, value in profiles.items():
            seconds = self.get_non_scientific_number(value)
            # Special case for transfer data keys
            if key in TD_KEYS:
                name = constants.TRANSFER_DATA_TYPES[key][0]
                self._logger.debug(
                    f"{direction} TD: {name.upper()} - {seconds} seconds to transfer {name} data for all objects"
                )
                continue
            msg = f"{direction} {key} - {seconds} seconds {PROFILE_KEYS[key]}"
            if key in INFO_KEYS:
                self._logger.info(msg)
            else:
                self._logger.debug(msg)

    def get_non_scientific_number(self, x: float):
        float_str = f'{x:.64f}'.rstrip('0')

        significant_digits = 0
        for index, c in enumerate(float_str):
            if significant_digits == 3:
                return float_str[:index:]

            if c != "0" and c != ".":
                significant_digits += 1

    def reset(self):
        self.pull_profiles = {}
        self._is_push = False
        self._logger = get_logger()

    def set_push(self, is_push=True):
        self._is_push = is_push
