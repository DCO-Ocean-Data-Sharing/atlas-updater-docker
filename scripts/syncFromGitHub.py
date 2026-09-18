import json
import os
import urllib.request

BASE_URL = "https://raw.githubusercontent.com/DCO-Ocean-Data-Sharing/atlas-updater-docker/refs/heads/automation-test/"

# Get the list of supporting MapServer files to synchronise
map_files_url = BASE_URL + "maps/sync-files.json"

with urllib.request.urlopen(map_files_url) as response:
    map_config = json.load(response)

# Synchronise supporting MapServer files first
for file_name in map_config["files"]:
    file_url = BASE_URL + "maps/" + file_name
    file_destination = "/maps/" + file_name

    os.makedirs(os.path.dirname(file_destination), exist_ok=True)
    urllib.request.urlretrieve(file_url, file_destination)
    print(f"Synchronised maps/{file_name}")

# Synchronise the main MapServer configuration last
urllib.request.urlretrieve(
    BASE_URL + "maps/mapserver.map",
    "/maps/mapserver.map"
)
print("Synchronised maps/mapserver.map")

# Get the list of Python scripts to synchronise
scripts_list_url = BASE_URL + "scripts/scripts.json"

with urllib.request.urlopen(scripts_list_url) as response:
    scripts_config = json.load(response)

# Synchronise each listed Python script
for script_name in scripts_config["scripts"]:
    script_url = BASE_URL + "scripts/" + script_name
    script_destination = "/scripts/" + script_name

    urllib.request.urlretrieve(script_url, script_destination)
    print(f"Synchronised scripts/{script_name}")

print("GitHub synchronisation completed successfully.")
