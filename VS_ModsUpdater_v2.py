#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vintage Story mod management:

"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-02"  # Last update

import configparser
import datetime as dt
import json
import logging
import os
import platform
import re
import zipfile
from pathlib import Path
from urllib.error import URLError, HTTPError

import requests
from bs4 import BeautifulSoup
from packaging.version import Version
from requests.exceptions import RequestException
from rich import print


# from rich.prompt import Prompt


def normalize_keys(d):
    """Normalize the keys of a dictionary to lowercase"""
    if isinstance(d, dict):
        return {k.lower(): normalize_keys(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [normalize_keys(i) for i in d]
    else:
        return d


def fix_json(json_data):
    # Correction 1 : Remove final commas
    json_data = re.sub(r",\s*([}\]])", r"\1", json_data)

    # Correction 2 : Add missing quotation marks around keys
    json_data = re.sub(r'(?<!")(\b\w+\b)(?=\s*:)', r'"\1"', json_data)
    return json_data


def version_compare(local_version, online_version):
    # Compare
    if Version(local_version) < Version(online_version):
        new_version = True
        return new_version
    else:
        new_version = False
        return new_version


# Check for script update on ModDB
class UpdateScript:
    URLS = {
        "windows": 'https://mods.vintagestory.at/modsupdater#tab-files',
        "linux": 'https://mods.vintagestory.at/modsupdaterforlinux#tab-files'
    }

    def __init__(self, app_config):
        self.my_os = getattr(app_config, 'system', None)
        self.url_base_script = getattr(app_config, 'url_base_mod', None)
        if not self.my_os:
            raise ValueError(
                "The 'app_config' parameter must have a 'system' attribute.")

        self.my_os = self.my_os.lower()
        logging.info(f'OS: {self.my_os} - Checking for ModsUpdater update')

        url_script = self.get_url()
        if not url_script:
            raise ValueError("Unsupported operating system; cannot construct URL.")

        self.new_version = self.fetch_page(url_script)

    def get_url(self):
        """Retrieve the URL for the update script based on the operating system."""
        return self.URLS.get(self.my_os, '')

    def fetch_page(self, url):
        """Fetch and parse the page for the update script, handling errors."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            page_content = response.content
            if 'not found' in response.text.lower():
                self.log_error("Content indicates page not found.")
                return None, None

            # Parsing page content for latest version and download URL
            soup = BeautifulSoup(page_content, features="html.parser")
            changelog = soup.find("div", {"class": "changelogtext"})
            download_link = soup.find("a", {"class": "downloadbutton"})

            # Retrieve version number from changelog
            latest_version = re.search('<strong>v(.*)</strong>', str(changelog))
            new_version = version_compare(__version__, latest_version[1])
            url = f'{self.url_base_script}{download_link["href"]}'
            logging.info("Check for script update done.")
            return new_version, url

        except (URLError, HTTPError, RequestException) as e:
            self.log_error(f"Error accessing URL: {e}")

    @staticmethod
    def log_error(message):
        print(message)
        logging.error(message)


# Config manager
class ConfigManager:
    """Create config.ini or retrieve configuration"""
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
        "Mod_Exclusion": {}
    }

    def __init__(self, app_config, config_path="config.ini"):
        self.config_parser = configparser.ConfigParser(allow_no_value=True,
                                                       interpolation=None)
        self.config_path = Path(config_path)
        self.path_logs = app_config.path_logs
        self.load_config()

    def load_config(self):
        """Load configuration from file or initialize with default values if missing."""
        # Load default configuration
        self.config_parser.read_dict(self.DEFAULT_CONFIG)

        # Load config.ini if exists
        if self.config_path.is_file():
            self.config_parser.read(self.config_path, encoding="utf-8-sig")
        else:
            # Creates config.ini if does not exist
            self.save_config()

    def get(self, section, key, fallback=None):
        """Retrieve a configuration value with a fallback option."""
        return self.config_parser.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        """Set a configuration value and save it to file."""
        if section not in self.config_parser:
            self.config_parser.add_section(section)
        self.config_parser[section][key] = value
        self.save_config()

    def save_config(self):
        """Save the current configuration to file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as configfile:
                self.config_parser.write(configfile)
                self.configure_logging()
                logging.info(f"{self.config_path.name} file has been created.")
        except (FileNotFoundError, IOError, PermissionError) as e:
            logging.error(f"Failed to create config file: {e}")
            print(f"Error: Could not create config file due to {e}.")

    def configure_logging(self):
        """Configure logging with a timestamped filename."""
        timestamp = dt.datetime.today().strftime("%Y%m%d%H%M%S")
        log_file = self.path_logs / f'log-{timestamp}.txt'
        """Configure logging based on the configuration."""
        log_level = self.get("Logging", "log_level", "DEBUG").upper()
        logging.basicConfig(
            filename=log_file,
            level=getattr(logging, log_level, logging.DEBUG),
            format="%(asctime)s - %(levelname)s - %(message)s",
        )


# App configuration
class AppConfiguration:
    def __init__(self):
        self.url_base_mod = 'https://mods.vintagestory.at'
        self.url_api = 'https://mods.vintagestory.at/api'
        self.system = platform.system()
        self.app_path = os.getcwd()
        self.home_dir = Path.home()
        self.config_file_path = Path(self.app_path, "config.ini")
        self.path_temp = Path(self.app_path, "temp")
        self.path_logs = Path(self.app_path, "logs")
        # Mod path definition
        mods_paths = {
            "Windows": Path(self.home_dir,
                            r"AppData\Roaming\VintagestoryData\Mods"),
            "Linux": Path("")  # Change path linux
        }
        # Dict for languages - Region, language-abr, language, index
        self.dic_lang = {
            "US": ["en", "English", '1'],
            "FR": ["fr", "Français", '2']
        }
        self.config_file_found = True
        self.translations = None
        # Directory creation
        self.setup_directories()
        # Load app settings
        self.path_logs = Path(self.app_path, "logs")
        config_manager = ConfigManager(self)
        config_manager.configure_logging()
        self.lang = config_manager.get("Language", "language", "en_US")
        self.log_level = config_manager.get("Logging", "log_level", "DEBUG")
        self.game_version = config_manager.get("Game_Version", "version", "")
        self.path_mods = config_manager.get("ModsPath", "path", mods_paths[self.system])
        # load lang file
        self.load_lang()

    def setup_directories(self):
        required_directories = [self.path_temp, self.path_logs]
        for directory in required_directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)

    def load_lang(self):
        # JSON file loading according to language
        with open(f'lang/{self.lang}.json', 'r', encoding='utf-8') as f:
            self.translations = json.load(f)


class ConsoleDisplayInfo:
    def __init__(self, app_config):
        self.title_modsupdater_title = None
        self.path_mods = getattr(app_config, 'path_mods', None)
        self.translations = getattr(app_config, 'translations')
        self.conf_file = getattr(app_config, 'config_file_path')
        self.config_file_found = getattr(app_config, "config_file_found")
        self.game_version = getattr(app_config, "game_version")
        self.lang = getattr(app_config, "lang")
        if self.game_version is None:
            self.game_version = self.translations.get("game_version")
        self.display()

    def display(self):
        # look for script update
        update_script = UpdateScript(appconfig)
        new_version, url_script = update_script.new_version
        if new_version:
            text = f'[red]{self.translations.get("title_new_version")}[/red] - {url_script}'
        else:
            text = f'[bold cyan]{self.translations.get("title_no_new_version")}[/bold cyan]'
        # *** Welcome text ***
        column, row = os.get_terminal_size()
        txt_title = f'\n\n[bold cyan]{self.translations.get("title_modsupdater_title").format(mu_ver=__version__)}[/bold cyan]'
        lines = txt_title.splitlines() + text.splitlines()
        for line in lines:
            print(line.center(column))
        # Display default configuration
        if not self.config_file_found:
            lst_lines = [
                f"[bold cyan]{self.translations.get("first_launch_text")}[/bold cyan] :",
                f"\t- [bold cyan]{self.translations.get("first_launch_language")} : [/bold cyan]{self.lang}",
                f"\t- [bold cyan]{self.translations.get("first_launch_mods_location")} : [/bold cyan]{self.path_mods}",
                f"\t- [bold cyan]{self.translations.get("first_launch_game_version")} : [/bold cyan]{self.game_version}",
                f"\t- [bold cyan]force_Update : [/bold cyan]",
                f"\t- [bold cyan]disable_mod_dev : [/bold cyan]",
                f"\t- [bold cyan]auto_update : [/bold cyan]",
            ]
            for line in lst_lines:
                print(line)
        # Ask to continue or quit


class Mods:
    def __init__(self, app_config):
        self.path_mods = Path(getattr(app_config, 'path_mods', None))
        self.url_api = getattr(app_config, 'url_api', None)
        self.game_version = getattr(app_config, 'game_version', None)
        self.modinfo_content = ""
        self.mod_name = None
        self.mod_version = None
        self.mod_modid = None
        self.mod_description = None
        self.mod_dic = {}
        self.mod_dic_sorted = {}
        self.mod_infos = []
        self.mods_to_update = []
        self.list_mods()

    # Retrieve the last game version
    def get_last_game_version(self):
        gameversions_api_url = f'{self.url_api}/gameversions'
        try:
            response = requests.get(gameversions_api_url)
            response.raise_for_status()  # Checks that the request was successful (status code 200)
            gameversion_data = response.json()  # Retrieves JSON content
            logging.info(f"Game version data retrieved.")
            # Retrieve the latest version
            return gameversion_data['gameversions'][0]['name']

        except:
            logging.warning(f"Cannot reach gameversion api.")
            return None

    # Creation of the mods list in a dictionary
    def list_mods(self):
        def process_zip_mod(zip_mod):
            with zipfile.ZipFile(zip_mod, "r") as zip_modfile:
                with zip_modfile.open("modinfo.json", "r") as modinfo_json:
                    modinfo_content = modinfo_json.read().decode("utf-8-sig")
                    try:
                        python_obj = json.loads(modinfo_content)
                    except json.JSONDecodeError:
                        python_obj = json.loads(fix_json(modinfo_content))
                    python_obj_normalized = normalize_keys(python_obj)

                    mod_name = python_obj_normalized.get("name", "").capitalize()
                    mod_version = python_obj_normalized.get("version", "")
                    mod_modid = python_obj_normalized.get("modid", "")
                    mod_description = python_obj_normalized.get("description", "")
                    self.add_mod_info(mod_name, mod_version, mod_modid, mod_description,
                                      zip_mod.name)

        def process_cs_mod(cs_mod):
            with open(cs_mod, "r", encoding="utf-8-sig") as cs_modfile:
                cs_file = cs_modfile.read()
                mod_name = \
                    re.search(r"(namespace )(\w*)", cs_file, flags=re.IGNORECASE)[
                        2].capitalize()
                mod_version = \
                    re.search(r"(Version\s=\s\")([\d.]*)\"", cs_file,
                              flags=re.IGNORECASE)[
                        2]
                mod_description = \
                    re.search(r'Description = "(.*)",', cs_file, flags=re.IGNORECASE)[1]
                self.add_mod_info(mod_name, mod_version, mod_name, mod_description,
                                  cs_mod.name)

        for mod in self.path_mods.iterdir():
            if zipfile.is_zipfile(mod):
                process_zip_mod(mod)
            elif Path(mod).suffix.lower() == ".cs":
                process_cs_mod(mod)
        # mod_dic sorted by mod name
        elem_sorted = sorted(self.mod_dic.items(), key=lambda item: item[1]["name"])
        self.mod_dic_sorted = {key: value for key, value in elem_sorted}

    def add_mod_info(self, mod_name: str, mod_version: str, mod_modid: str,
                     mod_description: str, mod_file: str) -> None:
        self.mod_dic[mod_file] = {
            "name": mod_name,
            "version": mod_version,
            "modid": mod_modid,
            "description": mod_description
        }

    # Get info stored in mod_dic_sorted
    def get_mod_info(self, mod_file):
        try:
            self.mod_name = self.mod_dic_sorted[mod_file]['name']
            self.mod_version = self.mod_dic_sorted[mod_file]['version']
            self.mod_modid = self.mod_dic_sorted[mod_file]['modid']
            self.mod_description = self.mod_dic_sorted[mod_file]['description']
            return self.mod_name, self.mod_version, self.mod_modid, self.mod_description
        except:
            logging.warning(
                f"Mod file '{mod_file}' not found in sorted mod dictionary.")
            return None

    def get_mod_api_data(self, modid):
        mod_url_api = f'{self.url_api}/mod/{modid}'
        logging.info(f"Retrieving mod info from: {mod_url_api}")

        try:
            response = requests.get(mod_url_api)
            response.raise_for_status()  # Checks that the request was successful (status code 200)
            mod_data = response.json()  # Retrieves JSON content
            logging.info(f"Mod data retrieved successfully.")
            return mod_data

        except requests.exceptions.HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')
        except Exception as err:
            logging.error(f'Other error occurred: {err}')

    # Fonction pour récupérer 'mainfile' selon le tag
    @staticmethod
    def get_mainfile_by_tag(mod_releases, target_tag):
        mainfiles = []
        for release in mod_releases:
            if target_tag in release['tags']:
                mainfiles.append(release['mainfile'])
        return mainfiles

    def url_mod_to_dl(self, modfile):
        mod_info = self.get_mod_info(modfile)
        if not mod_info:
            logging.warning(f"No information found for mod file: {modfile}")
            return

        mod_name, mod_version, mod_modid, mod_description = mod_info
        latest_gameversion = self.get_last_game_version()
        if not latest_gameversion:
            logging.warning("Cannot retrieve the latest game version.")
            return

        mod_api_data = self.get_mod_api_data(mod_modid)
        if not mod_api_data:
            logging.warning(
                f"No data found for mod '{mod_name}' with ID '{mod_modid}'.")
            return
        mod_releases = mod_api_data['mod']['releases']

        if self.game_version == "":
            self.game_version = self.get_last_game_version()[1:]

        tag_to_search = f'v{self.game_version}'
        try:
            result = self.get_mainfile_by_tag(mod_releases, tag_to_search)
            url_mod_to_download = f'https://mods.vintagestory.at/{result[0]}'
            return mod_name, url_mod_to_download
        except IndexError:
            info = f'{mod_name}: no download corresponding to the desired game version.'
            logging.info(info)
            return mod_name, info


appconfig = AppConfiguration()
consoledisplayinfo = ConsoleDisplayInfo(appconfig)
mods = Mods(appconfig)

print(mods.url_mod_to_dl('moremolds_v1420.zip'))
