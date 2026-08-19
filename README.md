# Atlas Updater - Docker

A Docker-based approach to keeping background data for the UN Ocean Decade Atlas updated

## Containers

- Author: [adamml]

1. mapserver
    - Runs a Mapserver instance to allow Web Map Services to be published for geospatial data that is used in the UN Ocean Decade atlas, but which is originally published in other formats.
1. atlas-update
    - Manages several small Python scripts to keep layers updated, and runs them on start-up and regularly through cron jobs

## Layers managed

- Last 10 days of Argo float locations from Ifremer Erddap ([source][1])
    - Synchronised by /scripts/fetchArgo.py
    - Cron job runs every three hours to synchronise the data
- Ocean Forecasting Systems atlas from Decade Collaborative Centre for Ocean Prediction / Mercator Ocean International ([source][2])
    - Synchronised by /scripts/fetchOceanPredictionLayer.py
    - Cron job runs every six hours to synchronise the data
- GlobalCoast pilot sites from CMCC ([source][3])
    - Live connection to remote GeoJSON file
    
## Getting started

1. Download the repository
1. Unzip the repository folder and from a terminal, navigate to the root folder
1. Run `docker compose up`

[1]: https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.geoJson?platform_number,project_name,platform_type,latitude,longitude&time%3E%3Dnow-10days&" +time%3Cnow
[2]: https://www.unoceanprediction.org/en/api/atlas/models
[3]: https://protocoast.cmcc.it/globalcoast-pilot-sites/data/pilot_sites.json