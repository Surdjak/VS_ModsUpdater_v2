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
__version__ = "2.0.0-dev1"  # Don't forget to change EXPECTED_VERSION
__date__ = "2024-11-29"  # Last update


# config.py


# from global_cache import global_cache
import global_cache
import configparser
import os
import logging
import utils
from pathlib import Path
import datetime as dt
from rich import print
from rich.prompt import Prompt


# The target version after migration
EXPECTED_VERSION = "2.0.0-dev1"

# Constants for paths
APPLICATION_PATH = os.getcwd()
CONFIG_FILE = Path(APPLICATION_PATH).parent / Path('config.ini')
TEMP_PATH = Path(APPLICATION_PATH).parent / Path('temp')
LOGS_PATH = Path(APPLICATION_PATH).parent / Path('logs')
LANG_PATH = Path(APPLICATION_PATH).parent / Path('lang')

# Constants for supported languages
SUPPORTED_LANGUAGES = {
    "US": ["en", "English", '1'],
    "FR": ["fr", "Français", '2']
}
DEFAULT_LANGUAGE = "en_US"

# Constants for url
URL_MODS = 'https://mods.vintagestory.at'
URL_API = 'https://mods.vintagestory.at/api'
URL_SCRIPT = {
    "windows": 'https://mods.vintagestory.at/modsupdater#tab-files',
    "linux": 'https://mods.vintagestory.at/modsupdaterforlinux#tab-files'
}

# Default configuration
DEFAULT_CONFIG = {
    "ModsUpdater": {"version": __version__},
    "Logging": {"log_level": "INFO"},
    "Options": {"force_update": "false", "disable_mod_dev": "false", "auto_update": "true"},
    "Backup_Mods": {"backup_folder": "backup_mods", "max_backups": 3},
    "ModsPath": {"path": str(global_cache.MODS_PATHS[global_cache.SYSTEM])},
    "Language": {"language": DEFAULT_LANGUAGE},
    "Game_Version": {"version": ""},
    "Mod_Exclusion": {'mods': ""}
}


# Example function that checks the configuration version in the cache
def get_config_version_from_cache():
    try:
        return global_cache.global_cache.config_cache['ModsUpdater']['version']
    except KeyError:
        return None  # If the version is not present in the cache


def read_version_from_config_file():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)  # Lire le fichier de configuration
    return config.get('ModsUpdater', 'version', fallback=None)


def migrate_config_if_needed():
    # Check the current version of the configuration file
    current_version = get_config_version_from_cache()  # Retrieve the config version from the global cache

    # If the current version is None (cache doesn't exist), read directly from config.ini
    if current_version is None:
        current_version = read_version_from_config_file()  # Function to read the version from config.ini

    if current_version != EXPECTED_VERSION:
        # If the configuration version is outdated, initiate the migration
        print(f"Old configuration detected (v{current_version}). Migrating...")
        print("All the old settings have been preserved.")
        old_config = configparser.ConfigParser()
        old_config.read(CONFIG_FILE)  # Read the current configuration file
        migrate_config(old_config)  # Migrate the configuration to the new version


def migrate_config(old_config):
    # Create a new configparser for the migrated file
    new_config = configparser.ConfigParser()

    # Copy sections, options and values from the old file
    for section in old_config.sections():
        if section == "Mod_Exclusion":  # Special handling of the Mod_Exclusion section
            if "mods" in old_config[section]:
                raw_mods = old_config[section]["mods"]
                new_config[section] = {
                    "mods": ", ".join(mod.strip() for mod in raw_mods.split(","))
                }
        else:
            # Copy each section and its options
            new_config[section] = {key: old_config[section][key] for key in old_config[section]}

    # Add or modify default sections
    new_config["ModsUpdater"] = {"version": EXPECTED_VERSION}

    # Save the new configuration
    with open(CONFIG_FILE, "w") as configfile:
        new_config.write(configfile)

    print(f"Configuration migrated to v{EXPECTED_VERSION}")


def create_config(language, mod_folder, game_version, auto_update):
    """
    Create the config.ini file with default or user-specified values.
    """
    DEFAULT_CONFIG["Language"]["language"] = language[0]
    DEFAULT_CONFIG["ModsPath"]["path"] = mod_folder
    DEFAULT_CONFIG["Game_Version"]["version"] = game_version
    DEFAULT_CONFIG["Options"]["auto_update"] = 'True' if auto_update == "auto" else 'False'

    config = configparser.ConfigParser()
    for section, options in DEFAULT_CONFIG.items():
        config.add_section(section)
        for key, value in options.items():
            config.set(section, key, str(value))
    try:
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
            logging.info(f"Config.ini file created")
    except (FileNotFoundError, IOError, PermissionError) as e:
        logging.error(f"Failed to create config file: {e}")


def load_config():
    """
    Load configuration into the global cache.
    """
    # Check if the cache is already populated
    if global_cache.global_cache.config_cache:
        return global_cache.global_cache.config_cache

    # Check the existence of the configuration file
    if not CONFIG_FILE.exists():
        raise FileNotFoundError("config.ini file not found.")

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    # Populate the config_cache
    for section in config.sections():
        global_cache.global_cache.config_cache[section] = {
            key: value for key, value in config.items(section)
        }

    return global_cache.global_cache.config_cache


def config_exists():
    """
    Check if the config.ini file exists.
    """
    return CONFIG_FILE.exists()


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
    while True:
        game_version = Prompt.ask(
            'What version of the game are you using? (Format: major.minor.patch, e.g., 1.19.8 or leave blank to use the latest game version)',
            default=last_game_version
            )
        # If valid, complete and return the version
        if utils.is_valid_version(game_version):
            return utils.complete_version(game_version)
        else:
            # If the format is invalid, display an error message and ask for the version again.
            print(
                "[bold red]Error: Please provide a valid version in the format major.minor.patch (e.g., 1.2.3).[/bold red]")


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
        utils.setup_directories(LOGS_PATH)

        timestamp = dt.datetime.today().strftime("%Y%m%d%H%M%S")
        log_file = Path(LOGS_PATH) / f'log_{timestamp}.txt'

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
        log_level = global_cache.global_cache.config_cache.get("Logging", {}).get("log_level", "DEBUG").upper()

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
