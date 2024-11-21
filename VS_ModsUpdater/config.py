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
__date__ = "2024-11-21"  # Last update

# config.py

import configparser
import os
import platform
import utils
from pathlib import Path
import datetime as dt
import logging
from rich import print
from rich.prompt import Prompt

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
XDG_CONFIG_HOME_PATH = os.getenv('XDG_CONFIG_HOME', os.path.expanduser(
    '~/.config'))  # Get the value of XDG_CONFIG_HOME environment variable
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
        "path": r"C:\Users\Jerome\AppData\Roaming\VintagestoryData\Mods"},
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

_cached_config = None


def create_config(language, mod_folder, game_version, auto_update):
    # Update value for lang and mods path
    DEFAULT_CONFIG["Language"]["language"] = language[0]
    DEFAULT_CONFIG["ModsPath"]["path"] = mod_folder
    DEFAULT_CONFIG["Game_Version"]["version"] = game_version
    auto_update = 'true' if auto_update == "auto" else 'false'
    DEFAULT_CONFIG["Options"]["auto_update"] = auto_update
    # Create the config.ini with default values
    config = configparser.ConfigParser()
    # Browse the dictionary and add sections and options
    for section, options in DEFAULT_CONFIG.items():
        config.add_section(section)  # Add section
        for key, value in options.items():
            config.set(section, key, str(value))  # Add options (Values converted to string)
    try:
        with open(CONFIG_FILE_PATH, 'w') as configfile:
            config.write(configfile)
    except (FileNotFoundError, IOError, PermissionError) as e:
        logging.error(f"Failed to create config file: {e}")


def load_config():
    """Load and return the parameters from config.ini with caching."""
    global _cached_config  # Using the global variable _cached_config

    # If the cache is already populated, do we return the configuration directly
    if _cached_config is not None:
        return _cached_config

    if not CONFIG_FILE_PATH.exists():
        raise FileNotFoundError("config.ini file not found.")

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_PATH)
    # We fetch config data
    version = config.get("ModsUpdater", "version")
    log_level = config.get("Logging", "log_level")
    force_update = config.get("Options", "force_update")
    disable_mod_dev = config.get("Options", "disable_mod_dev")
    auto_update = config.get("Options", "auto_update")
    mods_path = config.get("ModsPath", "path")
    language = config.get("Language", "language")
    game_version = config.get("Game_Version", "version")

    _cached_config = {
        "version": version,
        "log_level": log_level,
        "force_update": force_update,
        "disable_mod_dev": disable_mod_dev,
        "auto_update": auto_update,
        "mods_path": mods_path,
        "language": language,
        "game_version": game_version
    }
    return _cached_config


def config_exists():
    """Check if config.ini exists."""
    return CONFIG_FILE_PATH.exists()


def ask_mods_directory():
    """Ask the user to choose a folder for the mods."""
    mods_directory = Prompt.ask(
        'Enter the path to your mods folder. Leave blank for default path',
        default=MODS_PATHS[SYSTEM]
        )
    # Check if path exists
    if os.path.isdir(mods_directory):
        return mods_directory
    else:
        print(f"Error: {mods_directory} is not a valid directory.")
        return ask_mods_directory()  # Re-demander si le chemin est invalide


def ask_language_choice():
    """Ask the user to select a language at the first script launch."""
    print("[bold cyan]Please select your language:[/bold cyan]")

    # Display a message to prompt the user for language selection
    language_options = list(SUPPORTED_LANGUAGES.keys())
    for index, region in enumerate(language_options, start=1):
        language_name = SUPPORTED_LANGUAGES[region][1]
        print(f"    [bold]{index}.[/bold] {language_name} ({region})")

    # Use Prompt.ask to get the user's input
    choice_index = Prompt.ask(
        "Enter the number of your language choice",
        choices=[str(i) for i in range(1, len(language_options) + 1)],
        show_choices=False
    )

    # Convert the user's choice to the corresponding language key
    chosen_region = language_options[int(choice_index) - 1]
    language_code = SUPPORTED_LANGUAGES.get(chosen_region)[0]
    chosen_language = f'{language_code}_{chosen_region}'
    language_name = SUPPORTED_LANGUAGES[chosen_region][1]
    return chosen_language, language_name


def ask_game_version():
    """Ask the user to select the game version the first script launch."""
    last_game_version = utils.get_last_game_version()
    game_version = Prompt.ask(
        'What version of the game are you using? (Format: major.minor.patch, e.g., 1.19.8 or leave blank to use the latest game version)',
        default=last_game_version
        )
    # Check format
    result = utils.is_valid_version(game_version)

    if result:
        return game_version
    else:
        # If the format is invalid, display an error message and ask for the version again.
        print(
            "[bold red]Error: Please provide a valid version in the format major.minor.patch (e.g., 1.2.3).[/bold red]")
        return ask_game_version()  # Keep asking until a valid version is provided.


def ask_auto_update():
    """Ask the user if he wants to perform updates manually or automatically."""
    auto_update = Prompt.ask(
        'Do you want to perform updates manually or automatically ?)',
        choices=['auto', 'manual'],
        default='auto'
        )
    return auto_update


def configure_logging():
    utils.setup_directories(Path(LOGS_PATH))

    # logger
    timestamp = dt.datetime.today().strftime("%Y%m%d%H%M%S")
    log_file = Path(LOGS_PATH) / f'log_{timestamp}.txt'
    # Charge la configuration avant de configurer le logger
    # Récupère le niveau de log depuis la configuration
    # log_level = conf.get("Logging", "log_level").upper()
    log_level = 'DEBUG'
    # Configure logging based on the configuration
    # log_level = load_or_create_config().get("Logging", "log_level").upper()
    logging.basicConfig(
        filename=log_file,
        level=getattr(logging, log_level, logging.DEBUG),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


configure_logging()  # Load the logger

if __name__ == "__main__":  # For test
    pass
