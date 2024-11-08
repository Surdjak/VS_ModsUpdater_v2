#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2024  Laerinok
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-08"  # Last update

# config.py

from pathlib import Path
import os
import platform
import datetime as dt
import configparser
import logging


# Constants for url
URL_MODS = 'https://mods.vintagestory.at'
URL_API = 'https://mods.vintagestory.at/api'
URL_SCRIPT = {
    "windows": 'https://mods.vintagestory.at/modsupdater#tab-files',
    "linux": 'https://mods.vintagestory.at/modsupdaterforlinux#tab-files'
}
# Constants for file paths
APPLICATION_PATH = os.getcwd()
HOME_PATH = Path.home()
CONFIG_FILE_PATH = Path(APPLICATION_PATH).parent / Path('config.ini')
TEMP_PATH = Path(APPLICATION_PATH).parent / Path('temp')
LOGS_PATH = Path(APPLICATION_PATH).parent / Path('logs')
LANG_PATH = Path(APPLICATION_PATH).parent / Path('lang')
XDG_CONFIG_HOME_PATH = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))  # Get the value of XDG_CONFIG_HOME environment variable
MODS_PATHS = {
    "Windows": Path(HOME_PATH,
                    r'AppData\Roaming\VintagestoryData\Mods'),
    "Linux": Path(XDG_CONFIG_HOME_PATH, 'VintagestoryData')
}
# Constant for os
SYSTEM = platform.system()

# Supported languages - Region:[language-abr, language, index]
SUPPORTED_LANGUAGES = {
    "US": ["en", "English", '1'],
    "FR": ["fr", "Français", '2']
}
DEFAULT_LANGUAGE = "en_US"

"""Create default config.ini"""
DEFAULT_CONFIG = {
    "ModsUpdater": {"version": __version__},
    "Logging": {"log_level": "DEBUG"},
    "Options": {
        "force_update": "false",
        "disable_mod_dev": "false",
        "auto_update": "true",
    },
    "ModsPath": {
        "path": r"C:\Users\Jerome\AppData\Roaming\VintagestoryData_modding\Mods"},
    "Language": {"language": "en_US"},
    "Game_Version": {"version": ""},
    "Mod_Exclusion": {
        'mod1': "",
        'mod2': "",
        'mod3': "",
        'mod4': "",
        'mod5': "",
    }
}


# Function to create or load the config.ini file
def load_or_create_config():
    config = configparser.ConfigParser()
    # Check if config.ini exists
    if not CONFIG_FILE_PATH.exists():
        # Create the config.ini with default values
        config.read_dict(DEFAULT_CONFIG)
        with open(CONFIG_FILE_PATH, 'w') as configfile:
            config.write(configfile)
    else:
        # Load the existing config.ini
        config.read(CONFIG_FILE_PATH)

    return config


conf = load_or_create_config()
# Configure logging with a timestamped filename
timestamp = dt.datetime.today().strftime("%Y%m%d%H%M%S")
LOG_FILE = Path(LOGS_PATH) / f'log_{timestamp}.txt'
# Configure logging based on the configuration
log_level = conf.get("Logging", "log_level").upper()
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, log_level, logging.DEBUG),
    format="%(asctime)s - %(levelname)s - %(message)s",
)


if __name__ == "__main__":  # For test
    pass
