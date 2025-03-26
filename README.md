# <p align="center">Vintage Story ModsUpdater</p>
### <p align="center">Easily update your favorite mods</p>
<br><br>

===========================================================================

This a third-party program. It means it is NOT a mod. You do not have to put it in the mods folder.<br>

===========================================================================



I have resumed the development of v2. I started from scratch (again), and everything is now clearer and cleaner—at least much more than the previous version. I also hope it is better optimized and faster.
For now, it is far from complete; many features are still missing, but it can already update mods automatically.


### Functional Features:
* Automatic mod updates with version locking for a specific game version
* Backup of mods before updating them
* Improved logging
* Multi-threading
* Attempt to make the script more CDN-friendly
* Possible migration from an old version of ModsUpdater: the config file is retrieved and updated for the new version (not tested on older versions of ModsUpdater)

### Features Not Yet Functional:
* Retrieving mod changelogs
* Use of arguments
* Generating a list of installed mods (PDF + JSON)
* Manual updates (I first need to solve issues with changelog retrieval)
* Planned but not guaranteed: the ability to downgrade mods for a given game version


(updated 2025-03-26)

## migration function for config.ini
I’ve added a migration function from the old config to v2. Just put VS_ModsUpdater_v2.0.0-dev1.exe in the same folder as the previous version or copy the config.ini file next to VS_ModsUpdater_v2.0.0-dev1.exe.

## New options have arrived in the config.ini file:
The config.ini file is used to configure the behavior of the mods updater. Below are the available settings you can adjust.
```ìni
[Logging]
log_level = INFO
```
This option allows you to choose the logging level: DEBUG, INFO, WARNING, ERROR, or CRITICAL. By default, it is set to INFO.

```ìni
max_workers = 4
```
**max_workers** defines the number of threads that can be executed in parallel for multithreading tasks. By default, this value is equal to the number of physical cores on the processor. You can adjust this value to increase or decrease the processing speed based on your needs. However, a limit is set: the maximum number of threads cannot exceed 2.5 times the number of physical cores on the processor.

For example, for a processor with 4 cores, the maximum value for max_workers will be 10 (2.5 * 4 = 10), regardless of the number of threads you attempt to set. This limit helps prevent processor overload and ensures balanced resource utilization.

```ìni
[Backup_Mods]
backup_folder = backup_mods
max_backups = 3
```
These options define the folder where mod backups will be stored and the maximum number of backups to keep before older ones are overwritten. In case of issues, the original mods can be easily restored. By default, the backup_mods folder will be created in the ModsUpdater directory.

```ìni
[Mod_Exclusion]
mods = mod01.zip, mod02.zip, mod03.zip
```
The Mod_Exclusion section has been updated. You can now list the filenames of mods to exclude from the update process, separated by commas. Leave this field empty if no mods need to be excluded.