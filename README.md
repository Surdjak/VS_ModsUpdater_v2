
<p align="center" style="font-size: 2.5em;"><b>- Vintage Story ModsUpdater -</b></p>

This program automates the management of your mods for the game Vintage Story. It allows you to check for updates, download them (automatically or manually), and generate a list of your installed mods in JSON and PDF format.
## Key Features

- Script Update Check: Checks if a new version of the ModsUpdater tool is available.
- Configuration Migration: Automatically manages the migration of the old configuration file format to the new one, ensuring compatibility during application updates.
- Update Check: Compares the local versions of your mods with the latest versions available on ModDB.
- Automatic Download: Automatically downloads available updates (configurable).
- Manual Download: Displays changelogs and allows you to choose which updates to download.
- Backup Management: Creates backups of your mods before updating them, with a configurable retention policy.
- Excluded Mods Management: Allows you to ignore certain mods during update checks and downloads.
- Mod List Generation (PDF/JSON): Creates a PDF/JSON document listing your installed mods.
- Command Line Interface (CLI): Integration with arguments to customize execution.
- Multilingual Support: The interface is available in several languages (configurable).

**Important Note Regarding Configuration Migration:**

During updates of the ModsUpdater application, the format of the `config.ini` file may evolve. To facilitate these updates, the application includes an automatic migration mechanism. If an older version of the configuration file is detected, the application will attempt to convert it to the new format. In most cases, this migration will occur transparently. However, it is always recommended to check your `config.ini` file after an application update to ensure that all your settings are correctly preserved. In case of any issues, a backup of your old configuration (`config.old`) is kept (in the application directory).

## Configuration (`config.ini`)

The `config.ini` file contains the configuration parameters for the application. It is located in the same directory as the main script. Here are the main sections and their options:

```ini
[ModsUpdater]
version: Current version of the ModsUpdater application (information).

[Logging]
log_level: Level of detail for logs recorded by the application (e.g., DEBUG, INFO, WARNING, ERROR). DEBUG will display the most details.

[Options]
exclude_prerelease_mods: true to exclude pre-release mod versions during update checks, false to include them.
auto_update: true to enable automatic downloading of updates (after checking), false to use manual mode where you confirm each download.
max_workers: Maximum number of threads to use for downloading mods in parallel. Increasing this value may speed up downloads but may also consume more system resources.
timeout: Timeout in seconds for HTTP requests during update checks and mod downloads.

[Backup_Mods]
backup_folder: Name of the directory (created in the application directory) where mod backups will be stored.
max_backups: Maximum number of mod backups to keep. Older backups will be deleted when this limit is reached.
modlist_folder: Name of the directory (created in the application directory) where the mod list in PDF format will be saved.

[ModsPath]
path: Full path to the directory where your Vintage Story mods are installed on your computer. This is crucial for the application to find your mods. (Example for Windows: C:\Users\Jerome\AppData\Roaming\VintagestoryData\Mods)

[Language]
language: Language code to use for the application interface (e.g., en_US for English, fr_FR for French). This value must correspond to the name of a file (without the `.json` extension) present in the `lang` subdirectory of the application. Make sure the corresponding language file exists.

[Game_Version]
user_game_version: Maximum game version target for mod updates.
    If you specify a version (for example, 1.20.5), the application will not download mod updates that are only compatible with Vintage Story versions higher than the one specified.
    If this option is left empty (``) or set to None, the application will download the latest available update for each mod, regardless of the compatible Vintage Story version. Caution: this means you might download mods that are not compatible with your current game version. If you want to stay on a specific Vintage Story version, define the version, but remember to change it when you update the game.

[Mod_Exclusion]
mods: List of filenames (without the path) of mods to ignore during update checks and downloads. Filenames should be separated by commas and spaces (e.g., mod_a.zip, my_old_mod.cs).
```

## Command Line Arguments Usage

The script can be executed with arguments to customize its behavior:

- `--no-pause`: Disables the pause at the end of the script execution. Useful for non-interactive execution or in automated scripts.
- `--modspath "<path>"`: Allows you to specify the path to the Vintage Story mods directory directly during execution. The path must be enclosed in quotation marks if it contains spaces. This argument replaces the path defined in the `config.ini` file.
- `--no-pdf`: Disables the automatic generation of the mod list in PDF format at the end of execution.
- `--no-json`: Disables the automatic generation of the mod list in JSON format at the end of execution.
- `--log-level <level>`: Sets the level of detail for logs recorded by the application. Possible options are: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (in uppercase). This argument replaces the log level defined in the `[Logging]` section of `config.ini`.
- `--max-workers <number>`: Allows you to specify the maximum number of threads to use for mod processing. This argument replaces the `max_workers` value defined in the `[Options]` section of `config.ini`.
- `--timeout <seconds>`: Sets the timeout in seconds for HTTP requests during update checks and mod downloads. This argument replaces the `timeout` value defined in the `[Options]` section of `config.ini`.

**Usage Examples:**

```bash
.\VS_ModsUpdater.exe --modspath "D:\Vintage Story\mods" --no-pdf
```
This command will execute the script using the specified mods directory (`D:\Vintage Story\mods`) and will disable the generation of the PDF mod list file. The mods path specified here will replace the one configured in `config.ini`.



```bash
.\VS_ModsUpdater.exe --log-level INFO --max-workers 6 --timeout 15
```
This command will execute the script by setting the log level to `INFO`, using a maximum of 6 threads for mod processing, and a timeout of 15 seconds for HTTP requests. These parameters will replace those defined in the `config.ini` file for this execution.


## License

This program is distributed under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License.