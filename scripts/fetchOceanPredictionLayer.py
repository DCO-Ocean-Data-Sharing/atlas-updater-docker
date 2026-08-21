# FETCHOCEANPREDICTIONLAYER - collects the Decade Collaborative Centre for Ocean
# Predictions ocean forecasting systems layer for the UN Ocean Decade's Global
# Digital Atlas. The original source is Mercator Ocean International. Some
# reformatting is required as the source data is in a custom JSON format, not
# GeoJSON
#
# :author: Adam Leadbetter (@adamml)
# :date: 2026-08-20
# :version: 1.0.2
#
# Version History
# ---------------
#
# 1.0.2 2026-09-20 Filtered out global models
# 1.0.1 2026-09-19 Added ocean basins to output
# 1.0.0 2026-08-18 Initial version

import urllib.request
import json
import sys


#
# Define a custom exception to elegantly handle global coverage of some models
#
class GlobalModelException(Exception):
    def __init__ (self, message):
        self.message = message
        super().__init__(self.message)
        

#
# Get the Model Data layer from Mercator
#

modelsURL: str = "https://www.unoceanprediction.org/en/api/atlas/models"

models = {"type": "FeatureCollection", "features": []}

try:
    with urllib.request.urlopen(modelsURL, timeout=30) as resp:
        modelsJSON: dict = json.loads(resp.read())['data']
        for model in modelsJSON:
            # Get the Type of System
            typeOfSystem: str = None
            try:
                typeOfSystem = model["type_of_system"][0]["name"]
            except KeyError:
                pass
            # Get the atmospheric model used
            atmosphericModel = None
            try:
                atmosphericModel = model["atmospheric_model"][0]["name"]
            except KeyError:
                pass
            # Get the applications the forecasting sytem is used for
            applications = []
            for application in model["describe_the_main_applicat"]:
                applications.append(application["name"])
            # Get the variables employed
            variablesUsed = []
            try:
                for usedVariable in model["variables_employed"]:
                    variablesUsed.append(usedVariable["name"])
            except KeyError:
                pass
            # Get the essential ocean variables
            essential_ocean_variables = []
            try:
                for eov in model["model_informations"][0]["specify_the_eov"]:
                    essential_ocean_variables.append(eov["name"])
            except KeyError:
                pass
            # Get the organistions associated with the forecasting system
            organisations = []
            for organisation in model["organization_in_charge_of_"]:
                organisations.append(organisation["name"])
            # Get the ocean basins regions of interest associated with the forecasting system
            oceanBasins = []
            try:
                for oceanBasin in model["ocean_basins_regions_of_in"]:

                    # Filter global models
                    if oceanBasin["name"] == "Global":
                        raise GlobalModelException("Global model encountered")
                    oceanBasins.append(oceanBasin["name"])
                
                # Get the geographic bounding box
                bbox = [-90, -180, 90, 180]
                if not model["model_informations"][0]["model_domain_geographical_"]:
                    bbox[0] = model["model_informations"][0]["model_domain_geo_bot_left"]["lat"]
                    bbox[1] = model["model_informations"][0]["model_domain_geo_bot_left"]["lng"]
                    bbox[2] = model["model_informations"][0]["model_domain_geo_top_right"]["lat"]
                    bbox[3] = model["model_informations"][0]["model_domain_geo_top_right"]["lng"]

                # Filter global models
                if bbox[0] == -90 and bbox[1] == -180 and bbox[2] == 90 and bbox[3] == 180:
                    raise GlobalModelException("Global model encountered")
                
                # Build the GeoJSON
                models["features"].append({"type": "Feature",
                           "geometry": {
                               "type": "Polygon",
                               "coordinates": [[
                                   [float(bbox[1]), float(bbox[0])],
                                   [float(bbox[1]), float(bbox[2])],
                                   [float(bbox[3]), float(bbox[2])],
                                   [float(bbox[3]), float(bbox[0])],
                                   [float(bbox[1]), float(bbox[0])]]]},
                            "properties": {
                                "title": model["title"],
                                "dataPolicy": model["data_policy"][0]["name"],
                                "organization": organisations,
                                "otherLinks": model["other_links"],
                                "numericalModel": model["model_informations"][0]["numerical_model"][0]["name"],
                                "atmosphericModel": atmosphericModel,
                                "oceanBasins": oceanBasins,
                                "typeOfSystem": typeOfSystem,
                                "applications": applications,
                                "variablesUsed": variablesUsed,
                                "essentialOceanVariables": essential_ocean_variables}})
            except GlobalModelException as e:
                print(f"Exception encountered: {model['title']} is a global model...")
    with open('/maps/ocean_prediction_atlas.geojson', 'w') as f:
        json.dump(models, f, indent=2) 
except urllib.error.URLError as e:
    print(f"Network error encountered: {e.reason}")
except json.JSONDecodeError:
    print(f"JSON reading error: {e.reason}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: Unable to fetch data from Mercator API")
except PermissionError:
    print(f"Permission denied: Cannot write to output file to disk {e}")
except TypeError as e:
    print(f"Data error: The parsed JSON dictionary contains non-serializable objects: {e}")
except OSError as e:
    print(f"Disk or System error while writing output file: {e}")
