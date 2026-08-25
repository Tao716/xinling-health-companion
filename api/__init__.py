#!/usr/bin/env python
# encoding: utf-8
"""
@author: Datawhale
@file: __init__.py
@time: 2025/7/21 14:27
@project: resonant-soul
@desc: 
"""
import logging

from api import settings
from api.db.init_data import init_web_data
from api.utils import file_utils, show_configs
from api.utils.log_utils import initRootLogger

_INITIALIZED = False


def initialize_app():
    """Initialize logging, database, optional model client, and seed data once."""
    global _INITIALIZED
    if _INITIALIZED:
        return

    initRootLogger("resonant-soul")
    logging.info(r"""
______                                  _     _____             _ 
| ___ \                                | |   /  ___|           | |
| |_/ /___  ___  ___  _ __   __ _ _ __ | |_  \ `--.  ___  _   _| |
|    // _ \/ __|/ _ \| '_ \ / _` | '_ \| __|  `--. \/ _ \| | | | |
| |\ \  __/\__ \ (_) | | | | (_| | | | | |_  /\__/ / (_) | |_| | |
\_| \_\___||___/\___/|_| |_|\__,_|_| |_|\__| \____/ \___/ \__,_|_|
                                                                  
""")
    logging.info(
        f'project base: {file_utils.get_project_base_directory()}'
    )
    show_configs()
    settings.init_settings()
    init_web_data()
    _INITIALIZED = True
