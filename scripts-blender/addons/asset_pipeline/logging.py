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

import logging
from typing import List, Tuple
from . import prefs


def get_logger(name="asset_pipeline"):
    logger = logging.getLogger(name)
    addon_prefs = prefs.get_addon_prefs()
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
