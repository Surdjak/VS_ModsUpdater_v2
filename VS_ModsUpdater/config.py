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

"""
# Manage configuration using a global cache.
"""


__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-22"  # Last update


# config.py


import global_cache
import configparser
import os
import platform
import logging
import utils
from pathlib import Path
import datetime as dt
from rich import print
from rich.prompt import Prompt


# Constants for supported languages
SUPPORTED_LANGUAGES = {
    "US": ["en", "English", '1'],
    "FR": ["fr", "Français", '2']
}
DEFAULT_LANGUAGE = "en_US"

# Default configuration
DEFAULT_CONFIG = {
    "ModsUpdater": {"version": __version__},
    "Logging": {"log_level": "INFO"},
    "Options": {"force_update": "false", "disable_mod_dev": "false", "auto_update": "true"},
    "Backup_Mods": {"backup_folder": "backup_mods", "max_backups":3},
    "ModsPath": {"path": str(global_cache.MODS_PATHS[platform.system()])},
    "Language": {"language": DEFAULT_LANGUAGE},
    "Game_Version": {"version": ""},
    "Mod_Exclusion": {'mod1': "", 'mod2': "", 'mod3': "", 'mod4': "", 'mod5': ""}
}


def create_config(language, mod_folder, game_version, auto_update):
    """
    Create the config.ini file with default or user-specified values.
    """
    DEFAULT_CONFIG["Language"]["language"] = language[0]
    DEFAULT_CONFIG["ModsPath"]["path"] = mod_folder
    DEFAULT_CONFIG["Game_Version"]["version"] = game_version
    DEFAULT_CONFIG["Options"]["auto_update"] = 'true' if auto_update == "auto" else 'false'

    config = configparser.ConfigParser()
    for section, options in DEFAULT_CONFIG.items():
        config.add_section(section)
        for key, value in options.items():
            config.set(section, key, str(value))
    try:
        with open(global_cache.CONFIG_FILE_PATH, 'w') as configfile:
            config.write(configfile)
            logging.info(f"Config.ini file created")
    except (FileNotFoundError, IOError, PermissionError) as e:
        logging.error(f"Failed to create config file: {e}")


def load_config():
    """
    Load and cache the configuration from config.ini.
    """
    if global_cache.config_cache:
        return global_cache.config_cache

    if not global_cache.CONFIG_FILE_PATH.exists():
        raise FileNotFoundError("config.ini file not found.")

    config = configparser.ConfigParser()
    config.read(global_cache.CONFIG_FILE_PATH)
    global_cache.config_cache.update({
        "ModsUpdater": {"version": config.get("ModsUpdater", "version")},
        "Logging": {"log_level": config.get("Logging", "log_level")},
        "Options": {
            "force_update": config.get("Options", "force_update"),
            "disable_mod_dev": config.get("Options", "disable_mod_dev"),
            "auto_update": config.get("Options", "auto_update")
        },
        "Backup_Mods": {
            "backup_folder": config.get("Backup_Mods", "backup_folder"),
            "max_backups": config.get("Backup_Mods", "max_backups"),
        },
        "ModsPath": {"path": config.get("ModsPath", "path")},
        "Language": {"language": config.get("Language", "language")},
        "Game_Version": {"version": config.get("Game_Version", "version")},
        "Mod_Exclusion": {
            'mod1': config.get("Mod_Exclusion", "mod1"),
            'mod2': config.get("Mod_Exclusion", "mod2"),
            'mod3': config.get("Mod_Exclusion", "mod3"),
            'mod4': config.get("Mod_Exclusion", "mod4"),
            'mod5': config.get("Mod_Exclusion", "mod5")
        }
    })
    return global_cache.config_cache


def reload_config():
    """
    Clear the configuration cache and reload it.
    """
    global_cache.config_cache.clear()
    return load_config()


def config_exists():
    """
    Check if the config.ini file exists.
    """
    return global_cache.CONFIG_FILE_PATH.exists()


def ask_mods_directory():
    """Ask the user to choose a folder for the mods."""
    mods_directory = Prompt.ask(
        'Enter the path to your mods folder. Leave blank for default path',
        default=global_cache.MODS_PATHS[global_cache.SYSTEM]
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
        "Enter the number of your language choice (default: english)",
        choices=[str(i) for i in range(1, len(language_options) + 1)],
        show_choices=False,
        default=1
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
    # Check if a FileHandler is already present
    if not any(isinstance(handler, logging.FileHandler) for handler in logging.getLogger().handlers):
        # Remove existing handlers, if necessary.
        if logging.getLogger().hasHandlers():
            logging.getLogger().handlers.clear()

        # Ensure that the directories exist before configuring the logging.
        utils.setup_directories(global_cache.LOGS_PATH)

        timestamp = dt.datetime.today().strftime("%Y%m%d%H%M%S")
        log_file = Path(global_cache.LOGS_PATH) / f'log_{timestamp}.txt'

        # print(f"[bold cyan]Log file will be created at:[/bold cyan] {log_file}")  # test

        # Create a handler for the file.
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # On met par défaut à DEBUG, mais on mettra à jour après

        # Create a log format.
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Add the handler to the logger.
        logging.getLogger().addHandler(file_handler)

        # Retrieve the log level from the configuration and apply it.
        log_level = global_cache.config_cache.get("Logging", {}).get("log_level", "DEBUG").upper()

        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if log_level not in valid_log_levels:
            logging.warning(f"Invalid log level '{log_level}' in configuration. Defaulting to 'DEBUG'.")
            log_level = "DEBUG"

        # Apply the log level.
        logging.getLogger().setLevel(getattr(logging, log_level, logging.DEBUG))

        # print(f"[bold green]Logging configured successfully with '{log_level}' level and custom file handler![/bold green]")  # test

    else:
        # print(f"[bold yellow]FileHandler already present, skipping reconfiguration[/bold yellow]") # test
        pass  # test


if __name__ == "__main__":
    pass
