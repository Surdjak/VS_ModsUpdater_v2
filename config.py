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
__version__ = "2.0.0-dev2"  # Don't forget to change EXPECTED_VERSION
__date__ = "2025-03-25"  # Last update


# config.py

import configparser
import logging
import os
import platform
from pathlib import Path

from rich import print
from rich.prompt import Prompt

import global_cache
import utils

# The target version after migration
EXPECTED_VERSION = "2.0.0-dev2"

# Constant for os
SYSTEM = platform.system()
HOME_PATH = Path.home()
XDG_CONFIG_HOME_PATH = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))

MODS_PATHS = {
    "Windows": Path(HOME_PATH) / 'AppData' / 'Roaming' / 'VintagestoryData' / 'Mods',
    "Linux": Path(XDG_CONFIG_HOME_PATH) / 'VintagestoryData' / 'Mods'
}

# Constants for paths
APPLICATION_PATH = Path.cwd()
CONFIG_FILE = APPLICATION_PATH / 'config.ini'
TEMP_PATH = APPLICATION_PATH / 'temp'
LOGS_PATH = APPLICATION_PATH / 'logs'
LANG_PATH = APPLICATION_PATH / 'lang'

# Constants for supported languages
SUPPORTED_LANGUAGES = {
    "US": ["en", "English", '1'],
    "FR": ["fr", "Français", '2'],
    "UA": ["uk", "Yкраїнська", '3']
}
DEFAULT_LANGUAGE = "en_US"

# Constants for url
URL_BASE_MOD_API = "https://mods.vintagestory.at/api/mod/"
URL_BASE_MOD_DOWNLOAD = "https://moddbcdn.vintagestory.at/"
URL_BASE_MODS = 'https://mods.vintagestory.at/'
URL_MOD_DB = "https://mods.vintagestory.at/show/mod/"
URL_SCRIPT = {
    "windows": 'https://mods.vintagestory.at/modsupdater#tab-files',
    "linux": 'https://mods.vintagestory.at/modsupdaterforlinux#tab-files'
}

# Default configuration
DEFAULT_CONFIG = {
    "ModsUpdater": {"version": __version__},
    "Logging": {"log_level": "DEBUG"},  # Debug Set to INFO for full release !!
    "Options": {"force_update": "false", "exclude_prerelease_mods": "false", "auto_update": "true", "max_workers": os.cpu_count()},
    "Backup_Mods": {"backup_folder": "backup_mods", "max_backups": 3},
    "ModsPath": {"path": str(MODS_PATHS[SYSTEM])},
    "Language": {"language": DEFAULT_LANGUAGE},
    "Game_Version": {"user_game_version": ""},
    "Mod_Exclusion": {'mods': ""}
}

# Mapping for renamed sections or options
RENAME_MAP = {
    "Game_Version_max": "user_game_version",
    "ModPath": "ModsPath",
    "ver": "version",
    "disable_mod_dev": "exclude_prerelease_mods",
    "mod1": "mods",
    "mod2": "mods",
    "mod3": "mods",
    "mod4": "mods",
    "mod5": "mods",
    "mod6": "mods",
    "mod7": "mods",
    "mod8": "mods",
    "mod9": "mods",
    "mod10": "mods",
}

# Static list of User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:115.0) Gecko/20100101 Firefox/115.0",
]

# Maximum number of files to process simultaneously, best = nb of core of the processor
# MAX_WORKERS = 10  # à changer par valeur de config.ini


def read_version_from_config_file():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)  # Read the configuration file
    return config.get('ModsUpdater', 'version', fallback=None)


def migrate_config_if_needed():
    current_version = read_version_from_config_file()  # Function to read the version from config.ini
    if current_version != EXPECTED_VERSION:
        # If the configuration version is outdated, initiate the migration
        old_config = configparser.ConfigParser()
        old_config.read(CONFIG_FILE)  # Read the current configuration file
        migrate_config(old_config)  # Migrate the configuration to the new version


def migrate_config(old_config):
    """
    Migrate the configuration from an old version to the new format.
    This function:
      - Updates the version field.
      - Removes unnecessary legacy options (e.g., `system`).
      - Migrates renamed sections and options.
      - Preserves the order of sections as defined in `DEFAULT_CONFIG`.
      - Ensures all sections and options from the default config are present.
    """
    new_config = configparser.ConfigParser()

    logging.info("Starting migration process of old config.ini...")

    # Step 1: Handle ModsUpdater version migration
    new_config["ModsUpdater"] = {"version": EXPECTED_VERSION}  # Always set to latest version
    logging.debug("Migrating ModsUpdater section: version set to %s", EXPECTED_VERSION)

    # Step 2: Handle Options migration
    options_section = {}
    if "ModsUpdater" in old_config:
        for option in ["force_update",
                       "auto_update"]:  # Only migrate valid options from the old config
            if option in old_config["ModsUpdater"]:
                options_section[option] = old_config["ModsUpdater"][option]
                logging.debug("Migrating option '%s' to new config", option)

        # Handle 'disable_mod_dev' explicitly: replace it with 'exclude_prerelease_mods' in the new config
        if "disable_mod_dev" in old_config["ModsUpdater"]:
            options_section["exclude_prerelease_mods"] = old_config["ModsUpdater"][
                "disable_mod_dev"]
            logging.debug("'disable_mod_dev' replaced with 'exclude_prerelease_mods'.")

    # Merge with defaults, excluding unnecessary keys (e.g., log_level if already elsewhere)
    new_config["Options"] = {
        k: v
        for k, v in {**DEFAULT_CONFIG["Options"], **options_section}.items()
        if k != "log_level"  # Exclude log_level (already in [Logging])
    }
    logging.debug("Options section migrated successfully")

    # Step 3: Handle Game_Version_max -> user_game_version migration
    if "Game_Version_max" in old_config:
        user_game_version = old_config["Game_Version_max"].get("version")
        user_game_version = None if str(user_game_version) == "100.0.0" else user_game_version
        new_config["Game_Version"] = {"user_game_version": user_game_version or 'None'}
        logging.debug("Migrating Game_Version_max to user_game_version: %s", user_game_version)
    else:
        new_config["user_game_version"] = DEFAULT_CONFIG["Game_Version"]
        logging.debug("Using default user_game_version: %s", DEFAULT_CONFIG["Game_Version"]["user_game_version"])

    # Step 4: Handle ModPath -> ModsPath migration
    if "ModPath" in old_config:
        mods_path = old_config["ModPath"].get("path")
        if mods_path:  # Use existing path if available
            new_config["ModsPath"] = {"path": mods_path}
            logging.debug("Migrating ModPath to ModsPath: %s", mods_path)
        else:  # Fallback to cache value
            new_config["ModsPath"] = DEFAULT_CONFIG["ModsPath"]
            logging.debug("Using default ModsPath: %s", DEFAULT_CONFIG["ModsPath"]["path"])
    else:
        new_config["ModsPath"] = DEFAULT_CONFIG["ModsPath"]
        logging.debug("Using default ModsPath: %s", DEFAULT_CONFIG["ModsPath"]["path"])

    # Step 5: Handle Mod_Exclusion migration (dictionary to list)
    if "Mod_Exclusion" in old_config:
        mods_list = [
            value.strip()
            for key, value in old_config["Mod_Exclusion"].items()
            if value.strip()  # Ignore empty values
        ]
        if mods_list:  # Only add if valid mods exist
            new_config["Mod_Exclusion"] = {"mods": ", ".join(mods_list)}
            logging.debug("Migrating Mod_Exclusion with %d mods", len(mods_list))
    else:
        new_config["Mod_Exclusion"] = DEFAULT_CONFIG["Mod_Exclusion"]
        logging.debug("Using default Mod_Exclusion")

    # Step 6: Handle Language migration
    if "Language" in old_config:
        language = old_config["Language"].get("language")
        if language:
            new_config["Language"] = {"language": language}
            logging.debug("Migrating Language: %s", language)
    else:
        new_config["Language"] = DEFAULT_CONFIG["Language"]
        logging.debug("Using default Language: %s", DEFAULT_CONFIG["Language"]["language"])

    # Step 7: Add any missing sections or options from DEFAULT_CONFIG
    for section, defaults in DEFAULT_CONFIG.items():
        if section not in new_config:
            new_config[section] = defaults
            logging.debug("Adding missing section: %s", section)
        else:
            for key, value in defaults.items():
                if key not in new_config[section]:
                    new_config[section][key] = value
                    logging.debug("Adding missing option '%s' to section '%s'", key, section)

    # Step 8: Write the migrated configuration to the file, preserving the order of sections
    try:
        with open(CONFIG_FILE, "w") as configfile:
            # Write each section in the order of DEFAULT_CONFIG
            for section, _ in DEFAULT_CONFIG.items():
                if section in new_config:
                    configfile.write(f"[{section}]\n")
                    for key, value in new_config[section].items():
                        configfile.write(f"{key} = {value}\n")
                    configfile.write("\n")
        logging.info("Migration completed and configuration file written successfully.")
        print(f"Configuration migrated successfully to version {EXPECTED_VERSION}.")
    except Exception as e:
        logging.error("Error occurred while writing the migrated config: %s", str(e))


def create_config(language, mod_folder, user_game_version, auto_update):
    """
    Create the config.ini file with default or user-specified values.
    """
    DEFAULT_CONFIG["Language"]["language"] = language[0]
    DEFAULT_CONFIG["ModsPath"]["path"] = mod_folder
    DEFAULT_CONFIG["Game_Version"]["user_game_version"] = user_game_version
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
    # Check if the configuration file exists
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"The configuration file {CONFIG_FILE} was not found.")

    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        # ### Populate global_cache ###
        global_cache.config_cache['APPLICATION_PATH'] = APPLICATION_PATH
        global_cache.config_cache["SYSTEM"] = platform.system()
        # Fill the global cache with config.ini data
        for section in config.sections():
            global_cache.config_cache[section] = {key: value for key, value in
                                                  config.items(section)}
        # Fill with constants
        global_cache.config_cache['SYSTEM'] = platform.system()
        global_cache.config_cache['HOME_PATH'] = Path.home()
        global_cache.config_cache['XDG_CONFIG_HOME_PATH'] = os.getenv('XDG_CONFIG_HOME', str(global_cache.config_cache['HOME_PATH'] / '.config'))
        global_cache.config_cache['URL_BASE_MOD_API'] = URL_BASE_MOD_API
        global_cache.config_cache['URL_BASE_MOD_DOWNLOAD'] = URL_BASE_MOD_DOWNLOAD
        global_cache.config_cache['URL_BASE_MODS'] = URL_BASE_MODS
        global_cache.config_cache['URL_MOD_DB'] = URL_MOD_DB
        # Paths
        global_cache.config_cache["MODS_PATHS"] = {
            "Windows": Path(
                HOME_PATH) / 'AppData' / 'Roaming' / 'VintagestoryData' / 'Mods',
            "Linux": Path(XDG_CONFIG_HOME_PATH) / 'VintagestoryData' / 'Mods'
        }
        # Fill cache with user-agent
        global_cache.config_cache['USER_AGENTS'] = USER_AGENTS

        # Retrieve excluded mods from the config file
        excluded_mods = config.get("Mod_Exclusion", "mods", fallback="").split(", ")

        # Ensure we don't have empty strings in the list
        excluded_mods = [mod.strip() for mod in excluded_mods if mod.strip()]
        for mod in excluded_mods:
            global_cache.mods_data["excluded_mods"].append({"Filename": mod})

        # Handle the game version
        user_game_version = global_cache.config_cache.get("Game_Version", {}).get("user_game_version")
        if user_game_version == "None":
            user_game_version = None
        if not user_game_version:
            latest_game_version = utils.get_latest_game_version()
            if latest_game_version:
                global_cache.config_cache.setdefault("Game_Version", {})["user_game_version"] = latest_game_version
                logging.info(
                    f"Game version set to the latest available version: {latest_game_version}")
            else:
                logging.warning(
                    "Unable to retrieve the latest game version. The version is left empty.")
    except Exception as e:
        logging.error(f"Error occurred while loading the config.ini file: {e}")
        raise
    return global_cache.config_cache


def config_exists():
    """
    Check if the config.ini file exists.
    """
    return CONFIG_FILE.exists()


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
        return ask_mods_directory()  # Re-prompt if the path is invalid.


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
    while True:
        user_game_version = Prompt.ask(
            'Which version of the game are you using? You can set a game version to limit mod updates. Leave it empty to always use the latest available game version. If you enter a version, it will need to be updated when new game versions are released. Use a valid semver format: e.g., 1.2.3)',
            default=""
            )

        # If the user left the input empty, it will use the last game version
        if user_game_version == "":
            user_game_version = None
            return user_game_version

        # If valid, complete and return the version
        if utils.is_valid_version(user_game_version):
            return utils.complete_version(user_game_version)
        else:
            # If the format is invalid, display an error message and ask for the version again.
            print(
                "[bold red]Error: Please provide a valid version in the format major.minor.patch (e.g., 1.2.3).[/bold red]")


def configure_logging(logging_level):
    # Vérifier si un FileHandler est déjà présent
    if not any(isinstance(handler, logging.FileHandler) for handler in logging.getLogger().handlers):
        # Enlever les handlers existants si nécessaire.
        if logging.getLogger().hasHandlers():
            logging.getLogger().handlers.clear()

        # S'assurer que les répertoires existent avant de configurer le logging.
        utils.setup_directories(LOGS_PATH)

        log_file = Path(LOGS_PATH) / f'app_log.txt'

        # Créer un handler pour le fichier.
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Défini par défaut à DEBUG, mais mis à jour après

        # Créer un format de log.
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Ajouter le handler au logger.
        logging.getLogger().addHandler(file_handler)

        log_level = logging_level.upper()

        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if log_level not in valid_log_levels:
            logging.warning(f"Invalid log level '{log_level}' in configuration. Defaulting to 'DEBUG'.")
            log_level = "DEBUG"

        # Appliquer le niveau de log
        logging.getLogger().setLevel(getattr(logging, log_level, logging.DEBUG))

        logging.debug(f"Logging configured successfully with '{log_level}' level and custom file handler!")

    else:
        # If FileHandler is already present, do nothing.
        pass


if __name__ == "__main__":
    pass
