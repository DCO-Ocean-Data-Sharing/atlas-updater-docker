# Atlas Updater - Docker

A Docker-based approach to keeping background data for the UN Ocean Decade Atlas updated

- Author: [adamml](https://github.com/adamml)
- Version: 1.0.0

## Containers

1. mapserver
    - Runs a Mapserver instance to allow Web Map Services to be published for geospatial data that is used in the UN Ocean Decade atlas, but which is originally published in other formats.
1. atlas-update
    - Manages several small Python scripts to keep layers updated, and runs them on start-up and regularly through cron jobs

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
    - GeoPackage is created automatically if not already present and refreshed monthly on the first day of        each month
    - Run docker compose up --build on first deployment or after Dockerfile changes. For subsequent starts,       docker compose up can be used.. 
## Getting started

1. Download the repository
1. Unzip the repository folder and from a terminal, navigate to the root folder
1. Run `docker compose up`

[1]: https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.geoJson?platform_number,project_name,platform_type,latitude,longitude&time%3E%3Dnow-10days&"+time%3Cnow
[2]: https://www.unoceanprediction.org/en/api/atlas/models
[3]: https://protocoast.cmcc.it/globalcoast-pilot-sites/data/pilot_sites.json
[4]: https://services2.arcgis.com/qRqOFxxnwUHOSocZ/arcgis/rest/services/ONCSites_CO2_XYTableToPoint/FeatureServer/0/query?where=1=1&outFields=*&f=geojson
[5]: https://services9.arcgis.com/lm7wE8a9YA9rKfzy/arcgis/rest/services/Navigator_AllSites_010925_attributes/FeatureServer/0
