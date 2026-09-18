# Docker Atlas Updater and Synchronisation

A Docker-based approach to keeping background data, MapServer configuration and updater scripts for the UN Ocean Decade Atlas updated and synchronised.

- Docker implementation author: [adamml](https://github.com/adamml)
- GitHub synchronisation and automation: [ninaharmse777](https://github.com/ninaharmse777)
- Version: 1.0.0

## Containers

1. **mapserver** - Publishes Web Map Services for geospatial data used in the UN Ocean Decade Atlas.
2. **atlas-updater** - Runs Python scripts to keep data updated and synchronises MapServer configuration and approved Python updater scripts from this repository.

## Layers managed

Licensing and attribution of managed layers is handled in `/maps/mapserver.map`.

- **Argo float locations** from Ifremer Erddap ([source][1])
  - Updated by `/scripts/fetchArgo.py` every 3 hours
- **Ocean Forecasting Systems Atlas** from Decade Collaborative Centre for Ocean Prediction / Mercator Ocean International ([source][2])
  - Updated by `/scripts/fetchOceanPredictionLayer.py` every 6 hours
- **GlobalCoast pilot sites** from CMCC ([source][3])
  - Live connection to remote GeoJSON
- **Ocean Networks Canada observatories and instruments** ([source][4])
  - Live connection to remote GeoJSON
- **ProtectedSeas Navigator - All Sites** ([source][5])
  - Updated by `/scripts/fetchProtectedSeas.py` monthly
  - Converted to a spatially indexed GeoPackage using GDAL/ogr2ogr

## Automated GitHub synchronisation

`/scripts/syncFromGitHub.py` synchronises MapServer configuration and Python updater scripts from this repository every 6 hours.

MapServer supporting files to synchronise are listed in:

`/maps/sync-files.json`

Python updater scripts to synchronise are listed in:

`/scripts/scripts.json`

MapServer supporting files are downloaded first and `/maps/mapserver.map` is updated last. This ensures that required layer and symbol files are available before the main configuration changes.

The synchronisation uses only the Python standard library and adds no new dependencies. Existing dependencies, such as GDAL for ProtectedSeas, remain unchanged.

## Practical examples for future handover

Once the synchronisation setup is deployed, most routine Atlas updates can be managed through the repository without rebuilding or redeploying the Docker containers.

### Example 1: Update an existing MapServer layer

If the configuration of an existing layer needs to change, update its `.map` file.

For example:

`/maps/layers/03_ocean_networks_canada_observatories.map`

Because the file is already listed in `/maps/sync-files.json`, the updated version will be synchronised automatically.

### Example 2: Add a new MapServer layer

To add a new layer, for example `06_new_layer.map`:

1. Add the new file under `/maps/layers`
2. Add `layers/06_new_layer.map` to `/maps/sync-files.json`
3. Reference the new layer file in `/maps/mapserver.map`

The new configuration will then be picked up through the scheduled synchronisation.

### Example 3: Update an existing data fetcher

If an existing data source changes, update its corresponding fetch script.

For example:

`/scripts/fetchArgo.py`

Because the script is already listed in `/scripts/scripts.json`, the updated version will be synchronised automatically. Its existing cron schedule will continue to run as normal.

### Adding a new scheduled data source

If a completely new data source requires its own Python fetch script and schedule, add the script to `/scripts`, list it in `/scripts/scripts.json`, and add its schedule to `docker-compose.yml`.

Changes to `docker-compose.yml` need to be applied to the deployed Docker environment.

## Current schedules

- GitHub synchronisation: every 6 hours
- Argo floats: every 3 hours
- Ocean Forecasting Systems Atlas: every 6 hours
- ProtectedSeas Navigator: monthly on the first day of the month

## Getting started

1. Download the repository
1. Unzip the repository folder and from a terminal, navigate to the root folder
1. Run `docker compose up`

[1]: https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.geoJson?platform_number,project_name,platform_type,latitude,longitude&time%3E%3Dnow-10days&"+time%3Cnow
[2]: https://www.unoceanprediction.org/en/api/atlas/models
[3]: https://protocoast.cmcc.it/globalcoast-pilot-sites/data/pilot_sites.json
[4]: https://services2.arcgis.com/qRqOFxxnwUHOSocZ/arcgis/rest/services/ONCSites_CO2_XYTableToPoint/FeatureServer/0/query?where=1=1&outFields=*&f=geojson
[5]: https://services9.arcgis.com/lm7wE8a9YA9rKfzy/arcgis/rest/services/Navigator_AllSites_010925_attributes/FeatureServer/0
