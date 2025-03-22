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


(updated 2025-03-22)


## INFORMATION:
I just noticed a small bug after compilation. If you run the script for the first time and there is no config.ini file in the folder, the script will set the value to NONE for 'version', which causes the script to crash. You need to remove NONE and either leave it empty (to get the latest game version in progress), or specify the version you want (in the format 1.20.4).
If you have :
```ìni
[Game_Version]
version = NONE
```
Then change to (if you want the latest game version)
```ìni
[Game_Version]
version =
```
or (to have a specified version)
```ìni
[Game_Version]
version = 1.20.0
```

## migration function for config.ini
I’ve added a migration function from the old config to v2. Just put VS_ModsUpdater_v2.0.0-dev1.exe in the same folder as the previous version or copy the config.ini file next to VS_ModsUpdater_v2.0.0-dev1.exe.

## New options have arrived in the config.ini file:
```ìni
[Logging]
log_level = INFO
```
You can choose the log level: DEBUG, INFO, WARNING, ERROR, CRITICAL.
By default, it is set to INFO.

```ìni
max_workers = 4
```
For now, this is unused. I’m not sure if I’ll keep it or not. It controls the number of "workers" for multi-threading. The higher the number, the more tasks are done in parallel. It will be limited to a maximum value based on the number of CPU cores you have.

```ìni
[Backup_Mods]
backup_folder = backup_mods
max_backups = 3
```
These options define the number of mod backups to keep before updating them and their folder location. In case of issues, you can easily find the original mods. By default, the backup_mods folder is created in the ModsUpdater folder.

```ìni
[Mod_Exclusion]
mods = mod01.zip, mod02.zip, mod03.zip
```
The Mod_Exclusion section has changed. Now, simply list the file names to exclude from the update process, separated by commas. Leave it empty otherwise.



