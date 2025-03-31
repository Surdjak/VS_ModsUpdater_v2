# <p align="center">Vintage Story ModsUpdater</p>
### <p align="center">Easily update your favorite mods</p>
<br><br>

===========================================================================

This a third-party program. It means it is NOT a mod. You do not have to put it in the mods folder.<br>

===========================================================================


### Functional Features:
* Automatic mod updates with version locking for a specific game version
* Backup of mods before updating them
* Retrieving mod changelogs (now entiere changelogs must be retrieved)
* Generating a list of installed mods (PDF + JSON)
* Improved logging
* Multi-threading
* Possible migration from an old version of ModsUpdater: the config file is retrieved and updated for the new version (not tested on very old versions of ModsUpdater)

### Features Not Yet Functional:
* Use of arguments
* Manual updates
* Planned but not guaranteed: the ability to downgrade mods for a given game version


(updated 2025-03-31)

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
[Options]
auto_update = False
```
Not yet useful. only when manual donwload will be available

```ìni
[Options]
max_workers = 4
```
**max_workers** defines the number of threads that can be executed in parallel for multithreading tasks. By default, this value is equal to the number of physical cores on the processor. You can adjust this value to increase or decrease the processing speed based on your needs. However, a limit is set: the maximum number of threads cannot exceed 2.5 times the number of physical cores on the processor.

For example, for a processor with 4 cores, the maximum value for max_workers will be 10 (2.5 * 4 = 10), regardless of the number of threads you attempt to set. This limit helps prevent processor overload and ensures balanced resource utilization.

```ìni
[Options]
timeout = 10
```
The timeout parameter defines the maximum duration (in seconds) the program will wait for a response when sending requests. The default value is 10 seconds. Users can adjust this value according to their network environment and the response times of the servers contacted.

Important guidelines:
* Minimum values: It is recommended not to set timeout values that are too short. Values that are too low can cause frequent request failures, even when servers respond correctly but with a slight delay. A minimum value of 5 seconds is recommended, except in very specific cases.
* Maximum values: Conversely, excessively long timeout values can cause program freezes in case of server non-response. It is generally not recommended to exceed 60 seconds.
* Environment adaptation: The optimal timeout value depends on network stability and the response times of the servers contacted. In environments with unstable networks or slow servers, slightly higher values may be necessary.
* Testing and adjustments: It is recommended to test different timeout values to find the best compromise between program responsiveness and robustness to response time variations.

```ìni
[Backup_Mods]
backup_folder = backup_mods
max_backups = 3
modlist_folder = modlist
```
These options define the folder where mod backups will be stored and the maximum number of backups to keep before older ones are overwritten. In case of issues, the original mods can be easily restored. By default, the backup_mods folder will be created in the ModsUpdater directory. You can also set a folder for the exported modlist files.

```ìni
[Game_Version]
user_game_version = None
```
The user_game_version parameter allows you to specify the game version installed by the user.
* If a game version is specified (e.g., user_game_version = 1.20.5), the program will limit mod updates to this maximum version. This ensures that only mods compatible with this game version will be installed, avoiding potential incompatibility issues.
* (default): If the value of user_game_version is set to None or left blank (user_game_version =), the program will download and install the latest available mods, assuming they are compatible with the latest game version.

Version format: It is important to adhere to the version format used by the game (e.g., X.Y.Z). A malformed version can lead to errors.

```ìni
[Mod_Exclusion]
mods = mod01.zip, mod02.zip, mod03.zip
```
The Mod_Exclusion section has been updated. You can now list the filenames of mods to exclude from the update process, separated by commas. Leave this field empty if no mods need to be excluded.
