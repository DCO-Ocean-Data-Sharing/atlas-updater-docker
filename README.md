# Docker Atlas Updater and Synchronisation

A Docker-based approach to keeping background data, MapServer configuration and updater scripts for the UN Ocean Decade Atlas updated and synchronised.

- Authors:
    - [adamml](https://github.com/adamml)
    - [ninaharmse777](https://github.com/ninaharmse777)
    - [mlopezvelosa](https://github.com/mlopezvelosa)
- Version: 1.0.1
    - 1.0.1 adds a bridge between Mapserver WMS and Copernicus WMTS

## Containers

1. mapserver
    - Runs a Mapserver instance to allow Web Map Services to be published for geospatial data that is used in the UN Ocean Decade atlas, but which is originally published in other formats.
1. atlas-update
    - Manages several small Python scripts to keep layers updated, and runs them on start-up and regularly through cron jobs.
1. copernicus-bridge
    - Runs a Python micro-service to act as a bridge between Mapserver WMS calls and Copernicus' WMTS implementation.
    
## Layers managed

Licensing and attribution of the managed layers is handled in the `/maps/mapserver.map` file in this repository

- Last 10 days of Argo float locations from Ifremer Erddap ([source][1])
    - Synchronised by `/scripts/fetchArgo.py`
    - Cron job runs every three hours to synchronise the data
- Ocean Forecasting Systems atlas from Decade Collaborative Centre for Ocean Prediction / Mercator Ocean International ([source][2])
    - Synchronised by `/scripts/fetchOceanPredictionLayer.py`
    - Cron job runs every six hours to synchronise the data
- GlobalCoast pilot sites from CMCC ([source][3])
    - Live connection to remote GeoJSON file
- Ocean Networks Canada: locations of observatories and instruments ([source][4])
    - Live connection to remote GeoJSON data 
- ProtectedSeas Navigator - All Sites from ProtectedSeas ([source][5])
    - Synchronised by `/scripts/fetchProtectedSeas.py`
    - Downloaded in batches and converted to a spatially indexed GeoPackage using GDAL/ogr2ogr
    - GeoPackage is created automatically if not already present and refreshed monthly on the first day of each month
    - Run docker compose up --build on first deployment or after Dockerfile changes. For subsequent starts, docker compose up can be used.
- Copernicus Global ocean low and mid trophic levels biomass content hindcast
    - Live connection via the `copernicus-bridge` container from the Copernicus Marine Web Map Tile Service ([source][6])
    - Layers:
        - Ocean wet mass content of epipelagic micronekton
        - Ocean wet mass content of highly migrant lower mesopelagic micronekton
        - Ocean wet mass content of lower mesopelagic micronekton
        - Ocean wet mass content of migrant lower mesopelagic micronekton
        - Ocean wet mass content of migrant upper mesopelagic micronekton
        - Ocean wet mass content of upper mesopelagic micronekton
        - Net primary productivity of biomass expressed as carbon in sea water
        - Euphotic zone depth
        - Mass content of zooplankton expressed as carbon in sea water
          
## Automated GitHub synchronisation

`/scripts/syncFromGitHub.py` synchronises MapServer configuration and Python updater scripts from the GitHub Pages sitemap every 6 hours.

The sitemap used as the source is:

`https://dco-ocean-data-sharing.github.io/atlas-updater-docker/sitemap.xml`

Files listed in the sitemap under `/maps/` and `/scripts/` are synchronised to the corresponding directories in the running Docker environment.

Supporting MapServer files and Python scripts are synchronised first, with `/maps/mapserver.map` updated last. This ensures that required layer and symbol files are available before the main MapServer configuration changes.

The sitemap replaces the previously maintained `/maps/sync-files.json` and `/scripts/scripts.json` file lists, providing a single source for determining which files should be synchronised.

Changes to files already included in the sitemap can therefore be picked up automatically by the scheduled synchronisation. Changes to `docker-compose.yml` or other Docker configuration still need to be applied to the deployed Docker environment.
- GEBCO Global Bathymetry and Topography - Shaded Relief ([source][7])
    - Live connection to GEBCO’s `GEBCO_LATEST` Web Map Service through `maps/layers/15_gebco_latest_shaded_relief.map`
    - Global shaded-relief bathymetry and land topography; no numerical depth legend; not for navigation
    - GEBCO updates the Latest WMS separately from its annual grid releases; a six-monthly availability check is planned
- Mapping Bad Boats citizen-science observations from The Floating Stories Lab / ReTISS ([source][8])
    - Synchronised by `/scripts/fetchMappingBadBoats.py`
    - Coastal vessel observations, including vessel type, classification and nearby habitat, provided as GeoJSON point features
    - Cron job runs weekly to synchronise new and updated observations
- COSEA citizen-science marine observations from SPOTTERON ([source][9])
    - Synchronised by `/scripts/fetchCOSEA.py`
    - Georeferenced marine observations, including observation dates and category identifiers, provided as GeoJSON point features
    - Cron job runs weekly to synchronise new and updated observations

## Getting started

1. Download the repository
1. Unzip the repository folder and from a terminal, navigate to the root folder
1. Run `docker compose up`

[1]: https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.geoJson?platform_number,project_name,platform_type,latitude,longitude&time%3E%3Dnow-10days&"+time%3Cnow
[2]: https://www.unoceanprediction.org/en/api/atlas/models
[3]: https://protocoast.cmcc.it/globalcoast-pilot-sites/data/pilot_sites.json
[4]: https://services2.arcgis.com/qRqOFxxnwUHOSocZ/arcgis/rest/services/ONCSites_CO2_XYTableToPoint/FeatureServer/0/query?where=1=1&outFields=*&f=geojson
[5]: https://services9.arcgis.com/lm7wE8a9YA9rKfzy/arcgis/rest/services/Navigator_AllSites_010925_attributes/FeatureServer/0
[6]: https://wmts.marine.copernicus.eu/teroWmts/GLOBAL_MULTIYEAR_BGC_001_033/cmems_mod_glo_bgc_my_0.083deg-lmtl_P1D-i_202511?request=GetCapabilities&service=WMTS
[7]: https://www.gebco.net/data-products/gebco-web-services/web-map-service
[8]: https://services-eu1.arcgis.com/APM8FyQ4IgTmRlob/arcgis/rest/services/survey123_523fa2f55e7b42ee8752f33033616991_results/FeatureServer/0
[9]: https://www.spotteron.com/cosea/info
